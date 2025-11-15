"""
Portfolio Optimization Environment

OpenAI Gym-compatible environment for training RL agents on portfolio optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import gymnasium as gym
from gymnasium import spaces


class PortfolioEnv(gym.Env):
    """
    Portfolio optimization environment for RL agents.
    
    State: Portfolio allocation, market conditions, performance metrics
    Action: Rebalance portfolio (new allocation weights)
    Reward: Based on objective (Sharpe, volatility, income, etc.)
    """
    
    def __init__(
        self,
        etf_data: Dict[str, pd.DataFrame],
        etf_list: List[str],
        initial_capital: float = 100000,
        objective: str = 'sharpe',
        transaction_cost: float = 0.001,  # 0.1%
        rebalance_frequency: int = 5,  # days
        max_steps: int = 252,  # 1 year
        lookback_window: int = 60  # days for features
    ):
        """
        Initialize portfolio environment.
        
        Args:
            etf_data: Dict of {ticker: DataFrame} with OHLCV data
            etf_list: List of ETF tickers to trade
            initial_capital: Starting capital
            objective: Optimization objective ('sharpe', 'volatility', 'income', 'alpha')
            transaction_cost: Cost per trade as fraction
            rebalance_frequency: Days between rebalancing
            max_steps: Maximum episode length
            lookback_window: Days of history for state features
        """
        super().__init__()
        
        self.etf_data = etf_data
        self.etf_list = etf_list
        self.n_assets = len(etf_list)
        self.initial_capital = initial_capital
        self.objective = objective
        self.transaction_cost = transaction_cost
        self.rebalance_frequency = rebalance_frequency
        self.max_steps = max_steps
        self.lookback_window = lookback_window
        
        # Validate data
        self._validate_data()
        
        # State space: [portfolio_weights, returns, volatilities, correlations, ...]
        state_dim = (
            self.n_assets +  # current weights
            self.n_assets +  # recent returns
            self.n_assets +  # volatilities
            1 +  # portfolio value
            1 +  # days remaining
            1    # current drawdown
        )
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(state_dim,), dtype=np.float32
        )
        
        # Action space: portfolio weights (sum to 1)
        self.action_space = spaces.Box(
            low=0.0, high=1.0, shape=(self.n_assets,), dtype=np.float32
        )
        
        # Episode state
        self.current_step = 0
        self.portfolio_value = initial_capital
        self.portfolio_weights = np.zeros(self.n_assets)
        self.portfolio_history = []
        self.peak_value = initial_capital
        
    def _validate_data(self):
        """Validate ETF data has sufficient history"""
        for ticker in self.etf_list:
            if ticker not in self.etf_data:
                raise ValueError(f"Missing data for {ticker}")
            
            df = self.etf_data[ticker]
            if len(df) < self.lookback_window + self.max_steps:
                raise ValueError(
                    f"{ticker} has insufficient data: {len(df)} rows, "
                    f"need {self.lookback_window + self.max_steps}"
                )
    
    def reset(self, start_idx: Optional[int] = None) -> np.ndarray:
        """
        Reset environment to start of new episode.
        
        Args:
            start_idx: Optional starting index in data (for reproducibility)
        
        Returns:
            Initial state observation
        """
        # Random starting point if not specified
        if start_idx is None:
            # Calculate max start index with safety check
            min_data_len = min(len(self.etf_data[ticker]) for ticker in self.etf_list)
            max_start = min_data_len - self.max_steps - self.lookback_window
            
            # Ensure we have enough data
            if max_start <= self.lookback_window:
                # Not enough data - use shorter episode
                self.max_steps = min(50, min_data_len - self.lookback_window - 10)
                max_start = min_data_len - self.max_steps - self.lookback_window
                
                if max_start <= self.lookback_window:
                    raise ValueError(
                        f"Insufficient data: need at least {self.lookback_window + self.max_steps + 10} rows, "
                        f"but shortest ETF has only {min_data_len} rows"
                    )
            
            self.start_idx = np.random.randint(self.lookback_window, max_start)
        else:
            self.start_idx = start_idx
        
        self.current_step = 0
        self.portfolio_value = self.initial_capital
        self.portfolio_weights = np.ones(self.n_assets) / self.n_assets  # Equal weight start
        self.portfolio_history = [self.portfolio_value]
        self.peak_value = self.initial_capital
        
        # Return (observation, info) for Gymnasium compatibility
        return self._get_state(), {}
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in environment.
        
        Args:
            action: New portfolio weights (will be normalized)
        
        Returns:
            (state, reward, done, info)
        """
        # Normalize action to sum to 1
        action = np.clip(action, 0, 1)
        action = action / (action.sum() + 1e-8)
        
        # Calculate transaction costs
        weight_change = np.abs(action - self.portfolio_weights).sum()
        transaction_cost = weight_change * self.transaction_cost * self.portfolio_value
        
        # Update weights
        old_weights = self.portfolio_weights.copy()
        self.portfolio_weights = action
        
        # Simulate forward for rebalance_frequency days
        returns = []
        for _ in range(self.rebalance_frequency):
            if self.current_step >= self.max_steps:
                break
            
            # Get returns for this day
            day_returns = self._get_day_returns(self.current_step)
            portfolio_return = np.dot(self.portfolio_weights, day_returns)
            returns.append(portfolio_return)
            
            # Update portfolio value
            self.portfolio_value *= (1 + portfolio_return)
            self.current_step += 1
        
        # Apply transaction cost
        self.portfolio_value -= transaction_cost
        
        # Track history
        self.portfolio_history.append(self.portfolio_value)
        self.peak_value = max(self.peak_value, self.portfolio_value)
        
        # Calculate reward based on objective
        reward = self._calculate_reward(returns)
        
        # Check if done
        terminated = self.current_step >= self.max_steps
        truncated = False  # We don't use truncation in this environment
        
        # Info dict
        info = {
            'portfolio_value': self.portfolio_value,
            'portfolio_return': (self.portfolio_value / self.initial_capital) - 1,
            'transaction_cost': transaction_cost,
            'weights': self.portfolio_weights.copy()
        }
        
        # Return (observation, reward, terminated, truncated, info) for Gymnasium compatibility
        return self._get_state(), reward, terminated, truncated, info
    
    def _get_day_returns(self, step: int) -> np.ndarray:
        """Get returns for all ETFs for a specific day"""
        returns = np.zeros(self.n_assets)
        
        for i, ticker in enumerate(self.etf_list):
            df = self.etf_data[ticker]
            idx = self.start_idx + step
            
            if idx < len(df) and idx > 0:
                returns[i] = (df.iloc[idx]['Close'] / df.iloc[idx-1]['Close']) - 1
        
        return returns
    
    def _get_state(self) -> np.ndarray:
        """Get current state observation"""
        # Portfolio weights
        weights = self.portfolio_weights
        
        # Recent returns (last 20 days)
        recent_returns = np.zeros(self.n_assets)
        for i, ticker in enumerate(self.etf_list):
            df = self.etf_data[ticker]
            start = self.start_idx + self.current_step - 20
            end = self.start_idx + self.current_step
            if start >= 0 and end < len(df):
                prices = df.iloc[start:end]['Close'].values
                if len(prices) > 1:
                    recent_returns[i] = (prices[-1] / prices[0]) - 1
        
        # Volatilities (last 60 days)
        volatilities = np.zeros(self.n_assets)
        for i, ticker in enumerate(self.etf_list):
            df = self.etf_data[ticker]
            start = self.start_idx + self.current_step - 60
            end = self.start_idx + self.current_step
            if start >= 0 and end < len(df):
                returns = df.iloc[start:end]['Close'].pct_change().dropna()
                if len(returns) > 1:
                    volatilities[i] = returns.std() * np.sqrt(252)
        
        # Portfolio metrics
        portfolio_value_norm = self.portfolio_value / self.initial_capital
        days_remaining = (self.max_steps - self.current_step) / self.max_steps
        drawdown = (self.peak_value - self.portfolio_value) / self.peak_value if self.peak_value > 0 else 0
        
        # Concatenate all features
        state = np.concatenate([
            weights,
            recent_returns,
            volatilities,
            [portfolio_value_norm],
            [days_remaining],
            [drawdown]
        ])
        
        return state.astype(np.float32)
    
    def _calculate_reward(self, returns: List[float]) -> float:
        """Calculate reward based on objective"""
        if len(returns) == 0:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = returns_array.mean()
        std_return = returns_array.std() + 1e-8
        
        if self.objective == 'sharpe':
            # Maximize Sharpe ratio
            sharpe = (mean_return - 0.0001) / std_return  # 0.0001 = daily risk-free rate (~2.5% annual)
            reward = sharpe * 10
            
        elif self.objective == 'volatility':
            # Minimize volatility
            reward = -std_return * 100 + mean_return * 10
            
        elif self.objective == 'income':
            # Maximize returns (proxy for income)
            reward = mean_return * 100
            
        elif self.objective == 'alpha':
            # Maximize returns with penalty for high volatility
            reward = mean_return * 100 - std_return * 50
            
        else:
            raise ValueError(f"Unknown objective: {self.objective}")
        
        # Penalty for large drawdowns
        drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
        if drawdown > 0.1:
            reward -= drawdown * 50
        
        return reward
    
    def render(self, mode='human'):
        """Render environment (optional)"""
        if mode == 'human':
            print(f"Step: {self.current_step}/{self.max_steps}")
            print(f"Portfolio Value: ${self.portfolio_value:,.2f}")
            print(f"Return: {(self.portfolio_value/self.initial_capital - 1)*100:.2f}%")
            print(f"Weights: {self.portfolio_weights}")

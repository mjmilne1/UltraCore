"""Reinforcement Learning Trading Environment"""
import gym
from gym import spaces
import numpy as np
from typing import Dict, Tuple

from ..client import OpenMarketsClient


class TradingEnvironment(gym.Env):
    """
    OpenAI Gym environment for RL trading agents.
    
    State space:
    - Portfolio positions
    - Account balance
    - Market data (prices, volumes, technical indicators)
    - Order book depth
    
    Action space:
    - Buy/Sell/Hold for each position
    - Position size (continuous)
    
    Reward function:
    - Risk-adjusted returns (Sharpe ratio)
    - Transaction cost penalties
    - Drawdown penalties
    """
    
    def __init__(
        self,
        client: OpenMarketsClient,
        account_id: str,
        symbols: List[str],
        initial_balance: float = 100000.0
    ):
        super(TradingEnvironment, self).__init__()
        
        self.client = client
        self.account_id = account_id
        self.symbols = symbols
        self.initial_balance = initial_balance
        
        # State space: [balance, positions..., prices..., indicators...]
        self.observation_space = spaces.Box(
            low=0,
            high=np.inf,
            shape=(1 + len(symbols) * 10,),
            dtype=np.float32
        )
        
        # Action space: [action_type, symbol_index, quantity]
        # action_type: 0=hold, 1=buy, 2=sell
        self.action_space = spaces.Box(
            low=np.array([0, 0, 0]),
            high=np.array([2, len(symbols)-1, 1.0]),
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self) -> np.ndarray:
        """Reset environment to initial state."""
        self.balance = self.initial_balance
        self.positions = {symbol: 0 for symbol in self.symbols}
        self.episode_return = 0.0
        self.step_count = 0
        
        return self._get_observation()
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one trading step.
        
        Args:
            action: [action_type, symbol_index, quantity_fraction]
        
        Returns:
            observation, reward, done, info
        """
        action_type = int(action[0])  # 0=hold, 1=buy, 2=sell
        symbol_index = int(action[1])
        quantity_fraction = action[2]
        
        symbol = self.symbols[symbol_index]
        
        # Get current market data
        market_data = await self.client.get_market_data(symbol)
        current_price = market_data.last_price
        
        # Execute action
        reward = 0.0
        if action_type == 1:  # Buy
            # Calculate quantity based on available balance
            max_quantity = int((self.balance * quantity_fraction) / current_price)
            if max_quantity > 0:
                cost = max_quantity * current_price
                commission = cost * 0.0005  # 0.05% commission
                
                if self.balance >= (cost + commission):
                    self.positions[symbol] += max_quantity
                    self.balance -= (cost + commission)
                    
                    # Reward based on immediate price movement (simplified)
                    reward = -commission  # Penalize transaction costs
        
        elif action_type == 2:  # Sell
            # Calculate quantity to sell
            max_quantity = int(self.positions[symbol] * quantity_fraction)
            if max_quantity > 0:
                proceeds = max_quantity * current_price
                commission = proceeds * 0.0005
                
                self.positions[symbol] -= max_quantity
                self.balance += (proceeds - commission)
                
                reward = -commission
        
        # Calculate portfolio value
        portfolio_value = self.balance
        for sym, qty in self.positions.items():
            if qty > 0:
                md = await self.client.get_market_data(sym)
                portfolio_value += qty * md.last_price
        
        # Calculate reward: change in portfolio value
        reward += (portfolio_value - self.initial_balance) / self.initial_balance
        
        self.episode_return += reward
        self.step_count += 1
        
        # Episode ends after 252 steps (1 trading year)
        done = self.step_count >= 252
        
        observation = self._get_observation()
        info = {
            "portfolio_value": portfolio_value,
            "balance": self.balance,
            "positions": self.positions
        }
        
        return observation, reward, done, info
    
    def _get_observation(self) -> np.ndarray:
        """Get current environment state."""
        obs = [self.balance]
        
        for symbol in self.symbols:
            # Position quantity
            obs.append(self.positions[symbol])
            
            # Market data (would fetch real data in production)
            obs.extend([0.0] * 9)  # Placeholder for price, indicators
        
        return np.array(obs, dtype=np.float32)

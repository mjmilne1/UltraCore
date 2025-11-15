"""
ETF Data Provider for UltraOptimiser
Provides real ASX ETF historical data for portfolio optimization
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
import logging

from ultracore.market_data.etf.etf_data_system import get_etf_system
from ultracore.market_data.etf.data_mesh.etf_data_product import ETFDataProduct


logger = logging.getLogger(__name__)


class ETFDataProvider:
    """
    Provides ETF market data for UltraOptimiser
    
    Features:
    - Historical returns and volatility
    - Correlation matrices
    - Risk metrics (Sharpe, Sortino, max drawdown)
    - Expected returns estimation
    - Covariance matrices for optimization
    """
    
    def __init__(self, data_dir: str = "/data/etf"):
        """
        Initialize ETF data provider
        
        Args:
            data_dir: Directory where ETF data is stored
        """
        from pathlib import Path
        
        # Support both event-sourced system and direct Parquet loading
        self.data_dir = Path(data_dir)
        self.historical_dir = self.data_dir / "historical"
        
        # Try to initialize event sourcing system
        try:
            self.system = get_etf_system(data_dir=str(self.data_dir))
            self.data_product = self.system.get_data_product()
            self.use_event_sourcing = True
            logger.info("ETF Data Provider initialized with event sourcing")
        except Exception as e:
            logger.warning(f"Event sourcing not available: {e}. Using direct Parquet loading.")
            self.system = None
            self.data_product = None
            self.use_event_sourcing = False
        
        # Cache for frequently accessed data
        self._cache: Dict[str, pd.DataFrame] = {}
        
        # Discover available ETFs from Parquet files
        if self.historical_dir.exists():
            self.available_etfs = [f.stem for f in self.historical_dir.glob("*.parquet")]
            logger.info(f"Found {len(self.available_etfs)} ETFs in {self.historical_dir}")
        else:
            self.available_etfs = []
            logger.warning(f"Historical data directory not found: {self.historical_dir}")
        
    def load_etf_data(self, ticker: str) -> pd.DataFrame:
        """
        Load ETF data from Parquet file or event sourcing system
        
        Args:
            ticker: ETF ticker (without .AX suffix)
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume
        """
        # Check cache first
        if ticker in self._cache:
            return self._cache[ticker]
        
        # Try loading from Parquet file
        file_path = self.historical_dir / f"{ticker}.parquet"
        
        if file_path.exists():
            try:
                df = pd.read_parquet(file_path)
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date').sort_index()
                
                # Cache it
                self._cache[ticker] = df
                
                return df
            except Exception as e:
                logger.error(f"Error loading Parquet data for {ticker}: {e}")
        
        # Fallback to event sourcing system if available
        if self.use_event_sourcing and self.data_product:
            try:
                df = self.data_product.get_price_data_df(ticker)
                if not df.empty:
                    df = df.set_index('date').sort_index()
                    self._cache[ticker] = df
                    return df
            except Exception as e:
                logger.error(f"Error loading from event sourcing for {ticker}: {e}")
        
        logger.warning(f"No data found for {ticker}")
        return pd.DataFrame()
    
    def get_returns(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "daily"
    ) -> pd.DataFrame:
        """
        Get returns for multiple ETFs
        
        Args:
            tickers: List of ETF tickers
            start_date: Start date (None = 1 year ago)
            end_date: End date (None = today)
            period: 'daily', 'weekly', 'monthly'
        
        Returns:
            DataFrame with returns for each ticker
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()
        
        returns_dict = {}
        
        for ticker in tickers:
            df = self.load_etf_data(ticker)
            
            if df.empty:
                logger.warning(f"No data for {ticker}")
                continue
            
            # Filter by date range
            df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
            
            if df.empty:
                continue
            
            # Calculate returns using Adj Close
            returns = df['Adj Close'].pct_change().dropna()
            
            # Resample if needed
            if period == "weekly":
                returns = returns.resample('W').apply(lambda x: (1 + x).prod() - 1)
            elif period == "monthly":
                returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            returns_dict[ticker] = returns
        
        if not returns_dict:
            return pd.DataFrame()
        
        # Combine into single DataFrame
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()  # Remove rows with missing data
        
        return returns_df
    
    def calculate_expected_returns(
        self,
        tickers: List[str],
        method: str = "historical_mean",
        lookback_years: int = 3
    ) -> Dict[str, float]:
        """
        Calculate expected returns for ETFs
        
        Args:
            tickers: List of ETF tickers
            method: 'historical_mean', 'capm', 'exponential'
            lookback_years: Years of historical data to use
        
        Returns:
            Dictionary of ticker -> expected annual return
        """
        start_date = date.today() - timedelta(days=lookback_years * 365)
        returns_df = self.get_returns(tickers, start_date=start_date)
        
        if returns_df.empty:
            return {ticker: 0.08 for ticker in tickers}  # Default 8%
        
        expected_returns = {}
        
        if method == "historical_mean":
            # Annualized mean return
            for ticker in returns_df.columns:
                mean_daily = returns_df[ticker].mean()
                annual_return = (1 + mean_daily) ** 252 - 1  # 252 trading days
                expected_returns[ticker] = float(annual_return)
        
        elif method == "exponential":
            # Exponentially weighted mean (more weight on recent data)
            for ticker in returns_df.columns:
                ewm_return = returns_df[ticker].ewm(span=60).mean().iloc[-1]
                annual_return = (1 + ewm_return) ** 252 - 1
                expected_returns[ticker] = float(annual_return)
        
        else:
            # Default to historical mean
            return self.calculate_expected_returns(tickers, "historical_mean", lookback_years)
        
        return expected_returns
    
    def calculate_covariance_matrix(
        self,
        tickers: List[str],
        lookback_years: int = 3
    ) -> pd.DataFrame:
        """
        Calculate covariance matrix for portfolio optimization
        
        Args:
            tickers: List of ETF tickers
            lookback_years: Years of historical data
        
        Returns:
            Covariance matrix (annualized)
        """
        start_date = date.today() - timedelta(days=lookback_years * 365)
        returns_df = self.get_returns(tickers, start_date=start_date)
        
        if returns_df.empty:
            # Return identity matrix if no data
            return pd.DataFrame(
                np.eye(len(tickers)) * 0.04,  # 20% volatility
                index=tickers,
                columns=tickers
            )
        
        # Calculate covariance and annualize
        cov_matrix = returns_df.cov() * 252  # 252 trading days
        
        return cov_matrix
    
    def calculate_correlation_matrix(
        self,
        tickers: List[str],
        lookback_years: int = 3
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for diversification analysis
        
        Args:
            tickers: List of ETF tickers
            lookback_years: Years of historical data
        
        Returns:
            Correlation matrix
        """
        start_date = date.today() - timedelta(days=lookback_years * 365)
        returns_df = self.get_returns(tickers, start_date=start_date)
        
        if returns_df.empty:
            return pd.DataFrame(
                np.eye(len(tickers)),
                index=tickers,
                columns=tickers
            )
        
        return returns_df.corr()
    
    def calculate_risk_metrics(
        self,
        ticker: str,
        lookback_years: int = 3
    ) -> Dict[str, float]:
        """
        Calculate comprehensive risk metrics for an ETF
        
        Returns:
            Dictionary with volatility, sharpe, sortino, max_drawdown, etc.
        """
        start_date = date.today() - timedelta(days=lookback_years * 365)
        returns_df = self.get_returns([ticker], start_date=start_date)
        
        if returns_df.empty or ticker not in returns_df.columns:
            return {
                "volatility": 0.20,
                "sharpe_ratio": 0.5,
                "sortino_ratio": 0.6,
                "max_drawdown": -0.20,
                "var_95": -0.02,
                "cvar_95": -0.03,
                "mean_return": 0.08
            }
        
        returns = returns_df[ticker].dropna()
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 3% risk-free rate)
        risk_free_rate = 0.03
        excess_returns = returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else volatility
        sortino_ratio = excess_returns / downside_std if downside_std > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (95% confidence)
        var_95 = returns.quantile(0.05)
        
        # Conditional Value at Risk (CVaR)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Mean return (annualized)
        mean_return = returns.mean() * 252
        
        return {
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "max_drawdown": float(max_drawdown),
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "mean_return": float(mean_return)
        }
    
    def get_efficient_frontier_data(
        self,
        tickers: List[str],
        lookback_years: int = 3,
        num_portfolios: int = 100
    ) -> Dict[str, List]:
        """
        Generate data for efficient frontier visualization
        
        Args:
            tickers: List of ETF tickers
            lookback_years: Years of historical data
            num_portfolios: Number of random portfolios to generate
        
        Returns:
            Dictionary with returns, volatilities, sharpe_ratios, weights
        """
        # Get expected returns and covariance
        expected_returns = self.calculate_expected_returns(tickers, lookback_years=lookback_years)
        cov_matrix = self.calculate_covariance_matrix(tickers, lookback_years=lookback_years)
        
        returns_list = []
        volatilities_list = []
        sharpe_ratios_list = []
        weights_list = []
        
        risk_free_rate = 0.03
        
        # Generate random portfolios
        for _ in range(num_portfolios):
            # Random weights
            weights = np.random.random(len(tickers))
            weights /= weights.sum()
            
            # Portfolio return
            portfolio_return = sum(weights[i] * expected_returns[ticker] 
                                 for i, ticker in enumerate(tickers))
            
            # Portfolio volatility
            portfolio_variance = np.dot(weights, np.dot(cov_matrix.values, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Sharpe ratio
            sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            returns_list.append(portfolio_return)
            volatilities_list.append(portfolio_volatility)
            sharpe_ratios_list.append(sharpe)
            weights_list.append(weights.tolist())
        
        return {
            "returns": returns_list,
            "volatilities": volatilities_list,
            "sharpe_ratios": sharpe_ratios_list,
            "weights": weights_list,
            "tickers": tickers
        }
    
    def optimize_portfolio_mean_variance(
        self,
        tickers: List[str],
        target_return: Optional[float] = None,
        risk_budget: Optional[float] = None,
        lookback_years: int = 3
    ) -> Dict[str, any]:
        """
        Mean-variance portfolio optimization
        
        Args:
            tickers: List of ETF tickers
            target_return: Target annual return (None = maximize Sharpe)
            risk_budget: Maximum volatility allowed
            lookback_years: Years of historical data
        
        Returns:
            Optimal weights and portfolio metrics
        """
        from scipy.optimize import minimize
        
        # Get data
        expected_returns = self.calculate_expected_returns(tickers, lookback_years=lookback_years)
        cov_matrix = self.calculate_covariance_matrix(tickers, lookback_years=lookback_years)
        
        returns_array = np.array([expected_returns[t] for t in tickers])
        
        num_assets = len(tickers)
        
        # Objective: minimize negative Sharpe ratio (= maximize Sharpe)
        def objective(weights):
            portfolio_return = np.dot(weights, returns_array)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix.values, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            sharpe = (portfolio_return - 0.03) / portfolio_volatility
            return -sharpe  # Minimize negative = maximize
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]
        
        if target_return is not None:
            constraints.append({
                'type': 'eq',
                'fun': lambda w: np.dot(w, returns_array) - target_return
            })
        
        if risk_budget is not None:
            constraints.append({
                'type': 'ineq',
                'fun': lambda w: risk_budget - np.sqrt(np.dot(w, np.dot(cov_matrix.values, w)))
            })
        
        # Bounds: 0 <= weight <= 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(num_assets))
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / num_assets] * num_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        optimal_weights = result.x
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(optimal_weights, returns_array)
        portfolio_variance = np.dot(optimal_weights, np.dot(cov_matrix.values, optimal_weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility
        
        return {
            "optimal_weights": {ticker: float(weight) for ticker, weight in zip(tickers, optimal_weights)},
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "optimization_success": result.success,
            "optimization_message": result.message
        }
    
    def get_available_etfs(self) -> List[str]:
        """Get list of all available ETF tickers"""
        if self.use_event_sourcing and self.data_product:
            return self.data_product.get_all_tickers()
        return self.available_etfs
    
    def check_data_availability(self, tickers: List[str]) -> Dict[str, bool]:
        """Check which tickers have data available"""
        availability = {}
        for ticker in tickers:
            # Check Parquet file first
            file_path = self.historical_dir / f"{ticker}.parquet"
            if file_path.exists():
                availability[ticker] = True
            elif self.use_event_sourcing and self.data_product:
                # Fallback to event sourcing
                etf = self.data_product.get_etf(ticker)
                availability[ticker] = etf is not None and len(etf.price_history) > 0
            else:
                availability[ticker] = False
        return availability
    
    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get latest closing prices for ETFs"""
        prices = {}
        for ticker in tickers:
            df = self.load_etf_data(ticker)
            if not df.empty:
                prices[ticker] = float(df['Close'].iloc[-1])
        return prices

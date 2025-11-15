"""
ETF Data Provider for UltraOptimiser - Manus Data Integration
Provides real ASX ETF historical data from Manus-collected Parquet files
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ETFDataProviderManus:
    """
    Provides ETF market data for UltraOptimiser using Manus-collected data
    
    Features:
    - Loads data from Parquet files (133 ASX ETFs)
    - Historical returns and volatility
    - Correlation matrices
    - Risk metrics (Sharpe, Sortino, max drawdown)
    - Expected returns estimation
    - Covariance matrices for optimization
    - Mean-variance portfolio optimization
    """
    
    def __init__(self, data_dir: str = "data/etf/historical"):
        """
        Initialize ETF data provider
        
        Args:
            data_dir: Directory where Parquet files are stored
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")
        
        # Cache for loaded data
        self._cache: Dict[str, pd.DataFrame] = {}
        
        # Discover available ETFs
        self.available_etfs = self._discover_etfs()
        logger.info(f"ETF Data Provider initialized with {len(self.available_etfs)} ETFs")
    
    def _discover_etfs(self) -> List[str]:
        """Discover available ETFs from Parquet files"""
        etfs = []
        for file in self.data_dir.glob("*.parquet"):
            etfs.append(file.stem)  # Filename without extension
        return sorted(etfs)
    
    def load_etf_data(self, ticker: str) -> pd.DataFrame:
        """
        Load ETF data from Parquet file
        
        Args:
            ticker: ETF ticker (without .AX suffix)
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume
        """
        # Check cache first
        if ticker in self._cache:
            return self._cache[ticker]
        
        # Load from file
        file_path = self.data_dir / f"{ticker}.parquet"
        
        if not file_path.exists():
            logger.warning(f"Data file not found for {ticker}")
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date').sort_index()
            
            # Cache it
            self._cache[ticker] = df
            
            return df
        except Exception as e:
            logger.error(f"Error loading data for {ticker}: {e}")
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
            method: 'historical_mean', 'exponential'
            lookback_years: Years of historical data to use
        
        Returns:
            Dictionary of ticker -> expected annual return
        """
        start_date = date.today() - timedelta(days=lookback_years * 365)
        returns_df = self.get_returns(tickers, start_date=start_date)
        
        if returns_df.empty:
            logger.warning("No returns data available, using default 8%")
            return {ticker: 0.08 for ticker in tickers}
        
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
            logger.warning("No returns data, using default covariance")
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
                "cvar_95": -0.03
            }
        
        returns = returns_df[ticker].dropna()
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 3% risk-free rate)
        risk_free_rate = 0.03
        mean_return = returns.mean() * 252
        excess_returns = mean_return - risk_free_rate
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
        
        return {
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "max_drawdown": float(max_drawdown),
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "mean_return": float(mean_return)
        }
    
    def optimize_portfolio_mean_variance(
        self,
        tickers: List[str],
        risk_budget: float = 0.6,
        lookback_years: int = 3,
        target_return: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Optimize portfolio using mean-variance optimization
        
        Args:
            tickers: List of ETF tickers
            risk_budget: Risk tolerance (0-1, higher = more risk)
            lookback_years: Years of historical data
            target_return: Target annual return (None = maximize Sharpe)
        
        Returns:
            Dictionary with optimal_weights, expected_return, volatility, sharpe_ratio
        """
        # Get expected returns and covariance
        expected_returns = self.calculate_expected_returns(tickers, lookback_years=lookback_years)
        cov_matrix = self.calculate_covariance_matrix(tickers, lookback_years=lookback_years)
        
        # Convert to numpy arrays
        returns_array = np.array([expected_returns[t] for t in tickers])
        cov_array = cov_matrix.values
        
        # Simple optimization: maximize Sharpe ratio
        # Using scipy.optimize would be better, but keeping it simple
        
        num_assets = len(tickers)
        num_portfolios = 10000
        
        best_sharpe = -np.inf
        best_weights = None
        best_return = 0
        best_vol = 0
        
        risk_free_rate = 0.03
        
        for _ in range(num_portfolios):
            # Random weights
            weights = np.random.random(num_assets)
            weights /= weights.sum()
            
            # Portfolio metrics
            port_return = np.dot(weights, returns_array)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_array, weights)))
            
            # Apply risk budget constraint (target volatility)
            target_vol = 0.10 + (risk_budget * 0.20)  # 10% to 30% volatility
            
            # Sharpe ratio
            sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0
            
            # Check if this is better and within risk budget
            if sharpe > best_sharpe and port_vol <= target_vol * 1.2:
                best_sharpe = sharpe
                best_weights = weights
                best_return = port_return
                best_vol = port_vol
        
        # If no solution found, use equal weights
        if best_weights is None:
            best_weights = np.ones(num_assets) / num_assets
            best_return = np.dot(best_weights, returns_array)
            best_vol = np.sqrt(np.dot(best_weights.T, np.dot(cov_array, best_weights)))
            best_sharpe = (best_return - risk_free_rate) / best_vol if best_vol > 0 else 0
        
        # Convert to dictionary
        optimal_weights = {ticker: float(weight) for ticker, weight in zip(tickers, best_weights)}
        
        return {
            "optimal_weights": optimal_weights,
            "expected_return": float(best_return),
            "volatility": float(best_vol),
            "sharpe_ratio": float(best_sharpe),
            "tickers": tickers
        }
    
    def check_data_availability(self, tickers: List[str]) -> Dict[str, bool]:
        """Check which ETFs have data available"""
        availability = {}
        for ticker in tickers:
            file_path = self.data_dir / f"{ticker}.parquet"
            availability[ticker] = file_path.exists()
        return availability
    
    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get latest closing prices for ETFs"""
        prices = {}
        for ticker in tickers:
            df = self.load_etf_data(ticker)
            if not df.empty:
                prices[ticker] = float(df['Close'].iloc[-1])
        return prices

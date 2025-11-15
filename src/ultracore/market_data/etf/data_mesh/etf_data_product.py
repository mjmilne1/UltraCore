"""
ETF Data Product - Data Mesh Implementation
Treats ETF historical data as a first-class data product
with ownership, quality guarantees, and discoverability
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from uuid import UUID
import pandas as pd
import numpy as np

from ultracore.data_mesh.products.base import DataProduct
from ultracore.market_data.etf.aggregates.etf_aggregate import ETFAggregate, ETFPriceData


@dataclass
class ETFDataQuality:
    """Data quality metrics specific to ETF data"""
    completeness: float  # % of trading days with data
    timeliness: float    # Hours since last update
    accuracy: float      # Data validation score
    consistency: float   # Cross-validation with other sources
    
    def overall_score(self) -> float:
        """Calculate overall quality score"""
        return (
            self.completeness * 0.4 +
            min(self.timeliness / 24, 1.0) * 0.2 +
            self.accuracy * 0.3 +
            self.consistency * 0.1
        )


class ETFDataProduct(DataProduct):
    """
    ETF Historical Data Product
    
    Provides:
    - Complete historical OHLCV data for all ASX ETFs
    - Daily updates with quality guarantees
    - ML/RL-ready data formats
    - Data lineage and versioning
    """
    
    def __init__(self):
        super().__init__(
            product_id="etf-historical-data",
            name="ASX ETF Historical Market Data",
            description="Complete historical OHLCV data for all Australian ETFs",
            owner="Market Data Team",
            domain="Market Data"
        )
        
        self.etf_data: Dict[str, ETFAggregate] = {}
        
    def add_etf(self, etf: ETFAggregate) -> None:
        """Add ETF data to the product"""
        self.etf_data[etf.ticker] = etf
    
    def get_etf(self, ticker: str) -> Optional[ETFAggregate]:
        """Get ETF data by ticker"""
        return self.etf_data.get(ticker)
    
    def get_all_tickers(self) -> List[str]:
        """Get list of all available ETF tickers"""
        return list(self.etf_data.keys())
    
    def get_price_data_df(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get price data as pandas DataFrame for ML/RL training
        
        Returns DataFrame with columns:
        - date, open, high, low, close, adj_close, volume
        """
        etf = self.get_etf(ticker)
        if not etf:
            return pd.DataFrame()
        
        price_history = etf.price_history
        
        # Filter by date range if specified
        if start_date or end_date:
            price_history = etf.get_price_range(
                start_date or date.min,
                end_date or date.max
            )
        
        # Convert to DataFrame
        data = []
        for price in price_history:
            data.append({
                'date': price.date,
                'open': float(price.open),
                'high': float(price.high),
                'low': float(price.low),
                'close': float(price.close),
                'adj_close': float(price.adj_close),
                'volume': price.volume
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('date', inplace=True)
        
        return df
    
    def get_multi_etf_data(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        column: str = 'adj_close'
    ) -> pd.DataFrame:
        """
        Get data for multiple ETFs as a single DataFrame
        Useful for portfolio analysis and correlation studies
        
        Returns DataFrame with tickers as columns and dates as index
        """
        dfs = []
        
        for ticker in tickers:
            df = self.get_price_data_df(ticker, start_date, end_date)
            if not df.empty:
                df_col = df[[column]].rename(columns={column: ticker})
                dfs.append(df_col)
        
        if not dfs:
            return pd.DataFrame()
        
        # Merge all DataFrames on date index
        result = pd.concat(dfs, axis=1, join='outer')
        result.sort_index(inplace=True)
        
        return result
    
    def get_returns_df(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = 'daily'
    ) -> pd.DataFrame:
        """
        Calculate returns for ML/RL training
        
        Args:
            ticker: ETF ticker
            start_date: Start date
            end_date: End date
            period: 'daily', 'weekly', 'monthly'
        
        Returns:
            DataFrame with returns, log_returns, and cumulative_returns
        """
        df = self.get_price_data_df(ticker, start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Resample if needed
        if period == 'weekly':
            df = df.resample('W').last()
        elif period == 'monthly':
            df = df.resample('M').last()
        
        # Calculate returns
        df['returns'] = df['adj_close'].pct_change()
        df['log_returns'] = np.log(df['adj_close'] / df['adj_close'].shift(1))
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
        
        return df
    
    def get_technical_indicators(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Calculate technical indicators for ML features
        
        Includes:
        - Moving averages (SMA, EMA)
        - RSI
        - MACD
        - Bollinger Bands
        - Volume indicators
        """
        df = self.get_price_data_df(ticker, start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Simple Moving Averages
        df['sma_20'] = df['adj_close'].rolling(window=20).mean()
        df['sma_50'] = df['adj_close'].rolling(window=50).mean()
        df['sma_200'] = df['adj_close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['adj_close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['adj_close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['adj_close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['adj_close'].rolling(window=20).mean()
        bb_std = df['adj_close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Price momentum
        df['momentum_5'] = df['adj_close'] / df['adj_close'].shift(5) - 1
        df['momentum_10'] = df['adj_close'] / df['adj_close'].shift(10) - 1
        df['momentum_20'] = df['adj_close'] / df['adj_close'].shift(20) - 1
        
        return df
    
    def get_ml_features(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_technical: bool = True
    ) -> pd.DataFrame:
        """
        Get complete feature set for ML/RL training
        
        Returns DataFrame ready for model training with:
        - Price data
        - Returns
        - Technical indicators
        - Lagged features
        """
        if include_technical:
            df = self.get_technical_indicators(ticker, start_date, end_date)
        else:
            df = self.get_price_data_df(ticker, start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Add returns if not already present
        if 'returns' not in df.columns:
            df['returns'] = df['adj_close'].pct_change()
        
        # Lagged features (for time series prediction)
        for lag in [1, 2, 3, 5, 10]:
            df[f'close_lag_{lag}'] = df['adj_close'].shift(lag)
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # Forward returns (targets for prediction)
        df['returns_forward_1'] = df['returns'].shift(-1)
        df['returns_forward_5'] = df['adj_close'].shift(-5) / df['adj_close'] - 1
        df['returns_forward_20'] = df['adj_close'].shift(-20) / df['adj_close'] - 1
        
        return df
    
    def calculate_data_quality(self, ticker: str) -> ETFDataQuality:
        """Calculate data quality metrics for an ETF"""
        etf = self.get_etf(ticker)
        if not etf:
            return ETFDataQuality(
                completeness=0.0,
                timeliness=999.0,
                accuracy=0.0,
                consistency=0.0
            )
        
        # Completeness: % of expected trading days with data
        if not etf.price_history:
            completeness = 0.0
        else:
            start = etf.price_history[0].date
            end = etf.price_history[-1].date
            expected_days = (end - start).days * 5 / 7  # Rough estimate
            actual_days = len(etf.price_history)
            completeness = min(actual_days / expected_days, 1.0) if expected_days > 0 else 0.0
        
        # Timeliness: hours since last update
        if etf.last_updated:
            timeliness = (datetime.utcnow() - etf.last_updated).total_seconds() / 3600
        else:
            timeliness = 999.0
        
        # Accuracy: basic validation checks
        accuracy = 1.0  # Placeholder - would implement validation logic
        
        # Consistency: cross-validation with other sources
        consistency = 1.0  # Placeholder
        
        return ETFDataQuality(
            completeness=completeness,
            timeliness=timeliness,
            accuracy=accuracy,
            consistency=consistency
        )
    
    def export_to_parquet(
        self,
        output_dir: str,
        tickers: Optional[List[str]] = None
    ) -> List[str]:
        """
        Export ETF data to Parquet files for efficient storage and ML training
        
        Args:
            output_dir: Directory to save parquet files
            tickers: List of tickers to export (None = all)
        
        Returns:
            List of created file paths
        """
        import os
        
        if tickers is None:
            tickers = self.get_all_tickers()
        
        os.makedirs(output_dir, exist_ok=True)
        
        created_files = []
        
        for ticker in tickers:
            df = self.get_ml_features(ticker, include_technical=True)
            if not df.empty:
                filepath = os.path.join(output_dir, f"{ticker}.parquet")
                df.to_parquet(filepath)
                created_files.append(filepath)
        
        return created_files
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the data product"""
        total_etfs = len(self.etf_data)
        total_data_points = sum(len(etf.price_history) for etf in self.etf_data.values())
        
        # Calculate date ranges
        earliest_dates = [
            etf.price_history[0].date
            for etf in self.etf_data.values()
            if etf.price_history
        ]
        latest_dates = [
            etf.price_history[-1].date
            for etf in self.etf_data.values()
            if etf.price_history
        ]
        
        return {
            "total_etfs": total_etfs,
            "total_data_points": total_data_points,
            "average_data_points_per_etf": total_data_points / total_etfs if total_etfs > 0 else 0,
            "earliest_date": min(earliest_dates).isoformat() if earliest_dates else None,
            "latest_date": max(latest_dates).isoformat() if latest_dates else None,
            "data_product_id": self.product_id,
            "owner": self.owner
        }

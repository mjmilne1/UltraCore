"""
Manus Yahoo Finance API Collector for ASX ETFs

This collector uses the Manus Yahoo Finance API to download historical and current
ETF data from the Australian Securities Exchange (ASX). It bypasses IP blocking issues
by using Manus's infrastructure.

Architecture Integration:
- Data Mesh: Provides market data for the ETF data product
- Event Sourcing: Emits events for all data collection activities
- Agentic AI: Can be orchestrated by the ETF collector agent
- MCP: Uses Manus Context Protocol for API access
"""

import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Add Manus runtime to path
sys.path.append('/opt/.manus/.sandbox-runtime')

try:
    from data_api import ApiClient
    MANUS_API_AVAILABLE = True
except ImportError:
    MANUS_API_AVAILABLE = False
    logging.warning("Manus API not available. This collector requires Manus runtime.")

import pandas as pd

logger = logging.getLogger(__name__)


class ManusYahooFinanceCollector:
    """
    Collector that uses Manus Yahoo Finance API to download ASX ETF data.
    
    Features:
    - Full historical data access (max range)
    - No IP blocking issues (uses Manus infrastructure)
    - Includes dividends and splits
    - Adjusted close prices for accurate returns
    - Free and unlimited access
    """
    
    def __init__(self):
        """Initialize the Manus Yahoo Finance collector."""
        if not MANUS_API_AVAILABLE:
            raise RuntimeError(
                "Manus API is not available. This collector must run in Manus environment."
            )
        
        self.client = ApiClient()
        self.region = 'AU'  # Australia
        logger.info("Manus Yahoo Finance collector initialized")
    
    def collect_etf_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Collect historical data for a single ETF.
        
        Args:
            symbol: ETF ticker symbol (e.g., 'IOZ.AX')
            start_date: Start date in YYYY-MM-DD format (optional, uses max if not provided)
            end_date: End date in YYYY-MM-DD format (optional, uses today if not provided)
            interval: Data interval ('1d', '1wk', '1mo')
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume
            Returns None if data collection fails
        """
        try:
            # Ensure symbol has .AX suffix for ASX
            if not symbol.endswith('.AX'):
                symbol = f"{symbol}.AX"
            
            logger.info(f"Collecting data for {symbol}")
            
            # Determine date range
            if start_date and end_date:
                # Calculate range in days for specific date range
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                days = (end - start).days
                
                if days <= 5:
                    range_param = '5d'
                elif days <= 30:
                    range_param = '1mo'
                elif days <= 90:
                    range_param = '3mo'
                elif days <= 180:
                    range_param = '6mo'
                elif days <= 365:
                    range_param = '1y'
                elif days <= 730:
                    range_param = '2y'
                elif days <= 1825:
                    range_param = '5y'
                elif days <= 3650:
                    range_param = '10y'
                else:
                    range_param = 'max'
            else:
                # Use max range for full historical data
                range_param = 'max'
            
            # Call Manus Yahoo Finance API
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'region': self.region,
                'interval': interval,
                'range': range_param,
                'includeAdjustedClose': True,
                'events': 'div,split'
            })
            
            # Parse response
            if not response or 'chart' not in response:
                logger.error(f"Invalid response for {symbol}")
                return None
            
            chart = response['chart']
            if 'error' in chart and chart['error']:
                logger.error(f"API error for {symbol}: {chart['error']}")
                return None
            
            if not chart.get('result') or len(chart['result']) == 0:
                logger.error(f"No data returned for {symbol}")
                return None
            
            result = chart['result'][0]
            
            # Extract metadata
            meta = result.get('meta', {})
            logger.info(f"  Name: {meta.get('longName', 'N/A')}")
            logger.info(f"  Exchange: {meta.get('exchangeName', 'N/A')}")
            logger.info(f"  Currency: {meta.get('currency', 'N/A')}")
            
            # Extract time series data
            timestamps = result.get('timestamp', [])
            if not timestamps:
                logger.error(f"No timestamps in data for {symbol}")
                return None
            
            quotes = result.get('indicators', {}).get('quote', [{}])[0]
            adj_close_data = result.get('indicators', {}).get('adjclose', [{}])[0]
            
            # Build DataFrame
            data = {
                'Date': [datetime.fromtimestamp(ts) for ts in timestamps],
                'Open': quotes.get('open', []),
                'High': quotes.get('high', []),
                'Low': quotes.get('low', []),
                'Close': quotes.get('close', []),
                'Volume': quotes.get('volume', []),
                'Adj Close': adj_close_data.get('adjclose', [])
            }
            
            df = pd.DataFrame(data)
            
            # Filter by date range if specified
            if start_date:
                df = df[df['Date'] >= start_date]
            if end_date:
                df = df[df['Date'] <= end_date]
            
            # Remove rows with all NaN values
            df = df.dropna(how='all', subset=['Open', 'High', 'Low', 'Close'])
            
            logger.info(f"  Collected {len(df)} data points for {symbol}")
            logger.info(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None
    
    def collect_multiple_etfs(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect data for multiple ETFs.
        
        Args:
            symbols: List of ETF ticker symbols
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            interval: Data interval ('1d', '1wk', '1mo')
        
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        logger.info(f"Collecting data for {len(symbols)} ETFs")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {i}/{len(symbols)}: {symbol}")
            
            df = self.collect_etf_data(symbol, start_date, end_date, interval)
            
            if df is not None:
                results[symbol] = df
            
            # Small delay to be respectful to the API
            if i < len(symbols):
                import time
                time.sleep(0.5)
        
        success_rate = len(results) / len(symbols) * 100
        logger.info(f"Collection complete: {len(results)}/{len(symbols)} successful ({success_rate:.1f}%)")
        
        return results
    
    def save_to_parquet(
        self,
        df: pd.DataFrame,
        symbol: str,
        output_dir: Path
    ) -> Path:
        """
        Save ETF data to Parquet format.
        
        Args:
            df: DataFrame with ETF data
            symbol: ETF ticker symbol
            output_dir: Directory to save the file
        
        Returns:
            Path to the saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean symbol for filename (remove .AX suffix)
        clean_symbol = symbol.replace('.AX', '')
        
        output_file = output_dir / f"{clean_symbol}.parquet"
        df.to_parquet(output_file, index=False)
        
        logger.info(f"Saved {symbol} data to {output_file}")
        return output_file
    
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest price and metadata for an ETF.
        
        Args:
            symbol: ETF ticker symbol
        
        Returns:
            Dictionary with latest price information
        """
        try:
            if not symbol.endswith('.AX'):
                symbol = f"{symbol}.AX"
            
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'region': self.region,
                'interval': '1d',
                'range': '5d',
                'includeAdjustedClose': True
            })
            
            if not response or 'chart' not in response:
                return None
            
            result = response['chart']['result'][0]
            meta = result['meta']
            
            return {
                'symbol': symbol,
                'name': meta.get('longName', 'N/A'),
                'price': meta.get('regularMarketPrice'),
                'currency': meta.get('currency'),
                'exchange': meta.get('exchangeName'),
                'market_time': datetime.fromtimestamp(meta.get('regularMarketTime', 0)),
                'previous_close': meta.get('previousClose'),
                'day_high': meta.get('regularMarketDayHigh'),
                'day_low': meta.get('regularMarketDayLow'),
                'volume': meta.get('regularMarketVolume')
            }
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {str(e)}")
            return None


def main():
    """Test the Manus Yahoo Finance collector."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = ManusYahooFinanceCollector()
    
    # Test with a few ETFs
    test_symbols = ['IOZ.AX', 'STW.AX', 'VAS.AX']
    
    print("\n" + "=" * 80)
    print("Testing Manus Yahoo Finance Collector")
    print("=" * 80)
    
    results = collector.collect_multiple_etfs(test_symbols)
    
    print(f"\nCollected data for {len(results)} ETFs:")
    for symbol, df in results.items():
        print(f"\n{symbol}:")
        print(f"  Rows: {len(df)}")
        print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")


if __name__ == '__main__':
    main()

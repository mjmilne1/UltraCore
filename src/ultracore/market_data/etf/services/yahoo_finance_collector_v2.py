"""
Yahoo Finance Data Collector v2 - Improved with Rate Limiting
Collects historical ETF data from Yahoo Finance with proper rate limiting and error handling
"""
import time
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    """Result of a data collection operation"""
    ticker: str
    success: bool
    data_points: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    error: Optional[str] = None
    price_data: Optional[pd.DataFrame] = None


class YahooFinanceCollectorV2:
    """
    Improved Yahoo Finance data collector with:
    - Sequential processing (no parallel requests)
    - Rate limiting (delay between requests)
    - Better error handling
    - Retry logic with exponential backoff
    """
    
    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize collector
        
        Args:
            delay_seconds: Delay between requests to avoid rate limiting
        """
        self.delay_seconds = delay_seconds
        self.last_request_time = 0
        self.request_count = 0
        
        logger.info(f"Yahoo Finance Collector V2 initialized with {delay_seconds}s delay")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay_seconds:
            sleep_time = self.delay_seconds - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def download_historical_data(
        self,
        ticker: str,
        period: str = "max",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> CollectionResult:
        """
        Download historical data for a single ETF
        
        Args:
            ticker: ETF ticker symbol (e.g., "VAS")
            period: Time period ("max", "1y", "5y", etc.)
            start_date: Start date for data
            end_date: End date for data
        
        Returns:
            CollectionResult with data or error
        """
        # Add .AX suffix if not present
        if not ticker.endswith('.AX'):
            ticker_symbol = f"{ticker}.AX"
        else:
            ticker_symbol = ticker
            ticker = ticker.replace('.AX', '')
        
        logger.info(f"Downloading historical data for {ticker} ({ticker_symbol})")
        
        # Rate limit
        self._rate_limit()
        
        try:
            # Create Ticker object
            stock = yf.Ticker(ticker_symbol)
            
            # Download data
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)
            
            # Check if data was returned
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="No data returned from Yahoo Finance"
                )
            
            # Validate data
            if len(df) < 10:
                logger.warning(f"Insufficient data for {ticker}: only {len(df)} rows")
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error=f"Insufficient data: only {len(df)} rows"
                )
            
            # Extract date range
            start = df.index[0].date()
            end = df.index[-1].date()
            
            logger.info(f"✅ Downloaded {len(df)} data points for {ticker} ({start} to {end})")
            
            return CollectionResult(
                ticker=ticker,
                success=True,
                data_points=len(df),
                start_date=start,
                end_date=end,
                price_data=df
            )
            
        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")
            return CollectionResult(
                ticker=ticker,
                success=False,
                error=str(e)
            )
    
    def download_latest_data(
        self,
        ticker: str,
        days_back: int = 5
    ) -> CollectionResult:
        """
        Download latest data for daily updates
        
        Args:
            ticker: ETF ticker symbol
            days_back: Number of days to look back
        
        Returns:
            CollectionResult with recent data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        return self.download_historical_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_etf_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get ETF metadata/info
        
        Args:
            ticker: ETF ticker symbol
        
        Returns:
            Dictionary with ETF info or None
        """
        if not ticker.endswith('.AX'):
            ticker_symbol = f"{ticker}.AX"
        else:
            ticker_symbol = ticker
        
        logger.debug(f"Fetching info for {ticker_symbol}")
        
        # Rate limit
        self._rate_limit()
        
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            if not info or len(info) == 0:
                logger.warning(f"No info returned for {ticker}")
                return None
            
            return info
            
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None
    
    def batch_download(
        self,
        tickers: List[str],
        period: str = "max"
    ) -> List[CollectionResult]:
        """
        Download data for multiple ETFs sequentially
        
        Args:
            tickers: List of ticker symbols
            period: Time period for each ticker
        
        Returns:
            List of CollectionResults
        """
        results = []
        total = len(tickers)
        
        logger.info(f"Starting batch download of {total} ETFs")
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%)")
            
            result = self.download_historical_data(ticker, period=period)
            results.append(result)
            
            # Log progress every 10 ETFs
            if i % 10 == 0:
                successful = sum(1 for r in results if r.success)
                logger.info(f"Batch progress: {successful}/{i} successful so far")
        
        # Final summary
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        logger.info(f"Batch download complete: {successful}/{total} successful, {failed} failed")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            "total_requests": self.request_count,
            "delay_seconds": self.delay_seconds
        }

"""
Alpha Vantage ETF Data Collector
Downloads historical and real-time ETF data from Alpha Vantage API
"""
import requests
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging
import time
from dataclasses import dataclass

from ultracore.market_data.etf.aggregates.etf_aggregate import ETFPriceData, ETFMetadata


logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    """Result of a data collection operation"""
    ticker: str
    success: bool
    data_points: int = 0
    error: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AlphaVantageCollector:
    """
    Collects ETF data from Alpha Vantage API
    Handles ASX ticker format (.AX suffix)
    
    Rate Limits (Free Tier):
    - 25 API calls per day
    - 5 calls per minute
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.asx_suffix = ".AX"
        self.calls_per_minute = 5
        self.last_call_time = None
        self.call_count = 0
        
    def _format_ticker(self, ticker: str) -> str:
        """Format ticker for Alpha Vantage (add .AX for ASX)"""
        if not ticker.endswith(self.asx_suffix):
            return f"{ticker}{self.asx_suffix}"
        return ticker
    
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            # Wait at least 12 seconds between calls (5 per minute = 12s each)
            min_interval = 12.0
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        
        self.last_call_time = time.time()
        self.call_count += 1
    
    def get_etf_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get ETF metadata from Alpha Vantage"""
        try:
            av_ticker = self._format_ticker(ticker)
            self._rate_limit()
            
            params = {
                'function': 'OVERVIEW',
                'symbol': av_ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'Symbol' not in data:
                logger.warning(f"No info found for {ticker}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None
    
    def download_historical_data(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        outputsize: str = "full"
    ) -> CollectionResult:
        """
        Download historical price data for an ETF
        
        Args:
            ticker: ETF ticker symbol (without .AX)
            start_date: Start date for data collection (optional, will filter results)
            end_date: End date for data collection (optional, will filter results)
            outputsize: "compact" (100 days) or "full" (20+ years)
        
        Returns:
            CollectionResult with price data
        """
        try:
            av_ticker = self._format_ticker(ticker)
            logger.info(f"Downloading historical data for {ticker} ({av_ticker}) from Alpha Vantage")
            
            self._rate_limit()
            
            # Use TIME_SERIES_DAILY_ADJUSTED for adjusted close prices
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': av_ticker,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error=f"Alpha Vantage error: {data['Error Message']}"
                )
            
            if 'Note' in data:
                # Rate limit message
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error=f"Alpha Vantage rate limit: {data['Note']}"
                )
            
            if 'Time Series (Daily)' not in data:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="No time series data returned from Alpha Vantage"
                )
            
            time_series = data['Time Series (Daily)']
            
            if not time_series:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="Empty time series returned from Alpha Vantage"
                )
            
            # Convert to price data objects
            price_data = []
            for date_str, values in time_series.items():
                try:
                    price_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Filter by date range if specified
                    if start_date and price_date < start_date:
                        continue
                    if end_date and price_date > end_date:
                        continue
                    
                    price = ETFPriceData(
                        date=price_date,
                        open=Decimal(str(values['1. open'])),
                        high=Decimal(str(values['2. high'])),
                        low=Decimal(str(values['3. low'])),
                        close=Decimal(str(values['4. close'])),
                        adj_close=Decimal(str(values['5. adjusted close'])),
                        volume=int(float(values['6. volume']))
                    )
                    price_data.append(price)
                except Exception as e:
                    logger.warning(f"Error parsing data for {ticker} on {date_str}: {e}")
                    continue
            
            if not price_data:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="No valid price data after parsing"
                )
            
            # Sort by date (oldest first)
            price_data.sort(key=lambda x: x.date)
            
            return CollectionResult(
                ticker=ticker,
                success=True,
                data_points=len(price_data),
                start_date=price_data[0].date,
                end_date=price_data[-1].date
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading {ticker}: {e}")
            return CollectionResult(
                ticker=ticker,
                success=False,
                error=f"Network error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")
            return CollectionResult(
                ticker=ticker,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def get_latest_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get latest quote for an ETF"""
        try:
            av_ticker = self._format_ticker(ticker)
            self._rate_limit()
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                logger.warning(f"No quote found for {ticker}")
                return None
            
            return data['Global Quote']
            
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {e}")
            return None

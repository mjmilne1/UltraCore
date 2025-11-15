"""
Yahoo Finance ETF Data Collector
Downloads historical and real-time ETF data from Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
import logging
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


class YahooFinanceCollector:
    """
    Collects ETF data from Yahoo Finance
    Handles ASX ticker format (.AX suffix)
    """
    
    def __init__(self):
        self.asx_suffix = ".AX"
        
    def _format_ticker(self, ticker: str) -> str:
        """Format ticker for Yahoo Finance (add .AX for ASX)"""
        if not ticker.endswith(self.asx_suffix):
            return f"{ticker}{self.asx_suffix}"
        return ticker
    
    def get_etf_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get ETF metadata from Yahoo Finance"""
        try:
            yf_ticker = self._format_ticker(ticker)
            etf = yf.Ticker(yf_ticker)
            info = etf.info
            
            if not info or 'symbol' not in info:
                logger.warning(f"No info found for {ticker}")
                return None
            
            return info
            
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None
    
    def download_historical_data(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "max"
    ) -> CollectionResult:
        """
        Download historical price data for an ETF
        
        Args:
            ticker: ETF ticker symbol (without .AX)
            start_date: Start date for data collection
            end_date: End date for data collection
            period: Period to download if dates not specified ("max", "1y", "5y", etc.)
        
        Returns:
            CollectionResult with price data
        """
        try:
            yf_ticker = self._format_ticker(ticker)
            logger.info(f"Downloading historical data for {ticker} ({yf_ticker})")
            
            # Download data
            if start_date and end_date:
                df = yf.download(
                    yf_ticker,
                    start=start_date,
                    end=end_date,
                    progress=False
                )
            else:
                df = yf.download(
                    yf_ticker,
                    period=period,
                    progress=False
                )
            
            if df.empty:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="No data returned from Yahoo Finance"
                )
            
            # Convert to price data objects
            price_data = []
            for idx, row in df.iterrows():
                try:
                    price = ETFPriceData(
                        date=idx.date(),
                        open=Decimal(str(row['Open'])),
                        high=Decimal(str(row['High'])),
                        low=Decimal(str(row['Low'])),
                        close=Decimal(str(row['Close'])),
                        adj_close=Decimal(str(row['Adj Close'])),
                        volume=int(row['Volume'])
                    )
                    price_data.append(price)
                except Exception as e:
                    logger.warning(f"Error parsing row for {ticker} on {idx}: {e}")
                    continue
            
            if not price_data:
                return CollectionResult(
                    ticker=ticker,
                    success=False,
                    error="No valid price data parsed"
                )
            
            logger.info(f"Successfully downloaded {len(price_data)} data points for {ticker}")
            
            return CollectionResult(
                ticker=ticker,
                success=True,
                data_points=len(price_data),
                start_date=price_data[0].date,
                end_date=price_data[-1].date
            )
            
        except Exception as e:
            logger.error(f"Error downloading data for {ticker}: {e}")
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
            days_back: Number of days to look back (to handle weekends/holidays)
        
        Returns:
            CollectionResult with latest price data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        return self.download_historical_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
    
    def extract_metadata(self, info: Dict[str, Any], ticker: str) -> ETFMetadata:
        """Extract ETF metadata from Yahoo Finance info"""
        return ETFMetadata(
            name=info.get('longName', info.get('shortName', ticker)),
            issuer=info.get('fundFamily', 'Unknown'),
            category=info.get('category', info.get('quoteType', 'ETF')),
            benchmark=None,  # Not available from Yahoo Finance
            management_fee=None,  # Not reliably available
            inception_date=None,  # Would need to parse from first available data
            description=info.get('longBusinessSummary', None),
            website=info.get('website', None)
        )
    
    def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker exists on Yahoo Finance"""
        try:
            yf_ticker = self._format_ticker(ticker)
            etf = yf.Ticker(yf_ticker)
            info = etf.info
            return bool(info and 'symbol' in info)
        except:
            return False
    
    def batch_download(
        self,
        tickers: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "max"
    ) -> List[CollectionResult]:
        """
        Download data for multiple ETFs
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for data collection
            end_date: End date for data collection
            period: Period to download if dates not specified
        
        Returns:
            List of CollectionResult objects
        """
        results = []
        
        for ticker in tickers:
            result = self.download_historical_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            results.append(result)
        
        return results

"""Yahoo Finance Service for UltraCore"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

class YahooFinanceService:
    def __init__(self):
        self.cache = {}
    
    async def get_company_data(self, ticker: str) -> Dict[str, Any]:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "company_info": {
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "description": info.get("longBusinessSummary", ""),
            },
            "market_data": {
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "market_cap": info.get("marketCap", 0),
                "volume": info.get("volume", 0),
            },
            "financial_metrics": {
                "pe_ratio": info.get("trailingPE", 0),
                "roe": info.get("returnOnEquity", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
            }
        }
    
    async def get_historical_data_for_ml(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        df['returns'] = df['Close'].pct_change()
        df['sma_5'] = df['Close'].rolling(window=5).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['volatility'] = df['returns'].rolling(window=20).std()
        return df.dropna()
    
    async def batch_get_prices(self, tickers: List[str]) -> Dict[str, float]:
        prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                prices[ticker] = float(info.get("currentPrice", info.get("regularMarketPrice", 0)))
            except:
                prices[ticker] = 0.0
        return prices

yahoo_service = YahooFinanceService()

"""
Enhanced DataMesh for UltraWealth
With automatic daily updates and data lineage tracking
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import json
from pathlib import Path

class UltraWealthDataMesh:
    def __init__(self):
        self.data_store = {}
        self.metadata_store = {}
        self.lineage_store = {}
        self.cache_dir = Path("data_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.last_update = {}
    
    async def ingest_etf_data(self, ticker: str, period: str = "2y", force_refresh: bool = False) -> Dict:
        """Ingest ETF data with caching and lineage tracking"""
        
        # Check if we need to refresh
        cache_file = self.cache_dir / f"{ticker}_{period}.parquet"
        needs_refresh = force_refresh or not cache_file.exists()
        
        if not needs_refresh:
            # Check if cache is stale (older than 1 day)
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            needs_refresh = cache_age > timedelta(days=1)
        
        if needs_refresh:
            # Fetch fresh data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            # Save to cache
            df.to_parquet(cache_file)
            
            # Store in memory
            mesh_key = f"etf:{ticker}:{period}"
            self.data_store[mesh_key] = df
            
            # Track lineage
            self.lineage_store[mesh_key] = {
                "source": "yahoo_finance",
                "ticker": ticker,
                "ingested_at": datetime.now().isoformat(),
                "records": len(df),
                "date_range": {
                    "start": df.index.min().isoformat(),
                    "end": df.index.max().isoformat()
                }
            }
            
            self.last_update[ticker] = datetime.now()
            
            return {
                "status": "ingested",
                "ticker": ticker,
                "records": len(df),
                "cached": True
            }
        else:
            # Load from cache
            df = pd.read_parquet(cache_file)
            mesh_key = f"etf:{ticker}:{period}"
            self.data_store[mesh_key] = df
            
            return {
                "status": "loaded_from_cache",
                "ticker": ticker,
                "records": len(df),
                "cache_age_hours": round(cache_age.total_seconds() / 3600, 2)
            }
    
    async def get_etf_data(self, ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get ETF data from DataMesh"""
        mesh_key = f"etf:{ticker}:{period}"
        
        # Try memory first
        if mesh_key in self.data_store:
            return self.data_store[mesh_key]
        
        # Try cache
        cache_file = self.cache_dir / f"{ticker}_{period}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self.data_store[mesh_key] = df
            return df
        
        # Ingest if not available
        await self.ingest_etf_data(ticker, period)
        return self.data_store.get(mesh_key)
    
    async def batch_ingest(self, tickers: List[str], period: str = "2y") -> Dict:
        """Batch ingest multiple ETFs"""
        results = []
        for ticker in tickers:
            try:
                result = await self.ingest_etf_data(ticker, period)
                results.append(result)
            except Exception as e:
                results.append({"ticker": ticker, "status": "failed", "error": str(e)})
        
        return {
            "total": len(tickers),
            "successful": len([r for r in results if r.get("status") in ["ingested", "loaded_from_cache"]]),
            "results": results
        }
    
    def get_data_lineage(self, ticker: str, period: str = "2y") -> Optional[Dict]:
        """Get data lineage for a ticker"""
        mesh_key = f"etf:{ticker}:{period}"
        return self.lineage_store.get(mesh_key)
    
    def get_update_status(self) -> Dict:
        """Get status of all cached data"""
        status = {}
        for ticker, last_update in self.last_update.items():
            age = datetime.now() - last_update
            status[ticker] = {
                "last_update": last_update.isoformat(),
                "age_hours": round(age.total_seconds() / 3600, 2),
                "needs_update": age > timedelta(days=1)
            }
        return status

ultrawealth_datamesh = UltraWealthDataMesh()

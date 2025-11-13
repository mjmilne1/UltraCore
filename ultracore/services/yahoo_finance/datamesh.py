"""DataMesh Integration for Financial Data - Persistent Version"""
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

class FinancialDataMeshNode:
    def __init__(self):
        self.data_store = {}
        self.metadata_store = {}
    
    async def ingest_company_data(self, ticker: str) -> Dict[str, Any]:
        from ultracore.services.yahoo_finance.service import yahoo_service
        data = await yahoo_service.get_company_data(ticker)
        mesh_key = f"company:{ticker}"
        self.data_store[mesh_key] = data
        self.metadata_store[mesh_key] = {
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "source": "yahoo_finance",
            "ticker": ticker,
            "quality_score": 1.0,
        }
        return {"mesh_key": mesh_key, "status": "ingested", "metadata": self.metadata_store[mesh_key]}
    
    async def ingest_time_series_data(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        from ultracore.services.yahoo_finance.service import yahoo_service
        df = await yahoo_service.get_historical_data_for_ml(ticker, period)
        mesh_key = f"timeseries:{ticker}:{period}"
        
        # Store the dataframe
        self.data_store[mesh_key] = df
        
        self.metadata_store[mesh_key] = {
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "period": period,
            "records": len(df),
            "features": list(df.columns),
        }
        
        print(f"[DataMesh] Stored {mesh_key} with {len(df)} records")  # Debug
        
        return {"mesh_key": mesh_key, "status": "ingested", "records": len(df)}
    
    async def query_latest_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        mesh_key = f"company:{ticker}"
        return self.data_store.get(mesh_key)
    
    async def query_time_series(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        mesh_key = f"timeseries:{ticker}:{period}"
        result = self.data_store.get(mesh_key)
        print(f"[DataMesh] Query {mesh_key}: {'Found' if result is not None else 'Not found'}")  # Debug
        return result

# Global singleton instance
financial_datamesh = FinancialDataMeshNode()

"""
Example: DataMesh Integration for Data Governance
"""
import asyncio
from ultracore.services.yahoo_finance import financial_datamesh, yahoo_service

async def datamesh_workflow():
    """Complete DataMesh workflow"""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    print("\n📊 DataMesh Ingestion Workflow\n")
    
    for ticker in tickers:
        # Ingest company data
        result = await financial_datamesh.ingest_company_data(ticker)
        print(f"✓ {ticker}: Ingested to {result['mesh_key']}")
        print(f"  Quality Score: {result['metadata']['quality_score']}")
        
        # Ingest time series
        ts_result = await financial_datamesh.ingest_time_series_data(ticker, "1y")
        print(f"  Time Series: {ts_result['records']} records")
        
        # Query back
        data = await financial_datamesh.query_latest_data(ticker)
        print(f"  Current Price: ${data['market_data']['current_price']:.2f}\n")

if __name__ == "__main__":
    asyncio.run(datamesh_workflow())

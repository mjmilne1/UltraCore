"""Complete Integration Demo"""
import asyncio
from ultracore.services.yahoo_finance import yahoo_service, financial_datamesh, ml_pipeline, mcp_tools

async def demo():
    print("\n" + "="*70)
    print("  ULTRACORE FINANCIAL INTEGRATION - DEMO")
    print("="*70 + "\n")
    
    # Test Yahoo Finance
    print("1️⃣  YAHOO FINANCE SERVICE")
    print("-" * 70)
    data = await yahoo_service.get_company_data("AAPL")
    print(f"✓ Company: {data['company_info']['name']}")
    print(f"✓ Price: ${data['market_data']['current_price']:.2f}")
    print(f"✓ Market Cap: ${data['market_data']['market_cap']:,.0f}")
    
    # Test DataMesh
    print("\n2️⃣  DATAMESH INTEGRATION")
    print("-" * 70)
    result = await financial_datamesh.ingest_company_data("MSFT")
    print(f"✓ Ingested: {result['mesh_key']}")
    await financial_datamesh.ingest_time_series_data("MSFT", "1y")
    print(f"✓ Time series ingested")
    
    # Test ML Pipeline
    print("\n3️⃣  ML PIPELINE")
    print("-" * 70)
    ml_result = await ml_pipeline.train_price_predictor("MSFT")
    print(f"✓ Model trained: {ml_result['test_score']:.4f} test score")
    prediction = await ml_pipeline.predict_next_price("MSFT")
    print(f"✓ Predicted price: ${prediction:.2f}")
    
    # Test MCP Tools
    print("\n4️⃣  MCP TOOLS")
    print("-" * 70)
    tools = mcp_tools.get_available_tools()
    print(f"✓ Available tools: {len(tools)}")
    price_result = await mcp_tools.get_stock_price("AAPL")
    print(f"✓ get_stock_price: ${price_result['price']:.2f}")
    
    # Batch Test
    print("\n5️⃣  BATCH OPERATIONS")
    print("-" * 70)
    tickers = ["AAPL", "MSFT", "GOOGL"]
    prices = await yahoo_service.batch_get_prices(tickers)
    print(f"✓ Batch prices for {len(tickers)} tickers:")
    for ticker, price in prices.items():
        print(f"  • {ticker}: ${price:.2f}")
    
    print("\n" + "="*70)
    print("✅ ALL INTEGRATIONS WORKING!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(demo())

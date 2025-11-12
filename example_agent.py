"""
Example: Using MCP Tools in Your Agentic AI
Enhanced version with better formatting
"""
import asyncio
from ultracore.services.yahoo_finance import mcp_tools

async def agent_get_market_data(ticker: str):
    """Agent function to get comprehensive market data"""
    print(f"   📡 Fetching data for {ticker}...")
    
    price = await mcp_tools.get_stock_price(ticker)
    info = await mcp_tools.get_company_info(ticker)
    
    print(f"   🤖 Training ML model and predicting...")
    prediction = await mcp_tools.predict_price(ticker)
    
    return {
        "current": price,
        "company": info,
        "forecast": prediction
    }

async def main():
    print("\n" + "="*70)
    print("  🤖 AGENT MARKET INTELLIGENCE SYSTEM")
    print("="*70 + "\n")
    
    # Example: Agent analyzing multiple stocks
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    for ticker in tickers:
        print(f"\n📊 Analyzing {ticker}...")
        result = await agent_get_market_data(ticker)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Company: {result['company']['company']['name']}")
        print(f"   Sector: {result['company']['company']['sector']}")
        print(f"   Current Price: ${result['current']['price']:.2f}")
        print(f"   Predicted Price: ${result['forecast']['predicted_price']:.2f}")
        print(f"   Expected Change: {result['forecast']['change']:+.2f}%")
        
        # Agent decision logic
        if result['forecast']['change'] > 5:
            print(f"   🚀 Signal: STRONG BUY")
        elif result['forecast']['change'] > 0:
            print(f"   📈 Signal: BUY")
        elif result['forecast']['change'] > -5:
            print(f"   📉 Signal: HOLD")
        else:
            print(f"   ⚠️  Signal: SELL")
    
    print("\n" + "="*70)
    print("✅ Agent Analysis Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

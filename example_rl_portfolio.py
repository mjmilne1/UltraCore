"""
Example: RL Portfolio Optimization Integration
"""
import asyncio
from ultracore.services.yahoo_finance import yahoo_service

async def get_portfolio_data_for_rl():
    """Get real-time portfolio data for RL training"""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    
    print("\n🎮 Getting Portfolio Data for RL...\n")
    
    # Get current prices
    prices = await yahoo_service.batch_get_prices(tickers)
    
    # Get detailed data for each
    portfolio_data = {}
    for ticker in tickers:
        data = await yahoo_service.get_company_data(ticker)
        portfolio_data[ticker] = {
            "price": prices[ticker],
            "market_cap": data["market_data"]["market_cap"],
            "pe_ratio": data["financial_metrics"]["pe_ratio"],
            "roe": data["financial_metrics"]["roe"]
        }
    
    print("Portfolio Data Ready:")
    for ticker, data in portfolio_data.items():
        print(f"  {ticker}: ${data['price']:.2f} | P/E: {data['pe_ratio']:.2f} | ROE: {data['roe']*100:.2f}%")
    
    return portfolio_data

if __name__ == "__main__":
    asyncio.run(get_portfolio_data_for_rl())

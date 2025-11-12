import asyncio
from ultracore.services.yahoo_finance import yahoo_service

async def test():
    data = await yahoo_service.get_company_data('AAPL')
    print(f"Company: {data['company_info']['name']}")
    print(f"Price: ${data['market_data']['current_price']:.2f}")
    print(f"Market Cap: ${data['market_data']['market_cap']:,.0f}")

asyncio.run(test())

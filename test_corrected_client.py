import asyncio
import os
os.environ["FISCAL_AI_API_KEY"] = "01c57741-7763-4e22-be72-de738b098a8b"

from ultracore.services.fiscal_ai.client import FiscalAIClient

async def test():
    print("\n" + "="*70)
    print("  TESTING CORRECTED FISCAL.AI CLIENT")
    print("="*70 + "\n")
    
    async with FiscalAIClient() as client:
        # Test 1: Company Profile
        print("📊 Test 1: Getting Apple company profile...")
        try:
            profile = await client.get_company_profile("AAPL")
            company_name = profile.get('companyName', 'N/A')
            sector = profile.get('sector', 'N/A')
            industry = profile.get('industry', 'N/A')
            print(f"✅ Success! Company: {company_name}")
            print(f"   Sector: {sector}")
            print(f"   Industry: {industry}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Stock Prices
        print("\n💰 Test 2: Getting latest stock price...")
        try:
            price = await client.get_latest_price("AAPL")
            if price:
                close_price = price.get('close', 'N/A')
                date = price.get('date', 'N/A')
                print(f"✅ Success! Latest price: ${close_price}")
                print(f"   Date: {date}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Income Statement
        print("\n📈 Test 3: Getting income statement...")
        try:
            income = await client.get_income_statement("AAPL", "annual", 1)
            if income and len(income) > 0:
                stmt = income[0]
                period = stmt.get('period', 'N/A')
                revenue = stmt.get('revenue', 'N/A')
                print(f"✅ Success! Period: {period}")
                if isinstance(revenue, (int, float)):
                    print(f"   Revenue: ${revenue:,.0f}")
                else:
                    print(f"   Revenue: {revenue}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Financial Ratios
        print("\n📊 Test 4: Getting financial ratios...")
        try:
            ratios = await client.get_company_ratios("AAPL", "annual", 1)
            if ratios and len(ratios) > 0:
                ratio = ratios[0]
                period = ratio.get('period', 'N/A')
                pe_ratio = ratio.get('peRatio', 'N/A')
                roe = ratio.get('returnOnEquity', 'N/A')
                print(f"✅ Success! Period: {period}")
                print(f"   P/E Ratio: {pe_ratio}")
                print(f"   ROE: {roe}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Company Search
        print("\n🔍 Test 5: Searching for companies...")
        try:
            companies = await client.search_companies(limit=5)
            if companies:
                print(f"✅ Success! Found {len(companies)} companies")
                for i, comp in enumerate(companies[:3], 1):
                    ticker = comp.get('ticker', 'N/A')
                    name = comp.get('companyName', 'N/A')
                    print(f"   {i}. {ticker}: {name}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*70)
    print("  🎉 ALL TESTS COMPLETE!")
    print("="*70 + "\n")

asyncio.run(test())

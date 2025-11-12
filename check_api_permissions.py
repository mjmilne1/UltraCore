import asyncio
import os
import json
os.environ["FISCAL_AI_API_KEY"] = "01c57741-7763-4e22-be72-de738b098a8b"

from ultracore.services.fiscal_ai.client import FiscalAIClient

async def check_permissions():
    print("\n" + "="*70)
    print("  CHECKING FISCAL.AI API KEY PERMISSIONS")
    print("="*70 + "\n")
    
    async with FiscalAIClient() as client:
        # Test all endpoints to see what's accessible
        test_endpoints = [
            ("Companies List", "v2/companies-list", {"limit": 5}),
            ("Company Profile", "v2/company/profile", {"ticker": "AAPL"}),
            ("Stock Prices", "v1/company/stock-prices", {"ticker": "AAPL"}),
            ("Income Statement", "v1/company/financials/income-statement/standardized", {"ticker": "AAPL", "period": "annual", "limit": 1}),
            ("Balance Sheet", "v1/company/financials/balance-sheet/standardized", {"ticker": "AAPL", "period": "annual", "limit": 1}),
            ("Cash Flow", "v1/company/financials/cash-flow/standardized", {"ticker": "AAPL", "period": "annual", "limit": 1}),
            ("Ratios", "v1/company/ratios", {"ticker": "AAPL", "period": "annual", "limit": 1}),
            ("Adjusted Metrics", "v1/company/adjusted-metrics", {"ticker": "AAPL"}),
            ("Segments & KPIs", "v1/company/segments-and-kpis", {"ticker": "AAPL"}),
            ("Filings", "v2/company/filings", {"ticker": "AAPL", "limit": 5}),
            ("Shares Outstanding", "v1/company/shares-outstanding", {"ticker": "AAPL"}),
            ("Earnings Summary", "v1/company/earnings-summary", {"ticker": "AAPL"}),
        ]
        
        accessible = []
        forbidden = []
        
        for name, endpoint, params in test_endpoints:
            try:
                result = await client._request(endpoint, params)
                accessible.append(name)
                print(f"✅ {name}: ACCESSIBLE")
                
                # Show sample data
                if isinstance(result, dict):
                    print(f"   Response type: dict with keys: {list(result.keys())[:5]}")
                elif isinstance(result, list):
                    print(f"   Response type: list with {len(result)} items")
                    if len(result) > 0:
                        print(f"   First item keys: {list(result[0].keys())[:5] if isinstance(result[0], dict) else 'N/A'}")
                
            except Exception as e:
                error_str = str(e)
                if "403" in error_str:
                    forbidden.append(name)
                    print(f"❌ {name}: FORBIDDEN (403)")
                elif "404" in error_str:
                    print(f"⚠️  {name}: NOT FOUND (404)")
                elif "401" in error_str:
                    print(f"❌ {name}: UNAUTHORIZED (401)")
                else:
                    print(f"❌ {name}: ERROR - {error_str[:60]}")
        
        print("\n" + "="*70)
        print("  SUMMARY")
        print("="*70)
        print(f"\n✅ Accessible Endpoints ({len(accessible)}):")
        for ep in accessible:
            print(f"   • {ep}")
        
        print(f"\n❌ Forbidden Endpoints ({len(forbidden)}):")
        for ep in forbidden:
            print(f"   • {ep}")
        
        if len(forbidden) > len(accessible):
            print("\n⚠️  API KEY LIMITATION DETECTED")
            print("="*70)
            print("Your API key appears to be on a FREE/TRIAL tier.")
            print("\nThis typically means:")
            print("  • Limited access to basic company data")
            print("  • No access to financial statements")
            print("  • No access to ratios and metrics")
            print("\nTo access full financial data:")
            print("  1. Check your Fiscal.ai dashboard")
            print("  2. Verify subscription status")
            print("  3. Upgrade to paid tier if needed")
            print("  4. Contact Fiscal.ai support")
        
        # If companies list worked, show what we got
        if "Companies List" in accessible:
            print("\n" + "="*70)
            print("  AVAILABLE DATA: COMPANIES LIST")
            print("="*70 + "\n")
            try:
                companies = await client.search_companies(limit=10)
                print(f"Retrieved {len(companies)} companies:\n")
                
                for i, company in enumerate(companies, 1):
                    print(f"{i}. {company}")
                    if i >= 3:
                        break
                        
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(check_permissions())

import httpx
import json
import os
from bs4 import BeautifulSoup

# SECURITY FIX: Load API key from environment variable
API_KEY = os.environ.get('FISCAL_AI_API_KEY')
if not API_KEY:
    raise ValueError("FISCAL_AI_API_KEY environment variable must be set")

async def get_swagger_spec():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to get OpenAPI/Swagger spec
        spec_urls = [
            "https://api.fiscal.ai/docs/swagger.json",
            "https://api.fiscal.ai/swagger.json",
            "https://api.fiscal.ai/openapi.json",
            "https://api.fiscal.ai/v1/swagger.json",
            "https://api.fiscal.ai/api-docs",
        ]
        
        print("\n" + "="*70)
        print("  FETCHING FISCAL.AI API SPECIFICATION")
        print("="*70)
        
        for url in spec_urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"\n✅ Found spec at: {url}")
                    spec = response.json()
                    print(f"\nAPI Info:")
                    if 'info' in spec:
                        print(f"  Title: {spec['info'].get('title')}")
                        print(f"  Version: {spec['info'].get('version')}")
                    
                    if 'paths' in spec:
                        print(f"\n📍 Available Endpoints:")
                        for path, methods in list(spec['paths'].items())[:20]:
                            print(f"  {path}")
                            for method, details in methods.items():
                                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                                    summary = details.get('summary', 'No description')
                                    print(f"    {method.upper()}: {summary}")
                        
                        if len(spec['paths']) > 20:
                            print(f"  ... and {len(spec['paths']) - 20} more endpoints")
                    
                    return spec
            except Exception as e:
                print(f"❌ {url}: {str(e)[:50]}")
        
        # If no spec found, scrape the docs page
        print(f"\n⚠️  No OpenAPI spec found. Scraping documentation page...")
        try:
            response = await client.get("https://api.fiscal.ai/docs")
            html = response.text
            
            # Look for endpoint patterns in the HTML
            import re
            endpoints = re.findall(r'/[a-z0-9/_\-{}]+', html)
            unique_endpoints = sorted(set(endpoints))
            
            print(f"\n📍 Endpoints found in documentation:")
            for endpoint in unique_endpoints[:30]:
                if endpoint not in ['/css', '/js', '/img', '/favicon']:
                    print(f"  {endpoint}")
            
        except Exception as e:
            print(f"Error scraping docs: {e}")

import asyncio
asyncio.run(get_swagger_spec())

# Now test the correct endpoints
print("\n" + "="*70)
print("  TESTING WITH CORRECT CONFIGURATION")
print("="*70)

async def test_correct_config():
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    
    # Common financial API endpoint patterns
    test_endpoints = [
        # Company/Stock endpoints
        ("GET", "companies/list"),
        ("GET", "companies"),
        ("GET", "stock/AAPL"),
        ("GET", "stocks/AAPL"),
        ("GET", "ticker/AAPL"),
        ("GET", "tickers/AAPL"),
        ("GET", "quote/AAPL"),
        ("GET", "profile/AAPL"),
        
        # Financial data endpoints
        ("GET", "financials/AAPL"),
        ("GET", "income-statement/AAPL"),
        ("GET", "balance-sheet/AAPL"),
        ("GET", "cash-flow/AAPL"),
        
        # Search
        ("GET", "search?q=Apple"),
        ("GET", "search?query=AAPL"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print(f"\nUsing: X-API-KEY header with key {API_KEY[:20]}...")
        
        for method, endpoint in test_endpoints:
            try:
                url = f"https://api.fiscal.ai/v1/{endpoint}"
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers
                )
                
                if response.status_code == 200:
                    print(f"\n✅ SUCCESS: {method} {endpoint}")
                    print(f"   Full URL: {url}")
                    try:
                        data = response.json()
                        preview = json.dumps(data, indent=4)
                        print(f"   Response: {preview[:300]}...")
                    except:
                        print(f"   Response: {response.text[:200]}")
                    
                    print(f"\n{'🎉'*25}")
                    print(f"   WORKING ENDPOINT FOUND!")
                    print(f"   URL Pattern: https://api.fiscal.ai/v1/{'{endpoint}'}")
                    print(f"   Headers: {{'X-API-KEY': '{API_KEY}'}}")
                    print(f"{'🎉'*25}\n")
                    return True
                    
                elif response.status_code == 404:
                    print(f"  ⚠️  {endpoint}: 404 (doesn't exist)")
                elif response.status_code == 401:
                    print(f"  ❌ {endpoint}: 401 (auth failed)")
                elif response.status_code == 400:
                    try:
                        error = response.json()
                        print(f"  ❌ {endpoint}: 400 - {error}")
                    except:
                        print(f"  ❌ {endpoint}: 400")
                else:
                    print(f"  ❌ {endpoint}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {endpoint}: {str(e)[:50]}")

asyncio.run(test_correct_config())

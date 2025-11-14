import requests
import json
import os

# SECURITY FIX: Load API key from environment variable
API_KEY = os.environ.get('FISCAL_AI_API_KEY')
if not API_KEY:
    raise ValueError("FISCAL_AI_API_KEY environment variable must be set")

# Test different API configurations
test_configs = [
    {
        "name": "Bearer Token in Authorization",
        "base_url": "https://api.fiscal.ai/v1",
        "headers": {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    },
    {
        "name": "X-API-Key Header",
        "base_url": "https://api.fiscal.ai/v1",
        "headers": {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    },
    {
        "name": "X-API-Key Header (lowercase)",
        "base_url": "https://api.fiscal.ai/v1",
        "headers": {"x-api-key": API_KEY, "Content-Type": "application/json"}
    },
    {
        "name": "api_key Query Parameter",
        "base_url": "https://api.fiscal.ai/v1",
        "headers": {"Content-Type": "application/json"},
        "params": {"api_key": API_KEY}
    },
    {
        "name": "No /v1 prefix",
        "base_url": "https://api.fiscal.ai",
        "headers": {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    },
    {
        "name": "fiscaldata.ai domain",
        "base_url": "https://api.fiscaldata.ai/v1",
        "headers": {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    }
]

# Test endpoints
test_endpoints = [
    "company/profile/AAPL",
    "companies/profile/AAPL",
    "companies/AAPL",
    "stock/AAPL",
    "ticker/AAPL",
    "companies",
    "status",
    "health"
]

async def test_api():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("\n" + "="*70)
        print("  FISCAL.AI API DIAGNOSTICS - TESTING NEW API KEY")
        print("="*70)
        print(f"\nAPI Key: {API_KEY[:20]}...")
        
        for config in test_configs:
            print(f"\n{'='*70}")
            print(f"🧪 Testing Configuration: {config['name']}")
            print(f"   Base URL: {config['base_url']}")
            print(f"   Headers: {config['headers']}")
            if config.get('params'):
                print(f"   Params: {config['params']}")
            print(f"{'-'*70}")
            
            for endpoint in test_endpoints:
                try:
                    url = f"{config['base_url']}/{endpoint}"
                    response = await client.get(
                        url,
                        headers=config['headers'],
                        params=config.get('params', {}),
                        follow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        print(f"   ✅ SUCCESS! Endpoint: {endpoint}")
                        print(f"      Full URL: {url}")
                        print(f"      Status: {response.status_code}")
                        
                        try:
                            data = response.json()
                            print(f"      Response Preview:")
                            preview = json.dumps(data, indent=8)
                            if len(preview) > 500:
                                print(f"{preview[:500]}...")
                            else:
                                print(preview)
                        except:
                            print(f"      Response Text: {response.text[:200]}")
                        
                        print(f"\n   {'🎉'*20}")
                        print(f"   🎉 WORKING CONFIGURATION FOUND!")
                        print(f"   {'🎉'*20}")
                        print(f"\n   Configuration Details:")
                        print(f"      Base URL: {config['base_url']}")
                        print(f"      Headers: {json.dumps(config['headers'], indent=8)}")
                        if config.get('params'):
                            print(f"      Params: {json.dumps(config['params'], indent=8)}")
                        print(f"      Working Endpoint: {endpoint}")
                        print(f"      Full URL Pattern: {config['base_url']}/{'{endpoint}'}")
                        print(f"\n   Save this configuration for your client!")
                        return True
                    elif response.status_code == 401:
                        print(f"   ❌ {endpoint}: 401 Unauthorized")
                    elif response.status_code == 403:
                        print(f"   ❌ {endpoint}: 403 Forbidden")
                    elif response.status_code == 404:
                        print(f"   ⚠️  {endpoint}: 404 Not Found (endpoint doesn't exist)")
                    elif response.status_code == 400:
                        print(f"   ❌ {endpoint}: 400 Bad Request")
                        try:
                            error = response.json()
                            if error:
                                print(f"      Error details: {json.dumps(error, indent=8)}")
                        except:
                            text = response.text[:200]
                            if text:
                                print(f"      Response: {text}")
                    else:
                        print(f"   ❌ {endpoint}: {response.status_code}")
                                
                except httpx.ConnectError as e:
                    print(f"   ❌ {endpoint}: Connection failed - {str(e)[:60]}")
                except httpx.TimeoutException:
                    print(f"   ❌ {endpoint}: Timeout")
                except Exception as e:
                    print(f"   ❌ {endpoint}: {str(e)[:80]}")
        
        print("\n" + "="*70)
        print("⚠️  NO WORKING CONFIGURATION FOUND")
        print("="*70)
        print("\nTroubleshooting steps:")
        print("  1. Verify API key is active at https://fiscal.ai/dashboard")
        print("  2. Check API documentation: https://docs.fiscal.ai")
        print("  3. Ensure subscription/trial is active")
        print("  4. Contact Fiscal.ai support if key is valid")
        print("\nAPI Key used: {API_KEY}")
        return False

import asyncio
result = asyncio.run(test_api())

if not result:
    print("\n" + "="*70)
    print("📚 Let's check the actual documentation...")
    print("="*70)
    print("\nAttempting to access Fiscal.ai documentation endpoints...")
    
    async def check_docs():
        async with httpx.AsyncClient(timeout=10.0) as client:
            docs_urls = [
                "https://docs.fiscal.ai",
                "https://api.fiscal.ai",
                "https://fiscal.ai/api",
                "https://api.fiscal.ai/docs"
            ]
            
            for url in docs_urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    print(f"\n{url}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   Content preview: {response.text[:200]}...")
                except Exception as e:
                    print(f"{url}: Failed - {str(e)[:50]}")
    
    asyncio.run(check_docs())

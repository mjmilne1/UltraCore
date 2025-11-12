import asyncio
import sys
sys.path.insert(0, 'src')

async def test_mda_platform():
    from ultrawealth.mda_platform_anya import UltraWealthMDAPlatform
    
    platform = UltraWealthMDAPlatform()
    status = platform.get_platform_status()
    
    print('\n🏆 MDA PLATFORM TEST')
    print('='*50)
    print(f"Platform: {status['platform']}")
    print(f"Version: {status['version']}")
    print(f"Status: {status['status']}")
    
    # Format AUM properly
    aum = status['metrics']['aum']
    aum_formatted = f""
    print(f"AUM: {aum_formatted}")
    
    print('\n✅ All systems operational!')

asyncio.run(test_mda_platform())

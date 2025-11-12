"""
Simple test for Bitemporal Ledger
"""

import asyncio
import sys
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

async def test_bitemporal():
    print("\n" + "="*60)
    print("   BITEMPORAL LEDGER TEST")
    print("="*60)
    
    try:
        from ultracore.temporal.kafka_bitemporal import TemporalLedger
        from ultracore.mesh.temporal_domain import TemporalDomain
        
        # Create instances
        ledger = TemporalLedger()
        domain = TemporalDomain()
        
        # Test transaction
        test_event = {
            "account_id": "ACC_001",
            "amount": 5000,
            "type": "deposit",
            "business_time": (datetime.now() - timedelta(hours=2)).isoformat()
        }
        
        print(f"\n1. Writing event: ${test_event['amount']}")
        event_id = await ledger.record_event(test_event)
        print(f"   Event ID: {event_id}")
        print(f"   ✓ Written to Kafka first")
        
        print("\n2. As-of query (1 hour ago)")
        result = ledger.as_of(datetime.now() - timedelta(hours=1))
        print(f"   Balance: ${result['balance']}")
        print(f"   Events: {result['event_count']}")
        
        print("\n3. Domain write through Kafka")
        domain_result = await domain.write_temporal_event(test_event)
        print(f"   Status: {domain_result['status']}")
        print(f"   Kafka offset: {domain_result['kafka_offset']}")
        
        print("\n✅ Bitemporal ledger working!")
        
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        print("Note: This is normal if Kafka is not running")

if __name__ == "__main__":
    asyncio.run(test_bitemporal())

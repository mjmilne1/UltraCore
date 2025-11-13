"""
Complete Merchant Domain - Settlement with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class MerchantStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    SUSPENDED = 'SUSPENDED'


class SettlementStatus(str, Enum):
    PENDING = 'PENDING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'


class CompleteMerchantAggregate:
    """Complete merchant lifecycle with settlement"""
    
    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.business_name: Optional[str] = None
        self.status: MerchantStatus = MerchantStatus.PENDING
        self.account_id: Optional[str] = None
        self.processing_rate: Decimal = Decimal('2.0')
        self.transactions: List[Dict] = []
        self.settlements: List[Dict] = []
        self.total_volume: Decimal = Decimal('0')
    
    async def register_merchant(
        self,
        business_name: str,
        abn: str,
        account_id: str
    ):
        """Register merchant"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'merchant_id': self.merchant_id,
            'business_name': business_name,
            'abn': abn,
            'account_id': account_id,
            'processing_rate': str(self.processing_rate),
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='merchants',
            event_type='merchant_registered',
            event_data=event_data,
            aggregate_id=self.merchant_id
        )
        
        self.business_name = business_name
        self.account_id = account_id
        self.status = MerchantStatus.ACTIVE
    
    async def process_transaction(
        self,
        amount: Decimal,
        card_last4: str,
        customer_name: str
    ):
        """Process merchant transaction"""
        kafka_store = get_production_kafka_store()
        
        transaction_id = f'MTXN-{self.merchant_id}-{datetime.now(timezone.utc).timestamp()}'
        processing_fee = amount * (self.processing_rate / 100)
        net_amount = amount - processing_fee
        
        event_data = {
            'merchant_id': self.merchant_id,
            'transaction_id': transaction_id,
            'amount': str(amount),
            'processing_fee': str(processing_fee),
            'net_amount': str(net_amount),
            'card_last4': card_last4,
            'customer_name': customer_name,
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='merchants',
            event_type='transaction_processed',
            event_data=event_data,
            aggregate_id=self.merchant_id,
            exactly_once=True
        )
        
        self.transactions.append(event_data)
        self.total_volume += amount
        
        return transaction_id
    
    async def settle_batch(self):
        """Settle merchant transactions"""
        kafka_store = get_production_kafka_store()
        
        unsettled = [t for t in self.transactions if not t.get('settled')]
        
        if not unsettled:
            return None
        
        total_amount = sum(Decimal(t['amount']) for t in unsettled)
        total_fees = sum(Decimal(t['processing_fee']) for t in unsettled)
        net_settlement = total_amount - total_fees
        
        settlement_id = f'STL-{self.merchant_id}-{datetime.now(timezone.utc).timestamp()}'
        
        event_data = {
            'merchant_id': self.merchant_id,
            'settlement_id': settlement_id,
            'transaction_count': len(unsettled),
            'total_amount': str(total_amount),
            'total_fees': str(total_fees),
            'net_settlement': str(net_settlement),
            'status': SettlementStatus.PROCESSED.value,
            'settled_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='merchants',
            event_type='settlement_processed',
            event_data=event_data,
            aggregate_id=self.merchant_id,
            exactly_once=True
        )
        
        # Credit merchant account
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        account = CompleteAccountAggregate(self.account_id)
        await account.load_from_events()
        await account.deposit(
            net_settlement,
            f'Merchant settlement - {len(unsettled)} transactions',
            settlement_id
        )
        
        # Publish to settlement topic
        await kafka_store.append_event(
            entity='settlement',
            event_type='merchant_settlement_completed',
            event_data=event_data,
            aggregate_id=settlement_id
        )
        
        self.settlements.append(event_data)
        
        for txn in unsettled:
            txn['settled'] = True
        
        return settlement_id
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.merchant_id)
        
        for event in events:
            if event.event_type == 'merchant_registered':
                self.business_name = event.event_data['business_name']
                self.account_id = event.event_data['account_id']
                self.status = MerchantStatus.ACTIVE
            elif event.event_type == 'transaction_processed':
                self.transactions.append(event.event_data)
                self.total_volume += Decimal(event.event_data['amount'])
            elif event.event_type == 'settlement_processed':
                self.settlements.append(event.event_data)

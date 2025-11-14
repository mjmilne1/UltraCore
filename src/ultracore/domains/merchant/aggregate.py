"""
Merchant Domain - Business Banking
"""
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store


class MerchantType(str, Enum):
    RETAIL = 'RETAIL'
    ECOMMERCE = 'ECOMMERCE'


class MerchantStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'


class RegisterMerchantRequest(BaseModel):
    business_name: str
    abn: str
    merchant_type: MerchantType
    monthly_volume: float


class ProcessPaymentRequest(BaseModel):
    amount: float
    card_last_4: str
    customer_name: str
    description: str


class MerchantAggregate:
    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.business_name: Optional[str] = None
        self.status: MerchantStatus = MerchantStatus.PENDING
        self.processing_rate: Decimal = Decimal('2.0')
    
    async def register_merchant(self, business_name: str, abn: str):
        store = get_event_store()
        
        event_data = {
            'merchant_id': self.merchant_id,
            'business_name': business_name,
            'abn': abn,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.merchant_id,
            aggregate_type='Merchant',
            event_type='MerchantRegistered',
            event_data=event_data,
            user_id='merchant_system'
        )
        
        self.business_name = business_name
        self.status = MerchantStatus.ACTIVE
    
    async def load_from_events(self):
        store = get_event_store()
        events = await store.get_events(self.merchant_id)
        
        for event in events:
            if event.event_type == 'MerchantRegistered':
                self.business_name = event.event_data['business_name']
                self.status = MerchantStatus.ACTIVE

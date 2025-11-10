"""
Payment Domain - Money Transfers & Payments
Now with Event Bus integration
"""
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.domains.account.aggregate import AccountAggregate
from ultracore.ml_models.pipeline import ml_pipeline
from ultracore.infrastructure.event_bus.publishers import DomainEventPublisher


class PaymentType(str, Enum):
    INTERNAL_TRANSFER = 'INTERNAL_TRANSFER'
    EXTERNAL_TRANSFER = 'EXTERNAL_TRANSFER'
    BILL_PAYMENT = 'BILL_PAYMENT'


class PaymentStatus(str, Enum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    FRAUD_HOLD = 'FRAUD_HOLD'


class CreatePaymentRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    payment_type: PaymentType
    description: str
    reference: Optional[str] = None


class PaymentAggregate:
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        self.from_account_id: Optional[str] = None
        self.to_account_id: Optional[str] = None
        self.amount: Decimal = Decimal('0')
        self.payment_type: Optional[PaymentType] = None
        self.status: PaymentStatus = PaymentStatus.PENDING
        self.fraud_score: Optional[float] = None
    
    async def initiate_payment(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        payment_type: PaymentType,
        description: str,
        reference: str = None
    ):
        store = get_event_store()
        
        event_data = {
            'payment_id': self.payment_id,
            'from_account_id': from_account_id,
            'to_account_id': to_account_id,
            'amount': str(amount),
            'payment_type': payment_type.value,
            'description': description,
            'initiated_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.payment_id,
            aggregate_type='Payment',
            event_type='PaymentInitiated',
            event_data=event_data,
            user_id='payment_system'
        )
        
        # Publish to Event Bus
        await DomainEventPublisher.publish_payment_event(
            event_type='PaymentInitiated',
            aggregate_id=self.payment_id,
            event_data=event_data
        )
        
        self.from_account_id = from_account_id
        self.to_account_id = to_account_id
        self.amount = amount
        self.payment_type = payment_type
        self.status = PaymentStatus.PENDING
    
    async def fraud_check(self):
        store = get_event_store()
        
        fraud_result = await ml_pipeline.detect_fraud({
            'amount': float(self.amount),
            'international': False,
            'unusual_time': False
        })
        
        self.fraud_score = fraud_result['fraud_score']
        
        event_data = {
            'payment_id': self.payment_id,
            'fraud_score': fraud_result['fraud_score'],
            'is_fraudulent': fraud_result['is_fraudulent'],
            'checked_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.payment_id,
            aggregate_type='Payment',
            event_type='PaymentFraudChecked',
            event_data=event_data,
            user_id='fraud_system'
        )
        
        # Publish fraud event if detected
        if fraud_result['is_fraudulent']:
            await DomainEventPublisher.publish_fraud_event(
                event_type='FraudDetected',
                aggregate_id=self.payment_id,
                event_data={
                    **event_data,
                    'fraud_flags': fraud_result['flags']
                }
            )
            self.status = PaymentStatus.FRAUD_HOLD
            return False
        
        return True
    
    async def process(self):
        store = get_event_store()
        
        from_account = AccountAggregate(self.from_account_id)
        await from_account.load_from_events()
        
        to_account = AccountAggregate(self.to_account_id)
        await to_account.load_from_events()
        
        if from_account.balance < self.amount:
            await self.fail('Insufficient funds')
            raise ValueError('Insufficient funds')
        
        await from_account.withdraw(
            amount=self.amount,
            description=f'Payment to {self.to_account_id}',
            reference=self.payment_id
        )
        
        await to_account.deposit(
            amount=self.amount,
            description=f'Payment from {self.from_account_id}',
            reference=self.payment_id
        )
        
        event_data = {
            'payment_id': self.payment_id,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.payment_id,
            aggregate_type='Payment',
            event_type='PaymentCompleted',
            event_data=event_data,
            user_id='payment_system'
        )
        
        # Publish to Event Bus
        await DomainEventPublisher.publish_payment_event(
            event_type='PaymentCompleted',
            aggregate_id=self.payment_id,
            event_data=event_data
        )
        
        self.status = PaymentStatus.COMPLETED
    
    async def fail(self, reason: str):
        store = get_event_store()
        
        event_data = {
            'payment_id': self.payment_id,
            'reason': reason,
            'failed_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.payment_id,
            aggregate_type='Payment',
            event_type='PaymentFailed',
            event_data=event_data,
            user_id='payment_system'
        )
        
        # Publish to Event Bus
        await DomainEventPublisher.publish_payment_event(
            event_type='PaymentFailed',
            aggregate_id=self.payment_id,
            event_data=event_data
        )
        
        self.status = PaymentStatus.FAILED
    
    async def load_from_events(self):
        store = get_event_store()
        events = await store.get_events(self.payment_id)
        
        for event in events:
            if event.event_type == 'PaymentInitiated':
                self.from_account_id = event.event_data['from_account_id']
                self.to_account_id = event.event_data['to_account_id']
                self.amount = Decimal(event.event_data['amount'])
                self.payment_type = PaymentType(event.event_data['payment_type'])
                self.status = PaymentStatus.PENDING
            elif event.event_type == 'PaymentCompleted':
                self.status = PaymentStatus.COMPLETED
            elif event.event_type == 'PaymentFailed':
                self.status = PaymentStatus.FAILED

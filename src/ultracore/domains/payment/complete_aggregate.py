"""
Complete Payment Domain - Full Payment Rails with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.data_mesh.integration import DataMeshPublisher
from ultracore.ml_models.enhanced_pipeline import enhanced_ml
from ultracore.ledger.general_ledger import ledger


class PaymentType(str, Enum):
    INTERNAL_TRANSFER = 'INTERNAL_TRANSFER'
    EXTERNAL_TRANSFER = 'EXTERNAL_TRANSFER'
    BILL_PAYMENT = 'BILL_PAYMENT'
    P2P = 'P2P'
    INTERNATIONAL = 'INTERNATIONAL'


class PaymentStatus(str, Enum):
    INITIATED = 'INITIATED'
    PENDING_FRAUD_CHECK = 'PENDING_FRAUD_CHECK'
    FRAUD_HOLD = 'FRAUD_HOLD'
    APPROVED = 'APPROVED'
    PROCESSING = 'PROCESSING'
    CLEARING = 'CLEARING'
    SETTLED = 'SETTLED'
    FAILED = 'FAILED'
    REVERSED = 'REVERSED'


class PaymentRail(str, Enum):
    BPAY = 'BPAY'
    OSKO = 'OSKO'
    DE = 'DE'
    SWIFT = 'SWIFT'
    INTERNAL = 'INTERNAL'


class CompletePaymentAggregate:
    """Complete payment lifecycle with fraud detection"""
    
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        self.from_account_id: Optional[str] = None
        self.to_account_id: Optional[str] = None
        self.amount: Decimal = Decimal('0')
        self.payment_type: Optional[PaymentType] = None
        self.payment_rail: Optional[PaymentRail] = None
        self.status: PaymentStatus = PaymentStatus.INITIATED
        self.fraud_score: Optional[float] = None
        self.fraud_flags: List[str] = []
        self.clearing_id: Optional[str] = None
        self.settlement_date: Optional[str] = None
    
    async def initiate_payment(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        payment_type: PaymentType,
        description: str,
        reference: Optional[str] = None
    ):
        """Initiate payment"""
        kafka_store = get_production_kafka_store()
        
        # Determine payment rail
        payment_rail = self._determine_payment_rail(payment_type, amount)
        
        event_data = {
            'payment_id': self.payment_id,
            'from_account_id': from_account_id,
            'to_account_id': to_account_id,
            'amount': str(amount),
            'payment_type': payment_type.value,
            'payment_rail': payment_rail.value,
            'description': description,
            'reference': reference,
            'initiated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_initiated',
            event_data=event_data,
            aggregate_id=self.payment_id,
            exactly_once=True
        )
        
        self.from_account_id = from_account_id
        self.to_account_id = to_account_id
        self.amount = amount
        self.payment_type = payment_type
        self.payment_rail = payment_rail
        self.status = PaymentStatus.INITIATED
        
        await DataMeshPublisher.publish_transaction_data(
            self.payment_id,
            event_data
        )
    
    async def fraud_check(self):
        """ML-powered fraud detection"""
        kafka_store = get_production_kafka_store()
        
        # Determine if unusual
        is_international = self.payment_type == PaymentType.INTERNATIONAL
        is_large_amount = self.amount > Decimal('5000')
        
        fraud_result = await enhanced_ml.detect_fraud({
            'amount': float(self.amount),
            'international': is_international,
            'unusual_time': False
        })
        
        self.fraud_score = fraud_result['fraud_score']
        self.fraud_flags = fraud_result.get('flags', [])
        
        is_fraudulent = fraud_result['is_fraudulent']
        
        event_data = {
            'payment_id': self.payment_id,
            'fraud_score': fraud_result['fraud_score'],
            'is_fraudulent': is_fraudulent,
            'fraud_flags': self.fraud_flags,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='fraud_check_completed',
            event_data=event_data,
            aggregate_id=self.payment_id
        )
        
        # Publish to fraud topic if detected
        if is_fraudulent:
            await kafka_store.append_event(
                entity='fraud',
                event_type='payment_fraud_detected',
                event_data={
                    **event_data,
                    'payment_details': {
                        'amount': str(self.amount),
                        'payment_type': self.payment_type.value
                    }
                },
                aggregate_id=self.payment_id
            )
            
            self.status = PaymentStatus.FRAUD_HOLD
            return False
        
        self.status = PaymentStatus.APPROVED
        return True
    
    async def process_payment(self):
        """Process approved payment"""
        if self.status != PaymentStatus.APPROVED:
            raise ValueError(f'Payment not approved. Status: {self.status}')
        
        kafka_store = get_production_kafka_store()
        
        # Place hold on source account
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        from_account = CompleteAccountAggregate(self.from_account_id)
        await from_account.load_from_events()
        await from_account.place_hold(self.payment_id, self.amount, 'Payment processing')
        
        event_data = {
            'payment_id': self.payment_id,
            'processing_started': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_processing_started',
            event_data=event_data,
            aggregate_id=self.payment_id
        )
        
        self.status = PaymentStatus.PROCESSING
    
    async def clear_payment(self):
        """Clear payment through payment rail"""
        kafka_store = get_production_kafka_store()
        
        clearing_id = f'CLR-{self.payment_id}'
        
        event_data = {
            'payment_id': self.payment_id,
            'clearing_id': clearing_id,
            'payment_rail': self.payment_rail.value,
            'cleared_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_cleared',
            event_data=event_data,
            aggregate_id=self.payment_id
        )
        
        self.clearing_id = clearing_id
        self.status = PaymentStatus.CLEARING
    
    async def settle_payment(self):
        """Settle payment"""
        kafka_store = get_production_kafka_store()
        
        # Execute account movements
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        
        from_account = CompleteAccountAggregate(self.from_account_id)
        await from_account.load_from_events()
        
        to_account = CompleteAccountAggregate(self.to_account_id)
        await to_account.load_from_events()
        
        # Release hold and withdraw
        await from_account.release_hold(self.payment_id)
        await from_account.withdraw(
            self.amount,
            f'Payment to {self.to_account_id}',
            self.payment_id
        )
        
        # Deposit to destination
        await to_account.deposit(
            self.amount,
            f'Payment from {self.from_account_id}',
            self.payment_id
        )
        
        settlement_date = datetime.now(timezone.utc).isoformat()
        
        event_data = {
            'payment_id': self.payment_id,
            'settlement_date': settlement_date,
            'settled_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_settled',
            event_data=event_data,
            aggregate_id=self.payment_id,
            exactly_once=True
        )
        
        # Post to ledger
        await ledger.post_journal_entry(
            entry_id=f'JE-PAY-{self.payment_id}',
            date=settlement_date,
            description=f'Payment settlement',
            reference=self.payment_id,
            debits=[{'account': '2000', 'amount': float(self.amount)}],
            credits=[{'account': '2000', 'amount': float(self.amount)}],
            posted_by='payment_system'
        )
        
        self.settlement_date = settlement_date
        self.status = PaymentStatus.SETTLED
    
    async def fail_payment(self, reason: str):
        """Fail payment"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'payment_id': self.payment_id,
            'reason': reason,
            'failed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_failed',
            event_data=event_data,
            aggregate_id=self.payment_id
        )
        
        # Release hold if exists
        if self.status in [PaymentStatus.PROCESSING, PaymentStatus.CLEARING]:
            from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
            from_account = CompleteAccountAggregate(self.from_account_id)
            await from_account.load_from_events()
            
            try:
                await from_account.release_hold(self.payment_id)
            except:
                pass
        
        self.status = PaymentStatus.FAILED
    
    async def reverse_payment(self, reason: str):
        """Reverse settled payment"""
        if self.status != PaymentStatus.SETTLED:
            raise ValueError('Only settled payments can be reversed')
        
        kafka_store = get_production_kafka_store()
        
        # Execute reverse movements
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        
        from_account = CompleteAccountAggregate(self.from_account_id)
        await from_account.load_from_events()
        
        to_account = CompleteAccountAggregate(self.to_account_id)
        await to_account.load_from_events()
        
        # Reverse: withdraw from destination, deposit to source
        await to_account.withdraw(
            self.amount,
            f'Payment reversal - {reason}',
            f'REV-{self.payment_id}'
        )
        
        await from_account.deposit(
            self.amount,
            f'Payment reversal - {reason}',
            f'REV-{self.payment_id}'
        )
        
        event_data = {
            'payment_id': self.payment_id,
            'reason': reason,
            'reversed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='payments',
            event_type='payment_reversed',
            event_data=event_data,
            aggregate_id=self.payment_id,
            exactly_once=True
        )
        
        # Post reversal to ledger
        await ledger.post_journal_entry(
            entry_id=f'JE-REV-{self.payment_id}',
            date=datetime.now(timezone.utc).isoformat(),
            description=f'Payment reversal: {reason}',
            reference=self.payment_id,
            debits=[{'account': '2000', 'amount': float(self.amount)}],
            credits=[{'account': '2000', 'amount': float(self.amount)}],
            posted_by='payment_system'
        )
        
        self.status = PaymentStatus.REVERSED
    
    def _determine_payment_rail(self, payment_type: PaymentType, amount: Decimal) -> PaymentRail:
        """Determine appropriate payment rail"""
        if payment_type == PaymentType.INTERNAL_TRANSFER:
            return PaymentRail.INTERNAL
        elif payment_type == PaymentType.INTERNATIONAL:
            return PaymentRail.SWIFT
        elif payment_type == PaymentType.BILL_PAYMENT:
            return PaymentRail.BPAY
        elif amount > Decimal('1000'):
            return PaymentRail.DE
        else:
            return PaymentRail.OSKO
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.payment_id)
        
        for event in events:
            if event.event_type == 'payment_initiated':
                self.from_account_id = event.event_data['from_account_id']
                self.to_account_id = event.event_data['to_account_id']
                self.amount = Decimal(event.event_data['amount'])
                self.payment_type = PaymentType(event.event_data['payment_type'])
                self.payment_rail = PaymentRail(event.event_data['payment_rail'])
                self.status = PaymentStatus.INITIATED
            elif event.event_type == 'fraud_check_completed':
                self.fraud_score = event.event_data['fraud_score']
                self.fraud_flags = event.event_data.get('fraud_flags', [])
                if event.event_data['is_fraudulent']:
                    self.status = PaymentStatus.FRAUD_HOLD
                else:
                    self.status = PaymentStatus.APPROVED
            elif event.event_type == 'payment_processing_started':
                self.status = PaymentStatus.PROCESSING
            elif event.event_type == 'payment_cleared':
                self.clearing_id = event.event_data['clearing_id']
                self.status = PaymentStatus.CLEARING
            elif event.event_type == 'payment_settled':
                self.settlement_date = event.event_data['settlement_date']
                self.status = PaymentStatus.SETTLED
            elif event.event_type == 'payment_failed':
                self.status = PaymentStatus.FAILED
            elif event.event_type == 'payment_reversed':
                self.status = PaymentStatus.REVERSED

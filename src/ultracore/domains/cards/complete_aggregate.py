"""
Complete Cards Domain - Full Card Lifecycle with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import random

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.enhanced_pipeline import enhanced_ml


class CardType(str, Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'
    PREPAID = 'PREPAID'


class CardStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'
    EXPIRED = 'EXPIRED'
    CANCELLED = 'CANCELLED'


class TransactionStatus(str, Enum):
    AUTHORIZED = 'AUTHORIZED'
    DECLINED = 'DECLINED'
    REVERSED = 'REVERSED'
    SETTLED = 'SETTLED'


class DisputeStatus(str, Enum):
    OPEN = 'OPEN'
    INVESTIGATING = 'INVESTIGATING'
    RESOLVED = 'RESOLVED'
    REJECTED = 'REJECTED'


class CompleteCardAggregate:
    """Complete card lifecycle with fraud detection"""
    
    def __init__(self, card_id: str):
        self.card_id = card_id
        self.account_id: Optional[str] = None
        self.card_type: Optional[CardType] = None
        self.card_number_last4: Optional[str] = None
        self.status: CardStatus = CardStatus.PENDING
        self.credit_limit: Decimal = Decimal('0')
        self.available_credit: Decimal = Decimal('0')
        self.daily_limit: Decimal = Decimal('5000')
        self.transactions: List[Dict] = []
        self.disputes: List[Dict] = []
        self.expiry_date: Optional[str] = None
    
    async def issue_card(
        self,
        account_id: str,
        card_type: CardType,
        credit_limit: Optional[Decimal] = None
    ):
        """Issue new card"""
        kafka_store = get_production_kafka_store()
        
        # Generate card details
        card_number_last4 = str(random.randint(1000, 9999))
        expiry_date = (datetime.now(timezone.utc) + timedelta(days=1095)).strftime('%m/%y')
        
        event_data = {
            'card_id': self.card_id,
            'account_id': account_id,
            'card_type': card_type.value,
            'card_number_last4': card_number_last4,
            'expiry_date': expiry_date,
            'credit_limit': str(credit_limit) if credit_limit else None,
            'issued_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='card_issued',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        self.account_id = account_id
        self.card_type = card_type
        self.card_number_last4 = card_number_last4
        self.expiry_date = expiry_date
        self.status = CardStatus.PENDING
        
        if credit_limit:
            self.credit_limit = credit_limit
            self.available_credit = credit_limit
    
    async def activate_card(self):
        """Activate card"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'card_id': self.card_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='card_activated',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        self.status = CardStatus.ACTIVE
    
    async def authorize_transaction(
        self,
        amount: Decimal,
        merchant: str,
        merchant_category: str,
        location: str
    ):
        """Authorize card transaction with fraud check"""
        if self.status != CardStatus.ACTIVE:
            return await self._decline_transaction(amount, merchant, 'Card not active')
        
        # Check limits
        if self.card_type == CardType.CREDIT:
            if amount > self.available_credit:
                return await self._decline_transaction(amount, merchant, 'Insufficient credit')
        else:
            from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
            account = CompleteAccountAggregate(self.account_id)
            await account.load_from_events()
            if amount > account.available_balance:
                return await self._decline_transaction(amount, merchant, 'Insufficient funds')
        
        # ML fraud detection
        fraud_result = await enhanced_ml.detect_fraud({
            'amount': float(amount),
            'international': 'international' in location.lower(),
            'unusual_time': datetime.now(timezone.utc).hour < 6 or datetime.now(timezone.utc).hour > 23
        })
        
        if fraud_result['is_fraudulent']:
            await self._block_card('Suspected fraud')
            return await self._decline_transaction(amount, merchant, 'Suspected fraud')
        
        kafka_store = get_production_kafka_store()
        
        transaction_id = f'TXN-{self.card_id}-{datetime.now(timezone.utc).timestamp()}'
        
        event_data = {
            'card_id': self.card_id,
            'transaction_id': transaction_id,
            'amount': str(amount),
            'merchant': merchant,
            'merchant_category': merchant_category,
            'location': location,
            'fraud_score': fraud_result['fraud_score'],
            'status': TransactionStatus.AUTHORIZED.value,
            'authorized_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='transaction_authorized',
            event_data=event_data,
            aggregate_id=self.card_id,
            exactly_once=True
        )
        
        # Place hold
        if self.card_type == CardType.CREDIT:
            self.available_credit -= amount
        else:
            from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
            account = CompleteAccountAggregate(self.account_id)
            await account.load_from_events()
            await account.place_hold(transaction_id, amount, f'Card transaction - {merchant}')
        
        self.transactions.append(event_data)
        return transaction_id
    
    async def _decline_transaction(self, amount: Decimal, merchant: str, reason: str):
        """Decline transaction"""
        kafka_store = get_production_kafka_store()
        
        transaction_id = f'TXN-{self.card_id}-{datetime.now(timezone.utc).timestamp()}'
        
        event_data = {
            'card_id': self.card_id,
            'transaction_id': transaction_id,
            'amount': str(amount),
            'merchant': merchant,
            'status': TransactionStatus.DECLINED.value,
            'decline_reason': reason,
            'declined_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='transaction_declined',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        return None
    
    async def settle_transaction(self, transaction_id: str):
        """Settle authorized transaction"""
        transaction = next((t for t in self.transactions if t['transaction_id'] == transaction_id), None)
        if not transaction:
            raise ValueError('Transaction not found')
        
        kafka_store = get_production_kafka_store()
        amount = Decimal(transaction['amount'])
        
        event_data = {
            'card_id': self.card_id,
            'transaction_id': transaction_id,
            'settled_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='transaction_settled',
            event_data=event_data,
            aggregate_id=self.card_id,
            exactly_once=True
        )
        
        # Execute payment
        if self.card_type == CardType.CREDIT:
            # Credit card: no immediate debit
            pass
        else:
            from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
            account = CompleteAccountAggregate(self.account_id)
            await account.load_from_events()
            await account.release_hold(transaction_id)
            await account.withdraw(amount, f"Card payment - {transaction['merchant']}", transaction_id)
        
        transaction['status'] = TransactionStatus.SETTLED.value
    
    async def dispute_transaction(self, transaction_id: str, reason: str):
        """Dispute a transaction"""
        transaction = next((t for t in self.transactions if t['transaction_id'] == transaction_id), None)
        if not transaction:
            raise ValueError('Transaction not found')
        
        kafka_store = get_production_kafka_store()
        
        dispute_id = f'DSP-{transaction_id}'
        
        event_data = {
            'card_id': self.card_id,
            'dispute_id': dispute_id,
            'transaction_id': transaction_id,
            'reason': reason,
            'status': DisputeStatus.OPEN.value,
            'disputed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='transaction_disputed',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        self.disputes.append(event_data)
        return dispute_id
    
    async def resolve_dispute(self, dispute_id: str, outcome: str, refund: bool):
        """Resolve dispute"""
        dispute = next((d for d in self.disputes if d['dispute_id'] == dispute_id), None)
        if not dispute:
            raise ValueError('Dispute not found')
        
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'card_id': self.card_id,
            'dispute_id': dispute_id,
            'outcome': outcome,
            'refund_issued': refund,
            'resolved_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='dispute_resolved',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        if refund:
            transaction_id = dispute['transaction_id']
            transaction = next((t for t in self.transactions if t['transaction_id'] == transaction_id), None)
            amount = Decimal(transaction['amount'])
            
            if self.card_type == CardType.CREDIT:
                self.available_credit += amount
            else:
                from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
                account = CompleteAccountAggregate(self.account_id)
                await account.load_from_events()
                await account.deposit(amount, f'Dispute refund - {dispute_id}', dispute_id)
        
        dispute['status'] = DisputeStatus.RESOLVED.value
    
    async def _block_card(self, reason: str):
        """Block card"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'card_id': self.card_id,
            'reason': reason,
            'blocked_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='card_blocked',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        self.status = CardStatus.BLOCKED
    
    async def cancel_card(self, reason: str):
        """Cancel card"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'card_id': self.card_id,
            'reason': reason,
            'cancelled_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='cards',
            event_type='card_cancelled',
            event_data=event_data,
            aggregate_id=self.card_id
        )
        
        self.status = CardStatus.CANCELLED
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.card_id)
        
        for event in events:
            if event.event_type == 'card_issued':
                self.account_id = event.event_data['account_id']
                self.card_type = CardType(event.event_data['card_type'])
                self.card_number_last4 = event.event_data['card_number_last4']
                self.expiry_date = event.event_data['expiry_date']
                if event.event_data.get('credit_limit'):
                    self.credit_limit = Decimal(event.event_data['credit_limit'])
                    self.available_credit = self.credit_limit
                self.status = CardStatus.PENDING
            elif event.event_type == 'card_activated':
                self.status = CardStatus.ACTIVE
            elif event.event_type == 'transaction_authorized':
                self.transactions.append(event.event_data)
                if self.card_type == CardType.CREDIT:
                    self.available_credit -= Decimal(event.event_data['amount'])
            elif event.event_type == 'transaction_settled':
                for txn in self.transactions:
                    if txn['transaction_id'] == event.event_data['transaction_id']:
                        txn['status'] = TransactionStatus.SETTLED.value
            elif event.event_type == 'transaction_disputed':
                self.disputes.append(event.event_data)
            elif event.event_type == 'card_blocked':
                self.status = CardStatus.BLOCKED
            elif event.event_type == 'card_cancelled':
                self.status = CardStatus.CANCELLED

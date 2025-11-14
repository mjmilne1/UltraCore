"""
Cards Domain - Credit & Debit Card Management
Complete card lifecycle: Issue, Activate, Transactions, Limits
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import random

from ultracore.infrastructure.event_store.store import get_event_store
# from ultracore.domains.account.aggregate import AccountAggregate  # TODO: Fix import path
from ultracore.ml_models.pipeline import ml_pipeline


class CardType(str, Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'
    PREPAID = 'PREPAID'


class CardStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'
    FROZEN = 'FROZEN'
    EXPIRED = 'EXPIRED'
    CANCELLED = 'CANCELLED'


class IssueCardRequest(BaseModel):
    account_id: str
    card_type: CardType
    credit_limit: Optional[float] = None


class CardTransactionRequest(BaseModel):
    merchant_name: str
    amount: float
    currency: str = 'AUD'
    merchant_category: str = 'RETAIL'


class CardAggregate:
    def __init__(self, card_id: str):
        self.card_id = card_id
        self.account_id: Optional[str] = None
        self.card_type: Optional[CardType] = None
        self.card_number: Optional[str] = None
        self.cvv: Optional[str] = None
        self.expiry_date: Optional[str] = None
        self.status: CardStatus = CardStatus.PENDING
        self.credit_limit: Decimal = Decimal('0')
        self.available_credit: Decimal = Decimal('0')
        self.daily_limit: Decimal = Decimal('5000')
        self.transactions: List[Dict] = []
    
    async def issue_card(
        self,
        account_id: str,
        card_type: CardType,
        credit_limit: Optional[Decimal] = None
    ):
        """Issue a new card"""
        store = get_event_store()
        
        # Generate card details
        card_number = self._generate_card_number()
        cvv = str(random.randint(100, 999))
        expiry_date = (datetime.now(timezone.utc) + timedelta(days=365*3)).strftime('%m/%y')
        
        if card_type == CardType.CREDIT:
            credit_limit = credit_limit or Decimal('5000')
            available_credit = credit_limit
        else:
            credit_limit = Decimal('0')
            available_credit = Decimal('0')
        
        event_data = {
            'card_id': self.card_id,
            'account_id': account_id,
            'card_type': card_type.value,
            'card_number': card_number,
            'cvv': cvv,
            'expiry_date': expiry_date,
            'credit_limit': str(credit_limit),
            'issued_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.card_id,
            aggregate_type='Card',
            event_type='CardIssued',
            event_data=event_data,
            user_id='card_system'
        )
        
        self.account_id = account_id
        self.card_type = card_type
        self.card_number = card_number
        self.cvv = cvv
        self.expiry_date = expiry_date
        self.status = CardStatus.PENDING
        self.credit_limit = credit_limit
        self.available_credit = available_credit
    
    async def activate(self):
        """Activate card"""
        store = get_event_store()
        
        event_data = {
            'card_id': self.card_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.card_id,
            aggregate_type='Card',
            event_type='CardActivated',
            event_data=event_data,
            user_id='card_system'
        )
        
        self.status = CardStatus.ACTIVE
    
    async def process_transaction(
        self,
        merchant_name: str,
        amount: Decimal,
        merchant_category: str = 'RETAIL'
    ):
        """Process card transaction with fraud detection"""
        if self.status != CardStatus.ACTIVE:
            raise ValueError(f'Card is {self.status}')
        
        # Fraud check
        fraud_result = await ml_pipeline.detect_fraud({
            'amount': float(amount),
            'international': False,
            'unusual_time': datetime.now(timezone.utc).hour < 6 or datetime.now(timezone.utc).hour > 22
        })
        
        if fraud_result['is_fraudulent']:
            await self.block('Suspected fraud')
            raise ValueError('Transaction blocked - suspected fraud')
        
        # Check limits
        if self.card_type == CardType.CREDIT:
            if amount > self.available_credit:
                raise ValueError('Credit limit exceeded')
        else:
            # Debit card - check account balance
            account = AccountAggregate(self.account_id)
            await account.load_from_events()
            if amount > account.balance:
                raise ValueError('Insufficient funds')
        
        store = get_event_store()
        
        event_data = {
            'card_id': self.card_id,
            'merchant_name': merchant_name,
            'merchant_category': merchant_category,
            'amount': str(amount),
            'fraud_score': fraud_result['fraud_score'],
            'transaction_time': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.card_id,
            aggregate_type='Card',
            event_type='CardTransactionProcessed',
            event_data=event_data,
            user_id='card_system'
        )
        
        # Update balances
        if self.card_type == CardType.CREDIT:
            self.available_credit -= amount
        else:
            account = AccountAggregate(self.account_id)
            await account.load_from_events()
            await account.withdraw(amount, f'Card purchase at {merchant_name}', self.card_id)
        
        self.transactions.append(event_data)
    
    async def block(self, reason: str):
        """Block card"""
        store = get_event_store()
        
        event_data = {
            'card_id': self.card_id,
            'reason': reason,
            'blocked_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.card_id,
            aggregate_type='Card',
            event_type='CardBlocked',
            event_data=event_data,
            user_id='card_system'
        )
        
        self.status = CardStatus.BLOCKED
    
    def _generate_card_number(self) -> str:
        """Generate fake card number"""
        return f'4532-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}'
    
    async def load_from_events(self):
        """Rebuild card state from events"""
        store = get_event_store()
        events = await store.get_events(self.card_id)
        
        for event in events:
            if event.event_type == 'CardIssued':
                self.account_id = event.event_data['account_id']
                self.card_type = CardType(event.event_data['card_type'])
                self.card_number = event.event_data['card_number']
                self.cvv = event.event_data['cvv']
                self.expiry_date = event.event_data['expiry_date']
                self.credit_limit = Decimal(event.event_data['credit_limit'])
                self.available_credit = self.credit_limit
                self.status = CardStatus.PENDING
            elif event.event_type == 'CardActivated':
                self.status = CardStatus.ACTIVE
            elif event.event_type == 'CardTransactionProcessed':
                amount = Decimal(event.event_data['amount'])
                if self.card_type == CardType.CREDIT:
                    self.available_credit -= amount
                self.transactions.append(event.event_data)
            elif event.event_type == 'CardBlocked':
                self.status = CardStatus.BLOCKED

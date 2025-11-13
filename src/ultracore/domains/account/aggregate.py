"""
Account Domain - Customer Banking Accounts
Complete account lifecycle management
"""
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.ledger.general_ledger import ledger


class AccountType(str, Enum):
    SAVINGS = 'SAVINGS'
    CHECKING = 'CHECKING'
    TERM_DEPOSIT = 'TERM_DEPOSIT'
    CREDIT_CARD = 'CREDIT_CARD'


class AccountStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    FROZEN = 'FROZEN'
    CLOSED = 'CLOSED'


class CreateAccountRequest(BaseModel):
    client_id: str
    account_type: AccountType
    currency: str = 'AUD'
    initial_deposit: float = 0.0


class TransactionRequest(BaseModel):
    amount: float
    description: str
    reference: Optional[str] = None


class AccountAggregate:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.client_id: Optional[str] = None
        self.account_type: Optional[AccountType] = None
        self.balance: Decimal = Decimal('0')
        self.status: AccountStatus = AccountStatus.PENDING
        self.currency: str = 'AUD'
        self.interest_rate: Decimal = Decimal('0')
        self.transactions: List[Dict] = []
    
    async def create_account(
        self,
        client_id: str,
        account_type: AccountType,
        currency: str = 'AUD',
        initial_deposit: Decimal = Decimal('0')
    ):
        """Create a new account"""
        store = get_event_store()
        
        # Set interest rate based on account type
        if account_type == AccountType.SAVINGS:
            interest_rate = Decimal('2.5')
        elif account_type == AccountType.TERM_DEPOSIT:
            interest_rate = Decimal('4.0')
        else:
            interest_rate = Decimal('0')
        
        event_data = {
            'account_id': self.account_id,
            'client_id': client_id,
            'account_type': account_type.value,
            'currency': currency,
            'interest_rate': str(interest_rate),
            'initial_deposit': str(initial_deposit),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='AccountCreated',
            event_data=event_data,
            user_id='account_system'
        )
        
        self.client_id = client_id
        self.account_type = account_type
        self.currency = currency
        self.interest_rate = interest_rate
        self.status = AccountStatus.PENDING
        
        # If initial deposit, process it
        if initial_deposit > 0:
            await self.deposit(initial_deposit, 'Initial deposit')
    
    async def activate(self):
        """Activate account after verification"""
        store = get_event_store()
        
        event_data = {
            'account_id': self.account_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='AccountActivated',
            event_data=event_data,
            user_id='account_system'
        )
        
        self.status = AccountStatus.ACTIVE
    
    async def deposit(self, amount: Decimal, description: str, reference: str = None):
        """Deposit money into account"""
        if amount <= 0:
            raise ValueError('Deposit amount must be positive')
        
        store = get_event_store()
        
        new_balance = self.balance + amount
        
        event_data = {
            'account_id': self.account_id,
            'transaction_type': 'DEPOSIT',
            'amount': str(amount),
            'previous_balance': str(self.balance),
            'new_balance': str(new_balance),
            'description': description,
            'reference': reference,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='MoneyDeposited',
            event_data=event_data,
            user_id='transaction_system'
        )
        
        # Post to General Ledger
        # DR: Cash, CR: Customer Deposits
        await ledger.post_journal_entry(
            entry_id=f'JE-DEP-{self.account_id}-{datetime.now(timezone.utc).timestamp()}',
            date=datetime.now(timezone.utc).isoformat(),
            description=f'Deposit to account {self.account_id}: {description}',
            reference=reference or self.account_id,
            debits=[{'account': '1000', 'amount': float(amount)}],  # Cash
            credits=[{'account': '2000', 'amount': float(amount)}],  # Customer Deposits
            posted_by='transaction_system'
        )
        
        self.balance = new_balance
        self.transactions.append(event_data)
    
    async def withdraw(self, amount: Decimal, description: str, reference: str = None):
        """Withdraw money from account"""
        if amount <= 0:
            raise ValueError('Withdrawal amount must be positive')
        
        if amount > self.balance:
            raise ValueError(f'Insufficient funds. Balance: {self.balance}, Requested: {amount}')
        
        store = get_event_store()
        
        new_balance = self.balance - amount
        
        event_data = {
            'account_id': self.account_id,
            'transaction_type': 'WITHDRAWAL',
            'amount': str(amount),
            'previous_balance': str(self.balance),
            'new_balance': str(new_balance),
            'description': description,
            'reference': reference,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='MoneyWithdrawn',
            event_data=event_data,
            user_id='transaction_system'
        )
        
        # Post to General Ledger
        # DR: Customer Deposits, CR: Cash
        await ledger.post_journal_entry(
            entry_id=f'JE-WD-{self.account_id}-{datetime.now(timezone.utc).timestamp()}',
            date=datetime.now(timezone.utc).isoformat(),
            description=f'Withdrawal from account {self.account_id}: {description}',
            reference=reference or self.account_id,
            debits=[{'account': '2000', 'amount': float(amount)}],  # Customer Deposits
            credits=[{'account': '1000', 'amount': float(amount)}],  # Cash
            posted_by='transaction_system'
        )
        
        self.balance = new_balance
        self.transactions.append(event_data)
    
    async def freeze(self, reason: str):
        """Freeze account (suspicious activity)"""
        store = get_event_store()
        
        event_data = {
            'account_id': self.account_id,
            'reason': reason,
            'frozen_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='AccountFrozen',
            event_data=event_data,
            user_id='risk_system'
        )
        
        self.status = AccountStatus.FROZEN
    
    async def close(self, reason: str):
        """Close account"""
        if self.balance != 0:
            raise ValueError('Cannot close account with non-zero balance')
        
        store = get_event_store()
        
        event_data = {
            'account_id': self.account_id,
            'reason': reason,
            'closed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.account_id,
            aggregate_type='Account',
            event_type='AccountClosed',
            event_data=event_data,
            user_id='account_system'
        )
        
        self.status = AccountStatus.CLOSED
    
    async def load_from_events(self):
        """Rebuild account state from events"""
        store = get_event_store()
        events = await store.get_events(self.account_id)
        
        for event in events:
            if event.event_type == 'AccountCreated':
                self.client_id = event.event_data['client_id']
                self.account_type = AccountType(event.event_data['account_type'])
                self.currency = event.event_data['currency']
                self.interest_rate = Decimal(event.event_data['interest_rate'])
                self.status = AccountStatus.PENDING
            elif event.event_type == 'AccountActivated':
                self.status = AccountStatus.ACTIVE
            elif event.event_type == 'MoneyDeposited':
                self.balance = Decimal(event.event_data['new_balance'])
                self.transactions.append(event.event_data)
            elif event.event_type == 'MoneyWithdrawn':
                self.balance = Decimal(event.event_data['new_balance'])
                self.transactions.append(event.event_data)
            elif event.event_type == 'AccountFrozen':
                self.status = AccountStatus.FROZEN
            elif event.event_type == 'AccountClosed':
                self.status = AccountStatus.CLOSED

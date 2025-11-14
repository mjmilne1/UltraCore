"""
Complete Account Domain - Full Account Lifecycle with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.data_mesh.integration import DataMeshPublisher
from ultracore.ledger.general_ledger import ledger


class AccountType(str, Enum):
    CHECKING = 'CHECKING'
    SAVINGS = 'SAVINGS'
    INVESTMENT = 'INVESTMENT'


class AccountStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    FROZEN = 'FROZEN'
    CLOSED = 'CLOSED'


class TransactionType(str, Enum):
    DEPOSIT = 'DEPOSIT'
    WITHDRAWAL = 'WITHDRAWAL'
    TRANSFER_IN = 'TRANSFER_IN'
    TRANSFER_OUT = 'TRANSFER_OUT'
    INTEREST = 'INTEREST'
    FEE = 'FEE'


class CompleteAccountAggregate:
    """Complete account lifecycle management"""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.client_id: Optional[str] = None
        self.account_type: Optional[AccountType] = None
        self.currency: str = 'AUD'
        self.balance: Decimal = Decimal('0')
        self.available_balance: Decimal = Decimal('0')
        self.status: AccountStatus = AccountStatus.PENDING
        self.transactions: List[Dict] = []
        self.holds: Dict[str, Decimal] = {}
        self.interest_rate: Decimal = Decimal('0')
        self.daily_limit: Decimal = Decimal('10000')
        self.monthly_fee: Decimal = Decimal('5')
    
    async def open_account(
        self,
        client_id: str,
        account_type: AccountType,
        initial_deposit: Decimal = Decimal('0')
    ):
        """Open new account"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'client_id': client_id,
            'account_type': account_type.value,
            'currency': self.currency,
            'initial_deposit': str(initial_deposit),
            'opened_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='account_opened',
            event_data=event_data,
            aggregate_id=self.account_id,
            exactly_once=True
        )
        
        self.client_id = client_id
        self.account_type = account_type
        self.balance = initial_deposit
        self.available_balance = initial_deposit
        self.status = AccountStatus.PENDING
        
        if initial_deposit > 0:
            await self.deposit(initial_deposit, 'Initial deposit', 'OPENING')
    
    async def activate(self):
        """Activate account"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='account_activated',
            event_data=event_data,
            aggregate_id=self.account_id
        )
        
        self.status = AccountStatus.ACTIVE
    
    async def deposit(
        self,
        amount: Decimal,
        description: str,
        reference: Optional[str] = None
    ):
        """Deposit funds"""
        kafka_store = get_production_kafka_store()
        
        previous_balance = self.balance
        new_balance = self.balance + amount
        
        event_data = {
            'account_id': self.account_id,
            'transaction_type': TransactionType.DEPOSIT.value,
            'amount': str(amount),
            'previous_balance': str(previous_balance),
            'new_balance': str(new_balance),
            'description': description,
            'reference': reference,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='funds_deposited',
            event_data=event_data,
            aggregate_id=self.account_id,
            exactly_once=True
        )
        
        # Post to ledger
        await ledger.post_journal_entry(
            entry_id=f'JE-DEP-{self.account_id}-{datetime.now(timezone.utc).timestamp()}',
            date=datetime.now(timezone.utc).isoformat(),
            description=description,
            reference=reference or self.account_id,
            debits=[{'account': '1000', 'amount': float(amount)}],
            credits=[{'account': '2000', 'amount': float(amount)}],
            posted_by='account_system'
        )
        
        self.balance = new_balance
        self.available_balance = new_balance - sum(self.holds.values())
        self.transactions.append(event_data)
        
        await DataMeshPublisher.publish_transaction_data(
            f"{self.account_id}-{len(self.transactions)}",
            event_data
        )
    
    async def withdraw(
        self,
        amount: Decimal,
        description: str,
        reference: Optional[str] = None
    ):
        """Withdraw funds"""
        if self.available_balance < amount:
            raise ValueError('Insufficient funds')
        
        kafka_store = get_production_kafka_store()
        
        previous_balance = self.balance
        new_balance = self.balance - amount
        
        event_data = {
            'account_id': self.account_id,
            'transaction_type': TransactionType.WITHDRAWAL.value,
            'amount': str(amount),
            'previous_balance': str(previous_balance),
            'new_balance': str(new_balance),
            'description': description,
            'reference': reference,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='funds_withdrawn',
            event_data=event_data,
            aggregate_id=self.account_id,
            exactly_once=True
        )
        
        await ledger.post_journal_entry(
            entry_id=f'JE-WD-{self.account_id}-{datetime.now(timezone.utc).timestamp()}',
            date=datetime.now(timezone.utc).isoformat(),
            description=description,
            reference=reference or self.account_id,
            debits=[{'account': '2000', 'amount': float(amount)}],
            credits=[{'account': '1000', 'amount': float(amount)}],
            posted_by='account_system'
        )
        
        self.balance = new_balance
        self.available_balance = new_balance - sum(self.holds.values())
        self.transactions.append(event_data)
    
    async def place_hold(self, hold_id: str, amount: Decimal, reason: str):
        """Place hold on funds"""
        if self.available_balance < amount:
            raise ValueError('Insufficient available funds')
        
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'hold_id': hold_id,
            'amount': str(amount),
            'reason': reason,
            'placed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='hold_placed',
            event_data=event_data,
            aggregate_id=self.account_id
        )
        
        self.holds[hold_id] = amount
        self.available_balance = self.balance - sum(self.holds.values())
    
    async def release_hold(self, hold_id: str):
        """Release hold"""
        if hold_id not in self.holds:
            raise ValueError('Hold not found')
        
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'hold_id': hold_id,
            'amount': str(self.holds[hold_id]),
            'released_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='hold_released',
            event_data=event_data,
            aggregate_id=self.account_id
        )
        
        del self.holds[hold_id]
        self.available_balance = self.balance - sum(self.holds.values())
    
    async def accrue_interest(self):
        """Calculate and accrue interest"""
        if self.account_type != AccountType.SAVINGS:
            return
        
        daily_rate = self.interest_rate / 365 / 100
        interest_amount = self.balance * daily_rate
        
        if interest_amount > 0:
            await self.deposit(
                interest_amount,
                'Interest accrued',
                'INTEREST_ACCRUAL'
            )
    
    async def charge_monthly_fee(self):
        """Charge monthly account fee"""
        if self.monthly_fee > 0 and self.balance >= self.monthly_fee:
            await self.withdraw(
                self.monthly_fee,
                'Monthly account fee',
                'MONTHLY_FEE'
            )
    
    async def freeze_account(self, reason: str):
        """Freeze account"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'reason': reason,
            'frozen_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='account_frozen',
            event_data=event_data,
            aggregate_id=self.account_id
        )
        
        self.status = AccountStatus.FROZEN
    
    async def close_account(self, reason: str):
        """Close account"""
        if self.balance != 0:
            raise ValueError('Account must have zero balance to close')
        
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'account_id': self.account_id,
            'reason': reason,
            'closed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='accounts',
            event_type='account_closed',
            event_data=event_data,
            aggregate_id=self.account_id
        )
        
        self.status = AccountStatus.CLOSED
    
    async def get_statement(self, from_date: str, to_date: str) -> Dict:
        """Generate account statement"""
        filtered_transactions = [
            t for t in self.transactions
            if from_date <= t['timestamp'] <= to_date
        ]
        
        total_deposits = sum(
            Decimal(t['amount']) for t in filtered_transactions
            if t['transaction_type'] in [TransactionType.DEPOSIT.value, TransactionType.TRANSFER_IN.value]
        )
        
        total_withdrawals = sum(
            Decimal(t['amount']) for t in filtered_transactions
            if t['transaction_type'] in [TransactionType.WITHDRAWAL.value, TransactionType.TRANSFER_OUT.value]
        )
        
        return {
            'account_id': self.account_id,
            'period': {'from': from_date, 'to': to_date},
            'opening_balance': str(filtered_transactions[0]['previous_balance']) if filtered_transactions else str(self.balance),
            'closing_balance': str(self.balance),
            'total_deposits': str(total_deposits),
            'total_withdrawals': str(total_withdrawals),
            'transaction_count': len(filtered_transactions),
            'transactions': filtered_transactions
        }
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.account_id)
        
        for event in events:
            if event.event_type in ['AccountCreated', 'account_opened']:
                self.client_id = event.event_data.get('client_id')
                self.account_type = AccountType(event.event_data.get('account_type'))
                self.status = AccountStatus.PENDING
            elif event.event_type == 'account_activated':
                self.status = AccountStatus.ACTIVE
            elif event.event_type == 'funds_deposited':
                self.balance = Decimal(event.event_data['new_balance'])
                self.transactions.append(event.event_data)
            elif event.event_type == 'funds_withdrawn':
                self.balance = Decimal(event.event_data['new_balance'])
                self.transactions.append(event.event_data)
            elif event.event_type == 'hold_placed':
                hold_id = event.event_data['hold_id']
                self.holds[hold_id] = Decimal(event.event_data['amount'])
            elif event.event_type == 'hold_released':
                hold_id = event.event_data['hold_id']
                if hold_id in self.holds:
                    del self.holds[hold_id]
            elif event.event_type == 'account_frozen':
                self.status = AccountStatus.FROZEN
            elif event.event_type == 'account_closed':
                self.status = AccountStatus.CLOSED
        
        self.available_balance = self.balance - sum(self.holds.values())

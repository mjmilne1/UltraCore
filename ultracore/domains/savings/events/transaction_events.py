"""
Savings Transaction Events
Events for deposits, withdrawals, and transfers
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ultracore.domains.savings.events.account_events import BaseEvent


class DepositMadeEvent(BaseEvent):
    """Event: Deposit made to savings account"""
    event_type: str = "savings.transaction.deposit"
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    source: str
    reference_number: str
    description: str
    balance_before: Decimal
    balance_after: Decimal


class WithdrawalMadeEvent(BaseEvent):
    """Event: Withdrawal made from savings account"""
    event_type: str = "savings.transaction.withdrawal"
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    destination: str
    reference_number: str
    description: str
    balance_before: Decimal
    balance_after: Decimal


class TransferInEvent(BaseEvent):
    """Event: Transfer received into savings account"""
    event_type: str = "savings.transaction.transfer_in"
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    source_account: str
    reference_number: str
    description: str
    balance_before: Decimal
    balance_after: Decimal


class TransferOutEvent(BaseEvent):
    """Event: Transfer sent from savings account"""
    event_type: str = "savings.transaction.transfer_out"
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    destination_account: str
    reference_number: str
    description: str
    balance_before: Decimal
    balance_after: Decimal

"""
Fee Events
Events for fee charges and waivers
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ultracore.domains.savings.events.account_events import BaseEvent


class MonthlyFeeChargedEvent(BaseEvent):
    """Event: Monthly account fee charged"""
    event_type: str = "savings.fee.monthly_charged"
    account_id: UUID
    transaction_id: UUID
    fee_amount: Decimal
    period: str
    balance_before: Decimal
    balance_after: Decimal


class FeeWaivedEvent(BaseEvent):
    """Event: Fee waived"""
    event_type: str = "savings.fee.waived"
    account_id: UUID
    fee_type: str
    fee_amount: Decimal
    waiver_reason: str
    period: str


class WithdrawalFeeChargedEvent(BaseEvent):
    """Event: Withdrawal fee charged"""
    event_type: str = "savings.fee.withdrawal_charged"
    account_id: UUID
    transaction_id: UUID
    withdrawal_transaction_id: UUID
    fee_amount: Decimal
    withdrawal_count: int
    withdrawal_limit: int
    balance_before: Decimal
    balance_after: Decimal

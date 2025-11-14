"""
Interest and Fee Events
Events for interest accrual, posting, and fee charges
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ultracore.domains.savings.events.account_events import BaseEvent


class InterestAccruedEvent(BaseEvent):
    """Event: Interest accrued for a day"""
    event_type: str = "savings.interest.accrued"
    account_id: UUID
    accrual_date: date
    balance: Decimal
    interest_rate: Decimal
    gross_interest: Decimal
    withholding_tax: Decimal
    net_interest: Decimal
    total_accrued: Decimal


class InterestPostedEvent(BaseEvent):
    """Event: Interest posted to account"""
    event_type: str = "savings.interest.posted"
    account_id: UUID
    posting_date: date
    period_start: date
    period_end: date
    gross_interest: Decimal
    withholding_tax: Decimal
    net_interest: Decimal
    balance_before: Decimal
    balance_after: Decimal
    transaction_id: UUID


class BonusInterestEarnedEvent(BaseEvent):
    """Event: Bonus interest earned"""
    event_type: str = "savings.interest.bonus_earned"
    account_id: UUID
    period: str
    bonus_rate: Decimal
    gross_bonus: Decimal
    withholding_tax: Decimal
    net_bonus: Decimal
    conditions_met: List[str]


class BonusInterestForfeitedEvent(BaseEvent):
    """Event: Bonus interest forfeited"""
    event_type: str = "savings.interest.bonus_forfeited"
    account_id: UUID
    period: str
    potential_bonus: Decimal
    reason: str
    conditions_failed: List[str]


class WithholdingTaxDeductedEvent(BaseEvent):
    """Event: Withholding tax deducted from interest"""
    event_type: str = "savings.tax.withholding_deducted"
    account_id: UUID
    transaction_id: UUID
    gross_interest: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    net_interest: Decimal
    ytd_withholding_tax: Decimal

"""
Savings Account Lifecycle Events
Events for account creation, activation, and closure
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event with common fields"""
    event_id: UUID
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: UUID
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


class SavingsAccountOpenedEvent(BaseEvent):
    """Event: Savings account opened"""
    event_type: str = "savings.account.opened"
    account_id: UUID
    client_id: UUID
    product_id: UUID
    account_number: str
    bsb: str
    account_name: str
    account_type: str
    opening_balance: Decimal
    tfn: Optional[str] = None
    tfn_exemption: Optional[str] = None
    withholding_tax_rate: Decimal


class SavingsAccountApprovedEvent(BaseEvent):
    """Event: Savings account approved"""
    event_type: str = "savings.account.approved"
    account_id: UUID
    approved_by: UUID
    approved_at: datetime


class SavingsAccountActivatedEvent(BaseEvent):
    """Event: Savings account activated"""
    event_type: str = "savings.account.activated"
    account_id: UUID
    activated_at: datetime


class SavingsAccountClosedEvent(BaseEvent):
    """Event: Savings account closed"""
    event_type: str = "savings.account.closed"
    account_id: UUID
    closure_reason: str
    final_balance: Decimal
    closed_by: UUID
    closed_at: datetime


class SavingsAccountFrozenEvent(BaseEvent):
    """Event: Savings account frozen"""
    event_type: str = "savings.account.frozen"
    account_id: UUID
    freeze_reason: str
    frozen_by: UUID
    frozen_at: datetime


class SavingsAccountDormantEvent(BaseEvent):
    """Event: Savings account marked as dormant"""
    event_type: str = "savings.account.dormant"
    account_id: UUID
    last_transaction_date: Optional[datetime]
    dormancy_date: datetime


class TFNProvidedEvent(BaseEvent):
    """Event: Tax File Number provided"""
    event_type: str = "savings.account.tfn_provided"
    account_id: UUID
    tfn: str
    previous_withholding_tax_rate: Decimal
    new_withholding_tax_rate: Decimal

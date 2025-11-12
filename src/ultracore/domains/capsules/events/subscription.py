"""Subscription Events"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field

from .base import CapsuleEvent


class CapsuleSubscribedEvent(CapsuleEvent):
    """
    Customer subscribed to a capsule.
    
    One-click investing: Customer selects capsule and invests!
    """
    
    event_type: str = "CapsuleSubscribed"
    
    subscription_id: str
    capsule_id: str
    customer_id: str
    portfolio_id: str
    
    # Investment
    investment_amount: Decimal
    
    # Recurring
    recurring: bool = False
    recurring_amount: Optional[Decimal] = None
    recurring_frequency: Optional[str] = None
    
    # Initial allocation
    target_allocations: dict  # ticker -> percentage
    
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)


class CapsuleUnsubscribedEvent(CapsuleEvent):
    """Customer unsubscribed from capsule."""
    
    event_type: str = "CapsuleUnsubscribed"
    
    subscription_id: str
    capsule_id: str
    customer_id: str
    
    # Unsubscribe reason
    reason: str
    
    # Final value
    final_value: Decimal
    total_return: Decimal
    
    unsubscribed_at: datetime = Field(default_factory=datetime.utcnow)


class RecurringInvestmentSetupEvent(CapsuleEvent):
    """Recurring investment setup for capsule."""
    
    event_type: str = "RecurringInvestmentSetup"
    
    subscription_id: str
    capsule_id: str
    customer_id: str
    
    # Recurring details
    recurring_amount: Decimal
    frequency: str  # weekly, monthly, etc.
    start_date: datetime
    
    setup_at: datetime = Field(default_factory=datetime.utcnow)

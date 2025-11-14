"""
Payment Schedule Models.

Models for recurring and scheduled payments.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ScheduleFrequency(str, Enum):
    """Schedule frequency."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ScheduleStatus(str, Enum):
    """Schedule status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PaymentSchedule(BaseModel):
    """Payment schedule model."""
    
    # Identity
    schedule_id: str
    tenant_id: str
    customer_id: str
    
    # Payment details
    from_account_id: str
    payment_method_id: str
    amount: Decimal
    currency: str = "AUD"
    description: str
    reference: Optional[str] = None
    
    # Schedule
    frequency: ScheduleFrequency
    start_date: date
    end_date: Optional[date] = None
    next_payment_date: date
    last_payment_date: Optional[date] = None
    
    # Limits
    max_payments: Optional[int] = None
    payments_made: int = 0
    
    # Status
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    
    # Notifications
    notify_before_days: int = 1
    notify_on_success: bool = True
    notify_on_failure: bool = True
    
    # Failure handling
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class ScheduledPaymentExecution(BaseModel):
    """Record of a scheduled payment execution."""
    
    execution_id: str
    schedule_id: str
    payment_id: Optional[str] = None  # Created payment ID
    
    # Execution details
    scheduled_date: date
    executed_at: Optional[datetime] = None
    amount: Decimal
    
    # Status
    status: str  # pending, completed, failed, skipped
    error_message: Optional[str] = None
    
    # Retry
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

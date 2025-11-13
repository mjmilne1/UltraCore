"""
Standing Order Model
Automated scheduled transfers between accounts
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from uuid import UUID, uuid4
from datetime import date, datetime
from decimal import Decimal


class TransferType(str, Enum):
    """Transfer type"""
    INTERNAL = "internal"  # Between own accounts
    EXTERNAL = "external"  # To external account (BPAY, EFT)
    LOAN_REPAYMENT = "loan_repayment"
    BILL_PAYMENT = "bill_payment"


class StandingOrderFrequency(str, Enum):
    """Standing order frequency"""
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class StandingOrderStatus(str, Enum):
    """Standing order status"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    """Execution status"""
    SUCCESS = "success"
    FAILED_INSUFFICIENT_FUNDS = "failed_insufficient_funds"
    FAILED_ACCOUNT_CLOSED = "failed_account_closed"
    FAILED_LIMIT_EXCEEDED = "failed_limit_exceeded"
    FAILED_OTHER = "failed_other"
    PENDING_RETRY = "pending_retry"


class StandingOrder(BaseModel):
    """
    Standing Order
    
    Automated scheduled transfers with smart execution
    and retry logic
    """
    
    # Identifiers
    standing_order_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    from_account_id: UUID
    to_account_id: Optional[UUID] = None  # For internal transfers
    customer_id: UUID
    
    # Transfer details
    transfer_type: TransferType
    amount: Decimal
    currency: str = Field(default="AUD")
    reference: str = Field(default="")
    description: str = Field(default="")
    
    # External transfer details (if applicable)
    bpay_code: Optional[str] = None
    bpay_reference: Optional[str] = None
    bsb: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    
    # Schedule
    frequency: StandingOrderFrequency
    start_date: date
    end_date: Optional[date] = None  # None = indefinite
    next_execution_date: Optional[date] = None
    last_execution_date: Optional[date] = None
    
    # Execution tracking
    total_executions: int = Field(default=0)
    successful_executions: int = Field(default=0)
    failed_executions: int = Field(default=0)
    total_amount_transferred: Decimal = Field(default=Decimal("0.00"))
    
    # Smart execution
    check_balance_before_execution: bool = Field(default=True)
    allow_partial_transfer: bool = Field(default=False)
    skip_weekends: bool = Field(default=True)
    skip_public_holidays: bool = Field(default=True)
    
    # Retry logic
    retry_on_failure: bool = Field(default=True)
    max_retry_attempts: int = Field(default=3)
    retry_interval_hours: int = Field(default=24)
    current_retry_count: int = Field(default=0)
    
    # Limits
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    
    # Status
    status: StandingOrderStatus = Field(default=StandingOrderStatus.PENDING)
    last_execution_status: Optional[ExecutionStatus] = None
    last_failure_reason: Optional[str] = None
    
    # Notifications
    notify_on_execution: bool = Field(default=True)
    notify_on_failure: bool = Field(default=True)
    notify_before_execution_days: int = Field(default=1)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def calculate_next_execution_date(self) -> Optional[date]:
        """Calculate next execution date"""
        from dateutil.relativedelta import relativedelta
        
        if self.status not in [StandingOrderStatus.ACTIVE, StandingOrderStatus.PENDING]:
            return None
        
        if self.frequency == StandingOrderFrequency.ONE_TIME:
            if self.total_executions == 0:
                self.next_execution_date = self.start_date
                return self.start_date
            else:
                return None  # One-time already executed
        
        if self.last_execution_date is None:
            self.next_execution_date = self.start_date
            return self.start_date
        
        next_date = self.last_execution_date
        
        if self.frequency == StandingOrderFrequency.DAILY:
            next_date += relativedelta(days=1)
        elif self.frequency == StandingOrderFrequency.WEEKLY:
            next_date += relativedelta(weeks=1)
        elif self.frequency == StandingOrderFrequency.FORTNIGHTLY:
            next_date += relativedelta(weeks=2)
        elif self.frequency == StandingOrderFrequency.MONTHLY:
            next_date += relativedelta(months=1)
        elif self.frequency == StandingOrderFrequency.QUARTERLY:
            next_date += relativedelta(months=3)
        elif self.frequency == StandingOrderFrequency.YEARLY:
            next_date += relativedelta(years=1)
        
        # Skip weekends if configured
        if self.skip_weekends:
            while next_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                next_date += relativedelta(days=1)
        
        # Check if past end date
        if self.end_date and next_date > self.end_date:
            return None
        
        self.next_execution_date = next_date
        return next_date
    
    def record_execution(
        self,
        execution_status: ExecutionStatus,
        amount_transferred: Decimal,
        failure_reason: Optional[str] = None
    ):
        """Record execution result"""
        self.total_executions += 1
        self.last_execution_date = date.today()
        self.last_execution_status = execution_status
        
        if execution_status == ExecutionStatus.SUCCESS:
            self.successful_executions += 1
            self.total_amount_transferred += amount_transferred
            self.current_retry_count = 0  # Reset retry count
            self.calculate_next_execution_date()
            
            # Mark as completed if one-time
            if self.frequency == StandingOrderFrequency.ONE_TIME:
                self.complete()
        else:
            self.failed_executions += 1
            self.last_failure_reason = failure_reason
            self.current_retry_count += 1
            
            # Mark as failed if max retries exceeded
            if self.current_retry_count >= self.max_retry_attempts:
                self.status = StandingOrderStatus.FAILED
    
    def activate(self):
        """Activate standing order"""
        self.status = StandingOrderStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        self.calculate_next_execution_date()
    
    def pause(self):
        """Pause standing order"""
        self.status = StandingOrderStatus.PAUSED
    
    def resume(self):
        """Resume standing order"""
        self.status = StandingOrderStatus.ACTIVE
        self.calculate_next_execution_date()
    
    def complete(self):
        """Mark as completed"""
        self.status = StandingOrderStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel standing order"""
        self.status = StandingOrderStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
    
    def should_retry(self) -> bool:
        """Check if should retry after failure"""
        return (
            self.retry_on_failure and
            self.current_retry_count < self.max_retry_attempts and
            self.last_execution_status != ExecutionStatus.SUCCESS
        )

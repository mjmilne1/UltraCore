"""
Payment API Schemas.

Request and response schemas for payment API endpoints.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from ..models.enums import PaymentSystem, PaymentStatus, PayIDType
from ..models.payment_method import PaymentMethodType, PaymentMethodStatus
from ..models.payment_schedule import ScheduleFrequency, ScheduleStatus
from ..models.payment_batch import BatchStatus


# Payment Schemas

class CreatePaymentRequest(BaseModel):
    """Request to create a payment."""
    from_account_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "AUD"
    description: str
    reference: Optional[str] = None
    
    # Recipient (one of these)
    to_account_id: Optional[str] = None
    to_bsb: Optional[str] = None
    to_account_number: Optional[str] = None
    to_account_name: Optional[str] = None
    to_payid: Optional[str] = None
    to_payid_type: Optional[PayIDType] = None
    
    # BPAY specific
    biller_code: Optional[str] = None
    biller_name: Optional[str] = None
    biller_reference: Optional[str] = None
    
    # International specific
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    beneficiary_bank_swift: Optional[str] = None
    beneficiary_country: Optional[str] = None
    
    # Options
    payment_system: Optional[PaymentSystem] = None
    urgency: str = "normal"  # instant, normal, scheduled


class PaymentResponse(BaseModel):
    """Payment response."""
    payment_id: str
    payment_system: PaymentSystem
    from_account_id: str
    amount: Decimal
    currency: str
    description: str
    reference: Optional[str]
    status: PaymentStatus
    initiated_at: datetime
    completed_at: Optional[datetime]
    estimated_delivery: Optional[str]
    fees: Optional[Decimal]


class ListPaymentsRequest(BaseModel):
    """Request to list payments."""
    account_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    payment_system: Optional[PaymentSystem] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    offset: int = 0


# Payment Method Schemas

class CreatePaymentMethodRequest(BaseModel):
    """Request to create a payment method."""
    method_type: PaymentMethodType
    nickname: Optional[str] = None
    
    # Bank account
    bsb: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    
    # Card (tokenized)
    card_token: Optional[str] = None
    
    # PayID
    payid: Optional[str] = None
    payid_type: Optional[str] = None
    
    # Limits
    daily_limit: Optional[Decimal] = None
    transaction_limit: Optional[Decimal] = None


class PaymentMethodResponse(BaseModel):
    """Payment method response."""
    payment_method_id: str
    method_type: PaymentMethodType
    status: PaymentMethodStatus
    nickname: Optional[str]
    is_verified: bool
    is_default: bool
    
    # Masked details
    display_name: str
    last_four: Optional[str]
    
    created_at: datetime
    last_used_at: Optional[datetime]


# Payment Schedule Schemas

class CreateScheduleRequest(BaseModel):
    """Request to create a payment schedule."""
    from_account_id: str
    payment_method_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "AUD"
    description: str
    reference: Optional[str] = None
    
    frequency: ScheduleFrequency
    start_date: date
    end_date: Optional[date] = None
    max_payments: Optional[int] = None
    
    notify_before_days: int = 1
    retry_on_failure: bool = True


class ScheduleResponse(BaseModel):
    """Payment schedule response."""
    schedule_id: str
    from_account_id: str
    amount: Decimal
    currency: str
    description: str
    frequency: ScheduleFrequency
    start_date: date
    end_date: Optional[date]
    next_payment_date: date
    status: ScheduleStatus
    payments_made: int
    max_payments: Optional[int]
    created_at: datetime


# Batch Payment Schemas

class BatchPaymentItemRequest(BaseModel):
    """Batch payment item."""
    to_account_id: Optional[str] = None
    to_bsb: Optional[str] = None
    to_account_number: Optional[str] = None
    to_account_name: Optional[str] = None
    to_payid: Optional[str] = None
    
    amount: Decimal = Field(..., gt=0)
    currency: str = "AUD"
    description: str
    reference: Optional[str] = None


class CreateBatchRequest(BaseModel):
    """Request to create a payment batch."""
    batch_name: str
    description: Optional[str] = None
    from_account_id: str
    items: List[BatchPaymentItemRequest]


class BatchResponse(BaseModel):
    """Payment batch response."""
    batch_id: str
    batch_name: str
    from_account_id: str
    total_items: int
    total_amount: Decimal
    status: BatchStatus
    items_processed: int
    items_successful: int
    items_failed: int
    created_at: datetime
    completed_at: Optional[datetime]


# Reconciliation Schemas

class CreateReconciliationRequest(BaseModel):
    """Request to create a reconciliation."""
    period_start: datetime
    period_end: datetime
    account_ids: Optional[List[str]] = None
    payment_systems: Optional[List[str]] = None


class ReconciliationResponse(BaseModel):
    """Reconciliation response."""
    reconciliation_id: str
    reconciliation_date: datetime
    period_start: datetime
    period_end: datetime
    status: str
    total_payments: int
    reconciled_payments: int
    unreconciled_payments: int
    total_amount: Decimal
    reconciled_amount: Decimal
    unreconciled_amount: Decimal
    discrepancy_count: int


class DiscrepancyResponse(BaseModel):
    """Discrepancy response."""
    discrepancy_id: str
    discrepancy_type: str
    payment_id: Optional[str]
    expected_amount: Optional[Decimal]
    actual_amount: Optional[Decimal]
    description: str
    status: str
    created_at: datetime


# Other Schemas

class CancelPaymentRequest(BaseModel):
    """Request to cancel a payment."""
    reason: str


class RefundPaymentRequest(BaseModel):
    """Request to refund a payment."""
    amount: Optional[Decimal] = None  # None for full refund
    reason: str


class ValidationResult(BaseModel):
    """Validation result."""
    valid: bool
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    requires_approval: bool = False

"""
Payment Batch and Reconciliation Models.

Models for batch payments and reconciliation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class BatchStatus(str, Enum):
    """Batch status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchPaymentItem(BaseModel):
    """Individual payment in a batch."""
    
    item_id: str
    
    # Recipient
    to_account_id: Optional[str] = None
    to_bsb: Optional[str] = None
    to_account_number: Optional[str] = None
    to_account_name: Optional[str] = None
    to_payid: Optional[str] = None
    
    # Amount
    amount: Decimal
    currency: str = "AUD"
    description: str
    reference: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, processing, completed, failed
    payment_id: Optional[str] = None  # Created payment ID
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaymentBatch(BaseModel):
    """Payment batch model."""
    
    # Identity
    batch_id: str
    tenant_id: str
    customer_id: str
    
    # Batch details
    batch_name: str
    description: Optional[str] = None
    from_account_id: str
    
    # Items
    items: List[BatchPaymentItem] = []
    total_items: int = 0
    total_amount: Decimal = Decimal("0")
    
    # Status
    status: BatchStatus = BatchStatus.DRAFT
    
    # Processing
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    
    # Approval
    requires_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class ReconciliationStatus(str, Enum):
    """Reconciliation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class ReconciliationDiscrepancy(BaseModel):
    """Reconciliation discrepancy."""
    
    discrepancy_id: str
    discrepancy_type: str  # missing_payment, duplicate, amount_mismatch, etc.
    
    # Details
    payment_id: Optional[str] = None
    expected_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    description: str
    
    # Resolution
    status: str = "open"  # open, investigating, resolved, waived
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaymentReconciliation(BaseModel):
    """Payment reconciliation model."""
    
    # Identity
    reconciliation_id: str
    tenant_id: str
    
    # Period
    reconciliation_date: datetime
    period_start: datetime
    period_end: datetime
    
    # Scope
    account_ids: List[str] = []
    payment_systems: List[str] = []
    
    # Counts
    total_payments: int = 0
    reconciled_payments: int = 0
    unreconciled_payments: int = 0
    
    # Amounts
    total_amount: Decimal = Decimal("0")
    reconciled_amount: Decimal = Decimal("0")
    unreconciled_amount: Decimal = Decimal("0")
    
    # Discrepancies
    discrepancies: List[ReconciliationDiscrepancy] = []
    discrepancy_count: int = 0
    
    # Status
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    
    # Processing
    processed_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

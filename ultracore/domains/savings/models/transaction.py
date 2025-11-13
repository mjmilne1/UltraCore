"""
Savings Transaction Model
Records all transactions on savings accounts
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Types of savings transactions"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTEREST_ACCRUAL = "interest_accrual"
    INTEREST_POSTING = "interest_posting"
    FEE_CHARGE = "fee_charge"
    FEE_WAIVER = "fee_waiver"
    WITHHOLDING_TAX = "withholding_tax"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    REVERSAL = "reversal"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class SavingsTransaction(BaseModel):
    """
    Savings Transaction Model
    
    Records all financial transactions on savings accounts with full audit trail.
    """
    
    # Identity
    transaction_id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    tenant_id: UUID
    
    # Transaction Details
    transaction_type: TransactionType
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    value_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Amounts
    amount: Decimal = Field(..., description="Transaction amount (positive for credits, negative for debits)")
    balance_before: Decimal
    balance_after: Decimal
    
    # Status
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    
    # References
    reference_number: str = Field(..., min_length=1, max_length=100)
    external_reference: Optional[str] = None
    related_transaction_id: Optional[UUID] = None  # For reversals, transfers
    
    # Description
    description: str
    notes: Optional[str] = None
    
    # Source/Destination
    source_account: Optional[str] = None
    destination_account: Optional[str] = None
    
    # Processing
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    
    # Event Sourcing
    event_id: Optional[UUID] = None
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    
    def is_debit(self) -> bool:
        """Check if transaction is a debit (reduces balance)"""
        return self.transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.FEE_CHARGE,
            TransactionType.WITHHOLDING_TAX,
            TransactionType.TRANSFER_OUT,
        ]
    
    def is_credit(self) -> bool:
        """Check if transaction is a credit (increases balance)"""
        return self.transaction_type in [
            TransactionType.DEPOSIT,
            TransactionType.INTEREST_POSTING,
            TransactionType.FEE_WAIVER,
            TransactionType.TRANSFER_IN,
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "110e8400-e29b-41d4-a716-446655440000",
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "880e8400-e29b-41d4-a716-446655440000",
                "transaction_type": "deposit",
                "amount": "1000.00",
                "balance_before": "5000.00",
                "balance_after": "6000.00",
                "status": "completed",
                "reference_number": "DEP20251113001",
                "description": "Cash deposit",
            }
        }

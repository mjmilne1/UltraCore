"""
Payment API Schemas

Pydantic models for payment rail endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class PaymentRailEnum(str, Enum):
    NPP = "NPP"
    BPAY = "BPAY"
    SWIFT = "SWIFT"
    CARD = "CARD"


class PaymentStatusEnum(str, Enum):
    INITIATED = "INITIATED"
    VALIDATING = "VALIDATING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


# ============================================================================
# Request Models
# ============================================================================

class NPPPaymentRequest(BaseModel):
    """NPP (Osko) payment request"""
    from_account_id: str = Field(..., description="Source account ID")
    amount: Decimal = Field(..., gt=0, le=999999.99, description="Amount (max $1M)")
    
    # Destination (PayID or BSB/Account)
    payid: Optional[str] = Field(None, description="PayID (email, mobile, ABN)")
    payid_type: Optional[str] = Field(None, pattern=r'^(EMAIL|MOBILE|ABN|ORG_ID)$')
    
    bsb: Optional[str] = Field(None, pattern=r'^\d{3}-?\d{3}$', description="BSB (6 digits)")
    account_number: Optional[str] = Field(None, pattern=r'^\d{6,9}$')
    beneficiary_name: Optional[str] = Field(None, max_length=140)
    
    description: str = Field(..., max_length=280, description="Payment description")
    reference: Optional[str] = Field(None, max_length=18)
    
    @validator('payid')
    def validate_destination(cls, v, values):
        # Must have either PayID or BSB/Account
        if not v and not values.get('bsb'):
            raise ValueError('Must provide either PayID or BSB/Account')
        return v


class BPAYPaymentRequest(BaseModel):
    """BPAY payment request"""
    from_account_id: str = Field(..., description="Source account ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    
    biller_code: str = Field(..., pattern=r'^\d{4,6}$', description="Biller code")
    reference_number: str = Field(..., min_length=1, max_length=20, description="Reference number")
    
    description: Optional[str] = Field(None, max_length=200)


class SWIFTPaymentRequest(BaseModel):
    """SWIFT international payment request"""
    from_account_id: str = Field(..., description="Source account ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(..., pattern=r'^[A-Z]{3}$', description="Currency code")
    
    # Beneficiary
    beneficiary_name: str = Field(..., max_length=140)
    swift_code: str = Field(..., pattern=r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$')
    iban: Optional[str] = Field(None, min_length=15, max_length=34)
    beneficiary_account: Optional[str] = None
    beneficiary_address: Optional[str] = None
    
    description: str = Field(..., max_length=140)
    reference: Optional[str] = Field(None, max_length=16)


# ============================================================================
# Response Models
# ============================================================================

class PaymentResponse(BaseModel):
    """Payment response"""
    payment_id: str
    rail: str
    status: str
    
    amount: float
    currency: str
    
    # External references
    external_reference: Optional[str] = None
    rail_transaction_id: Optional[str] = None
    
    # Status details
    status_message: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Fees
    processing_fee: float
    
    # Timing
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: dict = {}


class PaymentListResponse(BaseModel):
    """List of payments"""
    payments: List[PaymentResponse]
    total: int

"""
Payment Method Models.

Models for storing and managing payment methods.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PaymentMethodType(str, Enum):
    """Payment method types."""
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYID = "payid"
    DIGITAL_WALLET = "digital_wallet"


class PaymentMethodStatus(str, Enum):
    """Payment method status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    VERIFICATION_FAILED = "verification_failed"
    EXPIRED = "expired"


class BankAccountDetails(BaseModel):
    """Bank account details."""
    bsb: str = Field(..., min_length=6, max_length=6)
    account_number: str = Field(..., min_length=4, max_length=20)
    account_name: str


class CardDetails(BaseModel):
    """Card details (tokenized)."""
    card_token: str  # Tokenized card number
    last_four: str = Field(..., min_length=4, max_length=4)
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024)
    card_brand: str  # Visa, Mastercard, etc.
    cardholder_name: str


class PayIDDetails(BaseModel):
    """PayID details."""
    payid: str
    payid_type: str  # email, phone, abn
    payid_name: str


class DigitalWalletDetails(BaseModel):
    """Digital wallet details."""
    wallet_type: str  # apple_pay, google_pay, etc.
    wallet_token: str
    device_id: Optional[str] = None


class PaymentMethod(BaseModel):
    """Payment method model."""
    
    # Identity
    payment_method_id: str
    tenant_id: str
    customer_id: str
    
    # Type and status
    method_type: PaymentMethodType
    status: PaymentMethodStatus = PaymentMethodStatus.PENDING_VERIFICATION
    
    # Nickname
    nickname: Optional[str] = None
    
    # Details (one of these will be populated)
    bank_account: Optional[BankAccountDetails] = None
    card: Optional[CardDetails] = None
    payid: Optional[PayIDDetails] = None
    digital_wallet: Optional[DigitalWalletDetails] = None
    
    # Verification
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verification_method: Optional[str] = None
    
    # Default
    is_default: bool = False
    
    # Limits
    daily_limit: Optional[float] = None
    transaction_limit: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

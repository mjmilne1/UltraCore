"""
Share Accounts & Products Module
Manages equity shares, share products, dividends, and shareholder accounts
"""

from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class ShareProductType(str, Enum):
    """Types of share products"""
    ORDINARY_SHARES = "ordinary_shares"
    PREFERENCE_SHARES = "preference_shares"
    REDEEMABLE_SHARES = "redeemable_shares"
    CUMULATIVE_SHARES = "cumulative_shares"
    NON_CUMULATIVE_SHARES = "non_cumulative_shares"


class ShareAccountStatus(str, Enum):
    """Share account statuses"""
    PENDING = "pending"
    ACTIVE = "active"
    LOCKED = "locked"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class DividendStatus(str, Enum):
    """Dividend payment statuses"""
    DECLARED = "declared"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class ShareTransactionType(str, Enum):
    """Share transaction types"""
    PURCHASE = "purchase"
    SALE = "sale"
    DIVIDEND = "dividend"
    REDEMPTION = "redemption"
    TRANSFER = "transfer"


# ============================================================================
# SHARE PRODUCT
# ============================================================================

class ShareProduct(BaseModel):
    """
    Share Product Configuration
    
    Defines a type of shares that can be issued
    """
    product_id: str
    product_code: str
    product_name: str
    product_type: ShareProductType
    description: str
    
    # Pricing
    nominal_price: Decimal  # Par value per share
    minimum_shares: int = 1
    maximum_shares: Optional[int] = None
    
    # Dividends
    dividend_rate: Optional[Decimal] = None  # Annual dividend rate (%)
    dividend_frequency: str = "annually"  # annually, semi-annually, quarterly
    is_cumulative: bool = False  # Cumulative dividends
    
    # Features
    is_redeemable: bool = False
    redemption_price: Optional[Decimal] = None
    lock_in_period_days: int = 0
    
    # Voting rights
    has_voting_rights: bool = True
    votes_per_share: int = 1
    
    # Status
    is_active: bool = True
    available_from: date
    available_to: Optional[date] = None
    
    # Limits
    total_shares_authorized: Optional[int] = None
    total_shares_issued: int = 0
    total_shares_outstanding: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# SHARE ACCOUNT
# ============================================================================

class ShareAccount(BaseModel):
    """
    Share Account
    
    Represents a shareholder's account holding shares
    """
    account_id: str
    account_number: str
    external_id: Optional[str] = None
    
    # Shareholder
    client_id: str
    shareholder_name: str
    
    # Product
    product_id: str
    product_code: str
    product_name: str
    
    # Holdings
    total_shares: int = 0
    shares_purchased: int = 0
    shares_redeemed: int = 0
    shares_transferred_in: int = 0
    shares_transferred_out: int = 0
    
    # Valuation
    nominal_value_per_share: Decimal
    total_nominal_value: Decimal = Decimal("0")
    market_value_per_share: Optional[Decimal] = None
    total_market_value: Optional[Decimal] = None
    
    # Dividends
    total_dividends_paid: Decimal = Decimal("0")
    pending_dividends: Decimal = Decimal("0")
    
    # Purchase details
    total_amount_paid: Decimal = Decimal("0")
    average_purchase_price: Decimal = Decimal("0")
    
    # Status
    status: ShareAccountStatus = ShareAccountStatus.PENDING
    
    # Lock-in
    is_locked: bool = False
    lock_expiry_date: Optional[date] = None
    
    # Dates
    account_opened_date: date
    account_closed_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# SHARE TRANSACTION
# ============================================================================

class ShareTransaction(BaseModel):
    """Share transaction record"""
    transaction_id: str
    account_id: str
    
    transaction_type: ShareTransactionType
    transaction_date: date
    
    # Shares
    num_shares: int
    price_per_share: Decimal
    total_amount: Decimal
    
    # Fees
    transaction_fee: Decimal = Decimal("0")
    
    # Transfer details (if applicable)
    transfer_from_account_id: Optional[str] = None
    transfer_to_account_id: Optional[str] = None
    
    # Status
    status: str = "completed"  # pending, completed, cancelled
    
    # Reference
    reference: Optional[str] = None
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# DIVIDEND
# ============================================================================

class DividendDeclaration(BaseModel):
    """
    Dividend Declaration
    
    Declares dividends for a share product
    """
    dividend_id: str
    product_id: str
    
    # Dividend details
    dividend_amount_per_share: Decimal
    total_dividend_amount: Decimal
    
    # Dates
    declaration_date: date
    record_date: date  # Shareholders on this date receive dividend
    payment_date: date
    
    # Status
    status: DividendStatus = DividendStatus.DECLARED
    
    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Payment tracking
    total_paid: Decimal = Decimal("0")
    num_shareholders_paid: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class DividendPayment(BaseModel):
    """Individual dividend payment to shareholder"""
    payment_id: str
    dividend_id: str
    account_id: str
    
    num_shares: int
    amount_per_share: Decimal
    total_amount: Decimal
    
    # Tax
    withholding_tax: Decimal = Decimal("0")
    net_amount: Decimal
    
    payment_date: date
    payment_method: str = "bank_transfer"
    
    status: str = "paid"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateShareProductRequest(BaseModel):
    """Request to create share product"""
    product_code: str
    product_name: str
    product_type: ShareProductType
    description: str
    nominal_price: Decimal
    minimum_shares: int
    dividend_rate: Optional[Decimal] = None
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CreateShareAccountRequest(BaseModel):
    """Request to create share account"""
    client_id: str
    product_id: str
    num_shares: int
    price_per_share: Decimal
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class PurchaseSharesRequest(BaseModel):
    """Request to purchase shares"""
    account_id: str
    num_shares: int
    price_per_share: Decimal
    transaction_date: date
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class RedeemSharesRequest(BaseModel):
    """Request to redeem shares"""
    account_id: str
    num_shares: int
    redemption_price: Decimal
    transaction_date: date
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class DeclareDividendRequest(BaseModel):
    """Request to declare dividend"""
    product_id: str
    dividend_amount_per_share: Decimal
    record_date: date
    payment_date: date
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class TransferSharesRequest(BaseModel):
    """Request to transfer shares between accounts"""
    from_account_id: str
    to_account_id: str
    num_shares: int
    transfer_price: Decimal
    transaction_date: date
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }

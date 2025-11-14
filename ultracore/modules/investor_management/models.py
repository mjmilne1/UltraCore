"""
Investor Management Domain Models
Event-sourced models for loan sales and investor tracking
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass


class InvestorType(str, Enum):
    """Types of investors"""
    INSTITUTIONAL = "institutional"
    PRIVATE_EQUITY = "private_equity"
    HEDGE_FUND = "hedge_fund"
    ASSET_MANAGER = "asset_manager"
    BANK = "bank"
    INSURANCE_COMPANY = "insurance_company"
    PENSION_FUND = "pension_fund"
    FAMILY_OFFICE = "family_office"
    INDIVIDUAL = "individual"
    SPV = "special_purpose_vehicle"


class InvestorStatus(str, Enum):
    """Investor account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"


class TransferType(str, Enum):
    """Types of loan transfers"""
    SALE = "sale"  # Initial sale to investor
    INTERMEDIARY_SALE = "intermediary_sale"  # Investor to investor
    BUY_BACK = "buy_back"  # Repurchase by originator
    PARTIAL_SALE = "partial_sale"  # Sell portion of loan
    SECURITIZATION = "securitization"  # Transfer to SPV for securitization


class TransferStatus(str, Enum):
    """Status of loan transfer"""
    PENDING = "pending"
    APPROVED = "approved"
    SETTLEMENT_IN_PROGRESS = "settlement_in_progress"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REVERSED = "reversed"


class TransferSubStatus(str, Enum):
    """Sub-status for additional context"""
    AWAITING_APPROVAL = "awaiting_approval"
    AWAITING_SETTLEMENT = "awaiting_settlement"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_RECEIVED = "payment_received"
    DOCUMENTS_PENDING = "documents_pending"
    COMPLIANCE_REVIEW = "compliance_review"
    FRAUD_CHECK = "fraud_check"


class PaymentRoutingStatus(str, Enum):
    """Payment routing status"""
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"


# Domain Models

class Investor(BaseModel):
    """External investor/asset owner"""
    
    investor_id: str = Field(..., description="Unique investor ID")
    external_id: str = Field(..., description="External reference ID")
    investor_name: str = Field(..., description="Investor legal name")
    investor_type: InvestorType
    status: InvestorStatus = InvestorStatus.ACTIVE
    
    # Contact information
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    country: str = "AU"
    
    # Banking details
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_bsb: Optional[str] = None
    bank_swift: Optional[str] = None
    
    # Investment preferences
    min_investment_amount: Optional[Decimal] = None
    max_investment_amount: Optional[Decimal] = None
    preferred_loan_types: List[str] = []
    preferred_risk_rating: Optional[str] = None
    
    # Compliance
    kyc_verified: bool = False
    kyc_verification_date: Optional[datetime] = None
    aml_verified: bool = False
    aml_verification_date: Optional[datetime] = None
    accredited_investor: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    # Aggregates
    total_investments: Decimal = Decimal("0.00")
    active_loans: int = 0
    total_returns: Decimal = Decimal("0.00")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class LoanTransfer(BaseModel):
    """Loan ownership transfer"""
    
    transfer_id: str = Field(..., description="Unique transfer ID")
    external_id: str = Field(..., description="External reference ID")
    
    # Loan information
    loan_id: str = Field(..., description="Loan being transferred")
    loan_external_id: Optional[str] = None
    
    # Transfer details
    transfer_type: TransferType
    status: TransferStatus = TransferStatus.PENDING
    sub_status: Optional[TransferSubStatus] = None
    
    # Parties
    from_investor_id: Optional[str] = None  # None if from originator
    to_investor_id: str = Field(..., description="Investor receiving the loan")
    
    # Financial terms
    outstanding_principal: Decimal = Field(..., description="Principal at transfer")
    outstanding_interest: Decimal = Field(default=Decimal("0.00"))
    purchase_price: Decimal = Field(..., description="Actual purchase price")
    purchase_price_ratio: Decimal = Field(..., description="Price as % of principal")
    
    # For partial sales
    transfer_percentage: Decimal = Field(default=Decimal("100.00"), description="% of loan transferred")
    
    # Dates
    initiation_date: datetime = Field(default_factory=datetime.utcnow)
    approval_date: Optional[datetime] = None
    settlement_date: date = Field(..., description="When cash is exchanged")
    effective_date_from: date = Field(..., description="When investor starts receiving payments")
    effective_date_to: Optional[date] = None  # For temporary transfers
    
    # Accounting
    gain_loss_amount: Optional[Decimal] = None
    journal_entry_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    approved_by: Optional[str] = None
    
    # Additional data
    notes: Optional[str] = None
    documents: List[str] = []  # Document IDs
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class PaymentRouting(BaseModel):
    """Payment routing configuration for transferred loans"""
    
    routing_id: str = Field(..., description="Unique routing ID")
    loan_id: str
    investor_id: str
    transfer_id: str
    
    # Routing configuration
    route_principal: bool = True
    route_interest: bool = True
    route_fees: bool = False  # Fees may be retained by originator
    
    # Percentage routing (for partial sales)
    routing_percentage: Decimal = Decimal("100.00")
    
    # Status
    status: PaymentRoutingStatus = PaymentRoutingStatus.ACTIVE
    effective_from: date
    effective_to: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class InvestorPortfolio(BaseModel):
    """Investor's loan portfolio summary"""
    
    investor_id: str
    
    # Portfolio metrics
    total_loans: int = 0
    total_principal_outstanding: Decimal = Decimal("0.00")
    total_interest_outstanding: Decimal = Decimal("0.00")
    total_invested: Decimal = Decimal("0.00")
    
    # Performance metrics
    weighted_avg_interest_rate: Decimal = Decimal("0.00")
    weighted_avg_remaining_term: int = 0
    portfolio_yield: Decimal = Decimal("0.00")
    
    # Risk metrics
    non_performing_loans: int = 0
    non_performing_amount: Decimal = Decimal("0.00")
    default_rate: Decimal = Decimal("0.00")
    
    # Breakdown by loan type
    loan_type_breakdown: Dict[str, int] = {}
    
    # Updated timestamp
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class SecuritizationPool(BaseModel):
    """Pool of loans for securitization"""
    
    pool_id: str = Field(..., description="Unique pool ID")
    pool_name: str
    
    # SPV details
    spv_investor_id: str = Field(..., description="SPV as investor")
    
    # Pool composition
    loan_ids: List[str] = []
    total_loans: int = 0
    total_principal: Decimal = Decimal("0.00")
    
    # Pool characteristics
    weighted_avg_interest_rate: Decimal
    weighted_avg_maturity: int  # months
    pool_credit_rating: Optional[str] = None
    
    # Status
    status: str = "forming"  # forming, active, closed
    
    # Dates
    formation_date: date
    closing_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


# Request/Response Models

class CreateInvestorRequest(BaseModel):
    """Request to create new investor"""
    external_id: str
    investor_name: str
    investor_type: InvestorType
    email: str
    phone: Optional[str] = None
    country: str = "AU"
    created_by: str


class InitiateLoanTransferRequest(BaseModel):
    """Request to initiate loan transfer"""
    loan_id: str
    to_investor_id: str
    transfer_type: TransferType
    purchase_price_ratio: Decimal = Field(..., ge=0, le=2.0)  # 0-200%
    settlement_date: date
    effective_date_from: date
    transfer_percentage: Decimal = Field(default=Decimal("100.00"), ge=0, le=100)
    notes: Optional[str] = None
    created_by: str


class ApproveTransferRequest(BaseModel):
    """Request to approve transfer"""
    transfer_id: str
    approved_by: str
    notes: Optional[str] = None


class CancelTransferRequest(BaseModel):
    """Request to cancel transfer"""
    transfer_id: str
    reason: str
    cancelled_by: str

"""
Loan Account Models
Defines loan accounts, applications, and lifecycle states
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class LoanApplicationStatus(str, Enum):
    """Loan application statuses"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_ASSESSMENT = "under_assessment"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class LoanAccountStatus(str, Enum):
    """Loan account statuses"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    ARREARS = "arrears"
    DEFAULT = "default"
    HARDSHIP = "hardship"
    CLOSED_PAID = "closed_paid"
    CLOSED_WRITTEN_OFF = "closed_written_off"
    CLOSED_SOLD = "closed_sold"


class RepaymentStatus(str, Enum):
    """Repayment statuses"""
    CURRENT = "current"
    ARREARS_1_30_DAYS = "arrears_1_30_days"
    ARREARS_31_60_DAYS = "arrears_31_60_days"
    ARREARS_61_90_DAYS = "arrears_61_90_days"
    ARREARS_90_PLUS_DAYS = "arrears_90_plus_days"
    DEFAULT = "default"


class DisbursementMethod(str, Enum):
    """How loan funds are disbursed"""
    BANK_TRANSFER = "bank_transfer"  # Direct to customer account
    DIRECT_PAYMENT = "direct_payment"  # Direct to merchant/seller
    CHEQUE = "cheque"  # Legacy, not used for digital-only
    SPLIT = "split"  # Multiple disbursements


# ============================================================================
# LOAN APPLICATION
# ============================================================================

class LoanApplicant(BaseModel):
    """Loan applicant details"""
    applicant_id: str
    client_id: str  # Reference to UltraCore client
    is_primary: bool = True
    
    # Personal details
    first_name: str
    last_name: str
    date_of_birth: date
    email: str
    mobile: str
    
    # Employment
    employment_status: str  # employed, self_employed, retired, etc.
    employer_name: Optional[str] = None
    occupation: Optional[str] = None
    years_employed: Optional[int] = None
    
    # Income (annual)
    gross_income: Decimal
    net_income: Decimal
    other_income: Decimal = Decimal("0")
    
    # Expenses (monthly)
    living_expenses: Decimal
    existing_loan_repayments: Decimal = Decimal("0")
    credit_card_limits: Decimal = Decimal("0")
    
    # Assets
    total_assets: Decimal = Decimal("0")
    total_liabilities: Decimal = Decimal("0")
    
    # Residency
    is_australian_citizen: bool
    is_australian_resident: bool
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class LoanApplication(BaseModel):
    """
    Loan Application
    
    Represents a customer's application for a loan
    """
    application_id: str
    external_id: Optional[str] = None
    
    # Product
    product_id: str
    product_code: str
    
    # Loan details
    requested_amount: Decimal
    approved_amount: Optional[Decimal] = None
    term_months: int
    repayment_frequency: str
    loan_purpose: str
    
    # Applicants
    applicants: List[LoanApplicant]
    
    # Interest rate
    interest_rate: Optional[Decimal] = None
    comparison_rate: Optional[Decimal] = None
    
    # Security/Collateral
    has_security: bool = False
    security_value: Optional[Decimal] = None
    lvr: Optional[Decimal] = None  # Loan-to-Value Ratio
    
    # Status
    status: LoanApplicationStatus = LoanApplicationStatus.DRAFT
    
    # Assessment
    credit_score: Optional[int] = None
    risk_rating: Optional[str] = None
    affordability_score: Optional[Decimal] = None
    
    # Responsible lending
    responsible_lending_completed: bool = False
    suitability_assessment_completed: bool = False
    verification_completed: bool = False
    
    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# LOAN ACCOUNT
# ============================================================================

class LoanAccount(BaseModel):
    """
    Loan Account
    
    Represents an active loan account
    """
    account_id: str
    account_number: str  # Customer-facing account number
    external_id: Optional[str] = None
    
    # Application
    application_id: str
    
    # Product
    product_id: str
    product_code: str
    product_name: str
    
    # Customer
    client_id: str  # Primary borrower
    co_borrower_ids: List[str] = []
    
    # Loan terms
    principal_amount: Decimal
    approved_amount: Decimal
    disbursed_amount: Decimal = Decimal("0")
    current_principal: Decimal
    
    term_months: int
    remaining_term_months: int
    
    interest_rate: Decimal
    comparison_rate: Decimal
    rate_type: str  # fixed, variable
    
    repayment_frequency: str
    repayment_amount: Decimal
    
    # Dates
    approval_date: date
    disbursement_date: Optional[date] = None
    first_repayment_date: Optional[date] = None
    maturity_date: date
    
    # Security
    has_security: bool = False
    security_ids: List[str] = []  # References to collateral
    lvr: Optional[Decimal] = None
    
    # Balances
    outstanding_principal: Decimal
    outstanding_interest: Decimal = Decimal("0")
    outstanding_fees: Decimal = Decimal("0")
    total_outstanding: Decimal
    
    # Repayment tracking
    total_paid: Decimal = Decimal("0")
    principal_paid: Decimal = Decimal("0")
    interest_paid: Decimal = Decimal("0")
    fees_paid: Decimal = Decimal("0")
    
    next_repayment_date: Optional[date] = None
    next_repayment_amount: Optional[Decimal] = None
    
    # Arrears
    days_in_arrears: int = 0
    arrears_amount: Decimal = Decimal("0")
    repayment_status: RepaymentStatus = RepaymentStatus.CURRENT
    
    # Status
    status: LoanAccountStatus = LoanAccountStatus.PENDING_APPROVAL
    
    # Features
    allows_extra_repayments: bool = True
    allows_redraw: bool = False
    redraw_available: Decimal = Decimal("0")
    
    # Hardship
    is_in_hardship: bool = False
    hardship_arrangement_id: Optional[str] = None
    
    # Australian Compliance
    nccp_regulated: bool = True
    responsible_lending_file_id: Optional[str] = None
    credit_guide_provided: bool = False
    credit_guide_provided_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# LOAN DISBURSEMENT
# ============================================================================

class LoanDisbursement(BaseModel):
    """Loan disbursement record"""
    disbursement_id: str
    account_id: str
    
    amount: Decimal
    disbursement_method: DisbursementMethod
    
    # Bank transfer details
    recipient_account_name: Optional[str] = None
    recipient_bsb: Optional[str] = None
    recipient_account_number: Optional[str] = None
    
    # Direct payment details
    payee_name: Optional[str] = None
    payee_reference: Optional[str] = None
    
    disbursement_date: date
    status: str  # pending, completed, failed
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# LOAN REPAYMENT
# ============================================================================

class LoanRepayment(BaseModel):
    """Loan repayment record"""
    repayment_id: str
    account_id: str
    
    amount: Decimal
    principal_portion: Decimal
    interest_portion: Decimal
    fees_portion: Decimal = Decimal("0")
    
    repayment_date: date
    due_date: date
    
    is_scheduled: bool = True  # False for extra repayments
    payment_method: str  # direct_debit, bank_transfer, card
    
    status: str  # pending, completed, failed, dishonoured
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateLoanApplicationRequest(BaseModel):
    """Request to create loan application"""
    product_id: str
    requested_amount: Decimal
    term_months: int
    repayment_frequency: str
    loan_purpose: str
    applicants: List[LoanApplicant]
    has_security: bool = False
    security_value: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class ApproveLoanApplicationRequest(BaseModel):
    """Request to approve loan application"""
    application_id: str
    approved_amount: Decimal
    interest_rate: Decimal
    approved_by: str
    notes: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class DisburseLoanRequest(BaseModel):
    """Request to disburse loan"""
    account_id: str
    disbursement_method: DisbursementMethod
    recipient_account_name: Optional[str] = None
    recipient_bsb: Optional[str] = None
    recipient_account_number: Optional[str] = None
    disbursement_date: date
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class RecordRepaymentRequest(BaseModel):
    """Request to record repayment"""
    account_id: str
    amount: Decimal
    repayment_date: date
    payment_method: str
    is_scheduled: bool = True
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }

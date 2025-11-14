"""
Lending API Schemas.

Request and response schemas for lending API endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ..models.enums import (
    LoanType,
    LoanStatus,
    LoanPurpose,
    RepaymentFrequency,
    PropertyUsage
)


# Loan Application Schemas

class LoanApplicationRequest(BaseModel):
    """Request to create a loan application."""
    loan_type: LoanType
    loan_purpose: LoanPurpose
    amount: Decimal = Field(..., gt=0)
    term_months: int = Field(..., gt=0)
    
    # Applicant details
    annual_income: Decimal
    employment_status: str
    employment_years: int
    
    # Property (for home loans)
    property_value: Optional[Decimal] = None
    property_address: Optional[str] = None
    property_usage: Optional[PropertyUsage] = None
    
    # Business (for business loans)
    business_abn: Optional[str] = None
    business_name: Optional[str] = None
    business_industry: Optional[str] = None
    business_age_years: Optional[int] = None


class LoanApplicationResponse(BaseModel):
    """Loan application response."""
    application_id: str
    loan_type: LoanType
    amount: Decimal
    term_months: int
    status: str
    credit_score: Optional[int]
    decision: Optional[str]  # approved, declined, pending
    interest_rate: Optional[Decimal]
    comparison_rate: Optional[Decimal]
    monthly_repayment: Optional[Decimal]
    created_at: datetime


# Loan Schemas

class LoanResponse(BaseModel):
    """Loan response."""
    loan_id: str
    application_id: str
    customer_id: str
    loan_type: LoanType
    loan_purpose: LoanPurpose
    status: LoanStatus
    
    principal: Decimal
    term_months: int
    interest_rate: Decimal
    comparison_rate: Decimal
    
    current_balance: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    
    repayment_amount: Decimal
    repayment_frequency: RepaymentFrequency
    next_payment_date: Optional[date]
    
    days_in_arrears: int
    arrears_amount: Decimal
    
    disbursement_date: Optional[date]
    created_at: datetime


class HomeLoanResponse(LoanResponse):
    """Home loan response."""
    property_address: str
    property_value: Decimal
    property_usage: PropertyUsage
    lvr: Decimal
    lmi_required: bool
    rate_type: str
    offset_account_id: Optional[str]


class BusinessLoanResponse(LoanResponse):
    """Business loan response."""
    business_abn: str
    business_name: str
    business_industry: str
    director_guarantees: List[str]


# Loan Servicing Schemas

class MakeRepaymentRequest(BaseModel):
    """Request to make a loan repayment."""
    amount: Decimal = Field(..., gt=0)
    payment_method_id: str
    reference: Optional[str] = None


class RepaymentResponse(BaseModel):
    """Repayment response."""
    repayment_id: str
    loan_id: str
    amount: Decimal
    principal_portion: Decimal
    interest_portion: Decimal
    new_balance: Decimal
    payment_date: datetime


class LoanStatementRequest(BaseModel):
    """Request for loan statement."""
    from_date: date
    to_date: date


class LoanStatementResponse(BaseModel):
    """Loan statement response."""
    loan_id: str
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_repayments: Decimal
    total_interest_charged: Decimal
    transactions: List[Dict[str, Any]]


class DrawdownRequest(BaseModel):
    """Request to draw down from line of credit."""
    amount: Decimal = Field(..., gt=0)
    purpose: str
    to_account_id: str


# Restructuring Schemas

class RestructureRequest(BaseModel):
    """Request to restructure loan."""
    new_term_months: Optional[int] = None
    new_repayment_amount: Optional[Decimal] = None
    new_repayment_frequency: Optional[RepaymentFrequency] = None
    reason: str


class HardshipRequest(BaseModel):
    """Request for hardship assistance."""
    reason: str
    financial_situation: str
    proposed_arrangement: str
    duration_months: int


# Refinance Schemas

class RefinanceQuoteRequest(BaseModel):
    """Request for refinance quote."""
    current_loan_id: str
    new_amount: Optional[Decimal] = None
    new_term_months: Optional[int] = None
    cashout_amount: Optional[Decimal] = None


class RefinanceQuoteResponse(BaseModel):
    """Refinance quote response."""
    quote_id: str
    current_balance: Decimal
    new_amount: Decimal
    new_term_months: int
    new_interest_rate: Decimal
    new_monthly_repayment: Decimal
    estimated_savings: Decimal
    break_costs: Decimal
    valid_until: datetime


# Document Schemas

class DocumentUploadRequest(BaseModel):
    """Request to upload loan document."""
    document_type: str
    file_name: str
    file_url: str


class DocumentResponse(BaseModel):
    """Document response."""
    document_id: str
    document_type: str
    file_name: str
    uploaded_at: datetime
    verified: bool


# Other Schemas

class LoanCalculationRequest(BaseModel):
    """Request for loan calculations."""
    amount: Decimal
    term_months: int
    interest_rate: Decimal
    repayment_frequency: RepaymentFrequency = RepaymentFrequency.MONTHLY


class LoanCalculationResponse(BaseModel):
    """Loan calculation response."""
    amount: Decimal
    term_months: int
    interest_rate: Decimal
    repayment_amount: Decimal
    total_interest: Decimal
    total_repayable: Decimal
    comparison_rate: Decimal


class EligibilityCheckRequest(BaseModel):
    """Request for eligibility check."""
    loan_type: LoanType
    amount: Decimal
    annual_income: Decimal
    existing_debts: Decimal
    credit_score: Optional[int] = None


class EligibilityCheckResponse(BaseModel):
    """Eligibility check response."""
    eligible: bool
    max_loan_amount: Decimal
    estimated_rate: Decimal
    reasons: List[str]

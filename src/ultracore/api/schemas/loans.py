"""
Loan API Schemas

Pydantic models for loan endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from ultracore.api.schemas.common import LoanTypeEnum


# ============================================================================
# Request Models
# ============================================================================

class LoanApplicationRequest(BaseModel):
    """Loan application request"""
    customer_id: str = Field(..., description="Customer applying for loan")
    loan_type: LoanTypeEnum
    
    # Amount
    requested_amount: Decimal = Field(..., gt=0, description="Loan amount requested")
    currency: str = Field("AUD", pattern=r'^[A-Z]{3}$')
    
    # Terms
    term_months: int = Field(..., ge=1, le=360, description="Loan term in months")
    interest_rate: Decimal = Field(..., ge=0, le=100, description="Annual interest rate")
    
    # Purpose
    purpose: str = Field(..., max_length=500)
    
    # Employment (for underwriting)
    employment_status: Optional[str] = None
    annual_income: Optional[Decimal] = Field(None, ge=0)
    
    # Collateral (if secured)
    collateral_type: Optional[str] = None
    collateral_value: Optional[Decimal] = Field(None, ge=0)


class LoanRepaymentRequest(BaseModel):
    """Loan repayment request"""
    account_id: str = Field(..., description="Account to debit from")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_type: str = Field("REGULAR", pattern=r'^(REGULAR|EXTRA|FULL)$')


# ============================================================================
# Response Models
# ============================================================================

class LoanResponse(BaseModel):
    """Loan response"""
    loan_id: str
    customer_id: str
    loan_type: str
    status: str
    
    # Amount
    original_amount: float
    current_balance: float
    currency: str
    
    # Terms
    interest_rate: float
    term_months: int
    monthly_payment: float
    
    # Schedule
    disbursement_date: Optional[date] = None
    first_payment_date: Optional[date] = None
    maturity_date: Optional[date] = None
    
    # Balances
    principal_balance: float
    interest_balance: float
    fees_balance: float
    
    # Payment info
    payments_made: int
    payments_remaining: int
    next_payment_date: Optional[date] = None
    next_payment_amount: Optional[float] = None
    
    # Metadata
    created_at: datetime
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoanListResponse(BaseModel):
    """List of loans"""
    loans: List[LoanResponse]
    total: int


class LoanPaymentScheduleResponse(BaseModel):
    """Loan payment schedule"""
    loan_id: str
    payments: List[dict]
    total_payments: int
    total_principal: float
    total_interest: float

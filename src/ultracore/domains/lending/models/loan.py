"""Loan Models - Event-Sourced, UltraLedger Backed"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from .enums import (
    LoanType,
    LoanStatus,
    LoanPurpose,
    RepaymentFrequency,
    PropertyUsage
)


class Loan(BaseModel):
    """
    Base Loan model (Event-Sourced).
    
    Reconstructed from events.
    UltraLedger provides authoritative balance.
    
    Australian Compliance:
    - NCCP regulated (most consumer loans)
    - Responsible lending assessment
    - Comparison rate disclosure
    - Early repayment rights
    """
    
    # Identity
    loan_id: str
    application_id: str
    customer_id: str
    
    # Loan type
    loan_type: LoanType
    loan_purpose: LoanPurpose
    
    # Status
    status: LoanStatus = LoanStatus.APPLICATION
    
    # Amount and term
    principal: Decimal
    term_months: int
    
    # Interest
    interest_rate: Decimal  # p.a.
    comparison_rate: Decimal  # Australian requirement (includes fees)
    
    # Balances (from UltraLedger)
    current_balance: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    
    # Repayment
    repayment_amount: Decimal
    repayment_frequency: RepaymentFrequency
    next_payment_date: Optional[date] = None
    
    # Fees
    establishment_fee: Decimal
    monthly_fee: Decimal
    early_repayment_fee: Optional[Decimal] = None
    
    # Security
    secured: bool = False
    collateral_id: Optional[str] = None
    lvr: Optional[Decimal] = None  # Loan-to-Value Ratio
    
    # Dates
    disbursement_date: Optional[date] = None
    first_payment_date: Optional[date] = None
    final_payment_date: Optional[date] = None
    
    # Arrears
    days_in_arrears: int = 0
    arrears_amount: Decimal = Decimal("0.00")
    missed_payments: int = 0
    
    # NCCP
    nccp_regulated: bool = True
    responsible_lending_assessed: bool = False
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    version: int = 0
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class PersonalLoan(Loan):
    """
    Personal loan (unsecured consumer lending).
    
    Australian Market:
    - Typical amounts: $2,000 - $50,000
    - Typical terms: 1-7 years
    - Interest rates: 6% - 20% p.a.
    - Usually unsecured
    - NCCP regulated
    
    Use cases:
    - Debt consolidation
    - Car purchase
    - Home improvement
    - Wedding
    - Holiday
    """
    
    loan_type: LoanType = LoanType.PERSONAL
    
    # Typically unsecured
    secured: bool = False
    
    # Purpose
    loan_purpose: LoanPurpose
    
    # Credit card consolidation (common)
    consolidating_credit_cards: bool = False
    credit_cards_to_close: List[str] = []


class HomeLoan(Loan):
    """
    Home loan / Mortgage (secured consumer lending).
    
    Australian Market:
    - Typical amounts: $200,000 - $2,000,000+
    - Typical terms: 15-30 years
    - Interest rates: 3% - 7% p.a.
    - Always secured (property)
    - NCCP regulated
    - LVR restrictions (APRA)
    
    Types:
    - Owner-occupied (lower rates)
    - Investment (higher rates)
    - Fixed rate (1-5 years)
    - Variable rate
    """
    
    loan_type: LoanType = LoanType.HOME
    
    # Always secured
    secured: bool = True
    
    # Property
    property_address: str
    property_value: Decimal
    property_usage: PropertyUsage
    
    # LVR (Loan-to-Value Ratio)
    lvr: Decimal  # e.g., 0.80 = 80%
    
    # APRA restrictions
    lmi_required: bool = False  # Lenders Mortgage Insurance (LVR > 80%)
    lmi_amount: Optional[Decimal] = None
    
    # Rate type
    rate_type: str = "variable"  # variable, fixed
    fixed_period_months: Optional[int] = None
    
    # Interest only period (common in Australia)
    interest_only_period_months: int = 0
    
    # Offset account (Australian feature)
    offset_account_id: Optional[str] = None
    
    # Redraw facility
    redraw_facility: bool = True
    additional_repayments: Decimal = Decimal("0.00")


class BusinessLoan(Loan):
    """
    Business loan (commercial lending).
    
    Australian Market:
    - Typical amounts: $10,000 - $5,000,000+
    - Typical terms: 1-10 years
    - Interest rates: 5% - 15% p.a.
    - Often secured (property, equipment)
    - May require director guarantees
    - Not NCCP regulated (business purpose)
    
    Types:
    - Working capital
    - Equipment finance
    - Commercial property
    - Business expansion
    """
    
    loan_type: LoanType = LoanType.BUSINESS
    
    # Not NCCP regulated (business purpose)
    nccp_regulated: bool = False
    
    # Business details
    business_abn: str
    business_name: str
    business_industry: str
    business_age_years: int
    
    # Security
    secured: bool = True  # Usually secured
    director_guarantees: List[str] = []
    
    # Purpose
    loan_purpose: LoanPurpose


class LineOfCredit(Loan):
    """
    Line of Credit (revolving facility).
    
    Australian Features:
    - Approved limit
    - Draw down as needed
    - Repay and redraw
    - Interest on drawn balance only
    - Usually secured (property)
    
    Types:
    - Personal LOC
    - Home equity LOC
    - Business LOC
    """
    
    loan_type: LoanType = LoanType.LINE_OF_CREDIT
    
    # Credit limit
    credit_limit: Decimal
    available_credit: Decimal
    drawn_balance: Decimal = Decimal("0.00")
    
    # No fixed term
    term_months: int = 0  # Revolving
    
    # Minimum monthly payment (usually interest only)
    minimum_payment_percentage: Decimal = Decimal("0.02")  # 2% of balance


class BNPLPurchase(Loan):
    """
    Buy Now Pay Later (BNPL) - Installment plan.
    
    Australian BNPL Providers:
    - Afterpay
    - Zip
    - Klarna
    - Humm
    
    Features:
    - Short term (6 weeks - 24 months)
    - Interest-free if paid on time
    - Small amounts ($100 - $2,000 typically)
    - Late fees for missed payments
    - Regulated as credit (ASIC)
    
    Model:
    - 4 installments over 6 weeks (Afterpay style)
    - Weekly/fortnightly payments
    - No interest if paid on time
    - Late fees applied
    """
    
    loan_type: LoanType = LoanType.BNPL
    
    # BNPL specific
    merchant: str
    order_id: str
    
    # Installments
    number_of_installments: int = 4
    installment_amount: Decimal
    installments_paid: int = 0
    
    # Interest-free if paid on time
    interest_rate: Decimal = Decimal("0.00")
    
    # Short term
    term_months: int = 2  # Typically 6-8 weeks
    
    # Fees
    late_fee_per_installment: Decimal = Decimal("10.00")
    establishment_fee: Decimal = Decimal("0.00")  # Usually free
    
    # NCCP exemption (for small amounts)
    nccp_regulated: bool = False

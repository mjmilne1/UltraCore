"""Loan Application Events - Origination Workflow"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import LendingEvent


class LoanApplicationSubmittedEvent(LendingEvent):
    """
    Loan application submitted.
    
    Triggers:
    - Credit check (Equifax/Experian/Illion)
    - Income verification
    - Employment verification
    - Responsible lending assessment (NCCP)
    - Fraud detection (ML)
    - Collateral valuation (if secured)
    """
    
    event_type: str = "LoanApplicationSubmitted"
    regulatory_event: bool = True
    
    # Application details
    application_id: str
    loan_type: str  # personal, home, business, loc, bnpl
    loan_purpose: str
    
    # Amount and term
    loan_amount: Decimal
    loan_term_months: int
    requested_rate: Optional[Decimal] = None
    
    # Applicant details
    employment_type: str  # full_time, part_time, self_employed, casual
    annual_income: Decimal
    employment_duration_months: int
    
    # Expenses (NCCP requirement)
    monthly_living_expenses: Decimal
    monthly_debt_obligations: Decimal
    dependents: int = 0
    
    # Collateral (if secured)
    collateral_type: Optional[str] = None
    collateral_value: Optional[Decimal] = None
    
    # Property (for home loans)
    property_address: Optional[str] = None
    property_value: Optional[Decimal] = None
    property_usage: Optional[str] = None  # owner_occupied, investment
    
    # Submitted
    submitted_at: datetime
    submitted_via: str  # online, branch, broker


class CreditCheckCompletedEvent(LendingEvent):
    """
    Credit check completed.
    
    Australian Credit Bureaus:
    - Equifax (formerly Veda)
    - Experian
    - Illion (formerly Dun & Bradstreet)
    
    Comprehensive Credit Reporting (CCR):
    - Positive data (repayment history)
    - Negative data (defaults, judgments)
    - Credit score (0-1200 typically)
    """
    
    event_type: str = "CreditCheckCompleted"
    regulatory_event: bool = True
    
    application_id: str
    
    # Credit bureau
    bureau: str  # equifax, experian, illion
    bureau_reference: str
    
    # Credit score
    credit_score: int  # 0-1200
    credit_score_band: str  # excellent, good, fair, poor
    
    # Credit file data
    enquiries_last_12_months: int
    active_credit_accounts: int
    total_credit_limit: Decimal
    total_outstanding_balance: Decimal
    
    # Defaults and judgments
    payment_defaults: int = 0
    court_judgments: int = 0
    bankruptcies: int = 0
    
    # Repayment history (CCR)
    on_time_payments_percentage: Optional[Decimal] = None
    late_payments_60_plus_days: int = 0
    
    # Risk assessment
    credit_risk_rating: str  # low, medium, high
    
    # Completed
    completed_at: datetime


class LoanApprovedEvent(LendingEvent):
    """
    Loan application approved.
    
    NCCP Compliance:
    - Responsible lending assessment completed
    - Assessment of unsuitability performed
    - Credit contract disclosure provided
    - Cooling off period starts (some products)
    """
    
    event_type: str = "LoanApproved"
    regulatory_event: bool = True
    
    application_id: str
    
    # Approved terms
    approved_amount: Decimal
    approved_term_months: int
    interest_rate: Decimal
    comparison_rate: Decimal  # Australian requirement
    
    # Fees
    establishment_fee: Decimal
    monthly_fee: Decimal
    early_repayment_fee: Optional[Decimal] = None
    
    # Repayment
    repayment_amount: Decimal
    repayment_frequency: str  # weekly, fortnightly, monthly
    first_payment_date: date
    
    # Conditions
    conditions: List[str] = Field(default_factory=list)
    # e.g., "Provide proof of insurance", "Sign mortgage documents"
    
    # Security (if applicable)
    secured: bool = False
    collateral_id: Optional[str] = None
    lvr: Optional[Decimal] = None  # Loan-to-Value Ratio
    
    # NCCP assessment
    responsible_lending_assessed: bool = True
    assessment_outcome: str = "suitable"
    
    # Approved
    approved_by: str
    approved_at: datetime
    
    # Disbursement account
    disbursement_account_id: str


class LoanRejectedEvent(LendingEvent):
    """Loan application rejected."""
    
    event_type: str = "LoanRejected"
    regulatory_event: bool = True
    
    application_id: str
    
    # Rejection reasons
    rejection_reasons: List[str]
    # e.g., "Insufficient income", "Poor credit history", "Cannot demonstrate serviceability"
    
    # NCCP assessment
    assessment_outcome: str = "unsuitable"  # NCCP requirement
    
    # Adverse action notice (NCCP requirement)
    adverse_action_notice_sent: bool = True
    customer_notified_at: datetime
    
    rejected_by: str
    rejected_at: datetime


class LoanDisbursedEvent(LendingEvent):
    """
    Loan funds disbursed.
    
    UltraLedger entries:
    - DEBIT: Loan Receivable (Asset)
    - CREDIT: Customer Account (Liability)
    
    Triggers:
    - First repayment scheduled
    - Interest accrual starts
    - Collateral registration (if secured)
    """
    
    event_type: str = "LoanDisbursed"
    regulatory_event: bool = True
    
    # Disbursement
    disbursed_amount: Decimal
    disbursement_account_id: str
    disbursement_method: str = "transfer"
    
    # Loan details
    principal: Decimal
    interest_rate: Decimal
    term_months: int
    
    # Repayment schedule
    repayment_amount: Decimal
    repayment_frequency: str
    first_payment_date: date
    final_payment_date: date
    
    # Collateral (if secured)
    collateral_id: Optional[str] = None
    ppsr_registered: bool = False
    
    # Disbursed
    disbursed_at: datetime
    disbursed_by: str
    
    # UltraLedger
    ledger_entry_id: str

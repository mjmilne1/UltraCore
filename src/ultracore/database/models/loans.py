"""
UltraCore Database Models - Loans

Loan domain models:
- Loan (personal, home, auto, business)
- Loan payment schedule
- Loan payments
- Collateral
"""

from sqlalchemy import Column, String, Date, DateTime, Boolean, Enum, ForeignKey, Index, Numeric, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from decimal import Decimal

from ultracore.database.models.base import BaseModel
import enum


class LoanTypeEnum(str, enum.Enum):
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    AUTO = "AUTO"
    BUSINESS = "BUSINESS"
    STUDENT = "STUDENT"


class LoanStatusEnum(str, enum.Enum):
    APPLICATION = "APPLICATION"
    UNDERWRITING = "UNDERWRITING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    PAID_OFF = "PAID_OFF"
    DEFAULT = "DEFAULT"
    WRITTEN_OFF = "WRITTEN_OFF"
    REJECTED = "REJECTED"


class PaymentStatusEnum(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    LATE = "LATE"
    MISSED = "MISSED"
    WAIVED = "WAIVED"


class RepaymentFrequencyEnum(str, enum.Enum):
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class Loan(BaseModel):
    """
    Loan entity
    
    Complete loan lifecycle management
    """
    
    __tablename__ = "loans"
    __table_args__ = (
        Index('idx_loans_tenant_customer', 'tenant_id', 'customer_id'),
        Index('idx_loans_type', 'tenant_id', 'loan_type'),
        Index('idx_loans_status', 'tenant_id', 'status'),
        Index('idx_loans_maturity', 'tenant_id', 'maturity_date'),
        CheckConstraint('current_balance >= 0', name='chk_loan_balance_positive'),
        {'schema': 'lending', 'comment': 'Loan master data'}
    )
    
    # Loan identifiers
    loan_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Business loan ID (LOAN-xxx)"
    )
    
    loan_number = Column(
        String(20),
        unique=True,
        nullable=False,
        comment="Loan account number"
    )
    
    # Customer relationship
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey('customers.customers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    customer = relationship("Customer", back_populates="loans")
    
    # Loan details
    loan_type = Column(
        Enum(LoanTypeEnum, name='loan_type_enum'),
        nullable=False
    )
    
    status = Column(
        Enum(LoanStatusEnum, name='loan_status_enum'),
        nullable=False,
        default=LoanStatusEnum.APPLICATION
    )
    
    # Amounts
    requested_amount = Column(Numeric(18, 2), nullable=False)
    approved_amount = Column(Numeric(18, 2), nullable=True)
    disbursed_amount = Column(Numeric(18, 2), nullable=True)
    current_balance = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    # Balance breakdown
    principal_balance = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    interest_balance = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    fees_balance = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    currency = Column(String(3), nullable=False, default='AUD')
    
    # Terms
    interest_rate = Column(
        Numeric(10, 6),
        nullable=False,
        comment="Annual interest rate"
    )
    
    term_months = Column(Integer, nullable=False)
    
    repayment_frequency = Column(
        Enum(RepaymentFrequencyEnum, name='repayment_frequency_enum'),
        nullable=False,
        default=RepaymentFrequencyEnum.MONTHLY
    )
    
    monthly_payment = Column(Numeric(18, 2), nullable=True)
    
    # Dates
    application_date = Column(DateTime(timezone=True), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    disbursement_date = Column(Date, nullable=True)
    first_payment_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    
    # Payment tracking
    payments_made = Column(Integer, nullable=False, default=0)
    payments_remaining = Column(Integer, nullable=True)
    next_payment_date = Column(Date, nullable=True)
    next_payment_amount = Column(Numeric(18, 2), nullable=True)
    last_payment_date = Column(Date, nullable=True)
    
    # Delinquency
    days_past_due = Column(Integer, nullable=False, default=0)
    missed_payments = Column(Integer, nullable=False, default=0)
    
    # Purpose
    purpose = Column(String(500), nullable=True)
    
    # Collateral
    is_secured = Column(Boolean, default=False)
    collateral_type = Column(String(100), nullable=True)
    collateral_value = Column(Numeric(18, 2), nullable=True)
    
    # Underwriting
    credit_score = Column(Integer, nullable=True)
    debt_to_income_ratio = Column(Numeric(5, 2), nullable=True)
    loan_to_value_ratio = Column(Numeric(5, 2), nullable=True)
    
    # Risk
    risk_rating = Column(String(20), nullable=True)
    probability_of_default = Column(Numeric(5, 4), nullable=True)
    
    # IFRS 9 (impairment)
    stage = Column(Integer, nullable=True, comment="IFRS 9 Stage (1, 2, 3)")
    expected_credit_loss = Column(Numeric(18, 2), nullable=True)
    provision_amount = Column(Numeric(18, 2), nullable=True)
    
    # Relationships
    payment_schedule = relationship("LoanPaymentSchedule", back_populates="loan", uselist=False)
    payments = relationship("LoanPayment", back_populates="loan", lazy="dynamic")
    collateral_items = relationship("LoanCollateral", back_populates="loan", lazy="dynamic")
    
    def __repr__(self):
        return f"<Loan(id={self.loan_id}, type={self.loan_type}, balance={self.current_balance})>"


class LoanPaymentSchedule(BaseModel):
    """
    Loan payment schedule (amortization)
    
    Generated when loan is disbursed
    """
    
    __tablename__ = "loan_payment_schedules"
    __table_args__ = (
        Index('idx_schedules_loan', 'tenant_id', 'loan_id'),
        {'schema': 'lending', 'comment': 'Loan payment schedules'}
    )
    
    loan_id = Column(
        UUID(as_uuid=True),
        ForeignKey('lending.loans.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    
    loan = relationship("Loan", back_populates="payment_schedule")
    
    # Schedule details
    total_payments = Column(Integer, nullable=False)
    payment_amount = Column(Numeric(18, 2), nullable=False)
    total_principal = Column(Numeric(18, 2), nullable=False)
    total_interest = Column(Numeric(18, 2), nullable=False)
    total_amount = Column(Numeric(18, 2), nullable=False)
    
    # Schedule data (JSON array of payment details)
    schedule_data = Column(
        JSONB,
        nullable=False,
        comment="Complete amortization schedule"
    )
    
    generated_at = Column(DateTime(timezone=True), nullable=False)


class LoanPayment(BaseModel):
    """
    Loan payment history
    
    Tracks all payments made against the loan
    """
    
    __tablename__ = "loan_payments"
    __table_args__ = (
        Index('idx_payments_loan_date', 'tenant_id', 'loan_id', 'payment_date'),
        Index('idx_payments_status', 'tenant_id', 'status', 'payment_date'),
        
        # Partition by payment_date (time-series)
        {'postgresql_partition_by': 'RANGE (payment_date)'},
        
        {'schema': 'lending', 'comment': 'Loan payment history'}
    )
    
    payment_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Payment ID (PAY-xxx)"
    )
    
    loan_id = Column(
        UUID(as_uuid=True),
        ForeignKey('lending.loans.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    loan = relationship("Loan", back_populates="payments")
    
    # Payment details
    payment_number = Column(Integer, nullable=False)
    
    status = Column(
        Enum(PaymentStatusEnum, name='payment_status_enum'),
        nullable=False,
        default=PaymentStatusEnum.SCHEDULED
    )
    
    # Amounts
    scheduled_amount = Column(Numeric(18, 2), nullable=False)
    paid_amount = Column(Numeric(18, 2), nullable=True)
    
    principal_amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    interest_amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    fees_amount = Column(Numeric(18, 2), nullable=False, default=Decimal('0.00'))
    
    # Dates
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    
    # Payment method
    payment_method = Column(String(50), nullable=True)
    payment_account_id = Column(String(50), nullable=True)
    transaction_id = Column(String(50), nullable=True)
    
    # Balance after payment
    balance_after = Column(Numeric(18, 2), nullable=True)
    
    def __repr__(self):
        return f"<LoanPayment(id={self.payment_id}, loan={self.loan_id}, amount={self.paid_amount})>"


class LoanCollateral(BaseModel):
    """
    Loan collateral items
    
    For secured loans
    """
    
    __tablename__ = "loan_collateral"
    __table_args__ = (
        Index('idx_collateral_loan', 'tenant_id', 'loan_id'),
        {'schema': 'lending', 'comment': 'Loan collateral'}
    )
    
    collateral_id = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Collateral ID"
    )
    
    loan_id = Column(
        UUID(as_uuid=True),
        ForeignKey('lending.loans.id', ondelete='RESTRICT'),
        nullable=False
    )
    
    loan = relationship("Loan", back_populates="collateral_items")
    
    # Collateral details
    collateral_type = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Valuation
    estimated_value = Column(Numeric(18, 2), nullable=False)
    appraised_value = Column(Numeric(18, 2), nullable=True)
    current_value = Column(Numeric(18, 2), nullable=True)
    
    valuation_date = Column(Date, nullable=True)
    next_valuation_date = Column(Date, nullable=True)
    
    # Identification
    serial_number = Column(String(100), nullable=True)
    vin = Column(String(17), nullable=True, comment="Vehicle VIN")
    registration = Column(String(50), nullable=True)
    
    # Insurance
    insured = Column(Boolean, default=False)
    insurance_provider = Column(String(200), nullable=True)
    insurance_policy = Column(String(100), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    released_date = Column(Date, nullable=True)

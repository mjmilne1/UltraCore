"""
Savings Database Models
SQLAlchemy models for savings domain (read models / projections)
"""

from sqlalchemy import Column, String, Numeric, DateTime, Integer, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from ultracore.database.base import Base


class SavingsAccountModel(Base):
    """Savings Account (Read Model / Projection)"""
    
    __tablename__ = "savings_accounts"
    
    # Primary key
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Account details
    account_number = Column(String(50), unique=True, nullable=False, index=True)
    bsb = Column(String(10))
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # savings, high_interest_savings, youth_saver, etc.
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # pending, approved, active, frozen, dormant, closed
    
    # Balances
    balance = Column(Numeric(precision=18, scale=2), nullable=False, default=Decimal('0.00'))
    available_balance = Column(Numeric(precision=18, scale=2), nullable=False, default=Decimal('0.00'))
    hold_amount = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    accrued_interest = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    
    # Tax
    tfn = Column(String(20))
    withholding_tax_rate = Column(Numeric(precision=5, scale=2), default=Decimal('47.00'))
    tfn_exemption = Column(Boolean, default=False)
    
    # Dates
    opened_date = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    activated_at = Column(DateTime)
    closed_at = Column(DateTime)
    dormant_since = Column(DateTime)
    last_transaction_date = Column(DateTime)
    last_interest_posting_date = Column(DateTime)
    
    # Approval
    approved_by = Column(String(255))
    closed_by = Column(String(255))
    
    # Additional data
    additional_data = Column(JSONB)
    
    # Relationships
    transactions = relationship("SavingsTransactionModel", back_populates="account", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_savings_accounts_client', 'client_id'),
        Index('idx_savings_accounts_status', 'status'),
        Index('idx_savings_accounts_tenant', 'tenant_id'),
    )


class SavingsTransactionModel(Base):
    """Savings Transaction (Read Model / Projection)"""
    
    __tablename__ = "savings_transactions"
    
    # Primary key
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    account_id = Column(UUID(as_uuid=True), ForeignKey('savings_accounts.account_id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False, index=True)  # deposit, withdrawal, transfer_in, transfer_out, interest_posting, fee
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    balance_before = Column(Numeric(precision=18, scale=2), nullable=False)
    balance_after = Column(Numeric(precision=18, scale=2), nullable=False)
    
    # References
    reference_number = Column(String(100), index=True)
    description = Column(Text)
    
    # Dates
    transaction_date = Column(DateTime, nullable=False, index=True)
    value_date = Column(DateTime)
    
    # Additional data
    additional_data = Column(JSONB)
    
    # Relationships
    account = relationship("SavingsAccountModel", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_savings_transactions_account', 'account_id'),
        Index('idx_savings_transactions_date', 'transaction_date'),
        Index('idx_savings_transactions_type', 'transaction_type'),
    )


class SavingsProductModel(Base):
    """Savings Product (Read Model / Projection)"""
    
    __tablename__ = "savings_products"
    
    # Primary key
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Product details
    product_code = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Interest rates
    base_interest_rate = Column(Numeric(precision=5, scale=2), nullable=False)
    bonus_interest_rate = Column(Numeric(precision=5, scale=2), default=Decimal('0.00'))
    
    # Interest calculation
    interest_calculation_method = Column(String(50), nullable=False)  # daily_balance, minimum_balance, average_balance
    interest_posting_frequency = Column(String(50), nullable=False)  # monthly, quarterly, annually
    
    # Balances
    minimum_opening_balance = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    minimum_balance = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    maximum_balance = Column(Numeric(precision=18, scale=2))
    
    # Fees
    monthly_fee = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    withdrawal_fee = Column(Numeric(precision=18, scale=2), default=Decimal('0.00'))
    free_withdrawals_per_month = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Compliance
    pds_url = Column(String(500))
    kfs_url = Column(String(500))
    
    # Metadata
    bonus_conditions = Column(JSONB)
    fee_waiver_conditions = Column(JSONB)
    age_restrictions = Column(JSONB)
    additional_data = Column(JSONB)


class TermDepositModel(Base):
    """Term Deposit (Read Model / Projection)"""
    
    __tablename__ = "term_deposits"
    
    # Primary key
    deposit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Deposit details
    account_number = Column(String(50), unique=True, nullable=False, index=True)
    deposit_amount = Column(Numeric(precision=18, scale=2), nullable=False)
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=False)
    term_months = Column(Integer, nullable=False)
    
    # Dates
    start_date = Column(DateTime, nullable=False)
    maturity_date = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # active, matured, closed
    
    # Maturity options
    auto_renew = Column(Boolean, default=False)
    maturity_instruction = Column(String(50))  # transfer_to_savings, renew, close
    
    # Early withdrawal
    early_withdrawal_penalty_rate = Column(Numeric(precision=5, scale=2))
    
    # Tax
    tfn = Column(String(20))
    withholding_tax_rate = Column(Numeric(precision=5, scale=2), default=Decimal('47.00'))
    
    # Additional data
    additional_data = Column(JSONB)
    
    # Indexes
    __table_args__ = (
        Index('idx_term_deposits_client', 'client_id'),
        Index('idx_term_deposits_status', 'status'),
        Index('idx_term_deposits_maturity', 'maturity_date'),
    )

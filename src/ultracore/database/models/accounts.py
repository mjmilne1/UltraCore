"""
UltraCore Database Models - Accounts

Account domain models:
- Account (savings, checking, term deposit, etc.)
- Transaction (deposits, withdrawals, transfers)
- Account balances (separate for performance)
- Interest rates
"""

from sqlalchemy import Column, String, Date, DateTime, Boolean, Enum, ForeignKey, Index, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from decimal import Decimal

from ultracore.database.models.base import BaseModel
import enum


class AccountTypeEnum(str, enum.Enum):
    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    TERM_DEPOSIT = "TERM_DEPOSIT"
    LOAN = "LOAN"
    CREDIT_CARD = "CREDIT_CARD"


class AccountStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"
    DORMANT = "DORMANT"


class TransactionTypeEnum(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    INTEREST = "INTEREST"
    FEE = "FEE"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"


class TransactionStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    FAILED = "FAILED"


class Account(BaseModel):
    """
    Account entity
    
    Core banking accounts (savings, checking, etc.)
    """
    
    __tablename__ = "accounts"
    __table_args__ = (
        Index('idx_accounts_tenant_customer', 'tenant_id', 'customer_id'),
        Index('idx_accounts_number', 'tenant_id', 'account_number'),
        Index('idx_accounts_type', 'tenant_id', 'account_type'),
        Index('idx_accounts_status', 'tenant_id', 'status'),
        {'schema': 'accounts', 'comment': 'Account master data'}
    )
    
    # Account identifiers
    account_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Business account ID (ACC-xxx)"
    )
    
    account_number = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Account number"
    )
    
    # Customer relationship
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey('customers.customers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    customer = relationship("Customer", back_populates="accounts")
    
    # Account details
    account_type = Column(
        Enum(AccountTypeEnum, name='account_type_enum'),
        nullable=False
    )
    
    status = Column(
        Enum(AccountStatusEnum, name='account_status_enum'),
        nullable=False,
        default=AccountStatusEnum.ACTIVE
    )
    
    currency = Column(String(3), nullable=False, default='AUD')
    
    # Interest
    interest_bearing = Column(Boolean, default=False)
    current_interest_rate = Column(Numeric(10, 6), nullable=True)
    
    # Term deposit
    maturity_date = Column(Date, nullable=True)
    
    # Dates
    opened_date = Column(DateTime(timezone=True), nullable=False)
    closed_date = Column(DateTime(timezone=True), nullable=True)
    last_transaction_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="account", lazy="dynamic")
    balances = relationship("AccountBalance", back_populates="account", uselist=False)
    
    def __repr__(self):
        return f"<Account(id={self.account_id}, number={self.account_number})>"


class AccountBalance(BaseModel):
    """
    Account balance (separate table for performance)
    
    Updated atomically with transactions
    """
    
    __tablename__ = "account_balances"
    __table_args__ = (
        Index('idx_balances_account', 'tenant_id', 'account_id'),
        CheckConstraint('ledger_balance >= 0 OR account_type = \'LOAN\'', name='chk_balance_non_negative'),
        {'schema': 'accounts', 'comment': 'Account balances (separate for performance)'}
    )
    
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey('accounts.accounts.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    
    account = relationship("Account", back_populates="balances")
    
    # Balances (using NUMERIC for precision)
    ledger_balance = Column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="Actual balance"
    )
    
    available_balance = Column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="Available for withdrawal"
    )
    
    pending_credits = Column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal('0.00')
    )
    
    pending_debits = Column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal('0.00')
    )
    
    held_amount = Column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal('0.00')
    )
    
    minimum_balance = Column(Numeric(18, 2), nullable=True)
    
    last_balance_update = Column(DateTime(timezone=True), nullable=False)


class Transaction(BaseModel):
    """
    Transaction entity
    
    Time-series optimized (partition by transaction_date)
    """
    
    __tablename__ = "transactions"
    __table_args__ = (
        Index('idx_transactions_account_date', 'tenant_id', 'account_id', 'transaction_date'),
        Index('idx_transactions_type', 'tenant_id', 'transaction_type', 'transaction_date'),
        Index('idx_transactions_status', 'status', 'transaction_date'),
        
        # Partition by date (time-series optimization)
        {'postgresql_partition_by': 'RANGE (transaction_date)'},
        
        {'schema': 'accounts', 'comment': 'Transaction history (time-series)'}
    )
    
    # Transaction ID
    transaction_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Business transaction ID (TXN-xxx)"
    )
    
    # Account relationship
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey('accounts.accounts.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    account = relationship("Account", back_populates="transactions")
    
    # Transaction details
    transaction_type = Column(
        Enum(TransactionTypeEnum, name='transaction_type_enum'),
        nullable=False
    )
    
    status = Column(
        Enum(TransactionStatusEnum, name='transaction_status_enum'),
        nullable=False,
        default=TransactionStatusEnum.PENDING
    )
    
    # Amounts
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='AUD')
    
    balance_before = Column(Numeric(18, 2), nullable=False)
    balance_after = Column(Numeric(18, 2), nullable=False)
    
    # Description
    description = Column(String(500), nullable=True)
    reference = Column(String(100), nullable=True)
    
    # Related transactions (for transfers)
    related_account_id = Column(String(50), nullable=True)
    related_transaction_id = Column(String(50), nullable=True)
    
    # Dates
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    value_date = Column(DateTime(timezone=True), nullable=False)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    
    # ML features (for categorization)
    ml_category = Column(String(50), nullable=True)
    ml_confidence = Column(Numeric(5, 4), nullable=True)
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, type={self.transaction_type}, amount={self.amount})>"

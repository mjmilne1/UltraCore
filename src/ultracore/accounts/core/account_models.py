"""
UltraCore Account Models

Domain models for account management:
- Account (various types)
- Balance tracking
- Transaction processing
- Interest calculations
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import uuid4


# ============================================================================
# Enums
# ============================================================================

class AccountType(Enum):
    """Account types"""
    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    TERM_DEPOSIT = "TERM_DEPOSIT"
    LOAN = "LOAN"
    CREDIT_CARD = "CREDIT_CARD"


class AccountStatus(Enum):
    """Account status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"
    FROZEN = "FROZEN"
    DORMANT = "DORMANT"


class TransactionType(Enum):
    """Transaction types"""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    INTEREST_CREDIT = "INTEREST_CREDIT"
    FEE_DEBIT = "FEE_DEBIT"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    FAILED = "FAILED"


# ============================================================================
# Account Models
# ============================================================================

@dataclass
class InterestRate:
    """Interest rate configuration"""
    annual_rate: Decimal
    compounding_frequency: str = "MONTHLY"
    calculation_method: str = "DAILY_BALANCE"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None


@dataclass
class AccountBalance:
    """Account balance information"""
    ledger_balance: Decimal
    available_balance: Decimal
    pending_credits: Decimal = Decimal('0')
    pending_debits: Decimal = Decimal('0')
    held_amount: Decimal = Decimal('0')
    last_update: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Account:
    """Account aggregate"""
    # Required fields (no defaults)
    customer_id: str
    account_type: AccountType
    currency: str
    opened_by: str
    
    # Optional fields (with defaults)
    account_id: str = field(default_factory=lambda: f"ACC-{uuid4().hex[:8].upper()}")
    account_number: str = field(default_factory=lambda: f"{datetime.now().strftime('%Y%m%d')}{uuid4().hex[:6].upper()}")
    status: AccountStatus = AccountStatus.ACTIVE
    balance: AccountBalance = field(default_factory=lambda: AccountBalance(
        ledger_balance=Decimal('0'),
        available_balance=Decimal('0')
    ))
    interest_bearing: bool = False
    current_interest_rate: Optional[InterestRate] = None
    overdraft_limit: Decimal = Decimal('0')
    minimum_balance: Decimal = Decimal('0')
    maturity_date: Optional[date] = None
    opened_date: date = field(default_factory=date.today)
    closed_date: Optional[date] = None
    last_transaction_date: Optional[datetime] = None
    
    # Transaction tracking
    transactions: List['Transaction'] = field(default_factory=list)
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Transaction:
    """Transaction record - FIXED for Python 3.13"""
    # Required fields WITHOUT defaults (MUST come first)
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: datetime
    value_date: datetime
    
    # Optional fields WITH defaults (MUST come after)
    transaction_id: str = field(default_factory=lambda: f"TXN-{uuid4().hex[:8].upper()}")
    currency: str = 'AUD'
    status: TransactionStatus = TransactionStatus.PENDING
    balance_before: Decimal = Decimal('0')
    balance_after: Decimal = Decimal('0')
    description: Optional[str] = None
    reference: Optional[str] = None
    related_account_id: Optional[str] = None
    related_transaction_id: Optional[str] = None
    posted_date: Optional[datetime] = None
    reversed_by: Optional[str] = None
    reversal_reason: Optional[str] = None
    
    # ML/AI category
    ml_category: Optional[str] = None
    ml_confidence: Optional[float] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)




@dataclass
class AccountHold:
    """Account hold/freeze"""
    # Required fields
    account_id: str
    amount: Decimal
    reason: str
    
    # Optional fields with defaults
    hold_id: str = field(default_factory=lambda: f"HOLD-{uuid4().hex[:8].upper()}")
    hold_type: str = "TEMPORARY"
    placed_by: str = "SYSTEM"
    placed_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None
    metadata: dict = field(default_factory=dict)

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_available_balance(
    ledger_balance: Decimal,
    pending_debits: Decimal,
    held_amount: Decimal,
    overdraft_limit: Decimal = Decimal('0')
) -> Decimal:
    """Calculate available balance"""
    return ledger_balance - pending_debits - held_amount + overdraft_limit


def can_withdraw(
    account: Account,
    amount: Decimal
) -> bool:
    """Check if withdrawal is allowed"""
    available = calculate_available_balance(
        account.balance.ledger_balance,
        account.balance.pending_debits,
        account.balance.held_amount,
        account.overdraft_limit
    )
    return available >= amount


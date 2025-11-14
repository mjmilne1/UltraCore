"""
UltraCore Loan Management - Loan Account

Loan account management and lifecycle:
- Loan account creation
- Balance tracking
- Transaction history
- Account status management
- Collateral tracking
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid


# ============================================================================
# Loan Account Enums
# ============================================================================

class LoanStatus(str, Enum):
    """Loan account status"""
    PENDING = "PENDING"  # Approved but not funded
    ACTIVE = "ACTIVE"  # Funded and current
    DELINQUENT = "DELINQUENT"  # Payment overdue
    DEFAULT = "DEFAULT"  # In default
    WRITTEN_OFF = "WRITTEN_OFF"  # Written off as bad debt
    PAID_OFF = "PAID_OFF"  # Fully paid
    CLOSED = "CLOSED"  # Account closed
    SUSPENDED = "SUSPENDED"  # Temporarily suspended


class PaymentFrequency(str, Enum):
    """Payment frequency"""
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"


class InterestRateType(str, Enum):
    """Interest rate type"""
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"
    SPLIT = "SPLIT"  # Combination of fixed and variable


class RepaymentType(str, Enum):
    """Repayment calculation method"""
    PRINCIPAL_AND_INTEREST = "PRINCIPAL_AND_INTEREST"
    INTEREST_ONLY = "INTEREST_ONLY"
    BALLOON = "BALLOON"  # Final balloon payment
    REDUCING_BALANCE = "REDUCING_BALANCE"


class LoanTransactionType(str, Enum):
    """Types of loan transactions"""
    DISBURSEMENT = "DISBURSEMENT"
    PRINCIPAL_PAYMENT = "PRINCIPAL_PAYMENT"
    INTEREST_PAYMENT = "INTEREST_PAYMENT"
    FEE_CHARGE = "FEE_CHARGE"
    FEE_PAYMENT = "FEE_PAYMENT"
    PENALTY_CHARGE = "PENALTY_CHARGE"
    PENALTY_PAYMENT = "PENALTY_PAYMENT"
    REVERSAL = "REVERSAL"
    ADJUSTMENT = "ADJUSTMENT"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class LoanTerms:
    """Loan terms and conditions"""
    
    # Principal
    principal_amount: Decimal
    
    # Interest
    interest_rate: Decimal  # Annual percentage rate
    interest_rate_type: InterestRateType
    
    # Term
    term_months: int
    
    # Repayment
    repayment_type: RepaymentType
    repayment_frequency: PaymentFrequency
    first_payment_date: date
    
    # Balloon payment (if applicable)
    balloon_amount: Optional[Decimal] = None
    
    # Interest only period (if applicable)
    interest_only_months: int = 0
    
    # Fees
    establishment_fee: Decimal = Decimal('0.00')
    monthly_fee: Decimal = Decimal('0.00')
    early_repayment_fee: Decimal = Decimal('0.00')
    
    # Penalty rates
    penalty_interest_rate: Decimal = Decimal('0.00')  # Additional rate for arrears
    
    # Day count convention
    day_count_convention: str = "ACTUAL_365"  # ACTUAL_365, ACTUAL_360, 30_360


@dataclass
class LoanBalance:
    """Current loan balance snapshot"""
    
    # Principal
    principal_outstanding: Decimal
    principal_in_arrears: Decimal = Decimal('0.00')
    
    # Interest
    interest_accrued: Decimal = Decimal('0.00')
    interest_in_arrears: Decimal = Decimal('0.00')
    
    # Fees
    fees_outstanding: Decimal = Decimal('0.00')
    fees_in_arrears: Decimal = Decimal('0.00')
    
    # Penalties
    penalties_outstanding: Decimal = Decimal('0.00')
    
    # Total
    total_outstanding: Decimal = Decimal('0.00')
    total_arrears: Decimal = Decimal('0.00')
    
    # As of
    as_of_date: date = field(default_factory=date.today)
    
    def update_total(self):
        """Recalculate total balances"""
        self.total_outstanding = (
            self.principal_outstanding +
            self.interest_accrued +
            self.fees_outstanding +
            self.penalties_outstanding
        )
        
        self.total_arrears = (
            self.principal_in_arrears +
            self.interest_in_arrears +
            self.fees_in_arrears
        )


@dataclass
class LoanTransaction:
    """Individual loan transaction"""
    transaction_id: str
    loan_account_id: str
    
    # Transaction details
    transaction_type: LoanTransactionType
    transaction_date: date
    value_date: date  # Date transaction takes effect
    
    # Amount
    amount: Decimal
    
    # Balance impact
    principal_portion: Decimal = Decimal('0.00')
    interest_portion: Decimal = Decimal('0.00')
    fee_portion: Decimal = Decimal('0.00')
    penalty_portion: Decimal = Decimal('0.00')
    
    # Balance after transaction
    balance_after: Optional[Decimal] = None
    
    # Reference
    reference: Optional[str] = None
    description: str = ""
    
    # External reference (e.g., payment transaction ID)
    external_reference: Optional[str] = None
    
    # Reversal
    reversed: bool = False
    reversal_transaction_id: Optional[str] = None
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoanAccount:
    """Core loan account"""
    account_id: str
    
    # Application reference
    application_id: str
    
    # Customer
    customer_id: str
    
    # Product
    product_type: str
    product_code: Optional[str] = None
    
    # Terms
    terms: LoanTerms = field(default_factory=lambda: LoanTerms(
        principal_amount=Decimal('0.00'),
        interest_rate=Decimal('0.00'),
        interest_rate_type=InterestRateType.VARIABLE,
        term_months=0,
        repayment_type=RepaymentType.PRINCIPAL_AND_INTEREST,
        repayment_frequency=PaymentFrequency.MONTHLY,
        first_payment_date=date.today()
    ))
    
    # Balance
    current_balance: LoanBalance = field(default_factory=LoanBalance)
    
    # Status
    status: LoanStatus = LoanStatus.PENDING
    status_reason: Optional[str] = None
    
    # Dates
    approval_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    maturity_date: Optional[date] = None
    closed_date: Optional[date] = None
    
    # Delinquency
    days_past_due: int = 0
    last_payment_date: Optional[date] = None
    next_payment_date: Optional[date] = None
    
    # Transactions
    transactions: List[LoanTransaction] = field(default_factory=list)
    
    # GL account mapping
    gl_loan_account: Optional[str] = None
    gl_interest_income_account: Optional[str] = None
    gl_fee_income_account: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_transaction(self, transaction: LoanTransaction):
        """Add transaction to loan account"""
        self.transactions.append(transaction)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_balance(self):
        """Recalculate current balance from transactions"""
        # This would iterate through transactions
        # For now, just update total
        self.current_balance.update_total()
        self.updated_at = datetime.now(timezone.utc)


# ============================================================================
# Loan Account Manager
# ============================================================================

class LoanAccountManager:
    """
    Manages loan accounts
    """
    
    def __init__(self):
        self.accounts: Dict[str, LoanAccount] = {}
    
    async def create_loan_account(
        self,
        application_id: str,
        customer_id: str,
        product_type: str,
        terms: LoanTerms,
        approval_date: date
    ) -> LoanAccount:
        """Create a new loan account"""
        
        account_id = f"LOAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Calculate maturity date
        maturity_date = terms.first_payment_date + timedelta(
            days=terms.term_months * 30
        )
        
        # Initialize balance
        initial_balance = LoanBalance(
            principal_outstanding=terms.principal_amount,
            as_of_date=date.today()
        )
        initial_balance.update_total()
        
        account = LoanAccount(
            account_id=account_id,
            application_id=application_id,
            customer_id=customer_id,
            product_type=product_type,
            terms=terms,
            current_balance=initial_balance,
            status=LoanStatus.PENDING,
            approval_date=approval_date,
            maturity_date=maturity_date,
            next_payment_date=terms.first_payment_date
        )
        
        self.accounts[account_id] = account
        
        return account
    
    async def get_account(self, account_id: str) -> Optional[LoanAccount]:
        """Get loan account by ID"""
        return self.accounts.get(account_id)
    
    async def disburse_loan(
        self,
        account_id: str,
        disbursement_date: date,
        disbursed_by: str
    ) -> LoanTransaction:
        """Disburse loan funds"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if account.status != LoanStatus.PENDING:
            raise ValueError(f"Account not in PENDING status: {account.status}")
        
        # Create disbursement transaction
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        transaction = LoanTransaction(
            transaction_id=transaction_id,
            loan_account_id=account_id,
            transaction_type=LoanTransactionType.DISBURSEMENT,
            transaction_date=disbursement_date,
            value_date=disbursement_date,
            amount=account.terms.principal_amount,
            principal_portion=account.terms.principal_amount,
            description="Loan disbursement",
            created_by=disbursed_by
        )
        
        account.add_transaction(transaction)
        
        # Update account status
        account.status = LoanStatus.ACTIVE
        account.disbursement_date = disbursement_date
        
        return transaction
    
    async def update_account_status(
        self,
        account_id: str,
        new_status: LoanStatus,
        reason: Optional[str] = None
    ) -> LoanAccount:
        """Update account status"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        account.status = new_status
        account.status_reason = reason
        account.updated_at = datetime.now(timezone.utc)
        
        if new_status == LoanStatus.CLOSED:
            account.closed_date = date.today()
        
        return account
    
    async def get_accounts_by_customer(
        self,
        customer_id: str
    ) -> List[LoanAccount]:
        """Get all loan accounts for a customer"""
        return [
            acc for acc in self.accounts.values()
            if acc.customer_id == customer_id
        ]
    
    async def get_active_accounts(self) -> List[LoanAccount]:
        """Get all active loan accounts"""
        return [
            acc for acc in self.accounts.values()
            if acc.status == LoanStatus.ACTIVE
        ]


# ============================================================================
# Global Loan Account Manager
# ============================================================================

_loan_account_manager: Optional[LoanAccountManager] = None

def get_loan_account_manager() -> LoanAccountManager:
    """Get the singleton loan account manager"""
    global _loan_account_manager
    if _loan_account_manager is None:
        _loan_account_manager = LoanAccountManager()
    return _loan_account_manager

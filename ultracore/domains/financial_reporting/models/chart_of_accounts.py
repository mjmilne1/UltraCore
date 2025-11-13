"""
Chart of Accounts - Australian Accounting Standards
Optimized for AASB compliance and APRA prudential reporting
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal


class AccountType(str, Enum):
    """Account type classification"""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountSubType(str, Enum):
    """Account sub-type classification"""
    # Assets
    CURRENT_ASSET = "current_asset"
    NON_CURRENT_ASSET = "non_current_asset"
    CASH = "cash"
    LOANS = "loans"
    RECEIVABLES = "receivables"
    PPE = "ppe"
    INTANGIBLES = "intangibles"
    
    # Liabilities
    CURRENT_LIABILITY = "current_liability"
    NON_CURRENT_LIABILITY = "non_current_liability"
    DEPOSITS = "deposits"
    BORROWINGS = "borrowings"
    PAYABLES = "payables"
    PROVISIONS = "provisions"
    
    # Equity
    SHARE_CAPITAL = "share_capital"
    RETAINED_EARNINGS = "retained_earnings"
    RESERVES = "reserves"
    
    # Revenue
    INTEREST_INCOME = "interest_income"
    FEE_INCOME = "fee_income"
    OTHER_INCOME = "other_income"
    
    # Expenses
    INTEREST_EXPENSE = "interest_expense"
    OPERATING_EXPENSE = "operating_expense"
    LOAN_LOSS_PROVISION = "loan_loss_provision"
    DEPRECIATION = "depreciation"


class Account(BaseModel):
    """
    General Ledger Account
    
    Represents a single account in the chart of accounts
    """
    
    # Identifiers
    account_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Account details
    account_code: str  # e.g., "1010", "4010"
    account_name: str  # e.g., "Cash at Bank - Operating"
    account_type: AccountType
    account_subtype: AccountSubType
    
    # Hierarchy
    parent_account_id: Optional[UUID] = None
    level: int = Field(default=1)  # 1 = top level, 2 = sub-account, etc.
    
    # Balance
    current_balance: Decimal = Field(default=Decimal("0.00"))
    debit_balance: Decimal = Field(default=Decimal("0.00"))
    credit_balance: Decimal = Field(default=Decimal("0.00"))
    
    # Properties
    is_active: bool = Field(default=True)
    is_contra: bool = Field(default=False)  # Contra accounts (e.g., Accumulated Depreciation)
    is_system: bool = Field(default=False)  # System-managed accounts
    
    # APRA mapping
    apra_category: Optional[str] = None  # For prudential reporting
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_normal_balance_side(self) -> str:
        """Get the normal balance side for this account type"""
        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            return "debit" if not self.is_contra else "credit"
        else:  # LIABILITY, EQUITY, REVENUE
            return "credit" if not self.is_contra else "debit"
    
    def update_balance(self, debit_amount: Decimal, credit_amount: Decimal):
        """Update account balance"""
        self.debit_balance += debit_amount
        self.credit_balance += credit_amount
        
        # Calculate current balance based on account type
        if self.get_normal_balance_side() == "debit":
            self.current_balance = self.debit_balance - self.credit_balance
        else:
            self.current_balance = self.credit_balance - self.debit_balance
        
        self.updated_at = datetime.utcnow()


class ChartOfAccounts(BaseModel):
    """
    Chart of Accounts
    
    Complete chart of accounts for Australian accounting
    """
    
    tenant_id: UUID
    accounts: List[Account] = Field(default_factory=list)
    
    def add_account(self, account: Account):
        """Add account to chart"""
        self.accounts.append(account)
    
    def get_account(self, account_code: str) -> Optional[Account]:
        """Get account by code"""
        return next(
            (acc for acc in self.accounts if acc.account_code == account_code),
            None
        )
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[Account]:
        """Get all accounts of a specific type"""
        return [acc for acc in self.accounts if acc.account_type == account_type]
    
    def get_total_balance(self, account_type: AccountType) -> Decimal:
        """Get total balance for an account type"""
        accounts = self.get_accounts_by_type(account_type)
        return sum(acc.current_balance for acc in accounts)


# ============================================================================
# Australian Chart of Accounts - Default Structure
# ============================================================================

def create_australian_chart_of_accounts(tenant_id: UUID, created_by: str) -> ChartOfAccounts:
    """
    Create default Australian Chart of Accounts
    
    Optimized for:
    - AASB accounting standards
    - APRA prudential reporting
    - Core banking operations
    """
    
    coa = ChartOfAccounts(tenant_id=tenant_id)
    
    # ========================================================================
    # ASSETS (1000-1999)
    # ========================================================================
    
    # Current Assets (1000-1199)
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1000",
        account_name="Cash and Cash Equivalents",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.CASH,
        apra_category="Liquid Assets",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1010",
        account_name="Cash at Bank - Operating Account",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.CASH,
        parent_account_id=coa.get_account("1000").account_id,
        level=2,
        apra_category="Liquid Assets",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1020",
        account_name="Cash at Bank - Trust Account",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.CASH,
        parent_account_id=coa.get_account("1000").account_id,
        level=2,
        apra_category="Liquid Assets",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1100",
        account_name="Loans and Advances - Current Portion",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.LOANS,
        apra_category="Credit Risk Exposures",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1110",
        account_name="Personal Loans",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.LOANS,
        parent_account_id=coa.get_account("1100").account_id,
        level=2,
        apra_category="Credit Risk Exposures",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1120",
        account_name="Home Loans",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.LOANS,
        parent_account_id=coa.get_account("1100").account_id,
        level=2,
        apra_category="Credit Risk Exposures",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1150",
        account_name="Provision for Loan Losses - Current",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.LOANS,
        is_contra=True,
        apra_category="Provisions",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1160",
        account_name="Interest Receivable",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.RECEIVABLES,
        created_by=created_by,
    ))
    
    # Non-Current Assets (1200-1999)
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1200",
        account_name="Loans and Advances - Non-Current",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.NON_CURRENT_ASSET,
        apra_category="Credit Risk Exposures",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1300",
        account_name="Property, Plant & Equipment",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.PPE,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1340",
        account_name="Accumulated Depreciation",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.PPE,
        is_contra=True,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="1400",
        account_name="Intangible Assets",
        account_type=AccountType.ASSET,
        account_subtype=AccountSubType.INTANGIBLES,
        created_by=created_by,
    ))
    
    # ========================================================================
    # LIABILITIES (2000-2999)
    # ========================================================================
    
    # Current Liabilities (2000-2199)
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2000",
        account_name="Customer Deposits - Savings Accounts",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.DEPOSITS,
        apra_category="Stable Funding",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2010",
        account_name="Customer Deposits - Transaction Accounts",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.DEPOSITS,
        apra_category="Stable Funding",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2020",
        account_name="Customer Deposits - Term Deposits (< 12 months)",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.DEPOSITS,
        apra_category="Stable Funding",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2030",
        account_name="Interest Payable",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.PAYABLES,
        created_by=created_by,
    ))
    
    # Non-Current Liabilities (2200-2999)
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2200",
        account_name="Customer Deposits - Term Deposits (> 12 months)",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.DEPOSITS,
        apra_category="Stable Funding",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2300",
        account_name="Long-term Borrowings",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.BORROWINGS,
        apra_category="Wholesale Funding",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="2400",
        account_name="Provisions",
        account_type=AccountType.LIABILITY,
        account_subtype=AccountSubType.PROVISIONS,
        apra_category="Provisions",
        created_by=created_by,
    ))
    
    # ========================================================================
    # EQUITY (3000-3999)
    # ========================================================================
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="3000",
        account_name="Share Capital",
        account_type=AccountType.EQUITY,
        account_subtype=AccountSubType.SHARE_CAPITAL,
        apra_category="CET1 Capital",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="3100",
        account_name="Retained Earnings",
        account_type=AccountType.EQUITY,
        account_subtype=AccountSubType.RETAINED_EARNINGS,
        apra_category="CET1 Capital",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="3200",
        account_name="Reserves",
        account_type=AccountType.EQUITY,
        account_subtype=AccountSubType.RESERVES,
        apra_category="CET1 Capital",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="3300",
        account_name="Current Year Profit/Loss",
        account_type=AccountType.EQUITY,
        account_subtype=AccountSubType.RETAINED_EARNINGS,
        created_by=created_by,
    ))
    
    # ========================================================================
    # REVENUE (4000-4999)
    # ========================================================================
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4000",
        account_name="Interest Income",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.INTEREST_INCOME,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4010",
        account_name="Interest on Loans",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.INTEREST_INCOME,
        parent_account_id=coa.get_account("4000").account_id,
        level=2,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4100",
        account_name="Fee Income",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.FEE_INCOME,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4110",
        account_name="Loan Origination Fees",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.FEE_INCOME,
        parent_account_id=coa.get_account("4100").account_id,
        level=2,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4120",
        account_name="Account Maintenance Fees",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.FEE_INCOME,
        parent_account_id=coa.get_account("4100").account_id,
        level=2,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="4140",
        account_name="Late Payment Fees",
        account_type=AccountType.REVENUE,
        account_subtype=AccountSubType.FEE_INCOME,
        parent_account_id=coa.get_account("4100").account_id,
        level=2,
        created_by=created_by,
    ))
    
    # ========================================================================
    # EXPENSES (5000-5999)
    # ========================================================================
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5000",
        account_name="Interest Expense",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.INTEREST_EXPENSE,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5010",
        account_name="Interest on Deposits",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.INTEREST_EXPENSE,
        parent_account_id=coa.get_account("5000").account_id,
        level=2,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5200",
        account_name="Operating Expenses",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.OPERATING_EXPENSE,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5210",
        account_name="Employee Salaries and Wages",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.OPERATING_EXPENSE,
        parent_account_id=coa.get_account("5200").account_id,
        level=2,
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5300",
        account_name="Loan Loss Provisions",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.LOAN_LOSS_PROVISION,
        apra_category="Provisions",
        created_by=created_by,
    ))
    
    coa.add_account(Account(
        tenant_id=tenant_id,
        account_code="5400",
        account_name="Depreciation and Amortisation",
        account_type=AccountType.EXPENSE,
        account_subtype=AccountSubType.DEPRECIATION,
        created_by=created_by,
    ))
    
    return coa

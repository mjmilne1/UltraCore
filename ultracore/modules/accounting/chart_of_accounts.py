from datetime import timezone
"""
Chart of Accounts
Complete account structure for wealth management platform
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from enum import Enum
from datetime import datetime

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class AccountSubType(str, Enum):
    # Assets
    CURRENT_ASSET = "current_asset"
    CASH = "cash"
    INVESTMENTS = "investments"
    RECEIVABLES = "receivables"
    PREPAID = "prepaid"
    FIXED_ASSET = "fixed_asset"
    
    # Liabilities
    CURRENT_LIABILITY = "current_liability"
    PAYABLES = "payables"
    ACCRUED = "accrued"
    LONG_TERM_LIABILITY = "long_term_liability"
    
    # Equity
    CAPITAL = "capital"
    RETAINED_EARNINGS = "retained_earnings"
    UNREALIZED_GL = "unrealized_gl"
    REALIZED_GL = "realized_gl"
    
    # Revenue
    MANAGEMENT_FEES = "management_fees"
    TRANSACTION_FEES = "transaction_fees"
    PERFORMANCE_FEES = "performance_fees"
    OTHER_INCOME = "other_income"
    
    # Expenses
    OPERATING_EXPENSE = "operating_expense"
    TECHNOLOGY_EXPENSE = "technology_expense"
    COMPLIANCE_EXPENSE = "compliance_expense"
    MARKETING_EXPENSE = "marketing_expense"

class NormalBalance(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class Account:
    """Individual account in chart of accounts"""
    
    def __init__(
        self,
        account_number: str,
        name: str,
        account_type: AccountType,
        account_subtype: AccountSubType,
        normal_balance: NormalBalance,
        description: str = "",
        parent_account: Optional[str] = None
    ):
        self.account_number = account_number
        self.name = name
        self.account_type = account_type
        self.account_subtype = account_subtype
        self.normal_balance = normal_balance
        self.description = description
        self.parent_account = parent_account
        self.balance = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.is_active = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_number": self.account_number,
            "name": self.name,
            "account_type": self.account_type,
            "account_subtype": self.account_subtype,
            "normal_balance": self.normal_balance,
            "description": self.description,
            "parent_account": self.parent_account,
            "balance": self.balance,
            "created_at": self.created_at,
            "is_active": self.is_active
        }

class ChartOfAccounts:
    """
    Complete Chart of Accounts for wealth management
    """
    
    def __init__(self):
        self.accounts = {}
        self._initialize_standard_accounts()
    
    def _initialize_standard_accounts(self):
        """Initialize standard chart of accounts"""
        
        # ====================================================================
        # ASSETS (1000-1999)
        # ====================================================================
        
        # Current Assets (1000-1499)
        self._add_account(Account(
            "1000", "Cash and Cash Equivalents", 
            AccountType.ASSET, AccountSubType.CASH, NormalBalance.DEBIT,
            "Primary cash account"
        ))
        
        self._add_account(Account(
            "1010", "Client Cash Accounts",
            AccountType.ASSET, AccountSubType.CASH, NormalBalance.DEBIT,
            "Cash held for clients", "1000"
        ))
        
        self._add_account(Account(
            "1020", "Operating Cash",
            AccountType.ASSET, AccountSubType.CASH, NormalBalance.DEBIT,
            "Company operating cash", "1000"
        ))
        
        self._add_account(Account(
            "1100", "Settlements Receivable",
            AccountType.ASSET, AccountSubType.RECEIVABLES, NormalBalance.DEBIT,
            "Trades awaiting settlement"
        ))
        
        self._add_account(Account(
            "1110", "Fees Receivable",
            AccountType.ASSET, AccountSubType.RECEIVABLES, NormalBalance.DEBIT,
            "Management fees to be collected"
        ))
        
        # Investments (1500-1799)
        self._add_account(Account(
            "1500", "Investments - Equity Securities",
            AccountType.ASSET, AccountSubType.INVESTMENTS, NormalBalance.DEBIT,
            "Client equity holdings"
        ))
        
        self._add_account(Account(
            "1510", "Investments - Fixed Income",
            AccountType.ASSET, AccountSubType.INVESTMENTS, NormalBalance.DEBIT,
            "Client bond holdings"
        ))
        
        self._add_account(Account(
            "1520", "Investments - ETFs",
            AccountType.ASSET, AccountSubType.INVESTMENTS, NormalBalance.DEBIT,
            "Client ETF holdings"
        ))
        
        # Fixed Assets (1800-1999)
        self._add_account(Account(
            "1800", "Technology Infrastructure",
            AccountType.ASSET, AccountSubType.FIXED_ASSET, NormalBalance.DEBIT,
            "IT systems and infrastructure"
        ))
        
        # ====================================================================
        # LIABILITIES (2000-2999)
        # ====================================================================
        
        # Current Liabilities (2000-2499)
        self._add_account(Account(
            "2000", "Settlements Payable",
            AccountType.LIABILITY, AccountSubType.PAYABLES, NormalBalance.CREDIT,
            "Trade settlements due"
        ))
        
        self._add_account(Account(
            "2010", "Client Funds Held",
            AccountType.LIABILITY, AccountSubType.PAYABLES, NormalBalance.CREDIT,
            "Client cash held in trust"
        ))
        
        self._add_account(Account(
            "2100", "Fees Payable",
            AccountType.LIABILITY, AccountSubType.PAYABLES, NormalBalance.CREDIT,
            "Fees owed to third parties"
        ))
        
        self._add_account(Account(
            "2110", "Accrued Expenses",
            AccountType.LIABILITY, AccountSubType.ACCRUED, NormalBalance.CREDIT,
            "Expenses incurred but not paid"
        ))
        
        # ====================================================================
        # EQUITY (3000-3999)
        # ====================================================================
        
        self._add_account(Account(
            "3000", "Client Equity",
            AccountType.EQUITY, AccountSubType.CAPITAL, NormalBalance.CREDIT,
            "Total client equity"
        ))
        
        self._add_account(Account(
            "3100", "Retained Earnings",
            AccountType.EQUITY, AccountSubType.RETAINED_EARNINGS, NormalBalance.CREDIT,
            "Accumulated earnings"
        ))
        
        self._add_account(Account(
            "3200", "Unrealized Gains/Losses",
            AccountType.EQUITY, AccountSubType.UNREALIZED_GL, NormalBalance.CREDIT,
            "Mark-to-market adjustments"
        ))
        
        self._add_account(Account(
            "3210", "Realized Gains/Losses",
            AccountType.EQUITY, AccountSubType.REALIZED_GL, NormalBalance.CREDIT,
            "Gains/losses from closed positions"
        ))
        
        # ====================================================================
        # REVENUE (4000-4999)
        # ====================================================================
        
        self._add_account(Account(
            "4000", "Management Fees",
            AccountType.REVENUE, AccountSubType.MANAGEMENT_FEES, NormalBalance.CREDIT,
            "Asset management fees"
        ))
        
        self._add_account(Account(
            "4100", "Transaction Fees",
            AccountType.REVENUE, AccountSubType.TRANSACTION_FEES, NormalBalance.CREDIT,
            "Trading commission revenue"
        ))
        
        self._add_account(Account(
            "4200", "Performance Fees",
            AccountType.REVENUE, AccountSubType.PERFORMANCE_FEES, NormalBalance.CREDIT,
            "Performance-based fees"
        ))
        
        self._add_account(Account(
            "4300", "Interest Income",
            AccountType.REVENUE, AccountSubType.OTHER_INCOME, NormalBalance.CREDIT,
            "Interest earned on cash"
        ))
        
        # ====================================================================
        # EXPENSES (5000-5999)
        # ====================================================================
        
        self._add_account(Account(
            "5000", "Technology Expenses",
            AccountType.EXPENSE, AccountSubType.TECHNOLOGY_EXPENSE, NormalBalance.DEBIT,
            "IT and software costs"
        ))
        
        self._add_account(Account(
            "5100", "Compliance Expenses",
            AccountType.EXPENSE, AccountSubType.COMPLIANCE_EXPENSE, NormalBalance.DEBIT,
            "Regulatory and compliance costs"
        ))
        
        self._add_account(Account(
            "5200", "Marketing Expenses",
            AccountType.EXPENSE, AccountSubType.MARKETING_EXPENSE, NormalBalance.DEBIT,
            "Marketing and advertising"
        ))
        
        self._add_account(Account(
            "5300", "Operating Expenses",
            AccountType.EXPENSE, AccountSubType.OPERATING_EXPENSE, NormalBalance.DEBIT,
            "General operating costs"
        ))
        
        self._add_account(Account(
            "5310", "Professional Fees",
            AccountType.EXPENSE, AccountSubType.OPERATING_EXPENSE, NormalBalance.DEBIT,
            "Legal and consulting fees"
        ))
    
    def _add_account(self, account: Account):
        """Add account to chart"""
        self.accounts[account.account_number] = account
    
    def get_account(self, account_number: str) -> Optional[Account]:
        """Get account by number"""
        return self.accounts.get(account_number)
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[Account]:
        """Get all accounts of specific type"""
        return [
            acc for acc in self.accounts.values()
            if acc.account_type == account_type
        ]
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        return list(self.accounts.values())
    
    def update_account_balance(self, account_number: str, amount: float):
        """Update account balance"""
        account = self.get_account(account_number)
        if account:
            account.balance += amount
    
    def get_balance_sheet_accounts(self) -> Dict[str, List[Account]]:
        """Get accounts for balance sheet"""
        return {
            "assets": self.get_accounts_by_type(AccountType.ASSET),
            "liabilities": self.get_accounts_by_type(AccountType.LIABILITY),
            "equity": self.get_accounts_by_type(AccountType.EQUITY)
        }
    
    def get_income_statement_accounts(self) -> Dict[str, List[Account]]:
        """Get accounts for income statement"""
        return {
            "revenue": self.get_accounts_by_type(AccountType.REVENUE),
            "expenses": self.get_accounts_by_type(AccountType.EXPENSE)
        }

# Global instance
chart_of_accounts = ChartOfAccounts()

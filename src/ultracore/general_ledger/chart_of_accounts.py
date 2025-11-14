"""
Chart of Accounts - Australian Banking
Compliant with AASB (Australian Accounting Standards Board)

Account Structure: XXXX-YY-ZZZ
- XXXX: Account class (1000-5000)
- YY: Subclass
- ZZZ: Specific account

Classes:
1XXX - Assets
2XXX - Liabilities  
3XXX - Equity
4XXX - Revenue
5XXX - Expenses
"""
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class AccountType(str, Enum):
    ASSET = 'ASSET'
    LIABILITY = 'LIABILITY'
    EQUITY = 'EQUITY'
    REVENUE = 'REVENUE'
    EXPENSE = 'EXPENSE'


class AccountClass(str, Enum):
    # Assets (1XXX)
    CASH = '1000'
    NOSTRO_ACCOUNTS = '1100'
    CUSTOMER_LOANS = '1200'
    INTEREST_RECEIVABLE = '1300'
    PROPERTY_EQUIPMENT = '1400'
    INTANGIBLE_ASSETS = '1500'
    
    # Liabilities (2XXX)
    CUSTOMER_DEPOSITS = '2000'
    VOSTRO_ACCOUNTS = '2100'
    ACCOUNTS_PAYABLE = '2200'
    INTEREST_PAYABLE = '2300'
    BORROWINGS = '2400'
    
    # Equity (3XXX)
    SHARE_CAPITAL = '3000'
    RETAINED_EARNINGS = '3100'
    RESERVES = '3200'
    
    # Revenue (4XXX)
    INTEREST_INCOME = '4000'
    FEE_INCOME = '4100'
    MERCHANT_FEES = '4200'
    CARD_FEES = '4300'
    INVESTMENT_INCOME = '4400'
    
    # Expenses (5XXX)
    INTEREST_EXPENSE = '5000'
    OPERATING_EXPENSES = '5100'
    STAFF_COSTS = '5200'
    IT_EXPENSES = '5300'
    REGULATORY_COSTS = '5400'
    LOAN_LOSS_PROVISION = '5500'


class NormalBalance(str, Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'


class Account:
    """
    General Ledger Account
    
    Compliant with AASB accounting standards
    """
    
    def __init__(
        self,
        account_code: str,
        account_name: str,
        account_type: AccountType,
        normal_balance: NormalBalance,
        parent_account: Optional[str] = None
    ):
        self.account_code = account_code
        self.account_name = account_name
        self.account_type = account_type
        self.normal_balance = normal_balance
        self.parent_account = parent_account
        self.balance: float = 0.0
        self.is_active: bool = True
        self.created_at = datetime.now(timezone.utc)


class ChartOfAccounts:
    """
    Chart of Accounts - Australian Banking
    
    Complete CoA for a digital bank
    """
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self._initialize_standard_coa()
    
    def _initialize_standard_coa(self):
        """Initialize standard Australian banking Chart of Accounts"""
        
        # ASSETS (1XXX)
        self._add_account('1000-00-000', 'Cash and Cash Equivalents', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1000-01-001', 'Cash on Hand', AccountType.ASSET, NormalBalance.DEBIT, '1000-00-000')
        self._add_account('1000-01-002', 'Cash at RBA', AccountType.ASSET, NormalBalance.DEBIT, '1000-00-000')
        self._add_account('1000-01-003', 'Operating Account', AccountType.ASSET, NormalBalance.DEBIT, '1000-00-000')
        
        self._add_account('1100-00-000', 'Nostro Accounts', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1100-01-001', 'Nostro - Settlement Account', AccountType.ASSET, NormalBalance.DEBIT, '1100-00-000')
        self._add_account('1100-01-002', 'Nostro - NPP Account', AccountType.ASSET, NormalBalance.DEBIT, '1100-00-000')
        self._add_account('1100-01-003', 'Nostro - BPAY Account', AccountType.ASSET, NormalBalance.DEBIT, '1100-00-000')
        
        self._add_account('1200-00-000', 'Customer Loans', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1200-01-001', 'Personal Loans', AccountType.ASSET, NormalBalance.DEBIT, '1200-00-000')
        self._add_account('1200-01-002', 'Home Loans', AccountType.ASSET, NormalBalance.DEBIT, '1200-00-000')
        self._add_account('1200-01-003', 'Business Loans', AccountType.ASSET, NormalBalance.DEBIT, '1200-00-000')
        self._add_account('1200-02-001', 'Loan Loss Allowance', AccountType.ASSET, NormalBalance.CREDIT, '1200-00-000')
        
        self._add_account('1300-00-000', 'Interest Receivable', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1300-01-001', 'Accrued Loan Interest', AccountType.ASSET, NormalBalance.DEBIT, '1300-00-000')
        self._add_account('1300-01-002', 'Accrued Investment Interest', AccountType.ASSET, NormalBalance.DEBIT, '1300-00-000')
        
        self._add_account('1400-00-000', 'Property and Equipment', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1400-01-001', 'Computer Equipment', AccountType.ASSET, NormalBalance.DEBIT, '1400-00-000')
        self._add_account('1400-01-002', 'Office Equipment', AccountType.ASSET, NormalBalance.DEBIT, '1400-00-000')
        self._add_account('1400-02-001', 'Accumulated Depreciation', AccountType.ASSET, NormalBalance.CREDIT, '1400-00-000')
        
        self._add_account('1500-00-000', 'Intangible Assets', AccountType.ASSET, NormalBalance.DEBIT)
        self._add_account('1500-01-001', 'Software', AccountType.ASSET, NormalBalance.DEBIT, '1500-00-000')
        self._add_account('1500-01-002', 'Banking License', AccountType.ASSET, NormalBalance.DEBIT, '1500-00-000')
        
        # LIABILITIES (2XXX)
        self._add_account('2000-00-000', 'Customer Deposits', AccountType.LIABILITY, NormalBalance.CREDIT)
        self._add_account('2000-01-001', 'Transaction Accounts', AccountType.LIABILITY, NormalBalance.CREDIT, '2000-00-000')
        self._add_account('2000-01-002', 'Savings Accounts', AccountType.LIABILITY, NormalBalance.CREDIT, '2000-00-000')
        self._add_account('2000-01-003', 'Term Deposits', AccountType.LIABILITY, NormalBalance.CREDIT, '2000-00-000')
        
        self._add_account('2100-00-000', 'Vostro Accounts', AccountType.LIABILITY, NormalBalance.CREDIT)
        self._add_account('2100-01-001', 'Vostro - Correspondent Banks', AccountType.LIABILITY, NormalBalance.CREDIT, '2100-00-000')
        
        self._add_account('2200-00-000', 'Accounts Payable', AccountType.LIABILITY, NormalBalance.CREDIT)
        self._add_account('2200-01-001', 'Trade Payables', AccountType.LIABILITY, NormalBalance.CREDIT, '2200-00-000')
        self._add_account('2200-01-002', 'Merchant Settlements Payable', AccountType.LIABILITY, NormalBalance.CREDIT, '2200-00-000')
        
        self._add_account('2300-00-000', 'Interest Payable', AccountType.LIABILITY, NormalBalance.CREDIT)
        self._add_account('2300-01-001', 'Accrued Deposit Interest', AccountType.LIABILITY, NormalBalance.CREDIT, '2300-00-000')
        
        self._add_account('2400-00-000', 'Borrowings', AccountType.LIABILITY, NormalBalance.CREDIT)
        self._add_account('2400-01-001', 'RBA Facility', AccountType.LIABILITY, NormalBalance.CREDIT, '2400-00-000')
        
        # EQUITY (3XXX)
        self._add_account('3000-00-000', 'Share Capital', AccountType.EQUITY, NormalBalance.CREDIT)
        self._add_account('3000-01-001', 'Ordinary Shares', AccountType.EQUITY, NormalBalance.CREDIT, '3000-00-000')
        
        self._add_account('3100-00-000', 'Retained Earnings', AccountType.EQUITY, NormalBalance.CREDIT)
        self._add_account('3100-01-001', 'Current Year Earnings', AccountType.EQUITY, NormalBalance.CREDIT, '3100-00-000')
        self._add_account('3100-01-002', 'Prior Year Earnings', AccountType.EQUITY, NormalBalance.CREDIT, '3100-00-000')
        
        self._add_account('3200-00-000', 'Reserves', AccountType.EQUITY, NormalBalance.CREDIT)
        self._add_account('3200-01-001', 'General Reserve', AccountType.EQUITY, NormalBalance.CREDIT, '3200-00-000')
        self._add_account('3200-01-002', 'Regulatory Reserve (APRA)', AccountType.EQUITY, NormalBalance.CREDIT, '3200-00-000')
        
        # REVENUE (4XXX)
        self._add_account('4000-00-000', 'Interest Income', AccountType.REVENUE, NormalBalance.CREDIT)
        self._add_account('4000-01-001', 'Loan Interest Income', AccountType.REVENUE, NormalBalance.CREDIT, '4000-00-000')
        self._add_account('4000-01-002', 'Investment Interest Income', AccountType.REVENUE, NormalBalance.CREDIT, '4000-00-000')
        
        self._add_account('4100-00-000', 'Fee Income', AccountType.REVENUE, NormalBalance.CREDIT)
        self._add_account('4100-01-001', 'Account Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4100-00-000')
        self._add_account('4100-01-002', 'Transaction Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4100-00-000')
        self._add_account('4100-01-003', 'Late Payment Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4100-00-000')
        
        self._add_account('4200-00-000', 'Merchant Fees', AccountType.REVENUE, NormalBalance.CREDIT)
        self._add_account('4200-01-001', 'Merchant Service Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4200-00-000')
        self._add_account('4200-01-002', 'Merchant Processing Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4200-00-000')
        
        self._add_account('4300-00-000', 'Card Fees', AccountType.REVENUE, NormalBalance.CREDIT)
        self._add_account('4300-01-001', 'Card Issuance Fees', AccountType.REVENUE, NormalBalance.CREDIT, '4300-00-000')
        self._add_account('4300-01-002', 'Interchange Income', AccountType.REVENUE, NormalBalance.CREDIT, '4300-00-000')
        
        self._add_account('4400-00-000', 'Investment Income', AccountType.REVENUE, NormalBalance.CREDIT)
        self._add_account('4400-01-001', 'Capital Gains', AccountType.REVENUE, NormalBalance.CREDIT, '4400-00-000')
        self._add_account('4400-01-002', 'Dividend Income', AccountType.REVENUE, NormalBalance.CREDIT, '4400-00-000')
        
        # EXPENSES (5XXX)
        self._add_account('5000-00-000', 'Interest Expense', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5000-01-001', 'Deposit Interest Expense', AccountType.EXPENSE, NormalBalance.DEBIT, '5000-00-000')
        self._add_account('5000-01-002', 'Borrowing Interest Expense', AccountType.EXPENSE, NormalBalance.DEBIT, '5000-00-000')
        
        self._add_account('5100-00-000', 'Operating Expenses', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5100-01-001', 'Rent', AccountType.EXPENSE, NormalBalance.DEBIT, '5100-00-000')
        self._add_account('5100-01-002', 'Utilities', AccountType.EXPENSE, NormalBalance.DEBIT, '5100-00-000')
        self._add_account('5100-01-003', 'Office Supplies', AccountType.EXPENSE, NormalBalance.DEBIT, '5100-00-000')
        
        self._add_account('5200-00-000', 'Staff Costs', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5200-01-001', 'Salaries and Wages', AccountType.EXPENSE, NormalBalance.DEBIT, '5200-00-000')
        self._add_account('5200-01-002', 'Superannuation', AccountType.EXPENSE, NormalBalance.DEBIT, '5200-00-000')
        self._add_account('5200-01-003', 'Payroll Tax', AccountType.EXPENSE, NormalBalance.DEBIT, '5200-00-000')
        
        self._add_account('5300-00-000', 'IT Expenses', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5300-01-001', 'Cloud Infrastructure', AccountType.EXPENSE, NormalBalance.DEBIT, '5300-00-000')
        self._add_account('5300-01-002', 'Software Licenses', AccountType.EXPENSE, NormalBalance.DEBIT, '5300-00-000')
        self._add_account('5300-01-003', 'Cybersecurity', AccountType.EXPENSE, NormalBalance.DEBIT, '5300-00-000')
        
        self._add_account('5400-00-000', 'Regulatory Costs', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5400-01-001', 'APRA Levies', AccountType.EXPENSE, NormalBalance.DEBIT, '5400-00-000')
        self._add_account('5400-01-002', 'ASIC Fees', AccountType.EXPENSE, NormalBalance.DEBIT, '5400-00-000')
        self._add_account('5400-01-003', 'AUSTRAC Compliance', AccountType.EXPENSE, NormalBalance.DEBIT, '5400-00-000')
        self._add_account('5400-01-004', 'Audit Fees', AccountType.EXPENSE, NormalBalance.DEBIT, '5400-00-000')
        
        self._add_account('5500-00-000', 'Loan Loss Provision', AccountType.EXPENSE, NormalBalance.DEBIT)
        self._add_account('5500-01-001', 'Bad Debt Expense', AccountType.EXPENSE, NormalBalance.DEBIT, '5500-00-000')
        self._add_account('5500-01-002', 'Write-offs', AccountType.EXPENSE, NormalBalance.DEBIT, '5500-00-000')
    
    def _add_account(
        self,
        code: str,
        name: str,
        account_type: AccountType,
        normal_balance: NormalBalance,
        parent: Optional[str] = None
    ):
        """Add account to CoA"""
        account = Account(code, name, account_type, normal_balance, parent)
        self.accounts[code] = account
    
    def get_account(self, account_code: str) -> Optional[Account]:
        """Get account by code"""
        return self.accounts.get(account_code)
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[Account]:
        """Get all accounts of a specific type"""
        return [
            acc for acc in self.accounts.values()
            if acc.account_type == account_type
        ]
    
    def get_balance_sheet_accounts(self) -> Dict[str, List[Account]]:
        """Get all balance sheet accounts (Assets, Liabilities, Equity)"""
        return {
            'assets': self.get_accounts_by_type(AccountType.ASSET),
            'liabilities': self.get_accounts_by_type(AccountType.LIABILITY),
            'equity': self.get_accounts_by_type(AccountType.EQUITY)
        }
    
    def get_income_statement_accounts(self) -> Dict[str, List[Account]]:
        """Get all income statement accounts (Revenue, Expenses)"""
        return {
            'revenue': self.get_accounts_by_type(AccountType.REVENUE),
            'expenses': self.get_accounts_by_type(AccountType.EXPENSE)
        }


# Global Chart of Accounts
_chart_of_accounts: Optional[ChartOfAccounts] = None


def get_chart_of_accounts() -> ChartOfAccounts:
    global _chart_of_accounts
    if _chart_of_accounts is None:
        _chart_of_accounts = ChartOfAccounts()
    return _chart_of_accounts

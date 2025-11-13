"""
Financial Statements - Australian Accounting Standards
AASB 101 - Presentation of Financial Statements
AASB 107 - Statement of Cash Flows
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from enum import Enum


class FinancialYear(BaseModel):
    """
    Financial Year Configuration
    
    Flexible financial year configuration
    Default: Australian financial year (July 1 - June 30)
    """
    
    # Configuration
    start_month: int = Field(default=7, ge=1, le=12)  # July
    start_day: int = Field(default=1, ge=1, le=31)
    end_month: int = Field(default=6, ge=1, le=12)  # June
    end_day: int = Field(default=30, ge=1, le=31)
    
    # Year identifier
    year: int  # e.g., 2025 for FY2024-2025
    name: str  # e.g., "FY2025"
    
    # Calculated dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        self._calculate_dates()
    
    def _calculate_dates(self):
        """Calculate start and end dates"""
        # For Australian FY: FY2025 = Jul 1, 2024 to Jun 30, 2025
        if self.start_month > self.end_month:
            # Financial year spans calendar years
            self.start_date = date(self.year - 1, self.start_month, self.start_day)
            self.end_date = date(self.year, self.end_month, self.end_day)
        else:
            # Financial year within calendar year
            self.start_date = date(self.year, self.start_month, self.start_day)
            self.end_date = date(self.year, self.end_month, self.end_day)
    
    @classmethod
    def australian_fy(cls, year: int) -> "FinancialYear":
        """Create Australian financial year (Jul 1 - Jun 30)"""
        return cls(
            start_month=7,
            start_day=1,
            end_month=6,
            end_day=30,
            year=year,
            name=f"FY{year}"
        )
    
    @classmethod
    def calendar_year(cls, year: int) -> "FinancialYear":
        """Create calendar year (Jan 1 - Dec 31)"""
        return cls(
            start_month=1,
            start_day=1,
            end_month=12,
            end_day=31,
            year=year,
            name=f"CY{year}"
        )


class BalanceSheetLine(BaseModel):
    """Single line item in balance sheet"""
    
    line_id: UUID = Field(default_factory=uuid4)
    account_code: str
    account_name: str
    amount: Decimal
    level: int = Field(default=1)  # Indentation level
    is_total: bool = Field(default=False)
    is_subtotal: bool = Field(default=False)


class BalanceSheet(BaseModel):
    """
    Balance Sheet (Statement of Financial Position)
    AASB 101 - Presentation of Financial Statements
    
    Australian format with current/non-current classification
    """
    
    # Identifiers
    statement_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Period
    as_of_date: date
    financial_year: FinancialYear
    
    # ASSETS
    current_assets: List[BalanceSheetLine] = Field(default_factory=list)
    non_current_assets: List[BalanceSheetLine] = Field(default_factory=list)
    total_current_assets: Decimal = Field(default=Decimal("0.00"))
    total_non_current_assets: Decimal = Field(default=Decimal("0.00"))
    total_assets: Decimal = Field(default=Decimal("0.00"))
    
    # LIABILITIES
    current_liabilities: List[BalanceSheetLine] = Field(default_factory=list)
    non_current_liabilities: List[BalanceSheetLine] = Field(default_factory=list)
    total_current_liabilities: Decimal = Field(default=Decimal("0.00"))
    total_non_current_liabilities: Decimal = Field(default=Decimal("0.00"))
    total_liabilities: Decimal = Field(default=Decimal("0.00"))
    
    # EQUITY
    equity_lines: List[BalanceSheetLine] = Field(default_factory=list)
    total_equity: Decimal = Field(default=Decimal("0.00"))
    
    # Balancing check
    total_liabilities_and_equity: Decimal = Field(default=Decimal("0.00"))
    is_balanced: bool = Field(default=False)
    
    # Audit
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_totals(self):
        """Calculate all totals"""
        self.total_current_assets = sum(line.amount for line in self.current_assets if not line.is_total)
        self.total_non_current_assets = sum(line.amount for line in self.non_current_assets if not line.is_total)
        self.total_assets = self.total_current_assets + self.total_non_current_assets
        
        self.total_current_liabilities = sum(line.amount for line in self.current_liabilities if not line.is_total)
        self.total_non_current_liabilities = sum(line.amount for line in self.non_current_liabilities if not line.is_total)
        self.total_liabilities = self.total_current_liabilities + self.total_non_current_liabilities
        
        self.total_equity = sum(line.amount for line in self.equity_lines if not line.is_total)
        
        self.total_liabilities_and_equity = self.total_liabilities + self.total_equity
        
        # Check if balanced (Assets = Liabilities + Equity)
        self.is_balanced = abs(self.total_assets - self.total_liabilities_and_equity) < Decimal("0.01")


class IncomeStatementLine(BaseModel):
    """Single line item in income statement"""
    
    line_id: UUID = Field(default_factory=uuid4)
    account_code: str
    account_name: str
    amount: Decimal
    level: int = Field(default=1)
    is_total: bool = Field(default=False)
    is_subtotal: bool = Field(default=False)


class IncomeStatement(BaseModel):
    """
    Income Statement (Profit & Loss Statement)
    AASB 101 - Presentation of Financial Statements
    
    Australian format with detailed revenue and expense breakdown
    """
    
    # Identifiers
    statement_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Period
    period_start: date
    period_end: date
    financial_year: FinancialYear
    
    # REVENUE
    interest_income_lines: List[IncomeStatementLine] = Field(default_factory=list)
    fee_income_lines: List[IncomeStatementLine] = Field(default_factory=list)
    other_income_lines: List[IncomeStatementLine] = Field(default_factory=list)
    
    total_interest_income: Decimal = Field(default=Decimal("0.00"))
    total_fee_income: Decimal = Field(default=Decimal("0.00"))
    total_other_income: Decimal = Field(default=Decimal("0.00"))
    total_revenue: Decimal = Field(default=Decimal("0.00"))
    
    # EXPENSES
    interest_expense_lines: List[IncomeStatementLine] = Field(default_factory=list)
    operating_expense_lines: List[IncomeStatementLine] = Field(default_factory=list)
    loan_loss_provision_lines: List[IncomeStatementLine] = Field(default_factory=list)
    depreciation_lines: List[IncomeStatementLine] = Field(default_factory=list)
    other_expense_lines: List[IncomeStatementLine] = Field(default_factory=list)
    
    total_interest_expense: Decimal = Field(default=Decimal("0.00"))
    total_operating_expenses: Decimal = Field(default=Decimal("0.00"))
    total_loan_loss_provisions: Decimal = Field(default=Decimal("0.00"))
    total_depreciation: Decimal = Field(default=Decimal("0.00"))
    total_other_expenses: Decimal = Field(default=Decimal("0.00"))
    total_expenses: Decimal = Field(default=Decimal("0.00"))
    
    # PROFIT
    net_interest_income: Decimal = Field(default=Decimal("0.00"))  # Interest Income - Interest Expense
    operating_income: Decimal = Field(default=Decimal("0.00"))  # Total Revenue - Total Expenses
    net_profit_before_tax: Decimal = Field(default=Decimal("0.00"))
    income_tax_expense: Decimal = Field(default=Decimal("0.00"))
    net_profit_after_tax: Decimal = Field(default=Decimal("0.00"))
    
    # Audit
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_totals(self):
        """Calculate all totals"""
        # Revenue
        self.total_interest_income = sum(line.amount for line in self.interest_income_lines if not line.is_total)
        self.total_fee_income = sum(line.amount for line in self.fee_income_lines if not line.is_total)
        self.total_other_income = sum(line.amount for line in self.other_income_lines if not line.is_total)
        self.total_revenue = self.total_interest_income + self.total_fee_income + self.total_other_income
        
        # Expenses
        self.total_interest_expense = sum(line.amount for line in self.interest_expense_lines if not line.is_total)
        self.total_operating_expenses = sum(line.amount for line in self.operating_expense_lines if not line.is_total)
        self.total_loan_loss_provisions = sum(line.amount for line in self.loan_loss_provision_lines if not line.is_total)
        self.total_depreciation = sum(line.amount for line in self.depreciation_lines if not line.is_total)
        self.total_other_expenses = sum(line.amount for line in self.other_expense_lines if not line.is_total)
        self.total_expenses = (
            self.total_interest_expense +
            self.total_operating_expenses +
            self.total_loan_loss_provisions +
            self.total_depreciation +
            self.total_other_expenses
        )
        
        # Profit
        self.net_interest_income = self.total_interest_income - self.total_interest_expense
        self.operating_income = self.total_revenue - self.total_expenses
        self.net_profit_before_tax = self.operating_income
        
        # Tax (30% corporate tax rate in Australia)
        self.income_tax_expense = self.net_profit_before_tax * Decimal("0.30")
        self.net_profit_after_tax = self.net_profit_before_tax - self.income_tax_expense


class CashFlowLine(BaseModel):
    """Single line item in cash flow statement"""
    
    line_id: UUID = Field(default_factory=uuid4)
    description: str
    amount: Decimal
    level: int = Field(default=1)
    is_total: bool = Field(default=False)


class CashFlowStatement(BaseModel):
    """
    Cash Flow Statement
    AASB 107 - Statement of Cash Flows
    
    Australian format with operating, investing, and financing activities
    """
    
    # Identifiers
    statement_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Period
    period_start: date
    period_end: date
    financial_year: FinancialYear
    
    # OPERATING ACTIVITIES
    operating_activities: List[CashFlowLine] = Field(default_factory=list)
    net_cash_from_operating: Decimal = Field(default=Decimal("0.00"))
    
    # INVESTING ACTIVITIES
    investing_activities: List[CashFlowLine] = Field(default_factory=list)
    net_cash_from_investing: Decimal = Field(default=Decimal("0.00"))
    
    # FINANCING ACTIVITIES
    financing_activities: List[CashFlowLine] = Field(default_factory=list)
    net_cash_from_financing: Decimal = Field(default=Decimal("0.00"))
    
    # NET CHANGE IN CASH
    net_increase_in_cash: Decimal = Field(default=Decimal("0.00"))
    cash_at_beginning: Decimal = Field(default=Decimal("0.00"))
    cash_at_end: Decimal = Field(default=Decimal("0.00"))
    
    # Audit
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_totals(self):
        """Calculate all totals"""
        self.net_cash_from_operating = sum(line.amount for line in self.operating_activities if not line.is_total)
        self.net_cash_from_investing = sum(line.amount for line in self.investing_activities if not line.is_total)
        self.net_cash_from_financing = sum(line.amount for line in self.financing_activities if not line.is_total)
        
        self.net_increase_in_cash = (
            self.net_cash_from_operating +
            self.net_cash_from_investing +
            self.net_cash_from_financing
        )
        
        self.cash_at_end = self.cash_at_beginning + self.net_increase_in_cash


class FinancialRatios(BaseModel):
    """
    Financial Ratios and KPIs
    
    Key performance indicators for financial analysis
    """
    
    tenant_id: UUID
    as_of_date: date
    
    # Profitability Ratios
    net_interest_margin: Decimal = Field(default=Decimal("0.00"))  # (Interest Income - Interest Expense) / Avg Assets
    return_on_assets: Decimal = Field(default=Decimal("0.00"))  # Net Profit / Avg Assets
    return_on_equity: Decimal = Field(default=Decimal("0.00"))  # Net Profit / Avg Equity
    cost_to_income_ratio: Decimal = Field(default=Decimal("0.00"))  # Operating Expenses / Operating Income
    
    # Asset Quality Ratios
    non_performing_loan_ratio: Decimal = Field(default=Decimal("0.00"))  # NPL / Total Loans
    provision_coverage_ratio: Decimal = Field(default=Decimal("0.00"))  # Provisions / NPL
    loan_loss_rate: Decimal = Field(default=Decimal("0.00"))  # Loan Losses / Avg Loans
    
    # Liquidity Ratios
    liquidity_coverage_ratio: Decimal = Field(default=Decimal("0.00"))  # LCR (APRA requirement: ≥ 100%)
    net_stable_funding_ratio: Decimal = Field(default=Decimal("0.00"))  # NSFR (APRA requirement: ≥ 100%)
    loan_to_deposit_ratio: Decimal = Field(default=Decimal("0.00"))  # Total Loans / Total Deposits
    cash_ratio: Decimal = Field(default=Decimal("0.00"))  # Cash / Current Liabilities
    
    # Capital Ratios (APRA APS 110)
    cet1_ratio: Decimal = Field(default=Decimal("0.00"))  # CET1 Capital / RWA (minimum 4.5%)
    tier1_ratio: Decimal = Field(default=Decimal("0.00"))  # Tier 1 Capital / RWA (minimum 6%)
    total_capital_ratio: Decimal = Field(default=Decimal("0.00"))  # Total Capital / RWA (minimum 8%)
    leverage_ratio: Decimal = Field(default=Decimal("0.00"))  # Tier 1 Capital / Total Exposures (minimum 3%)
    
    # Calculated at
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

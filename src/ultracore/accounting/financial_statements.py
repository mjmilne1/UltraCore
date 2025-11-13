"""
UltraCore Accounting System - Financial Statements

AI-enhanced financial reporting:
- Balance Sheet (Statement of Financial Position)
- Profit & Loss (Income Statement)
- Cash Flow Statement
- Financial ratios and KPIs
- AI-powered insights and analysis
- Period-over-period comparisons
- Export capabilities
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio

from ultracore.accounting.chart_of_accounts import (
    get_chart_of_accounts, GLAccount, AccountType, AccountClass
)
from ultracore.accounting.general_ledger import (
    get_general_ledger, AccountBalance, TrialBalance
)


# ============================================================================
# Financial Statement Enums
# ============================================================================

class StatementType(str, Enum):
    """Types of financial statements"""
    BALANCE_SHEET = "BALANCE_SHEET"
    PROFIT_LOSS = "PROFIT_LOSS"
    CASH_FLOW = "CASH_FLOW"
    TRIAL_BALANCE = "TRIAL_BALANCE"
    GENERAL_LEDGER = "GENERAL_LEDGER"


class StatementFormat(str, Enum):
    """Statement presentation formats"""
    STANDARD = "STANDARD"  # Traditional format
    COMPARATIVE = "COMPARATIVE"  # Side-by-side periods
    CONSOLIDATED = "CONSOLIDATED"  # Multi-entity
    DETAILED = "DETAILED"  # Full detail
    SUMMARY = "SUMMARY"  # High-level only


class CashFlowMethod(str, Enum):
    """Cash flow statement methods"""
    DIRECT = "DIRECT"  # Show actual cash receipts/payments
    INDIRECT = "INDIRECT"  # Start from net income


class FinancialTrend(str, Enum):
    """Trend direction"""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    VOLATILE = "VOLATILE"


# ============================================================================
# Financial Statement Data Models
# ============================================================================

@dataclass
class BalanceSheetLine:
    """Line item on balance sheet"""
    line_id: str
    line_name: str
    account_type: AccountType
    amount: Decimal
    
    # Hierarchy
    level: int = 1  # 1=section, 2=subsection, 3=account
    parent_line: Optional[str] = None
    is_total: bool = False
    is_subtotal: bool = False
    
    # Formatting
    indent: int = 0
    bold: bool = False
    underline: bool = False
    
    # Period comparison
    prior_period_amount: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None
    change_percent: Optional[float] = None
    
    # Metadata
    account_codes: List[str] = field(default_factory=list)


@dataclass
class BalanceSheet:
    """Complete balance sheet"""
    statement_id: str
    as_of_date: date
    entity_name: str = "UltraCore Banking Platform"
    
    # Assets
    current_assets: List[BalanceSheetLine] = field(default_factory=list)
    non_current_assets: List[BalanceSheetLine] = field(default_factory=list)
    total_assets: Decimal = Decimal('0.00')
    
    # Liabilities
    current_liabilities: List[BalanceSheetLine] = field(default_factory=list)
    non_current_liabilities: List[BalanceSheetLine] = field(default_factory=list)
    total_liabilities: Decimal = Decimal('0.00')
    
    # Equity
    equity: List[BalanceSheetLine] = field(default_factory=list)
    total_equity: Decimal = Decimal('0.00')
    
    # Validation
    is_balanced: bool = True
    balance_difference: Decimal = Decimal('0.00')
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None
    statement_format: StatementFormat = StatementFormat.STANDARD
    
    # AI Insights
    ai_insights: List[str] = field(default_factory=list)
    health_score: float = 0.0  # 0-100
    
    def total_liabilities_and_equity(self) -> Decimal:
        """Calculate total liabilities + equity"""
        return self.total_liabilities + self.total_equity


@dataclass
class ProfitLossLine:
    """Line item on profit & loss statement"""
    line_id: str
    line_name: str
    amount: Decimal
    
    # Hierarchy
    level: int = 1
    parent_line: Optional[str] = None
    is_total: bool = False
    is_subtotal: bool = False
    
    # Formatting
    indent: int = 0
    bold: bool = False
    underline: bool = False
    
    # Period comparison
    prior_period_amount: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None
    change_percent: Optional[float] = None
    
    # Percentage of revenue
    percent_of_revenue: Optional[float] = None
    
    # Metadata
    account_codes: List[str] = field(default_factory=list)


@dataclass
class ProfitLossStatement:
    """Complete profit & loss (income) statement"""
    statement_id: str
    period_start: date
    period_end: date
    entity_name: str = "UltraCore Banking Platform"
    
    # Revenue
    revenue_lines: List[ProfitLossLine] = field(default_factory=list)
    total_revenue: Decimal = Decimal('0.00')
    
    # Operating Expenses
    expense_lines: List[ProfitLossLine] = field(default_factory=list)
    total_expenses: Decimal = Decimal('0.00')
    
    # Results
    operating_income: Decimal = Decimal('0.00')
    net_income: Decimal = Decimal('0.00')
    
    # Margins
    gross_margin_percent: float = 0.0
    operating_margin_percent: float = 0.0
    net_margin_percent: float = 0.0
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None
    statement_format: StatementFormat = StatementFormat.STANDARD
    
    # AI Insights
    ai_insights: List[str] = field(default_factory=list)
    profitability_score: float = 0.0  # 0-100


@dataclass
class CashFlowLine:
    """Line item on cash flow statement"""
    line_id: str
    line_name: str
    amount: Decimal
    
    # Category
    category: AccountClass  # OPERATING, INVESTING, FINANCING
    
    # Hierarchy
    level: int = 1
    parent_line: Optional[str] = None
    is_total: bool = False
    
    # Formatting
    indent: int = 0
    bold: bool = False
    
    # Period comparison
    prior_period_amount: Optional[Decimal] = None
    change_amount: Optional[Decimal] = None


@dataclass
class CashFlowStatement:
    """Complete cash flow statement"""
    statement_id: str
    period_start: date
    period_end: date
    entity_name: str = "UltraCore Banking Platform"
    method: CashFlowMethod = CashFlowMethod.INDIRECT
    
    # Cash flows by activity
    operating_activities: List[CashFlowLine] = field(default_factory=list)
    investing_activities: List[CashFlowLine] = field(default_factory=list)
    financing_activities: List[CashFlowLine] = field(default_factory=list)
    
    # Totals
    net_cash_from_operations: Decimal = Decimal('0.00')
    net_cash_from_investing: Decimal = Decimal('0.00')
    net_cash_from_financing: Decimal = Decimal('0.00')
    
    # Cash reconciliation
    beginning_cash: Decimal = Decimal('0.00')
    net_change_in_cash: Decimal = Decimal('0.00')
    ending_cash: Decimal = Decimal('0.00')
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None
    
    # AI Insights
    ai_insights: List[str] = field(default_factory=list)
    liquidity_score: float = 0.0  # 0-100


@dataclass
class FinancialRatios:
    """Key financial ratios and KPIs"""
    
    # Liquidity Ratios
    current_ratio: Optional[float] = None  # Current Assets / Current Liabilities
    quick_ratio: Optional[float] = None  # (Current Assets - Inventory) / Current Liabilities
    cash_ratio: Optional[float] = None  # Cash / Current Liabilities
    
    # Profitability Ratios
    return_on_assets: Optional[float] = None  # Net Income / Total Assets
    return_on_equity: Optional[float] = None  # Net Income / Total Equity
    profit_margin: Optional[float] = None  # Net Income / Revenue
    
    # Leverage Ratios
    debt_to_equity: Optional[float] = None  # Total Debt / Total Equity
    debt_to_assets: Optional[float] = None  # Total Debt / Total Assets
    equity_ratio: Optional[float] = None  # Total Equity / Total Assets
    
    # Efficiency Ratios
    asset_turnover: Optional[float] = None  # Revenue / Average Total Assets
    
    # Banking-specific
    loan_to_deposit: Optional[float] = None  # Total Loans / Total Deposits
    net_interest_margin: Optional[float] = None  # (Interest Income - Interest Expense) / Assets
    
    # Interpretation
    liquidity_health: str = "UNKNOWN"  # EXCELLENT, GOOD, FAIR, POOR
    profitability_health: str = "UNKNOWN"
    leverage_health: str = "UNKNOWN"
    
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FinancialInsight:
    """AI-generated financial insight"""
    insight_id: str
    category: str  # STRENGTH, WEAKNESS, OPPORTUNITY, RISK
    title: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    recommendation: Optional[str] = None
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Financial Statements Generator
# ============================================================================

class FinancialStatementsGenerator:
    """
    Generate financial statements with AI-powered analytics
    """
    
    def __init__(self):
        self.chart = get_chart_of_accounts()
        self.gl = get_general_ledger()
    
    # ========================================================================
    # Balance Sheet
    # ========================================================================
    
    async def generate_balance_sheet(
        self,
        as_of_date: date,
        comparative: bool = False,
        prior_date: Optional[date] = None,
        generated_by: Optional[str] = None
    ) -> BalanceSheet:
        """Generate balance sheet (statement of financial position)"""
        
        statement_id = f"BS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Get trial balance
        trial_balance = await self.gl.get_trial_balance(as_of_date)
        
        # Get prior period if comparative
        prior_trial = None
        if comparative and prior_date:
            prior_trial = await self.gl.get_trial_balance(prior_date)
        
        balance_sheet = BalanceSheet(
            statement_id=statement_id,
            as_of_date=as_of_date,
            generated_by=generated_by,
            statement_format=StatementFormat.COMPARATIVE if comparative else StatementFormat.STANDARD
        )
        
        # Build balance sheet sections
        await self._build_assets_section(balance_sheet, trial_balance, prior_trial)
        await self._build_liabilities_section(balance_sheet, trial_balance, prior_trial)
        await self._build_equity_section(balance_sheet, trial_balance, prior_trial)
        
        # Calculate totals
        balance_sheet.total_assets = sum(
            line.amount for section in [balance_sheet.current_assets, balance_sheet.non_current_assets]
            for line in section if line.is_total or line.is_subtotal
        )
        
        balance_sheet.total_liabilities = sum(
            line.amount for section in [balance_sheet.current_liabilities, balance_sheet.non_current_liabilities]
            for line in section if line.is_total or line.is_subtotal
        )
        
        balance_sheet.total_equity = sum(
            line.amount for line in balance_sheet.equity if line.is_total or line.is_subtotal
        )
        
        # Check if balanced
        balance_sheet.balance_difference = (
            balance_sheet.total_assets - 
            balance_sheet.total_liabilities_and_equity()
        )
        balance_sheet.is_balanced = abs(balance_sheet.balance_difference) < Decimal('0.01')
        
        # Generate AI insights
        balance_sheet.ai_insights = await self._generate_balance_sheet_insights(balance_sheet)
        balance_sheet.health_score = await self._calculate_balance_sheet_health(balance_sheet)
        
        return balance_sheet
    
    async def _build_assets_section(
        self,
        bs: BalanceSheet,
        trial: TrialBalance,
        prior_trial: Optional[TrialBalance]
    ):
        """Build assets section of balance sheet"""
        
        # Current Assets
        bs.current_assets.append(BalanceSheetLine(
            line_id="CA-HEADER",
            line_name="CURRENT ASSETS",
            account_type=AccountType.ASSET,
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_subtotal=True
        ))
        
        current_asset_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.ASSET and
               self.chart.get_account(acc.account_code).account_class == AccountClass.CURRENT
        ]
        
        current_total = Decimal('0.00')
        for acc in sorted(current_asset_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            current_total += amount
            
            prior_amount = None
            if prior_trial:
                prior_acc = next((a for a in prior_trial.accounts if a.account_code == acc.account_code), None)
                prior_amount = prior_acc.net_balance if prior_acc else Decimal('0.00')
            
            bs.current_assets.append(BalanceSheetLine(
                line_id=f"CA-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                account_type=AccountType.ASSET,
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code],
                prior_period_amount=prior_amount
            ))
        
        # Current Assets Total
        bs.current_assets[0].amount = current_total
        
        # Non-Current Assets
        bs.non_current_assets.append(BalanceSheetLine(
            line_id="NCA-HEADER",
            line_name="NON-CURRENT ASSETS",
            account_type=AccountType.ASSET,
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_subtotal=True
        ))
        
        non_current_asset_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.ASSET and
               self.chart.get_account(acc.account_code).account_class == AccountClass.NON_CURRENT
        ]
        
        non_current_total = Decimal('0.00')
        for acc in sorted(non_current_asset_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            non_current_total += amount
            
            bs.non_current_assets.append(BalanceSheetLine(
                line_id=f"NCA-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                account_type=AccountType.ASSET,
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code]
            ))
        
        bs.non_current_assets[0].amount = non_current_total
    
    async def _build_liabilities_section(
        self,
        bs: BalanceSheet,
        trial: TrialBalance,
        prior_trial: Optional[TrialBalance]
    ):
        """Build liabilities section"""
        
        # Current Liabilities
        bs.current_liabilities.append(BalanceSheetLine(
            line_id="CL-HEADER",
            line_name="CURRENT LIABILITIES",
            account_type=AccountType.LIABILITY,
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_subtotal=True
        ))
        
        current_liability_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.LIABILITY and
               self.chart.get_account(acc.account_code).account_class == AccountClass.CURRENT
        ]
        
        current_liab_total = Decimal('0.00')
        for acc in sorted(current_liability_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            current_liab_total += amount
            
            bs.current_liabilities.append(BalanceSheetLine(
                line_id=f"CL-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                account_type=AccountType.LIABILITY,
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code]
            ))
        
        bs.current_liabilities[0].amount = current_liab_total
        
        # Non-Current Liabilities
        non_current_liability_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.LIABILITY and
               self.chart.get_account(acc.account_code).account_class == AccountClass.NON_CURRENT
        ]
        
        if non_current_liability_accounts:
            bs.non_current_liabilities.append(BalanceSheetLine(
                line_id="NCL-HEADER",
                line_name="NON-CURRENT LIABILITIES",
                account_type=AccountType.LIABILITY,
                amount=Decimal('0.00'),
                level=1,
                bold=True,
                is_subtotal=True
            ))
            
            non_current_liab_total = Decimal('0.00')
            for acc in sorted(non_current_liability_accounts, key=lambda x: x.account_code):
                amount = acc.net_balance
                non_current_liab_total += amount
                
                bs.non_current_liabilities.append(BalanceSheetLine(
                    line_id=f"NCL-{acc.account_code}",
                    line_name=f"  {acc.account_name}",
                    account_type=AccountType.LIABILITY,
                    amount=amount,
                    level=2,
                    indent=1,
                    account_codes=[acc.account_code]
                ))
            
            bs.non_current_liabilities[0].amount = non_current_liab_total
    
    async def _build_equity_section(
        self,
        bs: BalanceSheet,
        trial: TrialBalance,
        prior_trial: Optional[TrialBalance]
    ):
        """Build equity section"""
        
        bs.equity.append(BalanceSheetLine(
            line_id="EQ-HEADER",
            line_name="EQUITY",
            account_type=AccountType.EQUITY,
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_total=True
        ))
        
        equity_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.EQUITY
        ]
        
        equity_total = Decimal('0.00')
        for acc in sorted(equity_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            equity_total += amount
            
            bs.equity.append(BalanceSheetLine(
                line_id=f"EQ-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                account_type=AccountType.EQUITY,
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code]
            ))
        
        bs.equity[0].amount = equity_total
    
    # ========================================================================
    # Profit & Loss Statement
    # ========================================================================
    
    async def generate_profit_loss(
        self,
        period_start: date,
        period_end: date,
        comparative: bool = False,
        prior_period_start: Optional[date] = None,
        prior_period_end: Optional[date] = None,
        generated_by: Optional[str] = None
    ) -> ProfitLossStatement:
        """Generate profit & loss (income) statement"""
        
        statement_id = f"PL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        pl = ProfitLossStatement(
            statement_id=statement_id,
            period_start=period_start,
            period_end=period_end,
            generated_by=generated_by,
            statement_format=StatementFormat.COMPARATIVE if comparative else StatementFormat.STANDARD
        )
        
        # Get account balances for period
        trial = await self.gl.get_trial_balance(period_end)
        
        # Build revenue section
        await self._build_revenue_section(pl, trial)
        
        # Build expenses section
        await self._build_expenses_section(pl, trial)
        
        # Calculate results
        pl.operating_income = pl.total_revenue - pl.total_expenses
        pl.net_income = pl.operating_income  # Simplified (no other income/expense)
        
        # Calculate margins
        if pl.total_revenue > 0:
            pl.net_margin_percent = float(pl.net_income / pl.total_revenue * 100)
            pl.operating_margin_percent = float(pl.operating_income / pl.total_revenue * 100)
            pl.gross_margin_percent = pl.net_margin_percent  # Simplified
        
        # Calculate percent of revenue for each line
        for line in pl.revenue_lines + pl.expense_lines:
            if pl.total_revenue > 0:
                line.percent_of_revenue = float(abs(line.amount) / pl.total_revenue * 100)
        
        # Generate AI insights
        pl.ai_insights = await self._generate_pl_insights(pl)
        pl.profitability_score = await self._calculate_profitability_score(pl)
        
        return pl
    
    async def _build_revenue_section(self, pl: ProfitLossStatement, trial: TrialBalance):
        """Build revenue section"""
        
        pl.revenue_lines.append(ProfitLossLine(
            line_id="REV-HEADER",
            line_name="REVENUE",
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_total=True
        ))
        
        revenue_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.REVENUE
        ]
        
        total_revenue = Decimal('0.00')
        for acc in sorted(revenue_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            total_revenue += amount
            
            pl.revenue_lines.append(ProfitLossLine(
                line_id=f"REV-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code]
            ))
        
        pl.revenue_lines[0].amount = total_revenue
        pl.total_revenue = total_revenue
    
    async def _build_expenses_section(self, pl: ProfitLossStatement, trial: TrialBalance):
        """Build expenses section"""
        
        pl.expense_lines.append(ProfitLossLine(
            line_id="EXP-HEADER",
            line_name="EXPENSES",
            amount=Decimal('0.00'),
            level=1,
            bold=True,
            is_total=True
        ))
        
        expense_accounts = [
            acc for acc in trial.accounts
            if acc.account_type == AccountType.EXPENSE
        ]
        
        total_expenses = Decimal('0.00')
        for acc in sorted(expense_accounts, key=lambda x: x.account_code):
            amount = acc.net_balance
            total_expenses += amount
            
            pl.expense_lines.append(ProfitLossLine(
                line_id=f"EXP-{acc.account_code}",
                line_name=f"  {acc.account_name}",
                amount=amount,
                level=2,
                indent=1,
                account_codes=[acc.account_code]
            ))
        
        pl.expense_lines[0].amount = total_expenses
        pl.total_expenses = total_expenses
    
    # ========================================================================
    # Cash Flow Statement
    # ========================================================================
    
    async def generate_cash_flow(
        self,
        period_start: date,
        period_end: date,
        method: CashFlowMethod = CashFlowMethod.INDIRECT,
        generated_by: Optional[str] = None
    ) -> CashFlowStatement:
        """Generate cash flow statement"""
        
        statement_id = f"CF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        cf = CashFlowStatement(
            statement_id=statement_id,
            period_start=period_start,
            period_end=period_end,
            method=method,
            generated_by=generated_by
        )
        
        # Get cash accounts
        cash_start = await self._get_cash_balance(period_start)
        cash_end = await self._get_cash_balance(period_end)
        
        cf.beginning_cash = cash_start
        cf.ending_cash = cash_end
        
        # Get P&L for period
        pl = await self.generate_profit_loss(period_start, period_end)
        
        if method == CashFlowMethod.INDIRECT:
            await self._build_cash_flow_indirect(cf, pl)
        else:
            await self._build_cash_flow_direct(cf)
        
        # Calculate totals
        cf.net_cash_from_operations = sum(l.amount for l in cf.operating_activities if l.is_total)
        cf.net_cash_from_investing = sum(l.amount for l in cf.investing_activities if l.is_total)
        cf.net_cash_from_financing = sum(l.amount for l in cf.financing_activities if l.is_total)
        
        cf.net_change_in_cash = (
            cf.net_cash_from_operations +
            cf.net_cash_from_investing +
            cf.net_cash_from_financing
        )
        
        # Generate insights
        cf.ai_insights = await self._generate_cashflow_insights(cf)
        cf.liquidity_score = await self._calculate_liquidity_score(cf)
        
        return cf
    
    async def _get_cash_balance(self, as_of: date) -> Decimal:
        """Get total cash balance"""
        # Get cash accounts (1100, 1110, 1120)
        cash_accounts = ['1100', '1110', '1120']
        total = Decimal('0.00')
        
        for acc_code in cash_accounts:
            balance = await self.gl.get_account_balance(acc_code, as_of)
            if balance:
                total += balance.net_balance
        
        return total
    
    async def _build_cash_flow_indirect(
        self,
        cf: CashFlowStatement,
        pl: ProfitLossStatement
    ):
        """Build cash flow using indirect method"""
        
        # Operating Activities
        cf.operating_activities.append(CashFlowLine(
            line_id="OP-NET-INCOME",
            line_name="Net Income",
            amount=pl.net_income,
            category=AccountClass.OPERATING,
            level=1
        ))
        
        # Adjustments (simplified)
        cf.operating_activities.append(CashFlowLine(
            line_id="OP-ADJUSTMENTS",
            line_name="Adjustments to reconcile net income to cash:",
            amount=Decimal('0.00'),
            category=AccountClass.OPERATING,
            level=1,
            bold=True
        ))
        
        # Would add depreciation, changes in working capital, etc.
        
        cf.operating_activities.append(CashFlowLine(
            line_id="OP-TOTAL",
            line_name="Net Cash from Operating Activities",
            amount=pl.net_income,  # Simplified
            category=AccountClass.OPERATING,
            level=1,
            bold=True,
            is_total=True
        ))
        
        # Investing Activities (placeholder)
        cf.investing_activities.append(CashFlowLine(
            line_id="INV-TOTAL",
            line_name="Net Cash from Investing Activities",
            amount=Decimal('0.00'),
            category=AccountClass.INVESTING,
            level=1,
            bold=True,
            is_total=True
        ))
        
        # Financing Activities (placeholder)
        cf.financing_activities.append(CashFlowLine(
            line_id="FIN-TOTAL",
            line_name="Net Cash from Financing Activities",
            amount=Decimal('0.00'),
            category=AccountClass.FINANCING,
            level=1,
            bold=True,
            is_total=True
        ))
    
    async def _build_cash_flow_direct(self, cf: CashFlowStatement):
        """Build cash flow using direct method"""
        # Direct method - would show actual cash receipts and payments
        pass
    
    # ========================================================================
    # Financial Ratios
    # ========================================================================
    
    async def calculate_financial_ratios(
        self,
        as_of_date: date,
        period_start: date,
        period_end: date
    ) -> FinancialRatios:
        """Calculate key financial ratios"""
        
        # Get statements
        bs = await self.generate_balance_sheet(as_of_date)
        pl = await self.generate_profit_loss(period_start, period_end)
        
        ratios = FinancialRatios()
        
        # Get key figures
        current_assets = bs.current_assets[0].amount if bs.current_assets else Decimal('0')
        current_liabilities = bs.current_liabilities[0].amount if bs.current_liabilities else Decimal('0')
        total_assets = bs.total_assets
        total_equity = bs.total_equity
        total_liabilities = bs.total_liabilities
        revenue = pl.total_revenue
        net_income = pl.net_income
        
        # Liquidity Ratios
        if current_liabilities > 0:
            ratios.current_ratio = float(current_assets / current_liabilities)
            ratios.quick_ratio = float(current_assets / current_liabilities)  # Simplified
            
            # Interpret
            if ratios.current_ratio >= 2.0:
                ratios.liquidity_health = "EXCELLENT"
            elif ratios.current_ratio >= 1.5:
                ratios.liquidity_health = "GOOD"
            elif ratios.current_ratio >= 1.0:
                ratios.liquidity_health = "FAIR"
            else:
                ratios.liquidity_health = "POOR"
        
        # Profitability Ratios
        if total_assets > 0:
            ratios.return_on_assets = float(net_income / total_assets * 100)
        
        if total_equity > 0:
            ratios.return_on_equity = float(net_income / total_equity * 100)
            
            # Interpret
            if ratios.return_on_equity >= 15.0:
                ratios.profitability_health = "EXCELLENT"
            elif ratios.return_on_equity >= 10.0:
                ratios.profitability_health = "GOOD"
            elif ratios.return_on_equity >= 5.0:
                ratios.profitability_health = "FAIR"
            else:
                ratios.profitability_health = "POOR"
        
        if revenue > 0:
            ratios.profit_margin = float(net_income / revenue * 100)
        
        # Leverage Ratios
        if total_equity > 0:
            ratios.debt_to_equity = float(total_liabilities / total_equity)
            
            # Interpret
            if ratios.debt_to_equity <= 0.5:
                ratios.leverage_health = "EXCELLENT"
            elif ratios.debt_to_equity <= 1.0:
                ratios.leverage_health = "GOOD"
            elif ratios.debt_to_equity <= 2.0:
                ratios.leverage_health = "FAIR"
            else:
                ratios.leverage_health = "POOR"
        
        if total_assets > 0:
            ratios.debt_to_assets = float(total_liabilities / total_assets)
            ratios.equity_ratio = float(total_equity / total_assets)
        
        # Banking-specific ratios
        # Get loan and deposit balances
        loan_balance = await self._get_account_group_balance(['1200'])
        deposit_balance = await self._get_account_group_balance(['2100', '2110'])
        
        if deposit_balance > 0:
            ratios.loan_to_deposit = float(loan_balance / deposit_balance)
        
        return ratios
    
    async def _get_account_group_balance(self, account_codes: List[str]) -> Decimal:
        """Get total balance for a group of accounts"""
        total = Decimal('0.00')
        for code in account_codes:
            balance = await self.gl.get_account_balance(code)
            if balance:
                total += balance.net_balance
        return total
    
    # ========================================================================
    # AI Insights Generation
    # ========================================================================
    
    async def _generate_balance_sheet_insights(self, bs: BalanceSheet) -> List[str]:
        """Generate AI-powered insights for balance sheet"""
        
        insights = []
        
        # Asset composition
        if bs.total_assets > 0:
            current_pct = float(bs.current_assets[0].amount / bs.total_assets * 100)
            insights.append(
                f"Current assets represent {current_pct:.1f}% of total assets, "
                f"indicating {'strong' if current_pct > 50 else 'limited'} short-term liquidity"
            )
        
        # Balance check
        if not bs.is_balanced:
            insights.append(
                f"⚠️ Balance sheet is out of balance by "
            )
        
        # Equity position
        if bs.total_assets > 0:
            equity_pct = float(bs.total_equity / bs.total_assets * 100)
            insights.append(
                f"Equity ratio of {equity_pct:.1f}% shows "
                f"{'strong' if equity_pct > 50 else 'moderate' if equity_pct > 30 else 'weak'} capital position"
            )
        
        return insights
    
    async def _calculate_balance_sheet_health(self, bs: BalanceSheet) -> float:
        """Calculate overall balance sheet health score (0-100)"""
        
        score = 100.0
        
        # Deduct for imbalance
        if not bs.is_balanced:
            score -= 50.0
        
        # Check liquidity
        if bs.total_assets > 0:
            current_ratio = bs.current_assets[0].amount / bs.current_liabilities[0].amount if bs.current_liabilities[0].amount > 0 else 0
            if current_ratio < 1.0:
                score -= 20.0
            elif current_ratio < 1.5:
                score -= 10.0
        
        # Check leverage
        if bs.total_assets > 0:
            debt_ratio = bs.total_liabilities / bs.total_assets
            if debt_ratio > 0.8:
                score -= 20.0
            elif debt_ratio > 0.6:
                score -= 10.0
        
        return max(0.0, score)
    
    async def _generate_pl_insights(self, pl: ProfitLossStatement) -> List[str]:
        """Generate AI insights for P&L"""
        
        insights = []
        
        # Profitability
        if pl.net_income > 0:
            insights.append(
                f"Net income of  with {pl.net_margin_percent:.1f}% margin "
                f"indicates {'strong' if pl.net_margin_percent > 20 else 'moderate' if pl.net_margin_percent > 10 else 'low'} profitability"
            )
        else:
            insights.append(f"⚠️ Net loss of  requires attention")
        
        # Revenue vs expenses
        if pl.total_revenue > 0:
            expense_ratio = float(pl.total_expenses / pl.total_revenue * 100)
            insights.append(
                f"Operating expenses at {expense_ratio:.1f}% of revenue - "
                f"{'efficient' if expense_ratio < 70 else 'moderate' if expense_ratio < 85 else 'high cost structure'}"
            )
        
        return insights
    
    async def _calculate_profitability_score(self, pl: ProfitLossStatement) -> float:
        """Calculate profitability health score"""
        
        score = 50.0  # Base score
        
        # Positive net income
        if pl.net_income > 0:
            score += 25.0
        
        # Margin quality
        if pl.net_margin_percent > 20:
            score += 25.0
        elif pl.net_margin_percent > 10:
            score += 15.0
        elif pl.net_margin_percent > 5:
            score += 5.0
        
        return min(100.0, score)
    
    async def _generate_cashflow_insights(self, cf: CashFlowStatement) -> List[str]:
        """Generate cashflow insights"""
        
        insights = []
        
        # Operating cash flow
        if cf.net_cash_from_operations > 0:
            insights.append(
                f"Positive operating cash flow of  "
                f"demonstrates strong cash generation"
            )
        else:
            insights.append(
                f"⚠️ Negative operating cash flow of  "
                f"may indicate liquidity concerns"
            )
        
        # Cash change
        if cf.net_change_in_cash > 0:
            insights.append(f"Cash increased by  during the period")
        else:
            insights.append(f"Cash decreased by ")
        
        return insights
    
    async def _calculate_liquidity_score(self, cf: CashFlowStatement) -> float:
        """Calculate liquidity score"""
        
        score = 50.0
        
        # Operating cash flow
        if cf.net_cash_from_operations > 0:
            score += 30.0
        
        # Net cash increase
        if cf.net_change_in_cash > 0:
            score += 20.0
        
        return min(100.0, score)


# ============================================================================
# Global Financial Statements Generator
# ============================================================================

_statements_generator: Optional[FinancialStatementsGenerator] = None

def get_statements_generator() -> FinancialStatementsGenerator:
    """Get the singleton statements generator"""
    global _statements_generator
    if _statements_generator is None:
        _statements_generator = FinancialStatementsGenerator()
    return _statements_generator

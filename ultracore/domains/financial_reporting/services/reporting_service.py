"""
Financial Reporting Service
Generates financial statements and reports
"""

from typing import List, Dict, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging

from ultracore.domains.financial_reporting.models.chart_of_accounts import (
    ChartOfAccounts,
    Account,
    AccountType,
    AccountSubType,
)
from ultracore.domains.financial_reporting.models.financial_statements import (
    FinancialYear,
    BalanceSheet,
    BalanceSheetLine,
    IncomeStatement,
    IncomeStatementLine,
    CashFlowStatement,
    CashFlowLine,
    FinancialRatios,
)

logger = logging.getLogger(__name__)


class FinancialReportingService:
    """
    Financial Reporting Service
    
    Generates financial statements and reports optimized for
    Australian accounting standards (AASB) and APRA prudential reporting
    """
    
    def __init__(self, chart_of_accounts: ChartOfAccounts):
        self.coa = chart_of_accounts
    
    def generate_balance_sheet(
        self,
        as_of_date: date,
        financial_year: Optional[FinancialYear] = None
    ) -> BalanceSheet:
        """
        Generate Balance Sheet (Statement of Financial Position)
        AASB 101 - Australian format
        
        Args:
            as_of_date: Balance sheet date
            financial_year: Financial year configuration
        
        Returns:
            Balance sheet
        """
        if financial_year is None:
            # Default to Australian FY
            financial_year = FinancialYear.australian_fy(as_of_date.year)
        
        bs = BalanceSheet(
            tenant_id=self.coa.tenant_id,
            as_of_date=as_of_date,
            financial_year=financial_year,
        )
        
        # CURRENT ASSETS
        cash_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.CASH and acc.is_active
        ]
        for acc in cash_accounts:
            bs.current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        current_loans = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.LOANS
            and acc.account_code.startswith("11")  # Current portion
            and acc.is_active
        ]
        for acc in current_loans:
            bs.current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        receivables = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.RECEIVABLES and acc.is_active
        ]
        for acc in receivables:
            bs.current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # NON-CURRENT ASSETS
        non_current_loans = [
            acc for acc in self.coa.accounts
            if acc.account_subtype in [AccountSubType.NON_CURRENT_ASSET]
            and acc.account_code.startswith("12")  # Non-current loans
            and acc.is_active
        ]
        for acc in non_current_loans:
            bs.non_current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        ppe = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.PPE and acc.is_active
        ]
        for acc in ppe:
            bs.non_current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        intangibles = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.INTANGIBLES and acc.is_active
        ]
        for acc in intangibles:
            bs.non_current_assets.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # CURRENT LIABILITIES
        current_deposits = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.DEPOSITS
            and acc.account_code.startswith("20")  # Current deposits
            and acc.is_active
        ]
        for acc in current_deposits:
            bs.current_liabilities.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        payables = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.PAYABLES and acc.is_active
        ]
        for acc in payables:
            bs.current_liabilities.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # NON-CURRENT LIABILITIES
        non_current_deposits = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.DEPOSITS
            and acc.account_code.startswith("22")  # Non-current deposits
            and acc.is_active
        ]
        for acc in non_current_deposits:
            bs.non_current_liabilities.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        borrowings = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.BORROWINGS and acc.is_active
        ]
        for acc in borrowings:
            bs.non_current_liabilities.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        provisions = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.PROVISIONS and acc.is_active
        ]
        for acc in provisions:
            bs.non_current_liabilities.append(BalanceSheetLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # EQUITY
        equity_accounts = self.coa.get_accounts_by_type(AccountType.EQUITY)
        for acc in equity_accounts:
            if acc.is_active:
                bs.equity_lines.append(BalanceSheetLine(
                    account_code=acc.account_code,
                    account_name=acc.account_name,
                    amount=acc.current_balance,
                    level=acc.level,
                ))
        
        # Calculate totals
        bs.calculate_totals()
        
        logger.info(
            f"Balance Sheet generated: Assets=${bs.total_assets}, "
            f"Liabilities=${bs.total_liabilities}, Equity=${bs.total_equity}, "
            f"Balanced={bs.is_balanced}"
        )
        
        return bs
    
    def generate_income_statement(
        self,
        period_start: date,
        period_end: date,
        financial_year: Optional[FinancialYear] = None
    ) -> IncomeStatement:
        """
        Generate Income Statement (Profit & Loss)
        AASB 101 - Australian format
        
        Args:
            period_start: Period start date
            period_end: Period end date
            financial_year: Financial year configuration
        
        Returns:
            Income statement
        """
        if financial_year is None:
            financial_year = FinancialYear.australian_fy(period_end.year)
        
        pnl = IncomeStatement(
            tenant_id=self.coa.tenant_id,
            period_start=period_start,
            period_end=period_end,
            financial_year=financial_year,
        )
        
        # INTEREST INCOME
        interest_income_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.INTEREST_INCOME and acc.is_active
        ]
        for acc in interest_income_accounts:
            pnl.interest_income_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # FEE INCOME
        fee_income_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.FEE_INCOME and acc.is_active
        ]
        for acc in fee_income_accounts:
            pnl.fee_income_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # OTHER INCOME
        other_income_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.OTHER_INCOME and acc.is_active
        ]
        for acc in other_income_accounts:
            pnl.other_income_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # INTEREST EXPENSE
        interest_expense_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.INTEREST_EXPENSE and acc.is_active
        ]
        for acc in interest_expense_accounts:
            pnl.interest_expense_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # OPERATING EXPENSES
        operating_expense_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.OPERATING_EXPENSE and acc.is_active
        ]
        for acc in operating_expense_accounts:
            pnl.operating_expense_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # LOAN LOSS PROVISIONS
        loan_loss_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.LOAN_LOSS_PROVISION and acc.is_active
        ]
        for acc in loan_loss_accounts:
            pnl.loan_loss_provision_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # DEPRECIATION
        depreciation_accounts = [
            acc for acc in self.coa.accounts
            if acc.account_subtype == AccountSubType.DEPRECIATION and acc.is_active
        ]
        for acc in depreciation_accounts:
            pnl.depreciation_lines.append(IncomeStatementLine(
                account_code=acc.account_code,
                account_name=acc.account_name,
                amount=acc.current_balance,
                level=acc.level,
            ))
        
        # Calculate totals
        pnl.calculate_totals()
        
        logger.info(
            f"Income Statement generated: Revenue=${pnl.total_revenue}, "
            f"Expenses=${pnl.total_expenses}, Net Profit=${pnl.net_profit_after_tax}"
        )
        
        return pnl
    
    def calculate_financial_ratios(
        self,
        balance_sheet: BalanceSheet,
        income_statement: IncomeStatement,
        total_loans: Decimal,
        non_performing_loans: Decimal,
        provisions: Decimal,
        risk_weighted_assets: Decimal,
        cet1_capital: Decimal,
        tier1_capital: Decimal,
        total_capital: Decimal
    ) -> FinancialRatios:
        """
        Calculate financial ratios and KPIs
        
        Args:
            balance_sheet: Balance sheet
            income_statement: Income statement
            total_loans: Total loan portfolio
            non_performing_loans: Non-performing loans
            provisions: Loan loss provisions
            risk_weighted_assets: Risk-weighted assets (RWA)
            cet1_capital: Common Equity Tier 1 capital
            tier1_capital: Tier 1 capital
            total_capital: Total capital
        
        Returns:
            Financial ratios
        """
        ratios = FinancialRatios(
            tenant_id=self.coa.tenant_id,
            as_of_date=balance_sheet.as_of_date,
        )
        
        # Profitability Ratios
        if balance_sheet.total_assets > 0:
            ratios.net_interest_margin = (
                income_statement.net_interest_income / balance_sheet.total_assets * 100
            )
            ratios.return_on_assets = (
                income_statement.net_profit_after_tax / balance_sheet.total_assets * 100
            )
        
        if balance_sheet.total_equity > 0:
            ratios.return_on_equity = (
                income_statement.net_profit_after_tax / balance_sheet.total_equity * 100
            )
        
        if income_statement.operating_income > 0:
            ratios.cost_to_income_ratio = (
                income_statement.total_operating_expenses / income_statement.operating_income * 100
            )
        
        # Asset Quality Ratios
        if total_loans > 0:
            ratios.non_performing_loan_ratio = (non_performing_loans / total_loans * 100)
            ratios.loan_loss_rate = (
                income_statement.total_loan_loss_provisions / total_loans * 100
            )
        
        if non_performing_loans > 0:
            ratios.provision_coverage_ratio = (provisions / non_performing_loans * 100)
        
        # Liquidity Ratios
        total_deposits = balance_sheet.total_current_liabilities  # Simplified
        if total_deposits > 0:
            ratios.loan_to_deposit_ratio = (total_loans / total_deposits * 100)
        
        if balance_sheet.total_current_liabilities > 0:
            cash_balance = sum(
                line.amount for line in balance_sheet.current_assets
                if "Cash" in line.account_name
            )
            ratios.cash_ratio = (cash_balance / balance_sheet.total_current_liabilities * 100)
        
        # Capital Ratios (APRA APS 110)
        if risk_weighted_assets > 0:
            ratios.cet1_ratio = (cet1_capital / risk_weighted_assets * 100)
            ratios.tier1_ratio = (tier1_capital / risk_weighted_assets * 100)
            ratios.total_capital_ratio = (total_capital / risk_weighted_assets * 100)
        
        if balance_sheet.total_assets > 0:
            ratios.leverage_ratio = (tier1_capital / balance_sheet.total_assets * 100)
        
        logger.info(
            f"Financial Ratios calculated: NIM={ratios.net_interest_margin}%, "
            f"ROA={ratios.return_on_assets}%, ROE={ratios.return_on_equity}%, "
            f"CET1={ratios.cet1_ratio}%"
        )
        
        return ratios

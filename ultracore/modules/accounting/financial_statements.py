"""
Financial Statements
Balance Sheet, Income Statement (P&L), Cash Flow Statement
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts, AccountType
from ultracore.modules.accounting.general_ledger import general_ledger

class FinancialStatements:
    """
    Generate financial statements
    """
    
    def generate_balance_sheet(
        self,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate Balance Sheet
        Assets = Liabilities + Equity
        """
        
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)
        
        # Assets
        asset_accounts = chart_of_accounts.get_accounts_by_type(AccountType.ASSET)
        assets = []
        total_assets = 0.0
        
        for account in asset_accounts:
            balance = general_ledger.get_account_balance(
                account.account_number,
                as_of_date
            )
            
            if balance != 0:
                assets.append({
                    "account_number": account.account_number,
                    "account_name": account.name,
                    "balance": balance
                })
                total_assets += balance
        
        # Liabilities
        liability_accounts = chart_of_accounts.get_accounts_by_type(AccountType.LIABILITY)
        liabilities = []
        total_liabilities = 0.0
        
        for account in liability_accounts:
            balance = general_ledger.get_account_balance(
                account.account_number,
                as_of_date
            )
            
            if balance != 0:
                liabilities.append({
                    "account_number": account.account_number,
                    "account_name": account.name,
                    "balance": balance
                })
                total_liabilities += balance
        
        # Equity
        equity_accounts = chart_of_accounts.get_accounts_by_type(AccountType.EQUITY)
        equity = []
        total_equity = 0.0
        
        for account in equity_accounts:
            balance = general_ledger.get_account_balance(
                account.account_number,
                as_of_date
            )
            
            if balance != 0:
                equity.append({
                    "account_number": account.account_number,
                    "account_name": account.name,
                    "balance": balance
                })
                total_equity += balance
        
        # Calculate net income and add to equity
        net_income = self._calculate_net_income(as_of_date)
        total_equity += net_income
        
        return {
            "statement": "Balance Sheet",
            "as_of_date": as_of_date.isoformat(),
            "assets": {
                "accounts": assets,
                "total": total_assets
            },
            "liabilities": {
                "accounts": liabilities,
                "total": total_liabilities
            },
            "equity": {
                "accounts": equity,
                "net_income": net_income,
                "total": total_equity
            },
            "total_liabilities_and_equity": total_liabilities + total_equity,
            "in_balance": abs(total_assets - (total_liabilities + total_equity)) < 0.01
        }
    
    def generate_income_statement(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate Income Statement (P&L)
        Revenue - Expenses = Net Income
        """
        
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Revenue
        revenue_accounts = chart_of_accounts.get_accounts_by_type(AccountType.REVENUE)
        revenue = []
        total_revenue = 0.0
        
        for account in revenue_accounts:
            # Get entries in period
            entries = general_ledger.get_account_ledger(
                account.account_number,
                start_date,
                end_date
            )
            
            period_total = sum(e["credit"] - e["debit"] for e in entries)
            
            if period_total != 0:
                revenue.append({
                    "account_number": account.account_number,
                    "account_name": account.name,
                    "amount": period_total
                })
                total_revenue += period_total
        
        # Expenses
        expense_accounts = chart_of_accounts.get_accounts_by_type(AccountType.EXPENSE)
        expenses = []
        total_expenses = 0.0
        
        for account in expense_accounts:
            entries = general_ledger.get_account_ledger(
                account.account_number,
                start_date,
                end_date
            )
            
            period_total = sum(e["debit"] - e["credit"] for e in entries)
            
            if period_total != 0:
                expenses.append({
                    "account_number": account.account_number,
                    "account_name": account.name,
                    "amount": period_total
                })
                total_expenses += period_total
        
        net_income = total_revenue - total_expenses
        
        return {
            "statement": "Income Statement",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "revenue": {
                "accounts": revenue,
                "total": total_revenue
            },
            "expenses": {
                "accounts": expenses,
                "total": total_expenses
            },
            "net_income": net_income,
            "profit_margin": (net_income / total_revenue * 100) if total_revenue > 0 else 0
        }
    
    def generate_cash_flow_statement(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate Cash Flow Statement
        Operating, Investing, Financing activities
        """
        
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Get cash account
        cash_account = chart_of_accounts.get_account("1000")
        
        # Get all cash entries in period
        cash_entries = general_ledger.get_account_ledger(
            "1000",
            start_date,
            end_date
        )
        
        # Categorize cash flows
        operating_activities = []
        investing_activities = []
        financing_activities = []
        
        operating_total = 0.0
        investing_total = 0.0
        financing_total = 0.0
        
        for entry in cash_entries:
            amount = entry["debit"] - entry["credit"]
            
            # Categorize based on description or related accounts
            # This is simplified - in production would need more sophisticated logic
            
            if "settlement" in entry["description"].lower():
                operating_activities.append({
                    "description": entry["description"],
                    "amount": amount
                })
                operating_total += amount
            elif "investment" in entry["description"].lower():
                investing_activities.append({
                    "description": entry["description"],
                    "amount": amount
                })
                investing_total += amount
            else:
                operating_activities.append({
                    "description": entry["description"],
                    "amount": amount
                })
                operating_total += amount
        
        # Calculate net change
        net_change = operating_total + investing_total + financing_total
        
        # Get beginning and ending cash balance
        beginning_balance = general_ledger.get_account_balance("1000", start_date)
        ending_balance = general_ledger.get_account_balance("1000", end_date)
        
        return {
            "statement": "Cash Flow Statement",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "operating_activities": {
                "activities": operating_activities,
                "total": operating_total
            },
            "investing_activities": {
                "activities": investing_activities,
                "total": investing_total
            },
            "financing_activities": {
                "activities": financing_activities,
                "total": financing_total
            },
            "net_change_in_cash": net_change,
            "beginning_cash_balance": beginning_balance,
            "ending_cash_balance": ending_balance
        }
    
    def _calculate_net_income(self, as_of_date: datetime) -> float:
        """Calculate net income up to date"""
        
        # Get year-to-date income
        start_of_year = datetime(as_of_date.year, 1, 1)
        
        income_stmt = self.generate_income_statement(start_of_year, as_of_date)
        
        return income_stmt["net_income"]

# Global instance
financial_statements = FinancialStatements()

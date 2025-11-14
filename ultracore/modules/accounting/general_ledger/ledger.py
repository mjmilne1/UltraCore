"""
General Ledger & Trial Balance
Complete ledger with trial balance generation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts, AccountType
from ultracore.modules.accounting.journal_entry import journal_entry_service
from datetime import timezone

class GeneralLedger:
    """
    General Ledger - aggregates all journal entries by account
    """
    
    def __init__(self):
        self.ledger = {}  # {account_number: [entries]}
    
    def post_journal_entry(self, entry):
        """Post journal entry to ledger"""
        
        for line in entry.lines:
            account_number = line.account_number
            
            if account_number not in self.ledger:
                self.ledger[account_number] = []
            
            self.ledger[account_number].append({
                "entry_id": entry.entry_id,
                "date": entry.date.isoformat(),
                "description": line.description or entry.description,
                "debit": line.debit,
                "credit": line.credit,
                "balance": 0  # Calculated later
            })
    
    def get_account_ledger(
        self,
        account_number: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ledger entries for specific account
        Calculates running balance
        """
        
        entries = self.ledger.get(account_number, [])
        
        # Filter by date if provided
        if start_date:
            entries = [
                e for e in entries
                if datetime.fromisoformat(e["date"]) >= start_date
            ]
        
        if end_date:
            entries = [
                e for e in entries
                if datetime.fromisoformat(e["date"]) <= end_date
            ]
        
        # Sort by date
        entries = sorted(entries, key=lambda x: x["date"])
        
        # Calculate running balance
        account = chart_of_accounts.get_account(account_number)
        balance = 0
        
        for entry in entries:
            if entry["debit"] > 0:
                if account.normal_balance.value == "debit":
                    balance += entry["debit"]
                else:
                    balance -= entry["debit"]
            else:
                if account.normal_balance.value == "credit":
                    balance += entry["credit"]
                else:
                    balance -= entry["credit"]
            
            entry["balance"] = balance
        
        return entries
    
    def get_account_balance(
        self,
        account_number: str,
        as_of_date: Optional[datetime] = None
    ) -> float:
        """Get account balance as of date"""
        
        entries = self.get_account_ledger(account_number, end_date=as_of_date)
        
        if not entries:
            return 0.0
        
        return entries[-1]["balance"]
    
    def generate_trial_balance(
        self,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate trial balance
        Lists all accounts with debit/credit balances
        """
        
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)
        
        trial_balance = []
        total_debits = 0.0
        total_credits = 0.0
        
        for account in chart_of_accounts.get_all_accounts():
            if not account.is_active:
                continue
            
            balance = self.get_account_balance(account.account_number, as_of_date)
            
            # Determine if balance is debit or credit
            if balance == 0:
                continue
            
            if balance > 0:
                if account.normal_balance.value == "debit":
                    debit_balance = balance
                    credit_balance = 0
                else:
                    debit_balance = 0
                    credit_balance = balance
            else:
                # Negative balance (opposite of normal)
                if account.normal_balance.value == "debit":
                    debit_balance = 0
                    credit_balance = abs(balance)
                else:
                    debit_balance = abs(balance)
                    credit_balance = 0
            
            trial_balance.append({
                "account_number": account.account_number,
                "account_name": account.name,
                "account_type": account.account_type,
                "debit": debit_balance,
                "credit": credit_balance
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
        
        # Sort by account number
        trial_balance = sorted(trial_balance, key=lambda x: x["account_number"])
        
        return {
            "as_of_date": as_of_date.isoformat(),
            "accounts": trial_balance,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "in_balance": abs(total_debits - total_credits) < 0.01,
            "difference": total_debits - total_credits
        }
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get summary of all accounts"""
        
        summary = {
            "total_accounts": len(chart_of_accounts.get_all_accounts()),
            "by_type": {}
        }
        
        for account_type in AccountType:
            accounts = chart_of_accounts.get_accounts_by_type(account_type)
            total_balance = sum(
                self.get_account_balance(acc.account_number)
                for acc in accounts
            )
            
            summary["by_type"][account_type.value] = {
                "count": len(accounts),
                "total_balance": total_balance
            }
        
        return summary

# Global instance
general_ledger = GeneralLedger()

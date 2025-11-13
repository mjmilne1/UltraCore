"""
Journal Entry System
Double-entry bookkeeping with validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts, NormalBalance

class JournalEntryLine:
    """Individual line in journal entry (debit or credit)"""
    
    def __init__(
        self,
        account_number: str,
        debit: float = 0.0,
        credit: float = 0.0,
        description: str = ""
    ):
        self.account_number = account_number
        self.debit = debit
        self.credit = credit
        self.description = description
        
        # Validate
        if debit > 0 and credit > 0:
            raise ValueError("Entry cannot have both debit and credit")
        
        if debit == 0 and credit == 0:
            raise ValueError("Entry must have either debit or credit")
    
    def get_amount(self) -> float:
        """Get absolute amount"""
        return self.debit if self.debit > 0 else self.credit
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_number": self.account_number,
            "debit": self.debit,
            "credit": self.credit,
            "description": self.description
        }

class JournalEntry:
    """
    Complete journal entry with multiple lines
    Enforces double-entry bookkeeping (debits = credits)
    """
    
    def __init__(
        self,
        entry_id: str,
        date: datetime,
        description: str,
        reference: str = "",
        source_type: str = "",
        source_id: str = ""
    ):
        self.entry_id = entry_id
        self.date = date
        self.description = description
        self.reference = reference
        self.source_type = source_type  # e.g., "trade", "settlement", "fee"
        self.source_id = source_id      # e.g., trade_id, settlement_id
        self.lines = []
        self.is_posted = False
        self.posted_at = None
        self.created_at = datetime.now(timezone.utc).isoformat()
    
    def add_line(self, line: JournalEntryLine):
        """Add line to journal entry"""
        
        # Validate account exists
        account = chart_of_accounts.get_account(line.account_number)
        if not account:
            raise ValueError(f"Account {line.account_number} not found")
        
        self.lines.append(line)
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate journal entry
        Ensures debits = credits
        """
        
        if len(self.lines) < 2:
            return {
                "valid": False,
                "error": "Journal entry must have at least 2 lines"
            }
        
        total_debits = sum(line.debit for line in self.lines)
        total_credits = sum(line.credit for line in self.lines)
        
        if abs(total_debits - total_credits) > 0.01:  # Allow tiny rounding
            return {
                "valid": False,
                "error": f"Debits ({total_debits}) != Credits ({total_credits})",
                "difference": total_debits - total_credits
            }
        
        return {
            "valid": True,
            "total_debits": total_debits,
            "total_credits": total_credits
        }
    
    def post(self):
        """
        Post journal entry to general ledger
        Updates account balances
        """
        
        if self.is_posted:
            raise ValueError("Entry already posted")
        
        # Validate first
        validation = self.validate()
        if not validation["valid"]:
            raise ValueError(f"Cannot post invalid entry: {validation['error']}")
        
        # Update account balances
        for line in self.lines:
            account = chart_of_accounts.get_account(line.account_number)
            
            if line.debit > 0:
                # Debit increases assets/expenses, decreases liabilities/equity/revenue
                if account.normal_balance == NormalBalance.DEBIT:
                    chart_of_accounts.update_account_balance(line.account_number, line.debit)
                else:
                    chart_of_accounts.update_account_balance(line.account_number, -line.debit)
            else:
                # Credit increases liabilities/equity/revenue, decreases assets/expenses
                if account.normal_balance == NormalBalance.CREDIT:
                    chart_of_accounts.update_account_balance(line.account_number, line.credit)
                else:
                    chart_of_accounts.update_account_balance(line.account_number, -line.credit)
        
        self.is_posted = True
        self.posted_at = datetime.now(timezone.utc).isoformat()
    
    def reverse(self) -> 'JournalEntry':
        """
        Create reversing entry
        """
        
        if not self.is_posted:
            raise ValueError("Cannot reverse unposted entry")
        
        reversing_entry = JournalEntry(
            entry_id=f"{self.entry_id}-REV",
            date=datetime.now(timezone.utc),
            description=f"REVERSAL: {self.description}",
            reference=self.reference,
            source_type=self.source_type,
            source_id=self.source_id
        )
        
        # Reverse all lines (swap debits and credits)
        for line in self.lines:
            reversing_entry.add_line(JournalEntryLine(
                account_number=line.account_number,
                debit=line.credit,  # Swap
                credit=line.debit,  # Swap
                description=f"Reversal: {line.description}"
            ))
        
        return reversing_entry
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "date": self.date.isoformat(),
            "description": self.description,
            "reference": self.reference,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "lines": [line.to_dict() for line in self.lines],
            "is_posted": self.is_posted,
            "posted_at": self.posted_at,
            "created_at": self.created_at
        }

class JournalEntryService:
    """
    Service for managing journal entries
    """
    
    def __init__(self):
        self.entries = {}
        self.entry_counter = 0
    
    def create_entry(
        self,
        description: str,
        date: Optional[datetime] = None,
        reference: str = "",
        source_type: str = "",
        source_id: str = ""
    ) -> JournalEntry:
        """Create new journal entry"""
        
        if date is None:
            date = datetime.now(timezone.utc)
        
        self.entry_counter += 1
        entry_id = f"JE-{self.entry_counter:08d}"
        
        entry = JournalEntry(
            entry_id=entry_id,
            date=date,
            description=description,
            reference=reference,
            source_type=source_type,
            source_id=source_id
        )
        
        self.entries[entry_id] = entry
        
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get journal entry"""
        return self.entries.get(entry_id)
    
    def get_entries_by_account(
        self,
        account_number: str
    ) -> List[JournalEntry]:
        """Get all entries affecting an account"""
        
        return [
            entry for entry in self.entries.values()
            if any(line.account_number == account_number for line in entry.lines)
        ]
    
    def get_entries_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[JournalEntry]:
        """Get entries within date range"""
        
        return [
            entry for entry in self.entries.values()
            if start_date <= entry.date <= end_date
        ]
    
    def get_all_entries(self) -> List[JournalEntry]:
        """Get all journal entries"""
        return list(self.entries.values())

# Global instance
journal_entry_service = JournalEntryService()

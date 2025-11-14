"""
Journal Service for General Ledger
Handles journal entries and posting to the general ledger
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum


class JournalEntryStatus(str, Enum):
    """Status of a journal entry"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    VOID = "VOID"


@dataclass
class JournalLine:
    """A single line in a journal entry"""
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    description: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate the journal line"""
        if self.debit < 0 or self.credit < 0:
            raise ValueError("Debit and credit amounts must be non-negative")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line cannot have both debit and credit")
        return True


@dataclass
class JournalEntry:
    """A complete journal entry"""
    entry_id: str
    entry_date: datetime
    description: str
    lines: List[JournalLine]
    status: JournalEntryStatus = JournalEntryStatus.DRAFT
    posted_date: Optional[datetime] = None
    reference: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate the journal entry"""
        # Validate all lines
        for line in self.lines:
            line.validate()
        
        # Check that debits equal credits
        total_debits = sum(line.debit for line in self.lines)
        total_credits = sum(line.credit for line in self.lines)
        
        if total_debits != total_credits:
            raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")
        
        # Must have at least 2 lines
        if len(self.lines) < 2:
            raise ValueError("Journal entry must have at least 2 lines")
        
        return True


class JournalService:
    """Service for managing journal entries"""
    
    def __init__(self):
        self.entries: Dict[str, JournalEntry] = {}
        self._next_id = 1
    
    def create_entry(
        self,
        description: str,
        lines: List[Dict[str, Any]],
        entry_date: Optional[datetime] = None,
        reference: Optional[str] = None
    ) -> JournalEntry:
        """Create a new journal entry"""
        if entry_date is None:
            entry_date = datetime.now(timezone.utc)
        
        # Convert dict lines to JournalLine objects
        journal_lines = [
            JournalLine(
                account_code=line['account_code'],
                account_name=line['account_name'],
                debit=Decimal(str(line.get('debit', 0))),
                credit=Decimal(str(line.get('credit', 0))),
                description=line.get('description')
            )
            for line in lines
        ]
        
        entry_id = f"JE{self._next_id:06d}"
        self._next_id += 1
        
        entry = JournalEntry(
            entry_id=entry_id,
            entry_date=entry_date,
            description=description,
            lines=journal_lines,
            reference=reference
        )
        
        # Validate before saving
        entry.validate()
        
        self.entries[entry_id] = entry
        return entry
    
    def post_entry(self, entry_id: str) -> JournalEntry:
        """Post a journal entry to the general ledger"""
        entry = self.entries.get(entry_id)
        if not entry:
            raise ValueError(f"Journal entry {entry_id} not found")
        
        if entry.status != JournalEntryStatus.DRAFT:
            raise ValueError(f"Only DRAFT entries can be posted. Current status: {entry.status}")
        
        # Validate again before posting
        entry.validate()
        
        entry.status = JournalEntryStatus.POSTED
        entry.posted_date = datetime.now(timezone.utc)
        
        return entry
    
    def reverse_entry(self, entry_id: str, reversal_date: Optional[datetime] = None) -> JournalEntry:
        """Reverse a posted journal entry"""
        original_entry = self.entries.get(entry_id)
        if not original_entry:
            raise ValueError(f"Journal entry {entry_id} not found")
        
        if original_entry.status != JournalEntryStatus.POSTED:
            raise ValueError(f"Only POSTED entries can be reversed. Current status: {original_entry.status}")
        
        if reversal_date is None:
            reversal_date = datetime.now(timezone.utc)
        
        # Create reversal lines (swap debits and credits)
        reversal_lines = [
            {
                'account_code': line.account_code,
                'account_name': line.account_name,
                'debit': float(line.credit),
                'credit': float(line.debit),
                'description': f"Reversal of {entry_id}"
            }
            for line in original_entry.lines
        ]
        
        # Create reversal entry
        reversal_entry = self.create_entry(
            description=f"Reversal of {original_entry.description}",
            lines=reversal_lines,
            entry_date=reversal_date,
            reference=entry_id
        )
        
        # Post the reversal
        self.post_entry(reversal_entry.entry_id)
        
        # Mark original as reversed
        original_entry.status = JournalEntryStatus.REVERSED
        
        return reversal_entry
    
    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get a journal entry by ID"""
        return self.entries.get(entry_id)
    
    def list_entries(
        self,
        status: Optional[JournalEntryStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[JournalEntry]:
        """List journal entries with optional filters"""
        entries = list(self.entries.values())
        
        if status:
            entries = [e for e in entries if e.status == status]
        
        if from_date:
            entries = [e for e in entries if e.entry_date >= from_date]
        
        if to_date:
            entries = [e for e in entries if e.entry_date <= to_date]
        
        return sorted(entries, key=lambda e: e.entry_date, reverse=True)


# Global instance
journal_service = JournalService()

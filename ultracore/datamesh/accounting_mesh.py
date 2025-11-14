"""
Accounting Data Mesh
Data governance and quality for accounting data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class AccountingDataMesh:
    """
    Data Mesh for accounting data
    """
    
    def __init__(self):
        self.data_store = {}
        self.lineage_store = {}
        self.quality_metrics = {}
        self.materialized_views = {
            "account_balances": {},
            "journal_entries_by_date": {},
            "trial_balance_cache": None
        }
    
    async def ingest_journal_entry(
        self,
        entry_id: str,
        entry_data: Dict[str, Any],
        source: str,
        created_by: str
    ) -> Dict[str, Any]:
        """Ingest journal entry with lineage"""
        
        quality_score = self._calculate_journal_quality(entry_data)
        
        lineage = {
            "entry_id": entry_id,
            "source": source,
            "created_by": created_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quality_score": quality_score,
            "version": len(self.lineage_store.get(entry_id, [])) + 1
        }
        
        mesh_key = f"journal:{entry_id}"
        self.data_store[mesh_key] = {
            "data": entry_data,
            "metadata": lineage
        }
        
        if entry_id not in self.lineage_store:
            self.lineage_store[entry_id] = []
        self.lineage_store[entry_id].append(lineage)
        
        # Update materialized views
        await self._update_journal_views(entry_id, entry_data)
        
        return {
            "entry_id": entry_id,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "version": lineage["version"]
        }
    
    async def ingest_account_balance(
        self,
        account_number: str,
        balance: float,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """Ingest account balance snapshot"""
        
        key = f"{account_number}:{as_of_date.date().isoformat()}"
        
        self.materialized_views["account_balances"][key] = {
            "account_number": account_number,
            "balance": balance,
            "as_of_date": as_of_date.isoformat()
        }
        
        return {
            "account_number": account_number,
            "balance": balance,
            "cached": True
        }
    
    def query_journal_entry(
        self,
        entry_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Query journal entry"""
        
        mesh_key = f"journal:{entry_id}"
        stored = self.data_store.get(mesh_key)
        
        if not stored:
            return None
        
        result = stored["data"].copy()
        
        if include_lineage:
            result["_lineage"] = self.lineage_store.get(entry_id, [])
            result["_quality"] = stored["metadata"]["quality_score"]
        
        return result
    
    def get_cached_trial_balance(self) -> Optional[Dict[str, Any]]:
        """Get cached trial balance"""
        return self.materialized_views["trial_balance_cache"]
    
    def cache_trial_balance(self, trial_balance: Dict[str, Any]):
        """Cache trial balance"""
        self.materialized_views["trial_balance_cache"] = {
            **trial_balance,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _update_journal_views(
        self,
        entry_id: str,
        entry_data: Dict[str, Any]
    ):
        """Update materialized views for journals"""
        
        date = entry_data.get("date", datetime.now(timezone.utc).isoformat())
        date_key = date[:10]  # YYYY-MM-DD
        
        if date_key not in self.materialized_views["journal_entries_by_date"]:
            self.materialized_views["journal_entries_by_date"][date_key] = []
        
        self.materialized_views["journal_entries_by_date"][date_key].append(entry_data)
    
    def _calculate_journal_quality(self, entry_data: Dict[str, Any]) -> float:
        """Calculate journal entry quality"""
        
        required_fields = [
            "entry_id", "date", "description", "lines"
        ]
        
        optional_fields = [
            "reference", "source_type", "source_id"
        ]
        
        required_score = sum(
            1 for field in required_fields
            if entry_data.get(field) is not None
        ) / len(required_fields) * 70
        
        optional_score = sum(
            1 for field in optional_fields
            if entry_data.get(field) is not None
        ) / len(optional_fields) * 30
        
        # Check if lines balance
        lines = entry_data.get("lines", [])
        if lines:
            total_debits = sum(line.get("debit", 0) for line in lines)
            total_credits = sum(line.get("credit", 0) for line in lines)
            
            if abs(total_debits - total_credits) < 0.01:
                balance_bonus = 10
            else:
                balance_bonus = 0
        else:
            balance_bonus = 0
        
        return min(100, round(required_score + optional_score + balance_bonus, 2))
    
    def _get_quality_level(self, score: float) -> str:
        """Convert quality score to level"""
        if score >= 95:
            return "excellent"
        elif score >= 85:
            return "good"
        elif score >= 70:
            return "acceptable"
        else:
            return "poor"

# Global instance
accounting_data_mesh = AccountingDataMesh()

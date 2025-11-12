"""
Cash Reconciliation Module
Automated reconciliation of cash accounts
"""

from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

class CashReconciliationService:
    """
    Cash Reconciliation Service
    
    Features:
    - Daily reconciliation
    - Discrepancy detection
    - Bank statement matching
    - Break investigation
    - Automated adjustments
    """
    
    def __init__(self):
        self.reconciliations = []
        self.discrepancies = []
        
    def reconcile_account(
        self,
        account_id: str,
        ledger_balance: Decimal,
        bank_balance: Decimal,
        pending_deposits: Decimal,
        pending_withdrawals: Decimal
    ) -> Dict[str, Any]:
        """
        Reconcile cash account
        
        Reconciliation Formula:
        Ledger Balance + Pending Deposits - Pending Withdrawals = Bank Balance
        """
        
        # Calculate expected bank balance
        expected_bank_balance = ledger_balance + pending_deposits - pending_withdrawals
        
        # Calculate difference
        difference = bank_balance - expected_bank_balance
        
        reconciled = abs(difference) < Decimal("0.01")  # Reconciled if within 1 cent
        
        reconciliation = {
            "reconciliation_id": f"RECON-{len(self.reconciliations) + 1:08d}",
            "account_id": account_id,
            "reconciliation_date": datetime.utcnow().isoformat(),
            "ledger_balance": float(ledger_balance),
            "bank_balance": float(bank_balance),
            "pending_deposits": float(pending_deposits),
            "pending_withdrawals": float(pending_withdrawals),
            "expected_bank_balance": float(expected_bank_balance),
            "difference": float(difference),
            "reconciled": reconciled,
            "status": "reconciled" if reconciled else "discrepancy_found"
        }
        
        # Record discrepancy if found
        if not reconciled:
            discrepancy = {
                "discrepancy_id": f"DISC-{len(self.discrepancies) + 1:06d}",
                "reconciliation_id": reconciliation["reconciliation_id"],
                "account_id": account_id,
                "amount": float(difference),
                "detected_at": datetime.utcnow().isoformat(),
                "resolved": False,
                "resolution": None
            }
            
            self.discrepancies.append(discrepancy)
            reconciliation["discrepancy_id"] = discrepancy["discrepancy_id"]
        
        self.reconciliations.append(reconciliation)
        
        return reconciliation
    
    def investigate_discrepancy(
        self,
        discrepancy_id: str,
        investigation_notes: str
    ) -> Dict[str, Any]:
        """Investigate discrepancy"""
        
        discrepancy = next(
            (d for d in self.discrepancies if d["discrepancy_id"] == discrepancy_id),
            None
        )
        
        if not discrepancy:
            return {
                "success": False,
                "error": "Discrepancy not found"
            }
        
        # Common causes
        possible_causes = []
        
        amount = abs(discrepancy["amount"])
        
        if amount < 10:
            possible_causes.append("Rounding difference")
        
        if amount in [10, 20, 50, 100]:
            possible_causes.append("Manual entry error")
        
        possible_causes.append("Timing difference")
        possible_causes.append("Unrecorded transaction")
        possible_causes.append("Bank error")
        
        return {
            "success": True,
            "discrepancy": discrepancy,
            "investigation_notes": investigation_notes,
            "possible_causes": possible_causes,
            "recommended_actions": [
                "Review recent transactions",
                "Check bank statement",
                "Verify pending items",
                "Contact bank if necessary"
            ]
        }
    
    def resolve_discrepancy(
        self,
        discrepancy_id: str,
        resolution: str,
        adjustment_required: bool = False,
        adjustment_amount: Decimal = Decimal("0.00")
    ) -> Dict[str, Any]:
        """Resolve discrepancy"""
        
        discrepancy = next(
            (d for d in self.discrepancies if d["discrepancy_id"] == discrepancy_id),
            None
        )
        
        if not discrepancy:
            return {
                "success": False,
                "error": "Discrepancy not found"
            }
        
        discrepancy["resolved"] = True
        discrepancy["resolution"] = resolution
        discrepancy["resolved_at"] = datetime.utcnow().isoformat()
        
        if adjustment_required:
            discrepancy["adjustment_amount"] = float(adjustment_amount)
        
        return {
            "success": True,
            "discrepancy": discrepancy,
            "adjustment_required": adjustment_required
        }
    
    def get_reconciliation_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get reconciliation report"""
        
        period_recons = [
            r for r in self.reconciliations
            if start_date <= datetime.fromisoformat(r["reconciliation_date"]) <= end_date
        ]
        
        reconciled_count = sum(1 for r in period_recons if r["reconciled"])
        discrepancy_count = len(period_recons) - reconciled_count
        
        unresolved_discrepancies = [
            d for d in self.discrepancies
            if not d["resolved"]
            and start_date <= datetime.fromisoformat(d["detected_at"]) <= end_date
        ]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_reconciliations": len(period_recons),
            "reconciled": reconciled_count,
            "discrepancies_found": discrepancy_count,
            "reconciliation_rate": (reconciled_count / len(period_recons) * 100) if period_recons else 0,
            "unresolved_discrepancies": len(unresolved_discrepancies),
            "discrepancy_details": unresolved_discrepancies
        }

# Global reconciliation service
reconciliation_service = CashReconciliationService()

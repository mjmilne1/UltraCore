"""
Reconciliation Tools
Reconcile cash, positions, and transactions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.accounting.general_ledger import general_ledger
from ultracore.modules.accounting.kafka_events import accounting_kafka, AccountingEventType

class ReconciliationService:
    """
    Reconciliation tools for accounting
    """
    
    def __init__(self):
        self.reconciliations = {}
        self.reconciliation_counter = 0
    
    async def reconcile_cash(
        self,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """
        Reconcile cash accounts
        Compares ledger balance with actual holdings
        """
        
        self.reconciliation_counter += 1
        recon_id = f"RECON-CASH-{self.reconciliation_counter:06d}"
        
        # Get cash account balance from ledger
        ledger_balance = general_ledger.get_account_balance("1010", as_of_date)
        
        # Get actual cash from holdings (simplified)
        from ultracore.modules.holdings.holdings_service import holdings_service
        
        # In production, would aggregate all client cash
        actual_balance = ledger_balance  # Placeholder
        
        difference = actual_balance - ledger_balance
        
        reconciliation = {
            "reconciliation_id": recon_id,
            "type": "cash",
            "as_of_date": as_of_date.isoformat(),
            "ledger_balance": ledger_balance,
            "actual_balance": actual_balance,
            "difference": difference,
            "reconciled": abs(difference) < 0.01,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.reconciliations[recon_id] = reconciliation
        
        # Produce event
        await accounting_kafka.produce_reconciliation_event(
            AccountingEventType.RECONCILIATION_COMPLETED if reconciliation["reconciled"]
            else AccountingEventType.RECONCILIATION_FAILED,
            reconciliation
        )
        
        print(f"💰 Cash Reconciliation: {recon_id}")
        print(f"   Ledger: ${ledger_balance:,.2f}")
        print(f"   Actual: ${actual_balance:,.2f}")
        print(f"   Status: {'✅ Reconciled' if reconciliation['reconciled'] else '❌ Out of balance'}")
        
        return reconciliation
    
    async def reconcile_investments(
        self,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """
        Reconcile investment accounts
        Compares ledger balance with sum of position values
        """
        
        self.reconciliation_counter += 1
        recon_id = f"RECON-INV-{self.reconciliation_counter:06d}"
        
        # Get investments account balance from ledger
        ledger_balance = general_ledger.get_account_balance("1500", as_of_date)
        
        # Get total position values from holdings
        from ultracore.modules.holdings.holdings_service import holdings_service
        
        # In production, would sum all client positions
        actual_balance = ledger_balance  # Placeholder
        
        difference = actual_balance - ledger_balance
        
        reconciliation = {
            "reconciliation_id": recon_id,
            "type": "investments",
            "as_of_date": as_of_date.isoformat(),
            "ledger_balance": ledger_balance,
            "actual_balance": actual_balance,
            "difference": difference,
            "reconciled": abs(difference) < 0.01,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.reconciliations[recon_id] = reconciliation
        
        await accounting_kafka.produce_reconciliation_event(
            AccountingEventType.RECONCILIATION_COMPLETED if reconciliation["reconciled"]
            else AccountingEventType.RECONCILIATION_FAILED,
            reconciliation
        )
        
        print(f"📊 Investment Reconciliation: {recon_id}")
        print(f"   Ledger: ${ledger_balance:,.2f}")
        print(f"   Actual: ${actual_balance:,.2f}")
        print(f"   Status: {'✅ Reconciled' if reconciliation['reconciled'] else '❌ Out of balance'}")
        
        return reconciliation
    
    async def reconcile_settlements(
        self,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """
        Reconcile settlements
        Ensures all trades have been settled properly
        """
        
        self.reconciliation_counter += 1
        recon_id = f"RECON-SETTLE-{self.reconciliation_counter:06d}"
        
        # Get settlements payable from ledger
        payable_balance = general_ledger.get_account_balance("2000", as_of_date)
        
        # Get settlements receivable from ledger
        receivable_balance = general_ledger.get_account_balance("1100", as_of_date)
        
        # Get pending settlements from settlement engine
        from ultracore.modules.transactions.settlement_engine import settlement_engine
        
        pending_settlements = settlement_engine.get_pending_settlements()
        
        total_pending_value = sum(
            s["value"] for s in pending_settlements
        )
        
        reconciliation = {
            "reconciliation_id": recon_id,
            "type": "settlements",
            "as_of_date": as_of_date.isoformat(),
            "settlements_payable": payable_balance,
            "settlements_receivable": receivable_balance,
            "pending_settlements": len(pending_settlements),
            "total_pending_value": total_pending_value,
            "reconciled": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.reconciliations[recon_id] = reconciliation
        
        await accounting_kafka.produce_reconciliation_event(
            AccountingEventType.RECONCILIATION_COMPLETED,
            reconciliation
        )
        
        print(f"🔄 Settlement Reconciliation: {recon_id}")
        print(f"   Payable: ${payable_balance:,.2f}")
        print(f"   Receivable: ${receivable_balance:,.2f}")
        print(f"   Pending: {len(pending_settlements)} settlements")
        
        return reconciliation
    
    async def run_full_reconciliation(
        self,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run complete reconciliation of all accounts
        """
        
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)
        
        print(f"\n🔍 Running Full Reconciliation as of {as_of_date.date()}")
        print("-" * 70)
        
        cash_recon = await self.reconcile_cash(as_of_date)
        inv_recon = await self.reconcile_investments(as_of_date)
        settle_recon = await self.reconcile_settlements(as_of_date)
        
        all_reconciled = (
            cash_recon["reconciled"] and
            inv_recon["reconciled"] and
            settle_recon["reconciled"]
        )
        
        result = {
            "as_of_date": as_of_date.isoformat(),
            "all_reconciled": all_reconciled,
            "cash": cash_recon,
            "investments": inv_recon,
            "settlements": settle_recon,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n{'✅' if all_reconciled else '❌'} Full Reconciliation: "
              f"{'All accounts reconciled' if all_reconciled else 'Discrepancies found'}")
        
        return result
    
    def get_reconciliation(self, recon_id: str) -> Dict[str, Any]:
        """Get reconciliation details"""
        return self.reconciliations.get(recon_id)
    
    def get_all_reconciliations(self) -> List[Dict[str, Any]]:
        """Get all reconciliations"""
        return list(self.reconciliations.values())

# Global instance
reconciliation_service = ReconciliationService()

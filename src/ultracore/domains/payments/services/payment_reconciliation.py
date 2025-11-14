"""
Payment Reconciliation Service.

Handles payment reconciliation and discrepancy management.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import uuid4

from ..models.payment_batch import (
    PaymentReconciliation,
    ReconciliationStatus,
    ReconciliationDiscrepancy
)


class PaymentReconciliationService:
    """Service for reconciling payments."""
    
    def __init__(self):
        """Initialize reconciliation service."""
        pass
    
    async def create_reconciliation(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
        account_ids: Optional[List[str]] = None,
        payment_systems: Optional[List[str]] = None
    ) -> PaymentReconciliation:
        """
        Create a new reconciliation.
        
        Args:
            tenant_id: Tenant ID
            period_start: Period start date
            period_end: Period end date
            account_ids: Optional list of account IDs to reconcile
            payment_systems: Optional list of payment systems to reconcile
            
        Returns:
            Created reconciliation
        """
        reconciliation = PaymentReconciliation(
            reconciliation_id=str(uuid4()),
            tenant_id=tenant_id,
            reconciliation_date=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            account_ids=account_ids or [],
            payment_systems=payment_systems or [],
            status=ReconciliationStatus.PENDING
        )
        
        # TODO: Persist to database
        # TODO: Publish ReconciliationCreated event
        
        return reconciliation
    
    async def run_reconciliation(
        self,
        reconciliation_id: str
    ) -> Dict[str, Any]:
        """
        Run a reconciliation.
        
        Args:
            reconciliation_id: Reconciliation ID
            
        Returns:
            Reconciliation result
        """
        # TODO: Load reconciliation from database
        # For now, simulate
        reconciliation = await self._load_reconciliation(reconciliation_id)
        
        if reconciliation.status != ReconciliationStatus.PENDING:
            return {
                "success": False,
                "error": f"Reconciliation is not in pending status: {reconciliation.status}"
            }
        
        # Update status
        reconciliation.status = ReconciliationStatus.IN_PROGRESS
        # TODO: Update database
        
        try:
            # Get payments from our system
            our_payments = await self._get_our_payments(
                reconciliation.period_start,
                reconciliation.period_end,
                reconciliation.account_ids,
                reconciliation.payment_systems
            )
            
            # Get payments from external systems (bank statements, etc.)
            external_payments = await self._get_external_payments(
                reconciliation.period_start,
                reconciliation.period_end,
                reconciliation.account_ids,
                reconciliation.payment_systems
            )
            
            # Reconcile
            result = await self._reconcile_payments(
                our_payments,
                external_payments,
                reconciliation
            )
            
            # Update reconciliation
            reconciliation.total_payments = result["total_payments"]
            reconciliation.reconciled_payments = result["reconciled_payments"]
            reconciliation.unreconciled_payments = result["unreconciled_payments"]
            reconciliation.total_amount = result["total_amount"]
            reconciliation.reconciled_amount = result["reconciled_amount"]
            reconciliation.unreconciled_amount = result["unreconciled_amount"]
            reconciliation.discrepancies = result["discrepancies"]
            reconciliation.discrepancy_count = len(result["discrepancies"])
            
            # Determine final status
            if reconciliation.discrepancy_count == 0:
                reconciliation.status = ReconciliationStatus.COMPLETED
            else:
                reconciliation.status = ReconciliationStatus.REQUIRES_REVIEW
            
            reconciliation.completed_at = datetime.utcnow()
            
            # TODO: Update database
            # TODO: Publish ReconciliationCompleted event
            
            return {
                "success": True,
                "reconciliation": reconciliation,
                "summary": {
                    "total_payments": reconciliation.total_payments,
                    "reconciled": reconciliation.reconciled_payments,
                    "unreconciled": reconciliation.unreconciled_payments,
                    "discrepancies": reconciliation.discrepancy_count,
                    "status": reconciliation.status
                }
            }
            
        except Exception as e:
            reconciliation.status = ReconciliationStatus.FAILED
            # TODO: Update database
            # TODO: Publish ReconciliationFailed event
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _load_reconciliation(self, reconciliation_id: str) -> PaymentReconciliation:
        """Load reconciliation from database."""
        # TODO: Implement database query
        # For now, return mock
        return PaymentReconciliation(
            reconciliation_id=reconciliation_id,
            tenant_id="tenant-1",
            reconciliation_date=datetime.utcnow(),
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            status=ReconciliationStatus.PENDING
        )
    
    async def _get_our_payments(
        self,
        period_start: datetime,
        period_end: datetime,
        account_ids: List[str],
        payment_systems: List[str]
    ) -> List[Dict[str, Any]]:
        """Get payments from our system."""
        # TODO: Query database for payments in period
        # For now, return mock data
        return [
            {
                "payment_id": "pay-1",
                "amount": Decimal("100.00"),
                "reference": "REF001",
                "timestamp": period_start + timedelta(hours=1)
            },
            {
                "payment_id": "pay-2",
                "amount": Decimal("250.00"),
                "reference": "REF002",
                "timestamp": period_start + timedelta(hours=2)
            }
        ]
    
    async def _get_external_payments(
        self,
        period_start: datetime,
        period_end: datetime,
        account_ids: List[str],
        payment_systems: List[str]
    ) -> List[Dict[str, Any]]:
        """Get payments from external systems."""
        # TODO: Fetch from bank APIs, statement files, etc.
        # For now, return mock data
        return [
            {
                "external_id": "ext-1",
                "amount": Decimal("100.00"),
                "reference": "REF001",
                "timestamp": period_start + timedelta(hours=1)
            },
            {
                "external_id": "ext-2",
                "amount": Decimal("250.00"),
                "reference": "REF002",
                "timestamp": period_start + timedelta(hours=2)
            }
        ]
    
    async def _reconcile_payments(
        self,
        our_payments: List[Dict[str, Any]],
        external_payments: List[Dict[str, Any]],
        reconciliation: PaymentReconciliation
    ) -> Dict[str, Any]:
        """Reconcile our payments against external payments."""
        reconciled = []
        unreconciled_ours = []
        unreconciled_external = []
        discrepancies = []
        
        # Create lookup maps
        our_map = {p["reference"]: p for p in our_payments}
        external_map = {p["reference"]: p for p in external_payments}
        
        # Match payments by reference
        all_refs = set(our_map.keys()) | set(external_map.keys())
        
        for ref in all_refs:
            our_payment = our_map.get(ref)
            external_payment = external_map.get(ref)
            
            if our_payment and external_payment:
                # Both exist - check amount
                if our_payment["amount"] == external_payment["amount"]:
                    reconciled.append({
                        "reference": ref,
                        "amount": our_payment["amount"],
                        "our_id": our_payment["payment_id"],
                        "external_id": external_payment["external_id"]
                    })
                else:
                    # Amount mismatch
                    discrepancies.append(ReconciliationDiscrepancy(
                        discrepancy_id=str(uuid4()),
                        discrepancy_type="amount_mismatch",
                        payment_id=our_payment["payment_id"],
                        expected_amount=our_payment["amount"],
                        actual_amount=external_payment["amount"],
                        description=f"Amount mismatch for reference {ref}"
                    ))
            elif our_payment:
                # Only in our system
                unreconciled_ours.append(our_payment)
                discrepancies.append(ReconciliationDiscrepancy(
                    discrepancy_id=str(uuid4()),
                    discrepancy_type="missing_external",
                    payment_id=our_payment["payment_id"],
                    expected_amount=our_payment["amount"],
                    description=f"Payment {ref} not found in external system"
                ))
            else:
                # Only in external system
                unreconciled_external.append(external_payment)
                discrepancies.append(ReconciliationDiscrepancy(
                    discrepancy_id=str(uuid4()),
                    discrepancy_type="missing_internal",
                    actual_amount=external_payment["amount"],
                    description=f"External payment {ref} not found in our system"
                ))
        
        # Calculate totals
        total_amount = sum(p["amount"] for p in our_payments)
        reconciled_amount = sum(p["amount"] for p in reconciled)
        unreconciled_amount = total_amount - reconciled_amount
        
        return {
            "total_payments": len(our_payments),
            "reconciled_payments": len(reconciled),
            "unreconciled_payments": len(unreconciled_ours) + len(unreconciled_external),
            "total_amount": total_amount,
            "reconciled_amount": reconciled_amount,
            "unreconciled_amount": unreconciled_amount,
            "discrepancies": discrepancies
        }
    
    async def resolve_discrepancy(
        self,
        reconciliation_id: str,
        discrepancy_id: str,
        resolution_notes: str,
        resolved_by: str
    ) -> Dict[str, Any]:
        """
        Resolve a reconciliation discrepancy.
        
        Args:
            reconciliation_id: Reconciliation ID
            discrepancy_id: Discrepancy ID
            resolution_notes: Resolution notes
            resolved_by: User resolving the discrepancy
            
        Returns:
            Resolution result
        """
        # TODO: Load reconciliation and discrepancy
        # TODO: Update discrepancy status
        # TODO: Update database
        # TODO: Publish DiscrepancyResolved event
        
        return {
            "success": True,
            "discrepancy_id": discrepancy_id,
            "status": "resolved",
            "resolved_by": resolved_by,
            "resolved_at": datetime.utcnow()
        }

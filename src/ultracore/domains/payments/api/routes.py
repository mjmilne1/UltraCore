"""
Payment API Routes.

REST API endpoints for payment operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from .schemas import (
    CreatePaymentRequest,
    PaymentResponse,
    ListPaymentsRequest,
    CreatePaymentMethodRequest,
    PaymentMethodResponse,
    CreateScheduleRequest,
    ScheduleResponse,
    CreateBatchRequest,
    BatchResponse,
    CreateReconciliationRequest,
    ReconciliationResponse,
    DiscrepancyResponse,
    CancelPaymentRequest,
    RefundPaymentRequest,
    ValidationResult
)
from ..services.payment_processing import PaymentProcessingService
from ..services.payment_validation import PaymentValidationService
from ..services.payment_routing import PaymentRoutingService
from ..services.payment_reconciliation import PaymentReconciliationService
from ..services.payment_notification import PaymentNotificationService

router = APIRouter(prefix="/payments", tags=["payments"])

# Initialize services
processing_service = PaymentProcessingService()
validation_service = PaymentValidationService()
routing_service = PaymentRoutingService()
reconciliation_service = PaymentReconciliationService()
notification_service = PaymentNotificationService()


# Payment Endpoints

@router.post("", response_model=PaymentResponse)
async def create_payment(request: CreatePaymentRequest):
    """
    Create a new payment.
    
    - Validates payment details
    - Routes to appropriate payment system
    - Returns payment details with status
    """
    try:
        # Determine payment system if not specified
        if not request.payment_system:
            routing_result = await routing_service.determine_payment_system(
                amount=request.amount,
                currency=request.currency,
                to_account={"bsb": request.to_bsb, "account_number": request.to_account_number} if request.to_bsb else None,
                to_payid=request.to_payid,
                urgency=request.urgency
            )
            
            if not routing_result.get("payment_system"):
                raise HTTPException(status_code=400, detail=routing_result.get("error", "Unable to determine payment system"))
            
            request.payment_system = routing_result["payment_system"]
        
        # Create payment
        payment = await processing_service.create_payment(
            tenant_id="default",  # TODO: Get from auth context
            from_account_id=request.from_account_id,
            from_customer_id="customer-1",  # TODO: Get from auth context
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            payment_system=request.payment_system,
            reference=request.reference,
            to_account_id=request.to_account_id,
            to_bsb=request.to_bsb,
            to_account_number=request.to_account_number,
            to_account_name=request.to_account_name,
            to_payid=request.to_payid,
            to_payid_type=request.to_payid_type,
            biller_code=request.biller_code,
            biller_name=request.biller_name
        )
        
        # Process payment
        await processing_service.process_payment(payment)
        
        return PaymentResponse(
            payment_id=payment.payment_id,
            payment_system=payment.payment_system,
            from_account_id=payment.from_account_id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            reference=payment.reference,
            status=payment.status,
            initiated_at=payment.initiated_at,
            completed_at=payment.completed_at,
            estimated_delivery="< 60 seconds" if payment.payment_system == "NPP" else "1-2 business days",
            fees=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str):
    """Get payment details by ID."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Payment not found")


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    account_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """List payments with filters."""
    # TODO: Implement database query
    return []


@router.post("/{payment_id}/cancel")
async def cancel_payment(payment_id: str, request: CancelPaymentRequest):
    """Cancel a pending payment."""
    try:
        result = await processing_service.cancel_payment(payment_id, request.reason)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{payment_id}/refund")
async def refund_payment(payment_id: str, request: RefundPaymentRequest):
    """Refund a completed payment."""
    try:
        result = await processing_service.refund_payment(
            payment_id,
            request.amount,
            request.reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Payment Method Endpoints

@router.post("/methods", response_model=PaymentMethodResponse)
async def create_payment_method(request: CreatePaymentMethodRequest):
    """Create a new payment method."""
    # TODO: Implement payment method creation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def list_payment_methods():
    """List customer's payment methods."""
    # TODO: Implement database query
    return []


@router.get("/methods/{method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(method_id: str):
    """Get payment method details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Payment method not found")


@router.delete("/methods/{method_id}")
async def delete_payment_method(method_id: str):
    """Delete a payment method."""
    # TODO: Implement deletion
    return {"success": True}


@router.post("/methods/{method_id}/verify")
async def verify_payment_method(method_id: str):
    """Verify a payment method."""
    # TODO: Implement verification
    return {"success": True, "verified": True}


# Payment Schedule Endpoints

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(request: CreateScheduleRequest):
    """Create a recurring payment schedule."""
    # TODO: Implement schedule creation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules():
    """List payment schedules."""
    # TODO: Implement database query
    return []


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get schedule details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str):
    """Pause a payment schedule."""
    # TODO: Implement pause
    return {"success": True, "status": "paused"}


@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str):
    """Resume a paused schedule."""
    # TODO: Implement resume
    return {"success": True, "status": "active"}


@router.delete("/schedules/{schedule_id}")
async def cancel_schedule(schedule_id: str):
    """Cancel a payment schedule."""
    # TODO: Implement cancellation
    return {"success": True, "status": "cancelled"}


# Batch Payment Endpoints

@router.post("/batches", response_model=BatchResponse)
async def create_batch(request: CreateBatchRequest):
    """Create a payment batch."""
    # TODO: Implement batch creation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/batches", response_model=List[BatchResponse])
async def list_batches():
    """List payment batches."""
    # TODO: Implement database query
    return []


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str):
    """Get batch details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Batch not found")


@router.post("/batches/{batch_id}/approve")
async def approve_batch(batch_id: str):
    """Approve a batch for processing."""
    # TODO: Implement approval
    return {"success": True, "status": "approved"}


@router.post("/batches/{batch_id}/process")
async def process_batch(batch_id: str):
    """Process an approved batch."""
    # TODO: Implement batch processing
    return {"success": True, "status": "processing"}


# Reconciliation Endpoints

@router.post("/reconciliations", response_model=ReconciliationResponse)
async def create_reconciliation(request: CreateReconciliationRequest):
    """Create a payment reconciliation."""
    try:
        reconciliation = await reconciliation_service.create_reconciliation(
            tenant_id="default",  # TODO: Get from auth context
            period_start=request.period_start,
            period_end=request.period_end,
            account_ids=request.account_ids,
            payment_systems=request.payment_systems
        )
        
        return ReconciliationResponse(
            reconciliation_id=reconciliation.reconciliation_id,
            reconciliation_date=reconciliation.reconciliation_date,
            period_start=reconciliation.period_start,
            period_end=reconciliation.period_end,
            status=reconciliation.status,
            total_payments=reconciliation.total_payments,
            reconciled_payments=reconciliation.reconciled_payments,
            unreconciled_payments=reconciliation.unreconciled_payments,
            total_amount=reconciliation.total_amount,
            reconciled_amount=reconciliation.reconciled_amount,
            unreconciled_amount=reconciliation.unreconciled_amount,
            discrepancy_count=reconciliation.discrepancy_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reconciliations", response_model=List[ReconciliationResponse])
async def list_reconciliations():
    """List reconciliations."""
    # TODO: Implement database query
    return []


@router.get("/reconciliations/{reconciliation_id}", response_model=ReconciliationResponse)
async def get_reconciliation(reconciliation_id: str):
    """Get reconciliation details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Reconciliation not found")


@router.post("/reconciliations/{reconciliation_id}/run")
async def run_reconciliation(reconciliation_id: str):
    """Run a reconciliation."""
    try:
        result = await reconciliation_service.run_reconciliation(reconciliation_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reconciliations/{reconciliation_id}/discrepancies", response_model=List[DiscrepancyResponse])
async def get_discrepancies(reconciliation_id: str):
    """Get reconciliation discrepancies."""
    # TODO: Implement database query
    return []


@router.post("/reconciliations/{reconciliation_id}/discrepancies/{discrepancy_id}/resolve")
async def resolve_discrepancy(
    reconciliation_id: str,
    discrepancy_id: str,
    resolution_notes: str
):
    """Resolve a reconciliation discrepancy."""
    try:
        result = await reconciliation_service.resolve_discrepancy(
            reconciliation_id,
            discrepancy_id,
            resolution_notes,
            "user-1"  # TODO: Get from auth context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints

@router.get("/systems")
async def get_available_systems(
    currency: str = Query("AUD"),
    amount: Optional[float] = Query(None)
):
    """Get available payment systems."""
    try:
        from decimal import Decimal
        result = await routing_service.get_available_systems(
            currency=currency,
            amount=Decimal(str(amount)) if amount else None
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_payment_status():
    """Get payment system status."""
    return {
        "npp": "operational",
        "bpay": "operational",
        "swift": "operational",
        "direct_entry": "operational",
        "timestamp": datetime.utcnow()
    }

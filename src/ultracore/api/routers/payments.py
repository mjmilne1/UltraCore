"""
Payment Router

Payment rail endpoints (NPP, BPAY, SWIFT)
"""

from fastapi import APIRouter, status, Query
from typing import Optional
from datetime import datetime

from ultracore.api.schemas.payments import (
    NPPPaymentRequest,
    BPAYPaymentRequest,
    SWIFTPaymentRequest,
    PaymentResponse,
    PaymentListResponse
)
from ultracore.api.exceptions import (
    NotFoundException,
    ValidationException,
    InsufficientFundsException
)
from ultracore.accounts.core.account_manager import get_account_manager
from ultracore.accounts.mcp.mcp_payment_rails import (
    get_payment_rail_manager,
    PaymentRail,
    PaymentRequest as MCPPaymentRequest
)
import uuid

router = APIRouter(prefix="/payments")


@router.post("/npp", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def npp_payment(request: NPPPaymentRequest) -> PaymentResponse:
    """
    NPP (Osko) Payment
    
    Real-time payment via New Payments Platform
    - Instant settlement
    - 24/7/365 availability
    - PayID or BSB/Account
    - Max $1M per transaction
    """
    account_manager = get_account_manager()
    payment_manager = get_payment_rail_manager()
    
    # Validate source account
    account = await account_manager.get_account(request.from_account_id)
    if not account:
        raise NotFoundException("Account", request.from_account_id)
    
    # Check sufficient funds
    if account.balance.available_balance < request.amount:
        raise InsufficientFundsException(
            account_id=request.from_account_id,
            requested=str(request.amount),
            available=str(account.balance.available_balance)
        )
    
    # Create payment request
    payment_id = f"PAY-NPP-{uuid.uuid4().hex[:12].upper()}"
    
    mcp_request = MCPPaymentRequest(
        payment_id=payment_id,
        rail=PaymentRail.NPP,
        direction="OUTBOUND",
        amount=request.amount,
        from_account_id=request.from_account_id,
        payid=request.payid,
        payid_type=request.payid_type,
        beneficiary_bsb=request.bsb,
        beneficiary_account=request.account_number,
        beneficiary_name=request.beneficiary_name,
        description=request.description,
        reference=request.reference,
        idempotency_key=f"{request.from_account_id}-{datetime.now(timezone.utc).timestamp()}"
    )
    
    # Submit payment
    response = await payment_manager.submit_payment(mcp_request)
    
    # If successful, debit account
    if response.status.value == "COMPLETED":
        await account_manager.withdraw(
            account_id=request.from_account_id,
            amount=request.amount,
            description=f"NPP Payment: {request.description}",
            reference=payment_id,
            withdrawn_by="PAYMENT_RAIL"
        )
    
    return PaymentResponse(
        payment_id=response.payment_id,
        rail=response.rail.value,
        status=response.status.value,
        amount=float(mcp_request.amount),
        currency="AUD",
        external_reference=response.external_reference,
        rail_transaction_id=response.rail_transaction_id,
        status_message=response.status_message,
        error_code=response.error_code,
        error_message=response.error_message,
        processing_fee=float(response.processing_fee),
        submitted_at=response.submitted_at,
        completed_at=response.completed_at,
        metadata=response.metadata
    )


@router.post("/bpay", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def bpay_payment(request: BPAYPaymentRequest) -> PaymentResponse:
    """
    BPAY Payment
    
    Bill payment via BPAY
    - 1-3 business day settlement
    - Biller validation
    - Reference number validation
    """
    account_manager = get_account_manager()
    payment_manager = get_payment_rail_manager()
    
    # Validate source account
    account = await account_manager.get_account(request.from_account_id)
    if not account:
        raise NotFoundException("Account", request.from_account_id)
    
    # Check sufficient funds
    if account.balance.available_balance < request.amount:
        raise InsufficientFundsException(
            account_id=request.from_account_id,
            requested=str(request.amount),
            available=str(account.balance.available_balance)
        )
    
    # Create payment request
    payment_id = f"PAY-BPAY-{uuid.uuid4().hex[:12].upper()}"
    
    mcp_request = MCPPaymentRequest(
        payment_id=payment_id,
        rail=PaymentRail.BPAY,
        direction="OUTBOUND",
        amount=request.amount,
        from_account_id=request.from_account_id,
        biller_code=request.biller_code,
        reference_number=request.reference_number,
        description=request.description or f"BPAY to {request.biller_code}",
        idempotency_key=f"{request.from_account_id}-{datetime.now(timezone.utc).timestamp()}"
    )
    
    # Submit payment
    response = await payment_manager.submit_payment(mcp_request)
    
    # Debit account (BPAY takes time but we debit immediately)
    if response.status.value in ["SUBMITTED", "PROCESSING"]:
        await account_manager.withdraw(
            account_id=request.from_account_id,
            amount=request.amount + response.processing_fee,
            description=f"BPAY Payment: {request.description or 'Bill Payment'}",
            reference=payment_id,
            withdrawn_by="PAYMENT_RAIL"
        )
    
    return PaymentResponse(
        payment_id=response.payment_id,
        rail=response.rail.value,
        status=response.status.value,
        amount=float(mcp_request.amount),
        currency="AUD",
        external_reference=response.external_reference,
        rail_transaction_id=response.rail_transaction_id,
        status_message=response.status_message,
        error_code=response.error_code,
        error_message=response.error_message,
        processing_fee=float(response.processing_fee),
        submitted_at=response.submitted_at,
        completed_at=response.completed_at,
        metadata=response.metadata
    )


@router.post("/swift", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def swift_payment(request: SWIFTPaymentRequest) -> PaymentResponse:
    """
    SWIFT Payment
    
    International wire transfer
    - Multi-currency support
    - 1-3 business day settlement
    - SWIFT/BIC validation
    - IBAN support
    """
    account_manager = get_account_manager()
    payment_manager = get_payment_rail_manager()
    
    # Validate source account
    account = await account_manager.get_account(request.from_account_id)
    if not account:
        raise NotFoundException("Account", request.from_account_id)
    
    # Check sufficient funds (TODO: handle FX conversion)
    if account.balance.available_balance < request.amount:
        raise InsufficientFundsException(
            account_id=request.from_account_id,
            requested=str(request.amount),
            available=str(account.balance.available_balance)
        )
    
    # Create payment request
    payment_id = f"PAY-SWIFT-{uuid.uuid4().hex[:12].upper()}"
    
    mcp_request = MCPPaymentRequest(
        payment_id=payment_id,
        rail=PaymentRail.SWIFT,
        direction="OUTBOUND",
        amount=request.amount,
        currency=request.currency,
        from_account_id=request.from_account_id,
        beneficiary_name=request.beneficiary_name,
        swift_code=request.swift_code,
        iban=request.iban,
        beneficiary_account=request.beneficiary_account,
        description=request.description,
        reference=request.reference,
        idempotency_key=f"{request.from_account_id}-{datetime.now(timezone.utc).timestamp()}"
    )
    
    # Submit payment
    response = await payment_manager.submit_payment(mcp_request)
    
    # Debit account
    if response.status.value in ["SUBMITTED", "PROCESSING"]:
        await account_manager.withdraw(
            account_id=request.from_account_id,
            amount=request.amount + response.processing_fee,
            description=f"SWIFT Payment: {request.description}",
            reference=payment_id,
            withdrawn_by="PAYMENT_RAIL"
        )
    
    return PaymentResponse(
        payment_id=response.payment_id,
        rail=response.rail.value,
        status=response.status.value,
        amount=float(mcp_request.amount),
        currency=request.currency,
        external_reference=response.external_reference,
        rail_transaction_id=response.rail_transaction_id,
        status_message=response.status_message,
        error_code=response.error_code,
        error_message=response.error_message,
        processing_fee=float(response.processing_fee),
        submitted_at=response.submitted_at,
        completed_at=response.completed_at,
        metadata=response.metadata
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(payment_id: str) -> PaymentResponse:
    """
    Get payment status
    
    Returns current status of a payment
    """
    payment_manager = get_payment_rail_manager()
    
    # Determine rail from payment_id
    if "NPP" in payment_id:
        rail = PaymentRail.NPP
    elif "BPAY" in payment_id:
        rail = PaymentRail.BPAY
    elif "SWIFT" in payment_id:
        rail = PaymentRail.SWIFT
    else:
        raise NotFoundException("Payment", payment_id)
    
    response = await payment_manager.get_payment_status(payment_id, rail)
    if not response:
        raise NotFoundException("Payment", payment_id)
    
    return PaymentResponse(
        payment_id=response.payment_id,
        rail=response.rail.value,
        status=response.status.value,
        amount=0.0,  # Not stored in status response
        currency="AUD",
        external_reference=response.external_reference,
        rail_transaction_id=response.rail_transaction_id,
        status_message=response.status_message,
        error_code=response.error_code,
        error_message=response.error_message,
        processing_fee=float(response.processing_fee),
        submitted_at=response.submitted_at,
        completed_at=response.completed_at,
        metadata=response.metadata
    )


@router.post("/npp/payid/register")
async def register_payid(
    account_id: str = Query(...),
    payid: str = Query(...),
    payid_type: str = Query(..., pattern=r'^(EMAIL|MOBILE|ABN|ORG_ID)$')
):
    """
    Register PayID
    
    Links a PayID to an account
    """
    account_manager = get_account_manager()
    payment_manager = get_payment_rail_manager()
    
    # Validate account
    account = await account_manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    # Register PayID
    result = await payment_manager.npp.register_payid(
        account_id=account_id,
        payid=payid,
        payid_type=payid_type
    )
    
    return result

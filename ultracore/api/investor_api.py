"""
FastAPI Endpoints for Investor Management
RESTful API for investor operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date
from decimal import Decimal

from ..modules.investor_management.models import (
    Investor, LoanTransfer, InvestorPortfolio,
    CreateInvestorRequest, InitiateLoanTransferRequest,
    ApproveTransferRequest, CancelTransferRequest,
    InvestorStatus, InvestorType, TransferType, TransferStatus
)
from ..modules.investor_management.investor_service import InvestorService
from ..modules.investor_management.transfer_service import LoanTransferService
from ..modules.investor_management.ai_matching import (
    InvestorMatchingEngine, LoanPricingEngine, FraudDetectionEngine
)


# Initialize router
router = APIRouter(prefix="/api/v1/investors", tags=["Investor Management"])

# Initialize services (in production, use dependency injection)
investor_service = InvestorService()
transfer_service = LoanTransferService(investor_service)
matching_engine = InvestorMatchingEngine()
pricing_engine = LoanPricingEngine()
fraud_engine = FraudDetectionEngine()


# ============================================================================
# INVESTOR ENDPOINTS
# ============================================================================

@router.post("/", response_model=Investor, status_code=201)
async def create_investor(request: CreateInvestorRequest):
    """
    Create a new investor
    
    Creates a new investor account in the system. The investor will be in
    UNDER_REVIEW status until KYC/AML verification is completed.
    """
    try:
        investor = investor_service.create_investor(request)
        return investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{investor_id}", response_model=Investor)
async def get_investor(investor_id: str):
    """
    Get investor details
    
    Retrieve complete details for a specific investor.
    """
    investor = investor_service.get_investor(investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor {investor_id} not found")
    return investor


@router.get("/", response_model=List[Investor])
async def list_investors(
    status: Optional[InvestorStatus] = Query(None, description="Filter by status"),
    investor_type: Optional[InvestorType] = Query(None, description="Filter by type")
):
    """
    List all investors
    
    Retrieve a list of all investors with optional filters.
    """
    investors = investor_service.list_investors(status=status, investor_type=investor_type)
    return investors


@router.post("/{investor_id}/verify-kyc", response_model=Investor)
async def verify_kyc(investor_id: str, verified_by: str):
    """
    Verify investor KYC
    
    Mark an investor as KYC verified. If both KYC and AML are verified,
    the investor will be automatically activated.
    """
    try:
        investor = investor_service.verify_kyc(investor_id, verified_by)
        return investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investor_id}/verify-aml", response_model=Investor)
async def verify_aml(investor_id: str, verified_by: str):
    """
    Verify investor AML
    
    Mark an investor as AML verified. If both KYC and AML are verified,
    the investor will be automatically activated.
    """
    try:
        investor = investor_service.verify_aml(investor_id, verified_by)
        return investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investor_id}/suspend", response_model=Investor)
async def suspend_investor(investor_id: str, reason: str, suspended_by: str):
    """
    Suspend investor account
    
    Suspend an investor account. Suspended investors cannot participate
    in new transfers.
    """
    try:
        investor = investor_service.suspend_investor(investor_id, reason, suspended_by)
        return investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investor_id}/activate", response_model=Investor)
async def activate_investor(investor_id: str, activated_by: str):
    """
    Activate investor account
    
    Activate a suspended investor account. Requires KYC and AML verification.
    """
    try:
        investor = investor_service.activate_investor(investor_id, activated_by)
        return investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# TRANSFER ENDPOINTS
# ============================================================================

@router.post("/transfers", response_model=LoanTransfer, status_code=201)
async def initiate_transfer(
    request: InitiateLoanTransferRequest,
    outstanding_principal: Decimal,
    outstanding_interest: Decimal = Decimal("0.00")
):
    """
    Initiate a loan transfer
    
    Initiate a transfer of loan ownership to an investor. The transfer will
    be in PENDING status until approved.
    """
    try:
        transfer = transfer_service.initiate_transfer(
            request,
            outstanding_principal,
            outstanding_interest
        )
        return transfer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfers/{transfer_id}/approve", response_model=LoanTransfer)
async def approve_transfer(transfer_id: str, request: ApproveTransferRequest):
    """
    Approve a loan transfer
    
    Approve a pending transfer. The transfer will move to APPROVED status
    and will be executed on the settlement date.
    """
    try:
        transfer = transfer_service.approve_transfer(request)
        return transfer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfers/{transfer_id}/cancel", response_model=LoanTransfer)
async def cancel_transfer(transfer_id: str, request: CancelTransferRequest):
    """
    Cancel a loan transfer
    
    Cancel a pending or approved transfer before settlement.
    """
    try:
        transfer = transfer_service.cancel_transfer(request)
        return transfer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transfers/{transfer_id}/execute", response_model=LoanTransfer)
async def execute_settlement(transfer_id: str):
    """
    Execute transfer settlement
    
    Execute the settlement for an approved transfer. This would normally
    be called automatically on the settlement date by a scheduled job.
    """
    try:
        transfer = transfer_service.execute_settlement(transfer_id)
        return transfer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transfers/{transfer_id}", response_model=LoanTransfer)
async def get_transfer(transfer_id: str):
    """
    Get transfer details
    
    Retrieve complete details for a specific transfer.
    """
    transfer = transfer_service.get_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail=f"Transfer {transfer_id} not found")
    return transfer


@router.get("/loans/{loan_id}/transfers", response_model=List[LoanTransfer])
async def get_transfers_for_loan(loan_id: str):
    """
    Get all transfers for a loan
    
    Retrieve the complete transfer history for a loan.
    """
    transfers = transfer_service.get_transfers_for_loan(loan_id)
    return transfers


@router.get("/loans/{loan_id}/active-transfer", response_model=Optional[LoanTransfer])
async def get_active_transfer(loan_id: str):
    """
    Get active transfer for a loan
    
    Retrieve the currently active transfer for a loan, if any.
    """
    transfer = transfer_service.get_active_transfer_for_loan(loan_id)
    return transfer


@router.get("/{investor_id}/transfers", response_model=List[LoanTransfer])
async def get_transfers_for_investor(investor_id: str):
    """
    Get all transfers for an investor
    
    Retrieve all transfers (incoming and outgoing) for an investor.
    """
    transfers = transfer_service.get_transfers_for_investor(investor_id)
    return transfers


@router.get("/loans/{loan_id}/owner")
async def get_loan_owner(loan_id: str):
    """
    Get current owner of a loan
    
    Returns the current owner of a loan (investor ID or "ORIGINATOR").
    """
    owner_id = transfer_service.get_loan_owner(loan_id)
    
    if not owner_id:
        return {
            "loan_id": loan_id,
            "owner_type": "ORIGINATOR",
            "owner_id": None
        }
    
    investor = investor_service.get_investor(owner_id)
    
    return {
        "loan_id": loan_id,
        "owner_type": "INVESTOR",
        "owner_id": owner_id,
        "owner_name": investor.investor_name if investor else "Unknown"
    }


# ============================================================================
# AI/ML ENDPOINTS
# ============================================================================

@router.post("/ai/match-investors")
async def match_investors(
    loan_id: str,
    principal_amount: float,
    loan_type: str,
    risk_rating: str,
    interest_rate: float,
    top_n: int = 5
):
    """
    AI-powered investor matching
    
    Use machine learning to find the best investors for a loan based on
    investment preferences, risk appetite, and portfolio composition.
    """
    loan_data = {
        "loan_id": loan_id,
        "principal_amount": principal_amount,
        "loan_type": loan_type,
        "risk_rating": risk_rating,
        "interest_rate": interest_rate
    }
    
    active_investors = investor_service.list_investors(status=InvestorStatus.ACTIVE)
    
    matches = matching_engine.match_investors_for_loan(
        loan_data,
        active_investors,
        top_n
    )
    
    return {
        "loan_id": loan_id,
        "matches": matches,
        "count": len(matches)
    }


@router.post("/ai/price-recommendation")
async def get_pricing_recommendation(
    loan_id: str,
    principal_amount: float,
    interest_rate: float,
    remaining_term_months: int,
    risk_rating: str,
    days_past_due: int = 0
):
    """
    AI-powered pricing recommendation
    
    Get a machine learning-based recommendation for the purchase price
    of a loan based on its characteristics and market conditions.
    """
    loan_data = {
        "loan_id": loan_id,
        "principal_amount": principal_amount,
        "interest_rate": interest_rate,
        "remaining_term_months": remaining_term_months,
        "risk_rating": risk_rating,
        "days_past_due": days_past_due
    }
    
    recommendation = pricing_engine.recommend_price(loan_data)
    
    return recommendation


@router.post("/ai/fraud-assessment")
async def assess_fraud_risk(
    transfer_id: str,
    purchase_price_ratio: float,
    outstanding_principal: float,
    investor_id: str
):
    """
    AI-powered fraud detection
    
    Assess the fraud risk of a transfer using machine learning to detect
    suspicious patterns and anomalies.
    """
    transfer_data = {
        "transfer_id": transfer_id,
        "purchase_price_ratio": purchase_price_ratio,
        "outstanding_principal": outstanding_principal
    }
    
    investor = investor_service.get_investor(investor_id)
    investor_history = {
        "total_transactions": investor.active_loans if investor else 0
    }
    
    assessment = fraud_engine.assess_transfer_risk(transfer_data, investor_history)
    
    return assessment


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@router.get("/{investor_id}/portfolio")
async def get_investor_portfolio(investor_id: str):
    """
    Get investor portfolio
    
    Retrieve complete portfolio information for an investor including
    all active loans and performance metrics.
    """
    investor = investor_service.get_investor(investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor {investor_id} not found")
    
    # Get all active transfers
    transfers = transfer_service.get_transfers_for_investor(investor_id)
    active_transfers = [t for t in transfers if t.status == TransferStatus.ACTIVE]
    
    # Calculate metrics
    total_principal = sum(t.outstanding_principal for t in active_transfers)
    total_invested = sum(t.purchase_price for t in active_transfers)
    
    portfolio = {
        "investor_id": investor_id,
        "investor_name": investor.investor_name,
        "total_loans": len(active_transfers),
        "total_principal_outstanding": str(total_principal),
        "total_invested": str(total_invested),
        "total_returns": str(investor.total_returns),
        "loans": [
            {
                "loan_id": t.loan_id,
                "transfer_id": t.transfer_id,
                "purchase_price": str(t.purchase_price),
                "outstanding_principal": str(t.outstanding_principal),
                "purchase_price_ratio": str(t.purchase_price_ratio),
                "effective_date": t.effective_date_from.isoformat(),
                "transfer_type": t.transfer_type.value
            }
            for t in active_transfers
        ]
    }
    
    return portfolio


# ============================================================================
# PAYMENT ROUTING ENDPOINTS
# ============================================================================

@router.get("/loans/{loan_id}/payment-routing")
async def get_payment_routing(loan_id: str):
    """
    Get payment routing for a loan
    
    Retrieve the active payment routing configuration for a loan.
    """
    routing = transfer_service.get_payment_routing_for_loan(loan_id)
    
    if not routing:
        return {
            "loan_id": loan_id,
            "routing_active": False,
            "message": "No active payment routing. Payments go to originator."
        }
    
    return {
        "loan_id": loan_id,
        "routing_active": True,
        "routing_id": routing.routing_id,
        "investor_id": routing.investor_id,
        "routing_percentage": str(routing.routing_percentage),
        "route_principal": routing.route_principal,
        "route_interest": routing.route_interest,
        "route_fees": routing.route_fees,
        "effective_from": routing.effective_from.isoformat()
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the investor management service.
    """
    return {
        "status": "healthy",
        "service": "investor_management",
        "version": "1.0.0",
        "features": {
            "investor_management": True,
            "loan_transfers": True,
            "ai_matching": True,
            "ai_pricing": True,
            "fraud_detection": True,
            "payment_routing": True,
            "event_sourcing": True,
            "kafka_streaming": True
        }
    }

"""
Lending API Routes.

REST API endpoints for lending operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from .schemas import (
    LoanApplicationRequest,
    LoanApplicationResponse,
    LoanResponse,
    HomeLoanResponse,
    BusinessLoanResponse,
    MakeRepaymentRequest,
    RepaymentResponse,
    LoanStatementRequest,
    LoanStatementResponse,
    DrawdownRequest,
    RestructureRequest,
    HardshipRequest,
    RefinanceQuoteRequest,
    RefinanceQuoteResponse,
    DocumentUploadRequest,
    DocumentResponse,
    LoanCalculationRequest,
    LoanCalculationResponse,
    EligibilityCheckRequest,
    EligibilityCheckResponse
)
from ..origination.application_service import LoanApplicationService
from ..ml.credit_scorer import CreditScorer

router = APIRouter(prefix="/loans", tags=["lending"])

# Initialize services
application_service = LoanApplicationService()
credit_scorer = CreditScorer()


# Loan Application Endpoints

@router.post("/applications", response_model=LoanApplicationResponse)
async def create_loan_application(request: LoanApplicationRequest):
    """
    Create a new loan application.
    
    - Validates eligibility
    - Runs credit assessment
    - Returns decision or pending status
    """
    try:
        # TODO: Implement application creation
        return LoanApplicationResponse(
            application_id="app-1",
            loan_type=request.loan_type,
            amount=request.amount,
            term_months=request.term_months,
            status="pending",
            credit_score=None,
            decision=None,
            interest_rate=None,
            comparison_rate=None,
            monthly_repayment=None,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}", response_model=LoanApplicationResponse)
async def get_loan_application(application_id: str):
    """Get loan application details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Application not found")


@router.get("/applications", response_model=List[LoanApplicationResponse])
async def list_loan_applications(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List loan applications."""
    # TODO: Implement database query
    return []


@router.post("/applications/{application_id}/submit")
async def submit_loan_application(application_id: str):
    """Submit application for assessment."""
    # TODO: Implement submission
    return {"success": True, "status": "submitted"}


@router.post("/applications/{application_id}/documents")
async def upload_application_document(
    application_id: str,
    request: DocumentUploadRequest
):
    """Upload document for application."""
    # TODO: Implement document upload
    return {"success": True, "document_id": "doc-1"}


# Loan Endpoints

@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: str):
    """Get loan details."""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Loan not found")


@router.get("", response_model=List[LoanResponse])
async def list_loans(
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List loans."""
    # TODO: Implement database query
    return []


@router.get("/{loan_id}/balance")
async def get_loan_balance(loan_id: str):
    """Get current loan balance."""
    # TODO: Query UltraLedger
    return {
        "loan_id": loan_id,
        "current_balance": "0.00",
        "principal_outstanding": "0.00",
        "interest_outstanding": "0.00",
        "as_at": datetime.utcnow()
    }


@router.get("/{loan_id}/statement", response_model=LoanStatementResponse)
async def get_loan_statement(
    loan_id: str,
    from_date: date = Query(...),
    to_date: date = Query(...)
):
    """Get loan statement for period."""
    # TODO: Implement statement generation
    raise HTTPException(status_code=501, detail="Not implemented")


# Repayment Endpoints

@router.post("/{loan_id}/repayments", response_model=RepaymentResponse)
async def make_repayment(loan_id: str, request: MakeRepaymentRequest):
    """Make a loan repayment."""
    try:
        # TODO: Implement repayment processing
        return RepaymentResponse(
            repayment_id="rep-1",
            loan_id=loan_id,
            amount=request.amount,
            principal_portion=Decimal("0"),
            interest_portion=Decimal("0"),
            new_balance=Decimal("0"),
            payment_date=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{loan_id}/repayments")
async def list_repayments(
    loan_id: str,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List loan repayments."""
    # TODO: Implement database query
    return []


@router.get("/{loan_id}/repayment-schedule")
async def get_repayment_schedule(loan_id: str):
    """Get loan repayment schedule."""
    # TODO: Generate repayment schedule
    return {
        "loan_id": loan_id,
        "schedule": []
    }


# Line of Credit Endpoints

@router.post("/{loan_id}/drawdown")
async def drawdown(loan_id: str, request: DrawdownRequest):
    """Draw down from line of credit."""
    try:
        # TODO: Implement drawdown
        return {
            "success": True,
            "drawdown_id": "draw-1",
            "amount": request.amount,
            "new_balance": "0.00",
            "available_credit": "0.00"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{loan_id}/available-credit")
async def get_available_credit(loan_id: str):
    """Get available credit for line of credit."""
    # TODO: Calculate available credit
    return {
        "loan_id": loan_id,
        "credit_limit": "0.00",
        "drawn_balance": "0.00",
        "available_credit": "0.00"
    }


# Restructuring Endpoints

@router.post("/{loan_id}/restructure")
async def restructure_loan(loan_id: str, request: RestructureRequest):
    """Request loan restructure."""
    try:
        # TODO: Implement restructuring
        return {
            "success": True,
            "restructure_id": "restr-1",
            "status": "pending_approval"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{loan_id}/hardship")
async def request_hardship(loan_id: str, request: HardshipRequest):
    """Request hardship assistance."""
    try:
        # TODO: Implement hardship request
        return {
            "success": True,
            "hardship_id": "hard-1",
            "status": "under_review"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Refinance Endpoints

@router.post("/refinance/quote", response_model=RefinanceQuoteResponse)
async def get_refinance_quote(request: RefinanceQuoteRequest):
    """Get refinance quote."""
    try:
        # TODO: Calculate refinance quote
        raise HTTPException(status_code=501, detail="Not implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refinance/apply")
async def apply_for_refinance(quote_id: str):
    """Apply for refinance."""
    # TODO: Implement refinance application
    return {
        "success": True,
        "application_id": "app-1"
    }


# Early Repayment Endpoints

@router.post("/{loan_id}/early-repayment/quote")
async def get_early_repayment_quote(loan_id: str):
    """Get early repayment quote."""
    # TODO: Calculate break costs
    return {
        "loan_id": loan_id,
        "current_balance": "0.00",
        "break_costs": "0.00",
        "total_to_pay": "0.00",
        "valid_until": datetime.utcnow()
    }


@router.post("/{loan_id}/early-repayment")
async def make_early_repayment(loan_id: str):
    """Make early repayment (full or partial)."""
    # TODO: Implement early repayment
    return {
        "success": True,
        "repayment_id": "rep-1"
    }


# Document Endpoints

@router.post("/{loan_id}/documents")
async def upload_loan_document(
    loan_id: str,
    request: DocumentUploadRequest
):
    """Upload loan document."""
    # TODO: Implement document upload
    return {
        "success": True,
        "document_id": "doc-1"
    }


@router.get("/{loan_id}/documents", response_model=List[DocumentResponse])
async def list_loan_documents(loan_id: str):
    """List loan documents."""
    # TODO: Implement database query
    return []


@router.get("/{loan_id}/documents/{document_id}")
async def get_loan_document(loan_id: str, document_id: str):
    """Get loan document."""
    # TODO: Implement document retrieval
    raise HTTPException(status_code=404, detail="Document not found")


# Calculation Endpoints

@router.post("/calculate", response_model=LoanCalculationResponse)
async def calculate_loan(request: LoanCalculationRequest):
    """Calculate loan repayments and costs."""
    try:
        # Calculate monthly repayment
        r = request.interest_rate / Decimal("100") / Decimal("12")
        n = request.term_months
        
        if r > 0:
            repayment = request.amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        else:
            repayment = request.amount / n
        
        total_repayable = repayment * n
        total_interest = total_repayable - request.amount
        
        # Comparison rate (simplified - should include fees)
        comparison_rate = request.interest_rate
        
        return LoanCalculationResponse(
            amount=request.amount,
            term_months=request.term_months,
            interest_rate=request.interest_rate,
            repayment_amount=repayment.quantize(Decimal("0.01")),
            total_interest=total_interest.quantize(Decimal("0.01")),
            total_repayable=total_repayable.quantize(Decimal("0.01")),
            comparison_rate=comparison_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eligibility", response_model=EligibilityCheckResponse)
async def check_eligibility(request: EligibilityCheckRequest):
    """Check loan eligibility."""
    try:
        # Simple eligibility check
        debt_to_income = request.existing_debts / request.annual_income
        max_dti = Decimal("0.35")  # 35% DTI ratio
        
        available_income = request.annual_income * (max_dti - debt_to_income)
        max_monthly_payment = available_income / Decimal("12")
        
        # Estimate max loan amount (simplified)
        r = Decimal("0.06") / Decimal("12")  # 6% p.a.
        n = 360  # 30 years
        
        if r > 0:
            max_loan = max_monthly_payment * ((1 + r) ** n - 1) / (r * (1 + r) ** n)
        else:
            max_loan = max_monthly_payment * n
        
        eligible = max_loan >= request.amount
        
        reasons = []
        if not eligible:
            reasons.append(f"Requested amount exceeds maximum ({max_loan:.2f})")
        if debt_to_income > max_dti:
            reasons.append("Debt-to-income ratio too high")
        
        return EligibilityCheckResponse(
            eligible=eligible,
            max_loan_amount=max_loan.quantize(Decimal("0.01")),
            estimated_rate=Decimal("6.00"),
            reasons=reasons
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Status Endpoints

@router.get("/products")
async def list_loan_products():
    """List available loan products."""
    return {
        "products": [
            {
                "product_id": "personal-loan",
                "name": "Personal Loan",
                "type": "PERSONAL",
                "min_amount": 2000,
                "max_amount": 50000,
                "min_term_months": 12,
                "max_term_months": 84,
                "interest_rate_from": 6.99
            },
            {
                "product_id": "home-loan",
                "name": "Home Loan",
                "type": "HOME",
                "min_amount": 200000,
                "max_amount": 2000000,
                "min_term_months": 180,
                "max_term_months": 360,
                "interest_rate_from": 3.99
            },
            {
                "product_id": "business-loan",
                "name": "Business Loan",
                "type": "BUSINESS",
                "min_amount": 10000,
                "max_amount": 5000000,
                "min_term_months": 12,
                "max_term_months": 120,
                "interest_rate_from": 5.99
            }
        ]
    }


@router.get("/status")
async def get_lending_status():
    """Get lending system status."""
    return {
        "status": "operational",
        "applications_enabled": True,
        "disbursements_enabled": True,
        "timestamp": datetime.utcnow()
    }

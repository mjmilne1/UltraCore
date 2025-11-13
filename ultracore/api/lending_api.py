"""
Lending API Endpoints
FastAPI REST API for lending operations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import date
from decimal import Decimal

from ..modules.lending.products.models import (
    LoanProduct, CreateLoanProductRequest, GetApplicableRateRequest,
    LoanProductType
)
from ..modules.lending.accounts.models import (
    LoanApplication, LoanAccount, CreateLoanApplicationRequest,
    ApproveLoanApplicationRequest, DisburseLoanRequest, RecordRepaymentRequest,
    LoanApplicationStatus, LoanAccountStatus
)
from ..modules.lending.collateral.models import (
    Collateral, CreateCollateralRequest, LinkCollateralToLoanRequest,
    CreateValuationRequest, RegisterPPSRRequest
)


# Create router
router = APIRouter(prefix="/api/v1/lending", tags=["lending"])


# ============================================================================
# LOAN PRODUCTS
# ============================================================================

@router.get("/products", response_model=List[dict])
async def list_loan_products(
    product_type: Optional[str] = None,
    is_active: bool = True
):
    """
    List loan products
    
    Query Parameters:
    - product_type: Filter by product type (personal, home, car, etc.)
    - is_active: Filter by active status
    
    Returns:
    - List of loan products
    """
    # In production, call actual service
    return [
        {
            "product_id": "PROD-001",
            "product_code": "PL-STANDARD-001",
            "product_name": "Personal Loan - Standard",
            "product_type": "personal",
            "min_loan_amount": "5000.00",
            "max_loan_amount": "50000.00",
            "base_interest_rate": "0.0850",
            "is_active": True
        }
    ]


@router.get("/products/{product_id}", response_model=dict)
async def get_loan_product(product_id: str):
    """
    Get loan product details
    
    Path Parameters:
    - product_id: Product ID
    
    Returns:
    - Product details
    """
    # In production, call actual service
    return {
        "product_id": product_id,
        "product_code": "PL-STANDARD-001",
        "product_name": "Personal Loan - Standard",
        "description": "Unsecured personal loan for general purposes",
        "min_loan_amount": "5000.00",
        "max_loan_amount": "50000.00",
        "min_term_months": 12,
        "max_term_months": 84,
        "base_interest_rate": "0.0850",
        "features": {
            "extra_repayments": True,
            "redraw": False,
            "offset_account": False
        }
    }


@router.post("/products", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_loan_product(request: CreateLoanProductRequest):
    """
    Create a new loan product
    
    Request Body:
    - Product configuration
    
    Returns:
    - Created product
    """
    # In production, call actual service
    return {
        "product_id": "PROD-NEW",
        "product_code": request.product_code,
        "message": "Product created successfully"
    }


@router.post("/products/calculate-rate", response_model=dict)
async def get_applicable_rate(request: GetApplicableRateRequest):
    """
    Get applicable interest rate for loan parameters
    
    Request Body:
    - product_id: Product ID
    - loan_amount: Loan amount
    - term_months: Loan term
    - lvr: Loan-to-Value Ratio (optional)
    
    Returns:
    - Applicable rate
    """
    return {
        "product_id": request.product_id,
        "loan_amount": str(request.loan_amount),
        "term_months": request.term_months,
        "interest_rate": "0.0650",
        "comparison_rate": "0.0680"
    }


@router.post("/products/calculate-repayment", response_model=dict)
async def calculate_repayment(
    product_id: str,
    loan_amount: float,
    term_months: int,
    repayment_frequency: str = "monthly"
):
    """
    Calculate loan repayment estimate
    
    Query Parameters:
    - product_id: Product ID
    - loan_amount: Loan amount
    - term_months: Loan term
    - repayment_frequency: Repayment frequency
    
    Returns:
    - Repayment estimate
    """
    return {
        "loan_amount": loan_amount,
        "term_months": term_months,
        "interest_rate": "0.0650",
        "repayment_frequency": repayment_frequency,
        "repayment_amount": "1250.00",
        "total_repayable": "75000.00",
        "total_interest": "25000.00"
    }


# ============================================================================
# LOAN APPLICATIONS
# ============================================================================

@router.post("/applications", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_loan_application(request: CreateLoanApplicationRequest):
    """
    Create a new loan application
    
    Request Body:
    - Application details
    
    Returns:
    - Created application
    """
    return {
        "application_id": "APP-001",
        "status": "draft",
        "message": "Application created successfully"
    }


@router.get("/applications/{application_id}", response_model=dict)
async def get_loan_application(application_id: str):
    """
    Get loan application details
    
    Path Parameters:
    - application_id: Application ID
    
    Returns:
    - Application details
    """
    return {
        "application_id": application_id,
        "status": "under_assessment",
        "product_id": "PROD-001",
        "requested_amount": "50000.00",
        "term_months": 60,
        "credit_score": 720,
        "risk_rating": "GOOD"
    }


@router.post("/applications/{application_id}/submit", response_model=dict)
async def submit_loan_application(application_id: str):
    """
    Submit loan application for assessment
    
    Path Parameters:
    - application_id: Application ID
    
    Returns:
    - Updated application
    """
    return {
        "application_id": application_id,
        "status": "submitted",
        "message": "Application submitted for assessment"
    }


@router.post("/applications/{application_id}/assess-credit", response_model=dict)
async def assess_credit(
    application_id: str,
    credit_history: dict
):
    """
    Assess creditworthiness using AI
    
    Path Parameters:
    - application_id: Application ID
    
    Request Body:
    - credit_history: Credit history data
    
    Returns:
    - Credit assessment
    """
    return {
        "application_id": application_id,
        "credit_score": 720,
        "risk_band": "GOOD",
        "factors": [
            "No credit defaults",
            "Good credit utilization: 25.0%",
            "Excellent credit history: 8 years"
        ]
    }


@router.post("/applications/{application_id}/assess-affordability", response_model=dict)
async def assess_affordability(
    application_id: str,
    applicant_income: float,
    applicant_expenses: float,
    existing_debts: float,
    loan_repayment: float
):
    """
    Assess loan affordability
    
    Path Parameters:
    - application_id: Application ID
    
    Query Parameters:
    - applicant_income: Monthly income
    - applicant_expenses: Monthly expenses
    - existing_debts: Existing debt repayments
    - loan_repayment: Proposed loan repayment
    
    Returns:
    - Affordability assessment
    """
    return {
        "application_id": application_id,
        "can_afford": True,
        "monthly_surplus": "1500.00",
        "dti_ratio": 0.35,
        "dsr_ratio": 0.50,
        "risk_level": "LOW"
    }


@router.post("/applications/{application_id}/approve", response_model=dict)
async def approve_application(
    application_id: str,
    request: ApproveLoanApplicationRequest
):
    """
    Approve loan application
    
    Path Parameters:
    - application_id: Application ID
    
    Request Body:
    - Approval details
    
    Returns:
    - Approved application
    """
    return {
        "application_id": application_id,
        "status": "approved",
        "approved_amount": str(request.approved_amount),
        "interest_rate": str(request.interest_rate),
        "message": "Application approved successfully"
    }


@router.post("/applications/{application_id}/decline", response_model=dict)
async def decline_application(
    application_id: str,
    decline_reason: str,
    declined_by: str
):
    """
    Decline loan application
    
    Path Parameters:
    - application_id: Application ID
    
    Query Parameters:
    - decline_reason: Reason for decline
    - declined_by: Decliner ID
    
    Returns:
    - Declined application
    """
    return {
        "application_id": application_id,
        "status": "declined",
        "decline_reason": decline_reason,
        "message": "Application declined"
    }


# ============================================================================
# LOAN ACCOUNTS
# ============================================================================

@router.get("/accounts/{account_id}", response_model=dict)
async def get_loan_account(account_id: str):
    """
    Get loan account details
    
    Path Parameters:
    - account_id: Account ID
    
    Returns:
    - Account details
    """
    return {
        "account_id": account_id,
        "account_number": "LA-123456",
        "status": "active",
        "principal_amount": "50000.00",
        "outstanding_principal": "45000.00",
        "outstanding_interest": "250.00",
        "total_outstanding": "45250.00",
        "interest_rate": "0.0650",
        "next_repayment_date": "2025-12-01",
        "next_repayment_amount": "1250.00",
        "days_in_arrears": 0
    }


@router.get("/accounts", response_model=List[dict])
async def list_loan_accounts(
    client_id: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List loan accounts
    
    Query Parameters:
    - client_id: Filter by client
    - status: Filter by status
    
    Returns:
    - List of loan accounts
    """
    return [
        {
            "account_id": "ACC-001",
            "account_number": "LA-123456",
            "client_id": "CLI-001",
            "product_name": "Personal Loan - Standard",
            "principal_amount": "50000.00",
            "outstanding_balance": "45000.00",
            "status": "active"
        }
    ]


@router.post("/accounts/{account_id}/disburse", response_model=dict)
async def disburse_loan(
    account_id: str,
    request: DisburseLoanRequest
):
    """
    Disburse loan funds
    
    Path Parameters:
    - account_id: Account ID
    
    Request Body:
    - Disbursement details
    
    Returns:
    - Disbursement record
    """
    return {
        "disbursement_id": "DIS-001",
        "account_id": account_id,
        "amount": "50000.00",
        "status": "completed",
        "message": "Loan disbursed successfully"
    }


@router.post("/accounts/{account_id}/repayments", response_model=dict)
async def record_repayment(
    account_id: str,
    request: RecordRepaymentRequest
):
    """
    Record loan repayment
    
    Path Parameters:
    - account_id: Account ID
    
    Request Body:
    - Repayment details
    
    Returns:
    - Repayment record
    """
    return {
        "repayment_id": "REP-001",
        "account_id": account_id,
        "amount": str(request.amount),
        "principal_portion": "1000.00",
        "interest_portion": "250.00",
        "status": "completed",
        "message": "Repayment recorded successfully"
    }


@router.get("/accounts/{account_id}/schedule", response_model=dict)
async def get_repayment_schedule(account_id: str):
    """
    Get loan repayment schedule
    
    Path Parameters:
    - account_id: Account ID
    
    Returns:
    - Repayment schedule
    """
    return {
        "account_id": account_id,
        "principal_amount": "50000.00",
        "interest_rate": "0.0650",
        "term_months": 60,
        "repayment_amount": "1250.00",
        "schedule": [
            {
                "installment_number": 1,
                "due_date": "2025-12-01",
                "principal_due": "1000.00",
                "interest_due": "250.00",
                "total_due": "1250.00",
                "closing_balance": "49000.00"
            }
        ]
    }


@router.get("/accounts/{account_id}/transactions", response_model=List[dict])
async def get_account_transactions(
    account_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
):
    """
    Get account transactions
    
    Path Parameters:
    - account_id: Account ID
    
    Query Parameters:
    - from_date: Start date
    - to_date: End date
    
    Returns:
    - List of transactions
    """
    return [
        {
            "transaction_id": "TXN-001",
            "transaction_date": "2025-11-01",
            "transaction_type": "repayment",
            "amount": "1250.00",
            "balance_after": "48750.00"
        }
    ]


# ============================================================================
# COLLATERAL
# ============================================================================

@router.post("/collateral", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_collateral(request: CreateCollateralRequest):
    """
    Register collateral
    
    Request Body:
    - Collateral details
    
    Returns:
    - Registered collateral
    """
    return {
        "collateral_id": "COL-001",
        "collateral_type": request.collateral_type.value,
        "current_value": str(request.current_value),
        "status": "pending_valuation",
        "message": "Collateral registered successfully"
    }


@router.get("/collateral/{collateral_id}", response_model=dict)
async def get_collateral(collateral_id: str):
    """
    Get collateral details
    
    Path Parameters:
    - collateral_id: Collateral ID
    
    Returns:
    - Collateral details
    """
    return {
        "collateral_id": collateral_id,
        "collateral_type": "vehicle",
        "description": "2023 Toyota Camry",
        "current_value": "35000.00",
        "status": "active",
        "is_insured": True
    }


@router.post("/collateral/{collateral_id}/link-to-loan", response_model=dict)
async def link_collateral_to_loan(
    collateral_id: str,
    request: LinkCollateralToLoanRequest
):
    """
    Link collateral to loan
    
    Path Parameters:
    - collateral_id: Collateral ID
    
    Request Body:
    - Link details
    
    Returns:
    - Link record
    """
    return {
        "link_id": "LINK-001",
        "collateral_id": collateral_id,
        "account_id": request.loan_account_id,
        "allocated_value": str(request.allocated_value),
        "message": "Collateral linked to loan successfully"
    }


@router.post("/collateral/{collateral_id}/valuations", response_model=dict)
async def create_valuation(
    collateral_id: str,
    request: CreateValuationRequest
):
    """
    Create collateral valuation
    
    Path Parameters:
    - collateral_id: Collateral ID
    
    Request Body:
    - Valuation details
    
    Returns:
    - Valuation record
    """
    return {
        "valuation_id": "VAL-001",
        "collateral_id": collateral_id,
        "valued_amount": str(request.valued_amount),
        "valuation_method": request.valuation_method.value,
        "message": "Valuation created successfully"
    }


@router.post("/collateral/{collateral_id}/ppsr", response_model=dict)
async def register_ppsr(
    collateral_id: str,
    request: RegisterPPSRRequest
):
    """
    Register PPSR (Personal Property Securities Register)
    
    Path Parameters:
    - collateral_id: Collateral ID
    
    Request Body:
    - PPSR registration details
    
    Returns:
    - PPSR registration record
    """
    return {
        "registration_id": "PPSR-001",
        "collateral_id": collateral_id,
        "ppsr_registration_number": request.ppsr_registration_number,
        "status": "active",
        "message": "PPSR registered successfully"
    }


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

@router.get("/analytics/portfolio-summary", response_model=dict)
async def get_portfolio_summary():
    """
    Get loan portfolio summary
    
    Returns:
    - Portfolio analytics
    """
    return {
        "total_accounts": 1250,
        "total_principal": "62500000.00",
        "total_outstanding": "58750000.00",
        "average_loan_size": "50000.00",
        "average_interest_rate": "0.0650",
        "arrears_rate": "0.025",
        "default_rate": "0.005"
    }


@router.get("/analytics/risk-distribution", response_model=dict)
async def get_risk_distribution():
    """
    Get risk distribution across portfolio
    
    Returns:
    - Risk analytics
    """
    return {
        "excellent": {"count": 500, "percentage": 40.0},
        "good": {"count": 450, "percentage": 36.0},
        "fair": {"count": 200, "percentage": 16.0},
        "poor": {"count": 75, "percentage": 6.0},
        "very_poor": {"count": 25, "percentage": 2.0}
    }

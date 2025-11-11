"""
Loan Router

Loan management endpoints
"""

from fastapi import APIRouter, status, Query, Path
from typing import Optional
from decimal import Decimal

from ultracore.api.schemas.loans import (
    LoanApplicationRequest,
    LoanRepaymentRequest,
    LoanResponse,
    LoanListResponse,
    LoanPaymentScheduleResponse
)
from ultracore.api.schemas.common import SuccessResponse
from ultracore.api.exceptions import NotFoundException, ValidationException
from ultracore.lending.loan_manager import get_loan_manager
from ultracore.lending.loan_models import LoanType
from ultracore.customers.core.customer_manager import get_customer_manager
from ultracore.accounts.core.account_manager import get_account_manager

router = APIRouter(prefix="/loans")


@router.post("/apply", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_loan(request: LoanApplicationRequest) -> LoanResponse:
    """
    Apply for a loan
    
    Creates a new loan application
    """
    loan_manager = get_loan_manager()
    customer_manager = get_customer_manager()
    
    # Validate customer
    customer = customer_manager.get_customer(request.customer_id)
    if not customer:
        raise NotFoundException("Customer", request.customer_id)
    
    # Map loan type
    loan_type = LoanType[request.loan_type.value]
    
    # Create loan application
    loan = await loan_manager.create_loan_application(
        customer_id=request.customer_id,
        loan_type=loan_type,
        requested_amount=request.requested_amount,
        term_months=request.term_months,
        purpose=request.purpose,
        annual_income=request.annual_income,
        employment_status=request.employment_status,
        created_by="API"
    )
    
    return _loan_to_response(loan)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: str) -> LoanResponse:
    """
    Get loan by ID
    
    Returns complete loan information
    """
    loan_manager = get_loan_manager()
    
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        raise NotFoundException("Loan", loan_id)
    
    return _loan_to_response(loan)


@router.get("", response_model=LoanListResponse)
async def list_loans(
    customer_id: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> LoanListResponse:
    """
    List loans
    
    Returns paginated list of loans
    """
    loan_manager = get_loan_manager()
    
    # Get loans
    if customer_id:
        all_loans = loan_manager.get_customer_loans(customer_id)
    else:
        all_loans = list(loan_manager.loans.values())
    
    # Apply filters
    if loan_type:
        all_loans = [l for l in all_loans if l.loan_type.value == loan_type]
    
    if status:
        all_loans = [l for l in all_loans if l.status.value == status]
    
    # Pagination
    total = len(all_loans)
    loans = all_loans[offset:offset + limit]
    
    return LoanListResponse(
        loans=[_loan_to_response(l) for l in loans],
        total=total
    )


@router.post("/{loan_id}/approve", response_model=LoanResponse)
async def approve_loan(
    loan_id: str,
    approved_amount: Optional[Decimal] = Query(None),
    interest_rate: Optional[Decimal] = Query(None)
) -> LoanResponse:
    """
    Approve loan application
    
    Approves and activates the loan
    """
    loan_manager = get_loan_manager()
    
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        raise NotFoundException("Loan", loan_id)
    
    # Approve loan
    await loan_manager.approve_loan(
        loan_id=loan_id,
        approved_amount=approved_amount,
        approved_rate=interest_rate,
        approved_by="API"
    )
    
    # Get updated loan
    loan = loan_manager.get_loan(loan_id)
    return _loan_to_response(loan)


@router.post("/{loan_id}/disburse", response_model=SuccessResponse)
async def disburse_loan(
    loan_id: str,
    disbursement_account_id: str = Query(..., description="Account to deposit funds")
) -> SuccessResponse:
    """
    Disburse loan funds
    
    Transfers approved loan amount to customer account
    """
    loan_manager = get_loan_manager()
    account_manager = get_account_manager()
    
    # Validate loan
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        raise NotFoundException("Loan", loan_id)
    
    # Validate account
    account = await account_manager.get_account(disbursement_account_id)
    if not account:
        raise NotFoundException("Account", disbursement_account_id)
    
    # Disburse
    await loan_manager.disburse_loan(
        loan_id=loan_id,
        disbursement_account_id=disbursement_account_id,
        disbursed_by="API"
    )
    
    return SuccessResponse(
        message="Loan disbursed successfully",
        data={
            "loan_id": loan_id,
            "amount": float(loan.approved_amount),
            "account_id": disbursement_account_id
        }
    )


@router.post("/{loan_id}/repay", response_model=SuccessResponse)
async def make_loan_payment(
    loan_id: str,
    request: LoanRepaymentRequest
) -> SuccessResponse:
    """
    Make loan payment
    
    Processes a loan repayment
    """
    loan_manager = get_loan_manager()
    account_manager = get_account_manager()
    
    # Validate loan
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        raise NotFoundException("Loan", loan_id)
    
    # Validate account
    account = await account_manager.get_account(request.account_id)
    if not account:
        raise NotFoundException("Account", request.account_id)
    
    # Check sufficient funds
    if account.balance.available_balance < request.amount:
        from ultracore.api.exceptions import InsufficientFundsException
        raise InsufficientFundsException(
            account_id=request.account_id,
            requested=str(request.amount),
            available=str(account.balance.available_balance)
        )
    
    # Process payment
    payment = await loan_manager.process_payment(
        loan_id=loan_id,
        amount=request.amount,
        payment_date=None,  # Today
        payment_account_id=request.account_id,
        processed_by="API"
    )
    
    return SuccessResponse(
        message="Payment processed successfully",
        data={
            "payment_id": payment.payment_id,
            "amount": float(request.amount),
            "principal_paid": float(payment.principal_amount),
            "interest_paid": float(payment.interest_amount),
            "new_balance": float(loan.current_balance)
        }
    )


@router.get("/{loan_id}/schedule", response_model=LoanPaymentScheduleResponse)
async def get_payment_schedule(loan_id: str) -> LoanPaymentScheduleResponse:
    """
    Get payment schedule
    
    Returns complete amortization schedule
    """
    loan_manager = get_loan_manager()
    
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        raise NotFoundException("Loan", loan_id)
    
    if not loan.payment_schedule:
        raise ValidationException("Payment schedule not yet generated")
    
    schedule = loan.payment_schedule
    
    return LoanPaymentScheduleResponse(
        loan_id=loan_id,
        payments=[
            {
                "payment_number": p.payment_number,
                "due_date": p.due_date.isoformat(),
                "payment_amount": float(p.payment_amount),
                "principal": float(p.principal_amount),
                "interest": float(p.interest_amount),
                "balance_after": float(p.balance_after),
                "status": p.status.value
            }
            for p in schedule.scheduled_payments
        ],
        total_payments=len(schedule.scheduled_payments),
        total_principal=float(schedule.total_principal),
        total_interest=float(schedule.total_interest)
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _loan_to_response(loan) -> LoanResponse:
    """Convert Loan model to LoanResponse"""
    
    return LoanResponse(
        loan_id=loan.loan_id,
        customer_id=loan.customer_id,
        loan_type=loan.loan_type.value,
        status=loan.status.value,
        original_amount=float(loan.approved_amount or loan.requested_amount),
        current_balance=float(loan.current_balance),
        currency=loan.currency,
        interest_rate=float(loan.interest_rate),
        term_months=loan.term_months,
        monthly_payment=float(loan.monthly_payment) if loan.monthly_payment else 0.0,
        disbursement_date=loan.disbursement_date,
        first_payment_date=loan.first_payment_date,
        maturity_date=loan.maturity_date,
        principal_balance=float(loan.principal_balance),
        interest_balance=float(loan.interest_balance),
        fees_balance=float(loan.fees_balance),
        payments_made=loan.payments_made,
        payments_remaining=loan.payments_remaining,
        next_payment_date=loan.next_payment_date,
        next_payment_amount=float(loan.next_payment_amount) if loan.next_payment_amount else None,
        created_at=loan.created_at,
        approved_at=loan.approved_at
    )

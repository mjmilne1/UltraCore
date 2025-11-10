from fastapi import APIRouter
from decimal import Decimal
import uuid

from ultracore.domains.loan.aggregate import LoanAggregate, LoanApplicationRequest

router = APIRouter()


@router.post('/')
async def apply_for_loan(request: LoanApplicationRequest):
    loan_id = f'LOAN-{str(uuid.uuid4())[:8]}'
    
    loan = LoanAggregate(loan_id)
    await loan.apply_for_loan(
        customer_id=request.customer_id,
        amount=Decimal(str(request.amount)),
        term_months=request.term_months,
        purpose=request.purpose
    )
    
    return {
        'loan_id': loan_id,
        'status': 'PENDING',
        'message': 'Loan application stored in event store'
    }


@router.get('/{loan_id}')
async def get_loan(loan_id: str):
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    
    return {
        'loan_id': loan.loan_id,
        'customer_id': loan.customer_id,
        'amount': str(loan.amount) if loan.amount else None,
        'term_months': loan.term_months,
        'status': loan.status
    }


@router.post('/{loan_id}/approve')
async def approve_loan(loan_id: str, approved_by: str = 'admin', ml_score: float = 750):
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    await loan.approve(approved_by, ml_score)
    
    return {
        'loan_id': loan_id,
        'status': 'APPROVED',
        'message': 'Loan approved - event stored'
    }

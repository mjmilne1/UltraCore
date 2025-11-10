"""
Loan Servicing API - Complete Loan Lifecycle Management
"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal
from pydantic import BaseModel

from ultracore.domains.loan.servicing import LoanServicing, PaymentFrequency
from ultracore.domains.loan.aggregate import LoanAggregate

router = APIRouter()


class SetupServicingRequest(BaseModel):
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY


class MakePaymentRequest(BaseModel):
    account_id: str
    payment_amount: float
    payment_date: str = None


@router.post('/{loan_id}/servicing/setup')
async def setup_loan_servicing(loan_id: str, request: SetupServicingRequest):
    '''Setup loan servicing after approval'''
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    
    if not loan.customer_id:
        raise HTTPException(status_code=404, detail='Loan not found')
    
    if loan.status != 'APPROVED':
        raise HTTPException(status_code=400, detail=f'Loan must be approved first')
    
    servicing = LoanServicing(loan_id)
    await servicing.setup_servicing(
        principal=loan.amount,
        interest_rate=loan.interest_rate,
        term_months=loan.term_months,
        frequency=request.payment_frequency
    )
    
    return {
        'loan_id': loan_id,
        'principal': str(servicing.principal),
        'interest_rate': str(servicing.interest_rate),
        'monthly_payment': servicing.payment_schedule[0]['payment_amount'] if servicing.payment_schedule else 0,
        'number_of_payments': len(servicing.payment_schedule)
    }


@router.get('/{loan_id}/servicing/schedule')
async def get_amortization_schedule(loan_id: str):
    '''Get complete amortization schedule'''
    servicing = LoanServicing(loan_id)
    await servicing.load_from_events()
    
    if not servicing.payment_schedule:
        raise HTTPException(status_code=404, detail='Servicing not setup')
    
    return {
        'loan_id': loan_id,
        'schedule': servicing.payment_schedule
    }


@router.post('/{loan_id}/servicing/payment')
async def make_loan_payment(loan_id: str, request: MakePaymentRequest):
    '''Make a loan payment'''
    servicing = LoanServicing(loan_id)
    await servicing.load_from_events()
    
    if not servicing.payment_schedule:
        raise HTTPException(status_code=404, detail='Servicing not setup')
    
    try:
        payment_result = await servicing.process_payment(
            payment_amount=Decimal(str(request.payment_amount)),
            account_id=request.account_id,
            payment_date=request.payment_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'loan_id': loan_id,
        'payment_processed': True,
        **payment_result
    }


@router.get('/{loan_id}/servicing/statement')
async def get_loan_statement(loan_id: str):
    '''Generate loan statement'''
    servicing = LoanServicing(loan_id)
    await servicing.load_from_events()
    
    if not servicing.payment_schedule:
        raise HTTPException(status_code=404, detail='Servicing not setup')
    
    return {
        'loan_id': loan_id,
        'current_balance': str(servicing.remaining_balance),
        'total_paid': str(servicing.total_principal_paid + servicing.total_interest_paid),
        'status': servicing.loan_status.value
    }

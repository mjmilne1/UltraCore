"""
Loan API with AI-Powered Processing
"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal
import uuid

# from ultracore.domains.loan.aggregate import LoanAggregate, LoanApplicationRequest  # TODO: Fix import path
from ultracore.agentic_ai.agents.anya import anya

router = APIRouter()


@router.post('/')
async def apply_for_loan(request: LoanApplicationRequest):
    """
    Apply for a loan with AI-powered review
    
    Automatically triggers:
    1. Loan application event
    2. AI review by Anya
    3. ML credit scoring
    4. Auto-decision (if confident)
    """
    loan_id = f'LOAN-{str(uuid.uuid4())[:8]}'
    
    loan = LoanAggregate(loan_id)
    
    # Step 1: Apply
    await loan.apply_for_loan(
        customer_id=request.customer_id,
        amount=Decimal(str(request.amount)),
        term_months=request.term_months,
        purpose=request.purpose
    )
    
    # Step 2: AI Review
    customer_data = {
        'annual_income': request.annual_income,
        'existing_debt': request.existing_debt,
        'employment_months': request.employment_months,
        'credit_history_score': request.credit_history_score
    }
    
    ai_review = await loan.ai_review(customer_data)
    
    # Step 3: Auto-decide
    decision = await loan.auto_decide()
    
    return {
        'loan_id': loan_id,
        'status': loan.status,
        'ai_recommendation': ai_review['ai_analysis']['analysis']['recommendation'],
        'credit_score': ai_review['credit_score']['credit_score'],
        'risk_category': ai_review['credit_score']['risk_category'],
        'decision': decision['decision'],
        'decision_method': decision['method'],
        'ai_reasoning': ai_review['ai_analysis']['analysis']['reasoning']
    }


@router.get('/{loan_id}')
async def get_loan(loan_id: str):
    """Get loan details - rebuilds from events"""
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    
    return {
        'loan_id': loan.loan_id,
        'customer_id': loan.customer_id,
        'amount': str(loan.amount) if loan.amount else None,
        'term_months': loan.term_months,
        'status': loan.status,
        'credit_score': loan.credit_score
    }


@router.post('/chat')
async def chat_with_anya(message: str):
    """Chat with Anya about loans"""
    response = await anya.chat(message)
    return {
        'agent': 'Anya',
        'message': response
    }


@router.post('/{loan_id}/manual-approve')
async def manual_approve(loan_id: str, approved_by: str = 'human_underwriter'):
    """Manual approval by human underwriter"""
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    await loan.approve(approved_by, loan.credit_score or 700)
    
    return {
        'loan_id': loan_id,
        'status': 'APPROVED',
        'approved_by': approved_by
    }


@router.post('/{loan_id}/manual-reject')
async def manual_reject(loan_id: str, reason: str, rejected_by: str = 'human_underwriter'):
    """Manual rejection by human underwriter"""
    loan = LoanAggregate(loan_id)
    await loan.load_from_events()
    await loan.reject(rejected_by, reason)
    
    return {
        'loan_id': loan_id,
        'status': 'REJECTED',
        'rejected_by': rejected_by,
        'reason': reason
    }

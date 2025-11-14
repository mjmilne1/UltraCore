"""
Complete Payment API - Full Payment Rails
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.payment.complete_aggregate import (  # TODO: Fix import path
    CompletePaymentAggregate,
    PaymentType,
    PaymentStatus
)

router = APIRouter()


class InitiatePaymentRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    payment_type: PaymentType
    description: str
    reference: str = None


@router.post('/initiate')
async def initiate_payment(request: InitiatePaymentRequest):
    '''
    Initiate payment with fraud detection
    
    Full payment lifecycle with clearing & settlement
    '''
    payment_id = f'PAY-{str(uuid.uuid4())[:8]}'
    
    payment = CompletePaymentAggregate(payment_id)
    await payment.initiate_payment(
        from_account_id=request.from_account_id,
        to_account_id=request.to_account_id,
        amount=Decimal(str(request.amount)),
        payment_type=request.payment_type,
        description=request.description,
        reference=request.reference
    )
    
    # Fraud check
    fraud_approved = await payment.fraud_check()
    
    if not fraud_approved:
        return {
            'payment_id': payment_id,
            'status': payment.status.value,
            'fraud_score': payment.fraud_score,
            'message': 'Payment held for fraud review'
        }
    
    # Process payment
    await payment.process_payment()
    await payment.clear_payment()
    await payment.settle_payment()
    
    return {
        'payment_id': payment_id,
        'status': payment.status.value,
        'payment_rail': payment.payment_rail.value,
        'fraud_score': payment.fraud_score,
        'settlement_date': payment.settlement_date
    }


@router.get('/{payment_id}')
async def get_payment(payment_id: str):
    '''Get payment status'''
    payment = CompletePaymentAggregate(payment_id)
    await payment.load_from_events()
    
    if not payment.from_account_id:
        raise HTTPException(status_code=404, detail='Payment not found')
    
    return {
        'payment_id': payment_id,
        'from_account': payment.from_account_id,
        'to_account': payment.to_account_id,
        'amount': str(payment.amount),
        'status': payment.status.value,
        'payment_type': payment.payment_type.value if payment.payment_type else None,
        'payment_rail': payment.payment_rail.value if payment.payment_rail else None,
        'fraud_score': payment.fraud_score,
        'clearing_id': payment.clearing_id,
        'settlement_date': payment.settlement_date
    }


@router.post('/{payment_id}/reverse')
async def reverse_payment(payment_id: str, reason: str):
    '''Reverse settled payment'''
    payment = CompletePaymentAggregate(payment_id)
    await payment.load_from_events()
    
    if not payment.from_account_id:
        raise HTTPException(status_code=404, detail='Payment not found')
    
    try:
        await payment.reverse_payment(reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'payment_id': payment_id,
        'status': payment.status.value,
        'reversed': True
    }

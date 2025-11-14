"""
Complete Merchant API - Settlement & Reconciliation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.merchant.complete_aggregate import CompleteMerchantAggregate  # TODO: Fix import path

router = APIRouter()


class RegisterMerchantRequest(BaseModel):
    business_name: str
    abn: str
    account_id: str


class ProcessTransactionRequest(BaseModel):
    amount: float
    card_last4: str
    customer_name: str


@router.post('/register')
async def register_merchant(request: RegisterMerchantRequest):
    '''Register merchant for payment processing'''
    merchant_id = f'MER-{str(uuid.uuid4())[:8]}'
    
    merchant = CompleteMerchantAggregate(merchant_id)
    await merchant.register_merchant(
        business_name=request.business_name,
        abn=request.abn,
        account_id=request.account_id
    )
    
    return {
        'merchant_id': merchant_id,
        'business_name': merchant.business_name,
        'status': merchant.status.value,
        'processing_rate': str(merchant.processing_rate) + '%'
    }


@router.post('/{merchant_id}/transactions')
async def process_transaction(merchant_id: str, request: ProcessTransactionRequest):
    '''
    Process merchant transaction
    
    Point-of-sale payment processing
    '''
    merchant = CompleteMerchantAggregate(merchant_id)
    await merchant.load_from_events()
    
    if not merchant.business_name:
        raise HTTPException(status_code=404, detail='Merchant not found')
    
    transaction_id = await merchant.process_transaction(
        amount=Decimal(str(request.amount)),
        card_last4=request.card_last4,
        customer_name=request.customer_name
    )
    
    processing_fee = Decimal(str(request.amount)) * (merchant.processing_rate / 100)
    net_amount = Decimal(str(request.amount)) - processing_fee
    
    return {
        'merchant_id': merchant_id,
        'transaction_id': transaction_id,
        'amount': str(request.amount),
        'processing_fee': str(processing_fee),
        'net_amount': str(net_amount)
    }


@router.post('/{merchant_id}/settle')
async def settle_batch(merchant_id: str):
    '''
    Settle merchant transactions
    
    Batch settlement to merchant account
    '''
    merchant = CompleteMerchantAggregate(merchant_id)
    await merchant.load_from_events()
    
    if not merchant.business_name:
        raise HTTPException(status_code=404, detail='Merchant not found')
    
    settlement_id = await merchant.settle_batch()
    
    if not settlement_id:
        return {
            'merchant_id': merchant_id,
            'message': 'No unsettled transactions'
        }
    
    return {
        'merchant_id': merchant_id,
        'settlement_id': settlement_id,
        'settlements_count': len(merchant.settlements)
    }


@router.get('/{merchant_id}')
async def get_merchant(merchant_id: str):
    '''Get merchant details'''
    merchant = CompleteMerchantAggregate(merchant_id)
    await merchant.load_from_events()
    
    if not merchant.business_name:
        raise HTTPException(status_code=404, detail='Merchant not found')
    
    return {
        'merchant_id': merchant_id,
        'business_name': merchant.business_name,
        'status': merchant.status.value,
        'account_id': merchant.account_id,
        'processing_rate': str(merchant.processing_rate) + '%',
        'total_volume': str(merchant.total_volume),
        'transaction_count': len(merchant.transactions),
        'settlement_count': len(merchant.settlements)
    }

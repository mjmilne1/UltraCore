"""
Merchant Domain API
"""
from fastapi import APIRouter, HTTPException
import uuid

from ultracore.domains.merchant.aggregate import (
    MerchantAggregate, RegisterMerchantRequest
)

router = APIRouter()


@router.post('/register')
async def register_merchant(request: RegisterMerchantRequest):
    '''Register new merchant'''
    merchant_id = f'MER-{str(uuid.uuid4())[:8]}'
    
    merchant = MerchantAggregate(merchant_id)
    await merchant.register_merchant(
        business_name=request.business_name,
        abn=request.abn
    )
    
    return {
        'merchant_id': merchant_id,
        'business_name': request.business_name,
        'status': 'ACTIVE',
        'processing_rate': '2.0%'
    }


@router.get('/{merchant_id}')
async def get_merchant(merchant_id: str):
    '''Get merchant details'''
    merchant = MerchantAggregate(merchant_id)
    await merchant.load_from_events()
    
    if not merchant.business_name:
        raise HTTPException(status_code=404, detail='Merchant not found')
    
    return {
        'merchant_id': merchant_id,
        'business_name': merchant.business_name,
        'status': merchant.status.value,
        'processing_rate': '2.0%'
    }

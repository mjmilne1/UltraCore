"""
Cards Domain API
"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal
import uuid

from ultracore.domains.cards.aggregate import (
    CardAggregate, IssueCardRequest, CardTransactionRequest, CardType
)

router = APIRouter()


@router.post('/')
async def issue_card(request: IssueCardRequest):
    '''
    Issue a new card
    
    Types: DEBIT, CREDIT, PREPAID
    '''
    card_id = f'CARD-{str(uuid.uuid4())[:8]}'
    
    card = CardAggregate(card_id)
    await card.issue_card(
        account_id=request.account_id,
        card_type=request.card_type,
        credit_limit=Decimal(str(request.credit_limit)) if request.credit_limit else None
    )
    
    # Auto-activate for demo
    await card.activate()
    
    return {
        'card_id': card_id,
        'card_number': card.card_number,
        'cvv': card.cvv,
        'expiry_date': card.expiry_date,
        'card_type': card.card_type.value,
        'status': card.status.value,
        'credit_limit': str(card.credit_limit) if card.card_type == CardType.CREDIT else None
    }


@router.get('/{card_id}')
async def get_card(card_id: str):
    '''Get card details'''
    card = CardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    return {
        'card_id': card.card_id,
        'card_number': card.card_number[-4:].rjust(len(card.card_number), '*'),  # Masked
        'card_type': card.card_type.value if card.card_type else None,
        'status': card.status.value,
        'expiry_date': card.expiry_date,
        'credit_limit': str(card.credit_limit) if card.card_type == CardType.CREDIT else None,
        'available_credit': str(card.available_credit) if card.card_type == CardType.CREDIT else None
    }


@router.post('/{card_id}/transaction')
async def process_transaction(card_id: str, request: CardTransactionRequest):
    '''
    Process card transaction
    
    Includes fraud detection
    '''
    card = CardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    try:
        await card.process_transaction(
            merchant_name=request.merchant_name,
            amount=Decimal(str(request.amount)),
            merchant_category=request.merchant_category
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'card_id': card_id,
        'merchant': request.merchant_name,
        'amount': str(request.amount),
        'status': 'APPROVED',
        'available_credit': str(card.available_credit) if card.card_type == CardType.CREDIT else None
    }


@router.get('/{card_id}/transactions')
async def get_card_transactions(card_id: str):
    '''Get card transaction history'''
    card = CardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    return {
        'card_id': card_id,
        'transactions': card.transactions,
        'total_transactions': len(card.transactions)
    }


@router.post('/{card_id}/block')
async def block_card(card_id: str, reason: str = 'Customer request'):
    '''Block card'''
    card = CardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    await card.block(reason)
    
    return {
        'card_id': card_id,
        'status': 'BLOCKED',
        'reason': reason
    }

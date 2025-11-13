"""
Complete Cards API - Full Card Lifecycle
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.cards.complete_aggregate import (  # TODO: Fix import path
    CompleteCardAggregate,
    CardType,
    CardStatus
)

router = APIRouter()


class IssueCardRequest(BaseModel):
    account_id: str
    card_type: CardType
    credit_limit: float = None


class AuthorizeTransactionRequest(BaseModel):
    amount: float
    merchant: str
    merchant_category: str
    location: str


class DisputeTransactionRequest(BaseModel):
    transaction_id: str
    reason: str


@router.post('/issue')
async def issue_card(request: IssueCardRequest):
    '''
    Issue new card
    
    Supports debit, credit, prepaid
    '''
    card_id = f'CRD-{str(uuid.uuid4())[:8]}'
    
    card = CompleteCardAggregate(card_id)
    await card.issue_card(
        account_id=request.account_id,
        card_type=request.card_type,
        credit_limit=Decimal(str(request.credit_limit)) if request.credit_limit else None
    )
    
    await card.activate_card()
    
    return {
        'card_id': card_id,
        'card_type': card.card_type.value,
        'card_number_last4': card.card_number_last4,
        'status': card.status.value,
        'expiry_date': card.expiry_date,
        'credit_limit': str(card.credit_limit) if card.credit_limit else None
    }


@router.post('/{card_id}/authorize')
async def authorize_transaction(card_id: str, request: AuthorizeTransactionRequest):
    '''
    Authorize card transaction
    
    ML fraud detection included
    '''
    card = CompleteCardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    transaction_id = await card.authorize_transaction(
        amount=Decimal(str(request.amount)),
        merchant=request.merchant,
        merchant_category=request.merchant_category,
        location=request.location
    )
    
    if not transaction_id:
        return {
            'authorized': False,
            'message': 'Transaction declined'
        }
    
    return {
        'authorized': True,
        'transaction_id': transaction_id,
        'card_id': card_id,
        'amount': str(request.amount)
    }


@router.post('/{card_id}/settle/{transaction_id}')
async def settle_transaction(card_id: str, transaction_id: str):
    '''Settle authorized transaction'''
    card = CompleteCardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    try:
        await card.settle_transaction(transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'card_id': card_id,
        'transaction_id': transaction_id,
        'settled': True
    }


@router.post('/{card_id}/dispute')
async def dispute_transaction(card_id: str, request: DisputeTransactionRequest):
    '''Dispute a transaction'''
    card = CompleteCardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    dispute_id = await card.dispute_transaction(
        transaction_id=request.transaction_id,
        reason=request.reason
    )
    
    return {
        'card_id': card_id,
        'dispute_id': dispute_id,
        'transaction_id': request.transaction_id
    }


@router.get('/{card_id}')
async def get_card(card_id: str):
    '''Get card details'''
    card = CompleteCardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    return {
        'card_id': card_id,
        'account_id': card.account_id,
        'card_type': card.card_type.value if card.card_type else None,
        'card_number_last4': card.card_number_last4,
        'status': card.status.value,
        'expiry_date': card.expiry_date,
        'credit_limit': str(card.credit_limit) if card.credit_limit else None,
        'available_credit': str(card.available_credit) if card.available_credit else None,
        'transaction_count': len(card.transactions),
        'dispute_count': len(card.disputes)
    }


@router.get('/{card_id}/transactions')
async def get_transactions(card_id: str):
    '''Get all card transactions'''
    card = CompleteCardAggregate(card_id)
    await card.load_from_events()
    
    if not card.account_id:
        raise HTTPException(status_code=404, detail='Card not found')
    
    return {
        'card_id': card_id,
        'transactions': card.transactions
    }

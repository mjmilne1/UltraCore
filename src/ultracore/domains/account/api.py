"""
Complete Account API - Full Account Lifecycle
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.account.complete_aggregate import (  # TODO: Fix import path
    CompleteAccountAggregate,
    AccountType,
    AccountStatus
)

router = APIRouter()


class CreateAccountRequest(BaseModel):
    client_id: str
    account_type: AccountType
    initial_deposit: float = 0


class DepositRequest(BaseModel):
    amount: float
    description: str
    reference: str = None


class WithdrawRequest(BaseModel):
    amount: float
    description: str
    reference: str = None


class PlaceHoldRequest(BaseModel):
    amount: float
    reason: str


@router.post('/open')
async def open_account(request: CreateAccountRequest):
    '''
    Open new account
    
    Creates account with initial deposit
    '''
    account_id = f'ACC-{str(uuid.uuid4())[:8]}'
    
    account = CompleteAccountAggregate(account_id)
    await account.open_account(
        client_id=request.client_id,
        account_type=request.account_type,
        initial_deposit=Decimal(str(request.initial_deposit))
    )
    
    # Auto-activate
    await account.activate()
    
    return {
        'account_id': account_id,
        'client_id': request.client_id,
        'account_type': request.account_type.value,
        'status': account.status.value,
        'balance': str(account.balance),
        'available_balance': str(account.available_balance)
    }


@router.post('/{account_id}/deposit')
async def deposit(account_id: str, request: DepositRequest):
    '''Deposit funds'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    await account.deposit(
        amount=Decimal(str(request.amount)),
        description=request.description,
        reference=request.reference
    )
    
    return {
        'account_id': account_id,
        'new_balance': str(account.balance),
        'available_balance': str(account.available_balance)
    }


@router.post('/{account_id}/withdraw')
async def withdraw(account_id: str, request: WithdrawRequest):
    '''Withdraw funds'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    try:
        await account.withdraw(
            amount=Decimal(str(request.amount)),
            description=request.description,
            reference=request.reference
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'account_id': account_id,
        'new_balance': str(account.balance),
        'available_balance': str(account.available_balance)
    }


@router.post('/{account_id}/hold')
async def place_hold(account_id: str, request: PlaceHoldRequest):
    '''Place hold on funds'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    hold_id = f'HLD-{str(uuid.uuid4())[:8]}'
    
    try:
        await account.place_hold(
            hold_id=hold_id,
            amount=Decimal(str(request.amount)),
            reason=request.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'account_id': account_id,
        'hold_id': hold_id,
        'available_balance': str(account.available_balance)
    }


@router.delete('/{account_id}/hold/{hold_id}')
async def release_hold(account_id: str, hold_id: str):
    '''Release hold'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    try:
        await account.release_hold(hold_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'account_id': account_id,
        'available_balance': str(account.available_balance)
    }


@router.get('/{account_id}')
async def get_account(account_id: str):
    '''Get account details'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    return {
        'account_id': account_id,
        'client_id': account.client_id,
        'account_type': account.account_type.value if account.account_type else None,
        'status': account.status.value,
        'balance': str(account.balance),
        'available_balance': str(account.available_balance),
        'currency': account.currency,
        'holds': {k: str(v) for k, v in account.holds.items()}
    }


@router.get('/{account_id}/statement')
async def get_statement(account_id: str, from_date: str, to_date: str):
    '''Get account statement'''
    account = CompleteAccountAggregate(account_id)
    await account.load_from_events()
    
    if not account.client_id:
        raise HTTPException(status_code=404, detail='Account not found')
    
    statement = await account.get_statement(from_date, to_date)
    
    return statement

"""
Account Router

Account management endpoints
"""

from fastapi import APIRouter, status, Query, Path
from typing import List, Optional
from decimal import Decimal

from ultracore.api.schemas.accounts import (
    AccountCreateRequest,
    AccountResponse,
    AccountListResponse,
    AccountBalanceResponse
)
from ultracore.api.schemas.common import SuccessResponse
from ultracore.api.exceptions import NotFoundException, ValidationException, BusinessRuleException
from ultracore.accounts.core.account_manager import get_account_manager
from ultracore.accounts.core.account_models import AccountType
from ultracore.customers.core.customer_manager import get_customer_manager

router = APIRouter(prefix="/accounts")


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(request: AccountCreateRequest) -> AccountResponse:
    """
    Open a new account
    
    Creates a new account for an existing customer
    """
    manager = get_account_manager()
    customer_manager = get_customer_manager()
    
    # Validate customer exists
    customer = customer_manager.get_customer(request.customer_id)
    if not customer:
        raise NotFoundException("Customer", request.customer_id)
    
    # Map account type
    account_type = AccountType[request.account_type.value]
    
    # Create account
    account = await manager.open_account(
        customer_id=request.customer_id,
        account_type=account_type,
        currency=request.currency,
        opened_by="API",
        initial_deposit=request.initial_deposit,
        interest_bearing=request.interest_bearing,
        interest_rate=request.interest_rate,
        term_months=request.term_months
    )
    
    # Convert to response
    return _account_to_response(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str = Path(..., description="Account ID")
) -> AccountResponse:
    """
    Get account by ID
    
    Returns complete account information including balance
    """
    manager = get_account_manager()
    
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    return _account_to_response(account)


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> AccountListResponse:
    """
    List accounts
    
    Returns paginated list of accounts with optional filtering
    """
    manager = get_account_manager()
    
    # Get accounts
    if customer_id:
        all_accounts = await manager.get_customer_accounts(customer_id)
    else:
        all_accounts = list(manager.accounts.values())
    
    # Apply filters
    if account_type:
        all_accounts = [a for a in all_accounts if a.account_type.value == account_type]
    
    if status:
        all_accounts = [a for a in all_accounts if a.status.value == status]
    
    # Apply pagination
    total = len(all_accounts)
    accounts = all_accounts[offset:offset + limit]
    
    return AccountListResponse(
        accounts=[_account_to_response(a) for a in accounts],
        total=total
    )


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
async def get_account_balance(account_id: str) -> AccountBalanceResponse:
    """
    Get account balance
    
    Returns detailed balance information
    """
    manager = get_account_manager()
    
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    return AccountBalanceResponse(
        ledger_balance=float(account.balance.ledger_balance),
        available_balance=float(account.balance.available_balance),
        pending_credits=float(account.balance.pending_credits),
        pending_debits=float(account.balance.pending_debits),
        held_amount=float(account.balance.held_amount),
        minimum_balance=float(account.balance.minimum_balance) if account.balance.minimum_balance else None
    )


@router.post("/{account_id}/freeze", response_model=SuccessResponse)
async def freeze_account(account_id: str) -> SuccessResponse:
    """
    Freeze account
    
    Prevents all transactions on the account
    """
    manager = get_account_manager()
    
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    await manager.freeze_account(account_id, reason="Frozen via API", frozen_by="API")
    
    return SuccessResponse(
        message="Account frozen successfully",
        data={"account_id": account_id}
    )


@router.post("/{account_id}/unfreeze", response_model=SuccessResponse)
async def unfreeze_account(account_id: str) -> SuccessResponse:
    """
    Unfreeze account
    
    Allows transactions on the account again
    """
    manager = get_account_manager()
    
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    await manager.unfreeze_account(account_id, unfrozen_by="API")
    
    return SuccessResponse(
        message="Account unfrozen successfully",
        data={"account_id": account_id}
    )


@router.delete("/{account_id}", response_model=SuccessResponse)
async def close_account(account_id: str) -> SuccessResponse:
    """
    Close account
    
    Closes the account (requires zero balance)
    """
    manager = get_account_manager()
    
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    await manager.close_account(account_id, closed_by="API")
    
    return SuccessResponse(
        message="Account closed successfully",
        data={"account_id": account_id}
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _account_to_response(account) -> AccountResponse:
    """Convert Account model to AccountResponse"""
    
    balance = AccountBalanceResponse(
        ledger_balance=float(account.balance.ledger_balance),
        available_balance=float(account.balance.available_balance),
        pending_credits=float(account.balance.pending_credits),
        pending_debits=float(account.balance.pending_debits),
        held_amount=float(account.balance.held_amount),
        minimum_balance=float(account.balance.minimum_balance) if account.balance.minimum_balance else None
    )
    
    current_rate = None
    if account.interest_bearing and account.current_interest_rate:
        current_rate = float(account.current_interest_rate.annual_rate)
    
    return AccountResponse(
        account_id=account.account_id,
        account_number=account.account_number,
        customer_id=account.customer_id,
        account_type=account.account_type.value,
        status=account.status.value,
        currency=account.currency,
        balance=balance,
        interest_bearing=account.interest_bearing,
        current_interest_rate=current_rate,
        maturity_date=account.maturity_date,
        opened_date=account.opened_date,
        closed_date=account.closed_date,
        last_transaction_date=account.last_transaction_date
    )

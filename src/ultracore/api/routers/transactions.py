"""
Transaction Router

Transaction processing endpoints
"""

from fastapi import APIRouter, status, Query, Path
from typing import List, Optional
from datetime import datetime, timedelta

from ultracore.api.schemas.accounts import (
    DepositRequest,
    WithdrawalRequest,
    TransferRequest,
    TransactionResponse,
    TransactionListResponse
)
from ultracore.api.schemas.common import SuccessResponse
from ultracore.api.exceptions import (
    NotFoundException,
    InsufficientFundsException,
    BusinessRuleException
)
from ultracore.accounts.core.account_manager import get_account_manager
from ultracore.accounts.core.account_models import TransactionType

router = APIRouter(prefix="/transactions")


@router.post("/deposit", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def deposit(
    account_id: str = Query(..., description="Account ID"),
    request: DepositRequest = ...
) -> TransactionResponse:
    """
    Make a deposit
    
    Deposits money into an account
    """
    manager = get_account_manager()
    
    # Validate account exists
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    # Process deposit
    transaction = await manager.deposit(
        account_id=account_id,
        amount=request.amount,
        description=request.description or "Deposit",
        reference=request.reference,
        deposited_by="API"
    )
    
    return _transaction_to_response(transaction)


@router.post("/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def withdraw(
    account_id: str = Query(..., description="Account ID"),
    request: WithdrawalRequest = ...
) -> TransactionResponse:
    """
    Make a withdrawal
    
    Withdraws money from an account
    """
    manager = get_account_manager()
    
    # Validate account exists
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    # Check sufficient funds
    if account.balance.available_balance < request.amount:
        raise InsufficientFundsException(
            account_id=account_id,
            requested=str(request.amount),
            available=str(account.balance.available_balance)
        )
    
    # Process withdrawal
    transaction = await manager.withdraw(
        account_id=account_id,
        amount=request.amount,
        description=request.description or "Withdrawal",
        reference=request.reference,
        withdrawn_by="API"
    )
    
    return _transaction_to_response(transaction)


@router.post("/transfer", response_model=dict, status_code=status.HTTP_201_CREATED)
async def transfer(request: TransferRequest) -> dict:
    """
    Transfer between accounts
    
    Transfers money from one account to another
    """
    manager = get_account_manager()
    
    # Validate accounts exist
    from_account = await manager.get_account(request.from_account_id)
    if not from_account:
        raise NotFoundException("Source Account", request.from_account_id)
    
    to_account = await manager.get_account(request.to_account_id)
    if not to_account:
        raise NotFoundException("Destination Account", request.to_account_id)
    
    # Check sufficient funds
    if from_account.balance.available_balance < request.amount:
        raise InsufficientFundsException(
            account_id=request.from_account_id,
            requested=str(request.amount),
            available=str(from_account.balance.available_balance)
        )
    
    # Process transfer
    debit_txn, credit_txn = await manager.internal_transfer(
        from_account_id=request.from_account_id,
        to_account_id=request.to_account_id,
        amount=request.amount,
        description=request.description or "Internal Transfer",
        reference=request.reference,
        transferred_by="API"
    )
    
    return {
        "success": True,
        "message": "Transfer completed successfully",
        "data": {
            "debit_transaction": _transaction_to_response(debit_txn),
            "credit_transaction": _transaction_to_response(credit_txn)
        }
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str = Path(..., description="Transaction ID")
) -> TransactionResponse:
    """
    Get transaction by ID
    
    Returns transaction details
    """
    manager = get_account_manager()
    
    # Search through all accounts for the transaction
    for account in manager.accounts.values():
        for txn in account.transactions:
            if txn.transaction_id == transaction_id:
                return _transaction_to_response(txn)
    
    raise NotFoundException("Transaction", transaction_id)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    account_id: str = Query(..., description="Account ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> TransactionListResponse:
    """
    List transactions for an account
    
    Returns paginated transaction history
    """
    manager = get_account_manager()
    
    # Validate account exists
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    # Get transactions
    transactions = account.transactions
    
    # Apply filters
    if transaction_type:
        transactions = [t for t in transactions if t.transaction_type.value == transaction_type]
    
    if start_date:
        transactions = [t for t in transactions if t.transaction_date >= start_date]
    
    if end_date:
        transactions = [t for t in transactions if t.transaction_date <= end_date]
    
    # Sort by date (newest first)
    transactions = sorted(transactions, key=lambda t: t.transaction_date, reverse=True)
    
    # Apply pagination
    total = len(transactions)
    transactions = transactions[offset:offset + limit]
    
    return TransactionListResponse(
        transactions=[_transaction_to_response(t) for t in transactions],
        total=total
    )


@router.get("/account/{account_id}/statement")
async def get_account_statement(
    account_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get account statement
    
    Returns detailed account statement for a period
    """
    manager = get_account_manager()
    
    # Validate account
    account = await manager.get_account(account_id)
    if not account:
        raise NotFoundException("Account", account_id)
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get transactions in period
    transactions = [
        t for t in account.transactions
        if start_date <= t.transaction_date <= end_date
    ]
    
    # Sort by date
    transactions = sorted(transactions, key=lambda t: t.transaction_date)
    
    # Calculate totals
    total_credits = sum(
        t.amount for t in transactions 
        if t.transaction_type in [TransactionType.DEPOSIT, TransactionType.INTEREST]
    )
    total_debits = sum(
        t.amount for t in transactions
        if t.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.FEE]
    )
    
    return {
        "account_id": account_id,
        "account_number": account.account_number,
        "statement_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "opening_balance": float(transactions[0].balance_before if transactions else account.balance.ledger_balance),
        "closing_balance": float(account.balance.ledger_balance),
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "transaction_count": len(transactions),
        "transactions": [_transaction_to_response(t) for t in transactions]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _transaction_to_response(transaction) -> TransactionResponse:
    """Convert Transaction model to TransactionResponse"""
    
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        transaction_type=transaction.transaction_type.value,
        status=transaction.status.value,
        amount=float(transaction.amount),
        balance_after=float(transaction.balance_after),
        currency=transaction.currency,
        description=transaction.description,
        reference=transaction.reference,
        related_account_id=transaction.related_account_id,
        related_transaction_id=transaction.related_transaction_id,
        transaction_date=transaction.transaction_date,
        value_date=transaction.value_date,
        posted_date=transaction.posted_date
    )

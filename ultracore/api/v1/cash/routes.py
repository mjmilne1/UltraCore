"""
Cash Management API Router
Handles cash accounts, transactions, and payments
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal

router = APIRouter(prefix="/api/v1/cash", tags=["cash"])

# Models
class AccountType(str, Enum):
    SAVINGS = "SAVINGS"
    TRANSACTION = "TRANSACTION"
    INVESTMENT_CASH = "INVESTMENT_CASH"

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    FEE = "FEE"
    INTEREST = "INTEREST"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"

class CashAccountCreate(BaseModel):
    client_id: str
    account_type: AccountType
    currency: str = "AUD"
    account_name: Optional[str] = None

class CashAccountResponse(BaseModel):
    account_id: str
    client_id: str
    account_type: AccountType
    currency: str
    balance: Decimal
    available_balance: Decimal
    account_name: Optional[str]
    created_at: datetime
    status: str

class TransactionCreate(BaseModel):
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None

class TransactionResponse(BaseModel):
    transaction_id: str
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Decimal
    status: TransactionStatus
    description: Optional[str]
    reference: Optional[str]
    created_at: datetime

# In-memory storage (replace with database in production)
cash_accounts_db = {}
transactions_db = {}

@router.post("/accounts", response_model=CashAccountResponse, status_code=201)
async def create_cash_account(account: CashAccountCreate):
    """
    Create a new cash account
    
    - **client_id**: ID of the client
    - **account_type**: Type of cash account
    - **currency**: Account currency (default: AUD)
    - **account_name**: Optional account name
    """
    import uuid
    
    account_id = str(uuid.uuid4())
    
    account_data = {
        "account_id": account_id,
        **account.model_dump(),
        "balance": Decimal("0.00"),
        "available_balance": Decimal("0.00"),
        "created_at": datetime.now(),
        "status": "ACTIVE"
    }
    
    cash_accounts_db[account_id] = account_data
    
    return CashAccountResponse(**account_data)

@router.get("/accounts", response_model=List[CashAccountResponse])
async def list_cash_accounts(
    client_id: Optional[str] = None,
    account_type: Optional[AccountType] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List all cash accounts with optional filtering
    """
    filtered_accounts = list(cash_accounts_db.values())
    
    if client_id:
        filtered_accounts = [a for a in filtered_accounts if a["client_id"] == client_id]
    
    if account_type:
        filtered_accounts = [a for a in filtered_accounts if a["account_type"] == account_type]
    
    return [CashAccountResponse(**a) for a in filtered_accounts[skip:skip+limit]]

@router.get("/accounts/{account_id}", response_model=CashAccountResponse)
async def get_cash_account(account_id: str):
    """
    Get a specific cash account by ID
    """
    if account_id not in cash_accounts_db:
        raise HTTPException(status_code=404, detail="Cash account not found")
    
    return CashAccountResponse(**cash_accounts_db[account_id])

@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(transaction: TransactionCreate):
    """
    Create a new cash transaction
    
    - **account_id**: ID of the cash account
    - **transaction_type**: Type of transaction
    - **amount**: Transaction amount
    - **description**: Optional description
    - **reference**: Optional reference number
    """
    import uuid
    
    if transaction.account_id not in cash_accounts_db:
        raise HTTPException(status_code=404, detail="Cash account not found")
    
    account = cash_accounts_db[transaction.account_id]
    
    # Validate balance for withdrawals
    if transaction.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.FEE]:
        if account["available_balance"] < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Update account balance
    if transaction.transaction_type in [TransactionType.DEPOSIT, TransactionType.INTEREST]:
        account["balance"] += transaction.amount
        account["available_balance"] += transaction.amount
    elif transaction.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.FEE]:
        account["balance"] -= transaction.amount
        account["available_balance"] -= transaction.amount
    
    transaction_id = str(uuid.uuid4())
    
    transaction_data = {
        "transaction_id": transaction_id,
        **transaction.model_dump(),
        "balance_after": account["balance"],
        "status": TransactionStatus.COMPLETED,
        "created_at": datetime.now()
    }
    
    transactions_db[transaction_id] = transaction_data
    cash_accounts_db[transaction.account_id] = account
    
    return TransactionResponse(**transaction_data)

@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    account_id: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List all transactions with optional filtering
    """
    filtered_transactions = list(transactions_db.values())
    
    if account_id:
        filtered_transactions = [t for t in filtered_transactions if t["account_id"] == account_id]
    
    if transaction_type:
        filtered_transactions = [t for t in filtered_transactions if t["transaction_type"] == transaction_type]
    
    if status:
        filtered_transactions = [t for t in filtered_transactions if t["status"] == status]
    
    # Sort by created_at descending
    filtered_transactions.sort(key=lambda x: x["created_at"], reverse=True)
    
    return [TransactionResponse(**t) for t in filtered_transactions[skip:skip+limit]]

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """
    Get a specific transaction by ID
    """
    if transaction_id not in transactions_db:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse(**transactions_db[transaction_id])

@router.get("/accounts/{account_id}/balance")
async def get_account_balance(account_id: str):
    """
    Get current balance for a cash account
    """
    if account_id not in cash_accounts_db:
        raise HTTPException(status_code=404, detail="Cash account not found")
    
    account = cash_accounts_db[account_id]
    
    return {
        "account_id": account_id,
        "balance": account["balance"],
        "available_balance": account["available_balance"],
        "currency": account["currency"],
        "as_of": datetime.now()
    }

@router.get("/accounts/{account_id}/statement")
async def get_account_statement(
    account_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
):
    """
    Get account statement with transaction history
    """
    if account_id not in cash_accounts_db:
        raise HTTPException(status_code=404, detail="Cash account not found")
    
    account = cash_accounts_db[account_id]
    
    # Filter transactions for this account
    account_transactions = [t for t in transactions_db.values() if t["account_id"] == account_id]
    
    # Apply date filters
    if start_date:
        account_transactions = [t for t in account_transactions if t["created_at"] >= start_date]
    if end_date:
        account_transactions = [t for t in account_transactions if t["created_at"] <= end_date]
    
    # Sort by date descending
    account_transactions.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "account": CashAccountResponse(**account),
        "transactions": [TransactionResponse(**t) for t in account_transactions[:limit]],
        "total_transactions": len(account_transactions)
    }

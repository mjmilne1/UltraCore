"""
Account API Schemas

Pydantic models for account endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from ultracore.api.schemas.common import AccountTypeEnum


# ============================================================================
# Request Models
# ============================================================================

class AccountCreateRequest(BaseModel):
    """Create account request"""
    customer_id: str = Field(..., description="Customer ID who owns the account")
    account_type: AccountTypeEnum
    currency: str = Field("AUD", pattern=r'^[A-Z]{3}$')
    initial_deposit: Optional[Decimal] = Field(None, ge=0)
    
    # Interest settings (for savings/term deposit)
    interest_bearing: bool = False
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Term deposit specific
    term_months: Optional[int] = Field(None, ge=1, le=120)
    maturity_instruction: Optional[str] = Field(None, pattern=r'^(RENEW|TRANSFER|CLOSE)$')


class DepositRequest(BaseModel):
    """Deposit request"""
    amount: Decimal = Field(..., gt=0, description="Amount to deposit")
    description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)


class WithdrawalRequest(BaseModel):
    """Withdrawal request"""
    amount: Decimal = Field(..., gt=0, description="Amount to withdraw")
    description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)


class TransferRequest(BaseModel):
    """Transfer request"""
    from_account_id: str = Field(..., description="Source account ID")
    to_account_id: str = Field(..., description="Destination account ID")
    amount: Decimal = Field(..., gt=0, description="Amount to transfer")
    description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)


# ============================================================================
# Response Models
# ============================================================================

class AccountBalanceResponse(BaseModel):
    """Account balance information"""
    ledger_balance: float = Field(..., description="Actual balance in account")
    available_balance: float = Field(..., description="Available for withdrawal")
    pending_credits: float = Field(..., description="Pending deposits")
    pending_debits: float = Field(..., description="Pending withdrawals")
    held_amount: float = Field(..., description="Amount on hold")
    minimum_balance: Optional[float] = Field(None, description="Minimum required balance")


class AccountResponse(BaseModel):
    """Account response"""
    account_id: str
    account_number: str
    customer_id: str
    account_type: str
    status: str
    currency: str
    
    # Balance
    balance: AccountBalanceResponse
    
    # Interest
    interest_bearing: bool
    current_interest_rate: Optional[float] = None
    
    # Term deposit
    maturity_date: Optional[datetime] = None
    
    # Metadata
    opened_date: datetime
    closed_date: Optional[datetime] = None
    last_transaction_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """List of accounts"""
    accounts: List[AccountResponse]
    total: int


class TransactionResponse(BaseModel):
    """Transaction response"""
    transaction_id: str
    account_id: str
    transaction_type: str
    status: str
    
    amount: float
    balance_after: float
    currency: str
    
    description: Optional[str] = None
    reference: Optional[str] = None
    
    # Related accounts (for transfers)
    related_account_id: Optional[str] = None
    related_transaction_id: Optional[str] = None
    
    # Metadata
    transaction_date: datetime
    value_date: datetime
    posted_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """List of transactions"""
    transactions: List[TransactionResponse]
    total: int

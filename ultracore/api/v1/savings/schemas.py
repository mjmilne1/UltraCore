"""
Savings API Schemas
Request and response schemas for savings endpoints
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# Request Schemas

class CreateSavingsAccountRequest(BaseModel):
    """Request to create a new savings account"""
    client_id: UUID
    product_id: UUID
    account_name: str = Field(..., min_length=1, max_length=100)
    initial_deposit: Decimal = Field(default=Decimal("0.00"), ge=0)
    tfn: Optional[str] = Field(default=None, pattern=r"^\d{9}$|^$")
    tfn_exemption: Optional[str] = None
    pds_accepted: bool = Field(..., description="Customer must accept Product Disclosure Statement")


class DepositRequest(BaseModel):
    """Request to make a deposit"""
    amount: Decimal = Field(..., gt=0)
    source: str = Field(..., description="Source of funds")
    reference: Optional[str] = None
    description: Optional[str] = "Deposit"


class WithdrawalRequest(BaseModel):
    """Request to make a withdrawal"""
    amount: Decimal = Field(..., gt=0)
    destination: str = Field(..., description="Destination of funds")
    reference: Optional[str] = None
    description: Optional[str] = "Withdrawal"


class UpdateTFNRequest(BaseModel):
    """Request to update TFN"""
    tfn: str = Field(..., pattern=r"^\d{9}$")


class CloseAccountRequest(BaseModel):
    """Request to close account"""
    closure_reason: str = Field(..., min_length=1)


# Response Schemas

class SavingsAccountResponse(BaseModel):
    """Savings account response"""
    account_id: UUID
    client_id: UUID
    product_id: UUID
    tenant_id: UUID
    account_number: str
    bsb: str
    account_name: str
    account_type: str
    currency: str
    status: str
    balance: Decimal
    available_balance: Decimal
    hold_balance: Decimal
    interest_rate: Decimal
    bonus_interest_rate: Decimal
    accrued_interest: Decimal
    ytd_interest_earned: Decimal
    has_tfn: bool
    withholding_tax_rate: Decimal
    ytd_withholding_tax: Decimal
    fcs_eligible: bool
    opened_date: datetime
    last_transaction_date: Optional[datetime]
    last_interest_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Transaction response"""
    transaction_id: UUID
    account_id: UUID
    transaction_type: str
    transaction_date: datetime
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str
    reference_number: str
    description: str
    source_account: Optional[str]
    destination_account: Optional[str]
    
    class Config:
        from_attributes = True


class InterestProjectionResponse(BaseModel):
    """Interest projection response"""
    principal: Decimal
    annual_rate: Decimal
    months: int
    gross_interest: Decimal
    withholding_tax: Decimal
    net_interest: Decimal
    final_balance: Decimal


class AccountStatementResponse(BaseModel):
    """Account statement response"""
    account_id: UUID
    account_number: str
    account_name: str
    statement_period_start: date
    statement_period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_deposits: Decimal
    total_withdrawals: Decimal
    total_interest: Decimal
    total_fees: Decimal
    transactions: List[TransactionResponse]


class SavingsProductResponse(BaseModel):
    """Savings product response"""
    product_id: UUID
    product_code: str
    product_name: str
    product_type: str
    description: str
    is_active: bool
    base_interest_rate: Decimal
    bonus_interest_rate: Decimal
    interest_calculation_method: str
    interest_posting_frequency: str
    minimum_opening_balance: Decimal
    minimum_balance: Decimal
    maximum_balance: Optional[Decimal]
    monthly_fee: Decimal
    withdrawal_limit: Optional[int]
    pds_url: str
    kfs_url: str
    
    class Config:
        from_attributes = True

"""
Savings Account Model
Australian-compliant savings account with TFN withholding and FCS support
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SavingsAccountType(str, Enum):
    """Types of savings accounts"""
    SAVINGS = "savings"
    HIGH_INTEREST_SAVINGS = "high_interest_savings"
    YOUTH_SAVER = "youth_saver"
    PENSIONER_SAVER = "pensioner_saver"
    BUSINESS_SAVINGS = "business_savings"


class AccountStatus(str, Enum):
    """Account lifecycle status"""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    DORMANT = "dormant"
    FROZEN = "frozen"
    CLOSED = "closed"


class TFNExemption(str, Enum):
    """Tax File Number exemption categories"""
    UNDER_18 = "under_18"
    PENSIONER = "pensioner"
    NON_RESIDENT = "non_resident"
    EXEMPT_ORGANIZATION = "exempt_organization"


class SavingsAccount(BaseModel):
    """
    Savings Account Model
    
    Represents a savings or deposit account with full Australian compliance:
    - TFN withholding tax (47% if no TFN provided)
    - Financial Claims Scheme (FCS) eligibility ($250k guarantee)
    - APRA prudential standards compliance
    - ASIC consumer protection requirements
    """
    
    # Identity
    account_id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    product_id: UUID
    tenant_id: UUID
    
    # Account Details
    account_number: str = Field(..., min_length=6, max_length=20)
    bsb: str = Field(..., pattern=r"^\d{6}$", description="Australian Bank State Branch number")
    account_name: str = Field(..., min_length=1, max_length=100)
    account_type: SavingsAccountType
    currency: str = Field(default="AUD")
    
    # Status
    status: AccountStatus = Field(default=AccountStatus.PENDING_APPROVAL)
    
    # Balances
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    available_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    hold_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    # Interest
    interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    bonus_interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    accrued_interest: Decimal = Field(default=Decimal("0.00"), ge=0)
    ytd_interest_earned: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    # Australian Tax Compliance
    tfn: Optional[str] = Field(default=None, pattern=r"^\d{9}$|^$", description="Tax File Number (9 digits)")
    tfn_exemption: Optional[TFNExemption] = None
    withholding_tax_rate: Decimal = Field(default=Decimal("47.00"), description="47% if no TFN, 0% if TFN provided")
    ytd_withholding_tax: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    # Australian Regulatory Compliance
    fcs_eligible: bool = Field(default=True, description="Financial Claims Scheme eligibility")
    pds_accepted: bool = Field(default=False, description="Product Disclosure Statement accepted")
    pds_accepted_date: Optional[datetime] = None
    
    # Dates
    opened_date: datetime = Field(default_factory=datetime.utcnow)
    approved_date: Optional[datetime] = None
    activated_date: Optional[datetime] = None
    last_transaction_date: Optional[datetime] = None
    last_interest_date: Optional[date] = None
    dormancy_date: Optional[datetime] = None
    closure_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    @field_validator("tfn")
    @classmethod
    def validate_tfn(cls, v: Optional[str]) -> Optional[str]:
        """Validate Australian TFN format"""
        if v and len(v) == 9:
            # Basic TFN validation (real validation would use ATO algorithm)
            if not v.isdigit():
                raise ValueError("TFN must be 9 digits")
        return v
    
    @field_validator("bsb")
    @classmethod
    def validate_bsb(cls, v: str) -> str:
        """Validate Australian BSB format"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("BSB must be exactly 6 digits")
        return v
    
    def calculate_withholding_tax_rate(self) -> Decimal:
        """
        Calculate withholding tax rate based on TFN status
        
        Australian Tax Law:
        - No TFN provided: 47% withholding tax
        - TFN provided: 0% withholding tax (tax paid via personal tax return)
        - Exemptions: 0% for certain categories (under 18, pensioners, etc.)
        """
        if self.tfn or self.tfn_exemption:
            return Decimal("0.00")
        return Decimal("47.00")
    
    def update_withholding_tax_rate(self) -> None:
        """Update withholding tax rate based on current TFN status"""
        self.withholding_tax_rate = self.calculate_withholding_tax_rate()
    
    def is_dormant(self, dormancy_period_days: int = 365) -> bool:
        """
        Check if account is dormant
        
        ASIC guidelines: Account is dormant if no customer-initiated transactions
        for a specified period (typically 12 months)
        """
        if not self.last_transaction_date:
            days_since_opened = (datetime.utcnow() - self.opened_date).days
            return days_since_opened >= dormancy_period_days
        
        days_since_last_transaction = (datetime.utcnow() - self.last_transaction_date).days
        return days_since_last_transaction >= dormancy_period_days
    
    def is_fcs_protected(self, total_balance_with_institution: Decimal) -> bool:
        """
        Check if account is protected by Financial Claims Scheme
        
        FCS Protection:
        - Up to $250,000 per depositor per ADI
        - Aggregated across all accounts with the same institution
        - Only for ADI-licensed institutions
        """
        if not self.fcs_eligible:
            return False
        
        fcs_limit = Decimal("250000.00")
        return total_balance_with_institution <= fcs_limit
    
    def can_withdraw(self, amount: Decimal) -> tuple[bool, Optional[str]]:
        """
        Check if withdrawal is allowed
        
        Returns: (can_withdraw, reason_if_not)
        """
        if self.status != AccountStatus.ACTIVE:
            return False, f"Account is not active (status: {self.status})"
        
        if amount > self.available_balance:
            return False, f"Insufficient available balance (available: ${self.available_balance})"
        
        if amount <= 0:
            return False, "Withdrawal amount must be positive"
        
        return True, None
    
    def can_deposit(self, amount: Decimal) -> tuple[bool, Optional[str]]:
        """
        Check if deposit is allowed
        
        Returns: (can_deposit, reason_if_not)
        """
        if self.status == AccountStatus.CLOSED:
            return False, "Account is closed"
        
        if self.status == AccountStatus.FROZEN:
            return False, "Account is frozen"
        
        if amount <= 0:
            return False, "Deposit amount must be positive"
        
        return True, None
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "client_id": "660e8400-e29b-41d4-a716-446655440000",
                "product_id": "770e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "880e8400-e29b-41d4-a716-446655440000",
                "account_number": "1234567890",
                "bsb": "062000",
                "account_name": "John Smith Savings",
                "account_type": "high_interest_savings",
                "currency": "AUD",
                "status": "active",
                "balance": "10000.00",
                "available_balance": "10000.00",
                "interest_rate": "2.50",
                "bonus_interest_rate": "2.00",
                "tfn": "123456789",
                "withholding_tax_rate": "0.00",
                "fcs_eligible": True,
                "pds_accepted": True,
            }
        }

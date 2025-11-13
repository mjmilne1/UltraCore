"""
Savings Product Model
Configurable savings product with Australian compliance features
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProductType(str, Enum):
    """Types of savings products"""
    SAVINGS = "savings"
    HIGH_INTEREST_SAVINGS = "high_interest_savings"
    TERM_DEPOSIT = "term_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"
    YOUTH_SAVER = "youth_saver"
    PENSIONER_SAVER = "pensioner_saver"
    BUSINESS_SAVINGS = "business_savings"


class InterestCalculationMethod(str, Enum):
    """Methods for calculating interest"""
    DAILY_BALANCE = "daily_balance"
    MINIMUM_MONTHLY_BALANCE = "minimum_monthly_balance"
    AVERAGE_DAILY_BALANCE = "average_daily_balance"


class InterestPostingFrequency(str, Enum):
    """Frequency of interest posting to account"""
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    AT_MATURITY = "at_maturity"


class BonusCondition(BaseModel):
    """Condition for earning bonus interest"""
    condition_type: str = Field(..., description="Type of condition (e.g., 'minimum_deposit', 'no_withdrawals')")
    description: str
    threshold_amount: Optional[Decimal] = None
    threshold_count: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "minimum_monthly_deposit",
                "description": "Deposit at least $1,000 per month",
                "threshold_amount": "1000.00"
            }
        }


class FeeWaiverCondition(BaseModel):
    """Condition for waiving monthly fees"""
    condition_type: str
    description: str
    threshold_amount: Optional[Decimal] = None
    threshold_count: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "minimum_balance",
                "description": "Maintain minimum balance of $5,000",
                "threshold_amount": "5000.00"
            }
        }


class AgeRestriction(BaseModel):
    """Age restrictions for product eligibility"""
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "minimum_age": 18,
                "maximum_age": 25
            }
        }


class SavingsProduct(BaseModel):
    """
    Savings Product Configuration
    
    Defines a savings product with all features and conditions.
    Compliant with ASIC product disclosure requirements.
    """
    
    # Identity
    product_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Product Details
    product_code: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    product_type: ProductType
    description: str
    is_active: bool = Field(default=True)
    
    # Interest Rates
    base_interest_rate: Decimal = Field(..., ge=0, le=100, description="Annual interest rate (%)")
    bonus_interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    bonus_conditions: List[BonusCondition] = Field(default_factory=list)
    
    # Interest Calculation
    interest_calculation_method: InterestCalculationMethod
    interest_posting_frequency: InterestPostingFrequency
    
    # Balance Requirements
    minimum_opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    minimum_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    maximum_balance: Optional[Decimal] = Field(default=None, ge=0)
    
    # Fees
    monthly_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    fee_waiver_conditions: List[FeeWaiverCondition] = Field(default_factory=list)
    
    # Withdrawal Rules
    withdrawal_limit: Optional[int] = Field(default=None, ge=0, description="Max withdrawals per month (None = unlimited)")
    withdrawal_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    excess_withdrawal_fee: Decimal = Field(default=Decimal("0.00"), ge=0, description="Fee for withdrawals exceeding limit")
    
    # Account Management
    dormancy_period_days: int = Field(default=365, ge=30)
    allow_overdraft: bool = Field(default=False)
    overdraft_limit: Optional[Decimal] = Field(default=None)
    overdraft_interest_rate: Optional[Decimal] = Field(default=None)
    
    # Eligibility
    age_restrictions: Optional[AgeRestriction] = None
    requires_tfn: bool = Field(default=True, description="Require TFN to avoid withholding tax")
    
    # Australian Compliance
    pds_url: str = Field(..., description="Product Disclosure Statement URL")
    kfs_url: str = Field(..., description="Key Facts Sheet URL")
    target_market_determination_url: Optional[str] = Field(default=None, description="TMD URL (ASIC requirement)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    def calculate_total_interest_rate(self, bonus_earned: bool = False) -> Decimal:
        """Calculate total interest rate including bonus if applicable"""
        if bonus_earned:
            return self.base_interest_rate + self.bonus_interest_rate
        return self.base_interest_rate
    
    def is_eligible_by_age(self, age: int) -> bool:
        """Check if customer age meets product requirements"""
        if not self.age_restrictions:
            return True
        
        if self.age_restrictions.minimum_age and age < self.age_restrictions.minimum_age:
            return False
        
        if self.age_restrictions.maximum_age and age > self.age_restrictions.maximum_age:
            return False
        
        return True
    
    def calculate_monthly_fee(self, balance: Decimal, deposit_count: int = 0) -> Decimal:
        """
        Calculate monthly fee based on balance and conditions
        
        Returns: Fee amount (0 if waived)
        """
        if self.monthly_fee == Decimal("0.00"):
            return Decimal("0.00")
        
        # Check fee waiver conditions
        for condition in self.fee_waiver_conditions:
            if condition.condition_type == "minimum_balance":
                if condition.threshold_amount and balance >= condition.threshold_amount:
                    return Decimal("0.00")
            
            elif condition.condition_type == "minimum_deposits":
                if condition.threshold_count and deposit_count >= condition.threshold_count:
                    return Decimal("0.00")
        
        return self.monthly_fee
    
    def check_bonus_eligibility(
        self,
        monthly_deposits: Decimal,
        withdrawal_count: int,
        balance: Decimal
    ) -> tuple[bool, List[str]]:
        """
        Check if bonus interest conditions are met
        
        Returns: (eligible, list of conditions met/failed)
        """
        if not self.bonus_conditions:
            return True, []
        
        conditions_met = []
        conditions_failed = []
        
        for condition in self.bonus_conditions:
            if condition.condition_type == "minimum_monthly_deposit":
                if condition.threshold_amount and monthly_deposits >= condition.threshold_amount:
                    conditions_met.append(condition.description)
                else:
                    conditions_failed.append(condition.description)
            
            elif condition.condition_type == "no_withdrawals":
                if withdrawal_count == 0:
                    conditions_met.append(condition.description)
                else:
                    conditions_failed.append(condition.description)
            
            elif condition.condition_type == "minimum_balance":
                if condition.threshold_amount and balance >= condition.threshold_amount:
                    conditions_met.append(condition.description)
                else:
                    conditions_failed.append(condition.description)
        
        eligible = len(conditions_failed) == 0
        return eligible, conditions_met if eligible else conditions_failed
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "770e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "880e8400-e29b-41d4-a716-446655440000",
                "product_code": "HIS-001",
                "product_name": "High Interest Savings Account",
                "product_type": "high_interest_savings",
                "description": "Earn up to 4.50% p.a. with bonus interest",
                "base_interest_rate": "2.50",
                "bonus_interest_rate": "2.00",
                "interest_calculation_method": "daily_balance",
                "interest_posting_frequency": "monthly",
                "minimum_opening_balance": "0.00",
                "monthly_fee": "5.00",
                "pds_url": "https://example.com/pds/his-001.pdf",
                "kfs_url": "https://example.com/kfs/his-001.pdf",
            }
        }

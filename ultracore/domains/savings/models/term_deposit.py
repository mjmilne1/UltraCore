"""
Term Deposit Model
Australian-compliant fixed-term deposit accounts
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TermDepositStatus(str, Enum):
    """Term deposit lifecycle status"""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    MATURED = "matured"
    CLOSED = "closed"
    RENEWED = "renewed"


class InterestPaymentFrequency(str, Enum):
    """Frequency of interest payments"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    AT_MATURITY = "at_maturity"


class TermDeposit(BaseModel):
    """
    Term Deposit (Fixed Deposit) Model
    
    Australian-compliant term deposit with:
    - Fixed interest rate for fixed term
    - Early withdrawal penalties
    - Auto-renewal options
    - TFN withholding tax compliance
    - APRA reporting requirements
    """
    
    # Identity
    deposit_id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    product_id: UUID
    tenant_id: UUID
    
    # Account Details
    account_number: str = Field(..., min_length=6, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=100)
    currency: str = Field(default="AUD")
    
    # Status
    status: TermDepositStatus = Field(default=TermDepositStatus.PENDING_APPROVAL)
    
    # Principal and Interest
    principal_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0, le=100, description="Annual interest rate (%)")
    interest_payment_frequency: InterestPaymentFrequency
    
    # Term
    term_months: int = Field(..., ge=1, le=60, description="Term in months (1-60)")
    start_date: date
    maturity_date: date
    
    # Interest Tracking
    accrued_interest: Decimal = Field(default=Decimal("0.00"), ge=0)
    paid_interest: Decimal = Field(default=Decimal("0.00"), ge=0)
    last_interest_payment_date: Optional[date] = None
    
    # Maturity Options
    auto_renew: bool = Field(default=False)
    renewal_term_months: Optional[int] = Field(default=None)
    maturity_instruction: str = Field(default="hold", description="hold, renew, transfer, close")
    maturity_notification_sent: bool = Field(default=False)
    
    # Early Withdrawal
    allow_early_withdrawal: bool = Field(default=True)
    early_withdrawal_penalty_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    early_withdrawal_penalty_amount: Optional[Decimal] = None
    
    # Australian Tax Compliance
    tfn: Optional[str] = Field(default=None, pattern=r"^\d{9}$|^$")
    tfn_exemption: Optional[str] = None
    withholding_tax_rate: Decimal = Field(default=Decimal("47.00"))
    ytd_withholding_tax: Decimal = Field(default=Decimal("0.00"), ge=0)
    
    # Australian Compliance
    pds_accepted: bool = Field(default=False)
    pds_accepted_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    @field_validator("maturity_date", mode="before")
    @classmethod
    def calculate_maturity_date(cls, v, info):
        """Calculate maturity date if not provided"""
        if v:
            return v
        
        start_date = info.data.get("start_date")
        term_months = info.data.get("term_months")
        
        if start_date and term_months:
            return start_date + relativedelta(months=term_months)
        
        return v
    
    def calculate_maturity_value(self) -> Decimal:
        """
        Calculate total value at maturity (principal + interest)
        
        For interest paid at maturity, this includes all accrued interest.
        For periodic payments, this is principal + any remaining accrued interest.
        """
        if self.interest_payment_frequency == InterestPaymentFrequency.AT_MATURITY:
            total_interest = self.calculate_total_interest()
            withholding_tax = total_interest * (self.withholding_tax_rate / Decimal("100"))
            net_interest = total_interest - withholding_tax
            return self.principal_amount + net_interest
        else:
            # For periodic payments, only unpaid accrued interest is added
            return self.principal_amount + self.accrued_interest
    
    def calculate_total_interest(self) -> Decimal:
        """
        Calculate total interest for the full term
        
        Simple interest formula: P * r * t
        where P = principal, r = annual rate, t = time in years
        """
        years = Decimal(self.term_months) / Decimal("12")
        rate = self.interest_rate / Decimal("100")
        total_interest = self.principal_amount * rate * years
        return total_interest.quantize(Decimal("0.01"))
    
    def calculate_daily_interest(self) -> Decimal:
        """Calculate interest accrued per day"""
        annual_interest = self.principal_amount * (self.interest_rate / Decimal("100"))
        daily_interest = annual_interest / Decimal("365")
        return daily_interest.quantize(Decimal("0.01"))
    
    def calculate_early_withdrawal_penalty(self, withdrawal_date: date) -> Decimal:
        """
        Calculate penalty for early withdrawal
        
        Common penalty structures in Australia:
        - Forfeit X months of interest
        - Percentage of interest earned
        - Flat fee
        
        This implementation uses interest forfeiture based on penalty rate.
        """
        if not self.allow_early_withdrawal:
            raise ValueError("Early withdrawal not allowed for this term deposit")
        
        if withdrawal_date >= self.maturity_date:
            return Decimal("0.00")
        
        # Calculate interest that would have been earned
        days_held = (withdrawal_date - self.start_date).days
        years_held = Decimal(days_held) / Decimal("365")
        interest_earned = self.principal_amount * (self.interest_rate / Decimal("100")) * years_held
        
        # Apply penalty rate
        penalty = interest_earned * (self.early_withdrawal_penalty_rate / Decimal("100"))
        
        return penalty.quantize(Decimal("0.01"))
    
    def calculate_early_withdrawal_amount(self, withdrawal_date: date) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculate amount customer receives on early withdrawal
        
        Returns: (principal, interest, penalty)
        """
        penalty = self.calculate_early_withdrawal_penalty(withdrawal_date)
        
        # Calculate interest earned to date
        days_held = (withdrawal_date - self.start_date).days
        years_held = Decimal(days_held) / Decimal("365")
        gross_interest = self.principal_amount * (self.interest_rate / Decimal("100")) * years_held
        
        # Subtract penalty and withholding tax
        interest_after_penalty = max(Decimal("0.00"), gross_interest - penalty)
        withholding_tax = interest_after_penalty * (self.withholding_tax_rate / Decimal("100"))
        net_interest = interest_after_penalty - withholding_tax
        
        return self.principal_amount, net_interest, penalty
    
    def days_until_maturity(self) -> int:
        """Calculate days remaining until maturity"""
        today = date.today()
        if today >= self.maturity_date:
            return 0
        return (self.maturity_date - today).days
    
    def is_matured(self) -> bool:
        """Check if term deposit has matured"""
        return date.today() >= self.maturity_date
    
    def requires_maturity_notification(self) -> bool:
        """
        Check if maturity notification should be sent
        
        ASIC guidelines: Notify customer at least 30 days before maturity
        """
        if self.maturity_notification_sent:
            return False
        
        days_to_maturity = self.days_until_maturity()
        return 0 < days_to_maturity <= 30
    
    class Config:
        json_schema_extra = {
            "example": {
                "deposit_id": "990e8400-e29b-41d4-a716-446655440000",
                "client_id": "660e8400-e29b-41d4-a716-446655440000",
                "product_id": "770e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "880e8400-e29b-41d4-a716-446655440000",
                "account_number": "TD1234567890",
                "account_name": "John Smith Term Deposit",
                "principal_amount": "50000.00",
                "interest_rate": "4.50",
                "term_months": 12,
                "start_date": "2025-01-01",
                "maturity_date": "2026-01-01",
                "interest_payment_frequency": "at_maturity",
                "auto_renew": False,
                "tfn": "123456789",
                "withholding_tax_rate": "0.00",
            }
        }

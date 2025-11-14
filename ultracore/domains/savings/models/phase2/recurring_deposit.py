"""
Recurring Deposit Model
Automated periodic deposits with interest benefits
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from uuid import UUID, uuid4
from datetime import date, datetime
from decimal import Decimal


class DepositFrequency(str, Enum):
    """Deposit frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MaturityAction(str, Enum):
    """Action to take at maturity"""
    AUTO_RENEW = "auto_renew"
    TRANSFER_TO_SAVINGS = "transfer_to_savings"
    PAYOUT = "payout"
    HOLD = "hold"


class RecurringDepositStatus(str, Enum):
    """Recurring deposit status"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    MATURED = "matured"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class RecurringDeposit(BaseModel):
    """
    Recurring Deposit
    
    Automated periodic deposits with higher interest rates
    and maturity benefits
    """
    
    # Identifiers
    recurring_deposit_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    account_id: UUID  # Parent savings account
    customer_id: UUID
    
    # Product details
    product_name: str = Field(default="Recurring Deposit")
    deposit_amount: Decimal  # Amount per deposit
    frequency: DepositFrequency
    currency: str = Field(default="AUD")
    
    # Schedule
    start_date: date
    end_date: date  # Maturity date
    next_deposit_date: Optional[date] = None
    last_deposit_date: Optional[date] = None
    
    # Deposit tracking
    total_deposits_made: int = Field(default=0)
    total_deposits_expected: int = Field(default=0)
    total_amount_deposited: Decimal = Field(default=Decimal("0.00"))
    missed_deposits: int = Field(default=0)
    
    # Interest
    interest_rate: Decimal  # Annual interest rate (e.g., 5.5%)
    compounding_frequency: str = Field(default="monthly")  # daily, monthly, quarterly
    total_interest_accrued: Decimal = Field(default=Decimal("0.00"))
    bonus_interest_rate: Decimal = Field(default=Decimal("0.00"))  # For uninterrupted deposits
    
    # Maturity
    maturity_amount: Decimal = Field(default=Decimal("0.00"))  # Principal + Interest
    maturity_action: MaturityAction = Field(default=MaturityAction.TRANSFER_TO_SAVINGS)
    auto_renew_term_months: Optional[int] = None
    
    # Penalties
    early_withdrawal_penalty_rate: Decimal = Field(default=Decimal("1.00"))  # 1% of principal
    missed_deposit_grace_days: int = Field(default=3)
    
    # Status
    status: RecurringDepositStatus = Field(default=RecurringDepositStatus.PENDING)
    is_active: bool = Field(default=True)
    
    # Notifications
    notify_on_deposit: bool = Field(default=True)
    notify_on_missed_deposit: bool = Field(default=True)
    notify_before_maturity_days: int = Field(default=7)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    activated_at: Optional[datetime] = None
    matured_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    def calculate_expected_deposits(self) -> int:
        """Calculate total expected deposits based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        count = 0
        current_date = self.start_date
        
        while current_date <= self.end_date:
            count += 1
            
            if self.frequency == DepositFrequency.DAILY:
                current_date += relativedelta(days=1)
            elif self.frequency == DepositFrequency.WEEKLY:
                current_date += relativedelta(weeks=1)
            elif self.frequency == DepositFrequency.FORTNIGHTLY:
                current_date += relativedelta(weeks=2)
            elif self.frequency == DepositFrequency.MONTHLY:
                current_date += relativedelta(months=1)
            elif self.frequency == DepositFrequency.QUARTERLY:
                current_date += relativedelta(months=3)
            elif self.frequency == DepositFrequency.YEARLY:
                current_date += relativedelta(years=1)
        
        self.total_deposits_expected = count
        return count
    
    def calculate_next_deposit_date(self) -> Optional[date]:
        """Calculate next deposit date"""
        from dateutil.relativedelta import relativedelta
        
        if self.status not in [RecurringDepositStatus.ACTIVE, RecurringDepositStatus.PENDING]:
            return None
        
        if self.last_deposit_date is None:
            self.next_deposit_date = self.start_date
            return self.start_date
        
        next_date = self.last_deposit_date
        
        if self.frequency == DepositFrequency.DAILY:
            next_date += relativedelta(days=1)
        elif self.frequency == DepositFrequency.WEEKLY:
            next_date += relativedelta(weeks=1)
        elif self.frequency == DepositFrequency.FORTNIGHTLY:
            next_date += relativedelta(weeks=2)
        elif self.frequency == DepositFrequency.MONTHLY:
            next_date += relativedelta(months=1)
        elif self.frequency == DepositFrequency.QUARTERLY:
            next_date += relativedelta(months=3)
        elif self.frequency == DepositFrequency.YEARLY:
            next_date += relativedelta(years=1)
        
        if next_date > self.end_date:
            return None
        
        self.next_deposit_date = next_date
        return next_date
    
    def calculate_maturity_amount(self) -> Decimal:
        """
        Calculate maturity amount (principal + interest)
        
        Uses compound interest formula:
        A = P * (1 + r/n)^(n*t)
        
        Where:
        A = Maturity amount
        P = Principal (total deposits)
        r = Annual interest rate
        n = Compounding frequency per year
        t = Time in years
        """
        principal = self.total_amount_deposited
        rate = (self.interest_rate + self.bonus_interest_rate) / 100
        
        # Compounding frequency
        if self.compounding_frequency == "daily":
            n = 365
        elif self.compounding_frequency == "monthly":
            n = 12
        elif self.compounding_frequency == "quarterly":
            n = 4
        else:
            n = 1
        
        # Time in years
        days = (self.end_date - self.start_date).days
        years = Decimal(days) / Decimal(365)
        
        # Compound interest calculation
        amount = principal * ((1 + rate / n) ** (n * years))
        
        self.maturity_amount = amount
        self.total_interest_accrued = amount - principal
        
        return amount
    
    def record_deposit(self, amount: Decimal, deposit_date: date):
        """Record a successful deposit"""
        self.total_deposits_made += 1
        self.total_amount_deposited += amount
        self.last_deposit_date = deposit_date
        self.calculate_next_deposit_date()
    
    def record_missed_deposit(self):
        """Record a missed deposit"""
        self.missed_deposits += 1
        
        # Remove bonus interest if deposits are interrupted
        if self.missed_deposits > 0:
            self.bonus_interest_rate = Decimal("0.00")
    
    def activate(self):
        """Activate recurring deposit"""
        self.status = RecurringDepositStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        self.calculate_expected_deposits()
        self.calculate_next_deposit_date()
    
    def pause(self):
        """Pause recurring deposit"""
        self.status = RecurringDepositStatus.PAUSED
    
    def resume(self):
        """Resume recurring deposit"""
        self.status = RecurringDepositStatus.ACTIVE
        self.calculate_next_deposit_date()
    
    def mature(self):
        """Mark as matured"""
        self.status = RecurringDepositStatus.MATURED
        self.matured_at = datetime.utcnow()
        self.calculate_maturity_amount()
    
    def close(self):
        """Close recurring deposit"""
        self.status = RecurringDepositStatus.CLOSED
        self.closed_at = datetime.utcnow()
        self.is_active = False
    
    def calculate_early_withdrawal_penalty(self) -> Decimal:
        """Calculate penalty for early withdrawal"""
        penalty = self.total_amount_deposited * (self.early_withdrawal_penalty_rate / 100)
        return penalty

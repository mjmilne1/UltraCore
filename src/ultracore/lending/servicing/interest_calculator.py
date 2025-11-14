"""
UltraCore Loan Management - Interest Calculator

Interest calculation and accrual:
- Daily interest accrual
- Multiple calculation methods
- Day count conventions
- Compounding rules
- Interest capitalization
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import calendar

from ultracore.lending.servicing.loan_account import (
    LoanAccount, LoanTransaction, LoanTransactionType
)


# ============================================================================
# Interest Calculation Enums
# ============================================================================

class InterestCalculationMethod(str, Enum):
    """Interest calculation methods"""
    SIMPLE = "SIMPLE"  # Simple interest
    COMPOUND_DAILY = "COMPOUND_DAILY"  # Daily compounding
    COMPOUND_MONTHLY = "COMPOUND_MONTHLY"  # Monthly compounding
    REDUCING_BALANCE = "REDUCING_BALANCE"  # Standard loan calculation


class DayCountConvention(str, Enum):
    """Day count conventions"""
    ACTUAL_365 = "ACTUAL_365"  # Actual days / 365
    ACTUAL_360 = "ACTUAL_360"  # Actual days / 360 (US convention)
    THIRTY_360 = "30_360"  # 30 days per month / 360 days per year
    ACTUAL_ACTUAL = "ACTUAL_ACTUAL"  # Actual days / actual days in year


class InterestPostingFrequency(str, Enum):
    """How often interest is posted to account"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_PAYMENT = "ON_PAYMENT"  # Only when payment received
    AT_MATURITY = "AT_MATURITY"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class DailyInterestAccrual:
    """Daily interest accrual record"""
    accrual_id: str
    loan_account_id: str
    accrual_date: date
    
    # Balance
    principal_balance: Decimal
    
    # Rate
    annual_rate: Decimal
    daily_rate: Decimal
    
    # Calculation
    days: int
    interest_accrued: Decimal
    
    # Cumulative
    cumulative_accrued: Decimal
    
    # Method
    calculation_method: InterestCalculationMethod
    day_count_convention: DayCountConvention
    
    # Posted
    posted: bool = False
    posted_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InterestPosting:
    """Interest posting to loan account"""
    posting_id: str
    loan_account_id: str
    posting_date: date
    
    # Period
    period_start: date
    period_end: date
    days_in_period: int
    
    # Amount
    interest_amount: Decimal
    
    # Transaction
    transaction_id: str
    
    # Status
    reversed: bool = False
    reversal_posting_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Interest Calculator
# ============================================================================

class InterestCalculator:
    """
    Interest calculation engine
    Handles daily accrual and posting
    """
    
    def __init__(self):
        self.accruals: Dict[str, DailyInterestAccrual] = {}
        self.postings: Dict[str, InterestPosting] = {}
        
        # Configuration
        self.default_method = InterestCalculationMethod.REDUCING_BALANCE
        self.default_convention = DayCountConvention.ACTUAL_365
    
    async def calculate_daily_interest(
        self,
        loan_account: LoanAccount,
        calculation_date: date,
        method: Optional[InterestCalculationMethod] = None,
        convention: Optional[DayCountConvention] = None
    ) -> DailyInterestAccrual:
        """
        Calculate daily interest accrual
        """
        
        accrual_id = f"ACC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        calc_method = method or self.default_method
        day_convention = convention or self.default_convention
        
        # Get current principal balance
        principal = loan_account.current_balance.principal_outstanding
        
        # Get annual rate
        annual_rate = loan_account.terms.interest_rate
        
        # Calculate daily rate based on convention
        daily_rate = self._calculate_daily_rate(annual_rate, day_convention)
        
        # Calculate interest for one day
        days = 1
        interest_accrued = principal * daily_rate
        interest_accrued = interest_accrued.quantize(Decimal('0.01'))
        
        # Get cumulative (would sum from previous accruals)
        cumulative = interest_accrued  # Simplified
        
        accrual = DailyInterestAccrual(
            accrual_id=accrual_id,
            loan_account_id=loan_account.account_id,
            accrual_date=calculation_date,
            principal_balance=principal,
            annual_rate=annual_rate,
            daily_rate=daily_rate,
            days=days,
            interest_accrued=interest_accrued,
            cumulative_accrued=cumulative,
            calculation_method=calc_method,
            day_count_convention=day_convention
        )
        
        self.accruals[accrual_id] = accrual
        
        # Add to loan account's accrued interest
        loan_account.current_balance.interest_accrued += interest_accrued
        loan_account.current_balance.update_total()
        
        return accrual
    
    def _calculate_daily_rate(
        self,
        annual_rate: Decimal,
        convention: DayCountConvention
    ) -> Decimal:
        """Calculate daily interest rate"""
        
        if convention == DayCountConvention.ACTUAL_365:
            return annual_rate / Decimal('100') / Decimal('365')
        
        elif convention == DayCountConvention.ACTUAL_360:
            return annual_rate / Decimal('100') / Decimal('360')
        
        elif convention == DayCountConvention.THIRTY_360:
            return annual_rate / Decimal('100') / Decimal('360')
        
        elif convention == DayCountConvention.ACTUAL_ACTUAL:
            # Use 365 as default (would check if leap year in production)
            return annual_rate / Decimal('100') / Decimal('365')
        
        return annual_rate / Decimal('100') / Decimal('365')
    
    async def calculate_period_interest(
        self,
        loan_account: LoanAccount,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """
        Calculate interest for a period
        """
        
        total_interest = Decimal('0.00')
        current_date = start_date
        
        while current_date <= end_date:
            accrual = await self.calculate_daily_interest(
                loan_account,
                current_date
            )
            total_interest += accrual.interest_accrued
            current_date += timedelta(days=1)
        
        return total_interest
    
    async def post_accrued_interest(
        self,
        loan_account: LoanAccount,
        posting_date: date,
        period_start: date,
        period_end: date
    ) -> InterestPosting:
        """
        Post accrued interest to loan account
        Creates transaction and updates balance
        """
        
        posting_id = f"POST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Get unposted accruals for period
        interest_amount = loan_account.current_balance.interest_accrued
        
        if interest_amount <= 0:
            raise ValueError("No interest to post")
        
        # Create interest charge transaction
        from ultracore.lending.servicing.loan_account import LoanTransaction
        import uuid
        
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        transaction = LoanTransaction(
            transaction_id=transaction_id,
            loan_account_id=loan_account.account_id,
            transaction_type=LoanTransactionType.INTEREST_PAYMENT,
            transaction_date=posting_date,
            value_date=posting_date,
            amount=interest_amount,
            interest_portion=interest_amount,
            description=f"Interest for period {period_start} to {period_end}",
            created_by="SYSTEM"
        )
        
        loan_account.add_transaction(transaction)
        
        # Move from accrued to in arrears (customer now owes this)
        loan_account.current_balance.interest_accrued = Decimal('0.00')
        loan_account.current_balance.interest_in_arrears += interest_amount
        loan_account.current_balance.update_total()
        
        # Calculate days
        days = (period_end - period_start).days + 1
        
        # Create posting record
        posting = InterestPosting(
            posting_id=posting_id,
            loan_account_id=loan_account.account_id,
            posting_date=posting_date,
            period_start=period_start,
            period_end=period_end,
            days_in_period=days,
            interest_amount=interest_amount,
            transaction_id=transaction_id
        )
        
        self.postings[posting_id] = posting
        
        # Mark accruals as posted
        for accrual in self.accruals.values():
            if (accrual.loan_account_id == loan_account.account_id and
                period_start <= accrual.accrual_date <= period_end and
                not accrual.posted):
                accrual.posted = True
                accrual.posted_date = posting_date
        
        return posting
    
    async def capitalize_interest(
        self,
        loan_account: LoanAccount,
        capitalization_date: date
    ) -> LoanTransaction:
        """
        Capitalize accrued interest into principal
        (Add interest to principal balance)
        """
        
        interest_to_capitalize = loan_account.current_balance.interest_accrued
        
        if interest_to_capitalize <= 0:
            raise ValueError("No interest to capitalize")
        
        import uuid
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        transaction = LoanTransaction(
            transaction_id=transaction_id,
            loan_account_id=loan_account.account_id,
            transaction_type=LoanTransactionType.ADJUSTMENT,
            transaction_date=capitalization_date,
            value_date=capitalization_date,
            amount=interest_to_capitalize,
            principal_portion=interest_to_capitalize,
            description="Interest capitalization",
            created_by="SYSTEM"
        )
        
        loan_account.add_transaction(transaction)
        
        # Move interest to principal
        loan_account.current_balance.interest_accrued = Decimal('0.00')
        loan_account.current_balance.principal_outstanding += interest_to_capitalize
        loan_account.current_balance.update_total()
        
        return transaction
    
    async def get_accruals_for_period(
        self,
        loan_account_id: str,
        start_date: date,
        end_date: date
    ) -> List[DailyInterestAccrual]:
        """Get all accruals for a period"""
        
        return [
            a for a in self.accruals.values()
            if (a.loan_account_id == loan_account_id and
                start_date <= a.accrual_date <= end_date)
        ]


# ============================================================================
# Global Interest Calculator
# ============================================================================

_interest_calculator: Optional[InterestCalculator] = None

def get_interest_calculator() -> InterestCalculator:
    """Get the singleton interest calculator"""
    global _interest_calculator
    if _interest_calculator is None:
        _interest_calculator = InterestCalculator()
    return _interest_calculator

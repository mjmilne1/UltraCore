"""
UltraCore Loan Management - Amortization Engine

Amortization and repayment schedule calculation:
- Multiple amortization methods
- Flexible payment frequencies
- Interest calculation
- Payment allocation
- Schedule generation
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import calendar

from ultracore.lending.servicing.loan_account import (
    LoanAccount, LoanTerms, PaymentFrequency, RepaymentType,
    InterestRateType
)


# ============================================================================
# Amortization Enums
# ============================================================================

class PaymentAllocationMethod(str, Enum):
    """Method for allocating payments"""
    FIFO = "FIFO"  # First In First Out
    STANDARD = "STANDARD"  # Fees, Interest, Principal
    CUSTOM = "CUSTOM"


class DayCountConvention(str, Enum):
    """Day count conventions for interest calculation"""
    ACTUAL_365 = "ACTUAL_365"  # Actual days / 365
    ACTUAL_360 = "ACTUAL_360"  # Actual days / 360
    THIRTY_360 = "30_360"  # 30 days per month, 360 days per year
    ACTUAL_ACTUAL = "ACTUAL_ACTUAL"  # Actual days / actual days in year


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ScheduledPayment:
    """Individual scheduled payment"""
    payment_number: int
    payment_date: date
    
    # Payment breakdown
    payment_amount: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    fee_amount: Decimal = Decimal('0.00')
    
    # Balance after payment
    principal_balance: Decimal
    
    # Cumulative
    cumulative_principal: Decimal
    cumulative_interest: Decimal
    
    # Days
    days_in_period: int
    
    # Status
    paid: bool = False
    paid_date: Optional[date] = None
    paid_amount: Optional[Decimal] = None


@dataclass
class AmortizationSchedule:
    """Complete amortization schedule"""
    schedule_id: str
    loan_account_id: str
    
    # Schedule details
    generated_date: datetime
    
    # Loan details
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    payment_frequency: PaymentFrequency
    
    # Payments
    payments: List[ScheduledPayment] = field(default_factory=list)
    
    # Totals
    total_payments: Decimal = Decimal('0.00')
    total_principal: Decimal = Decimal('0.00')
    total_interest: Decimal = Decimal('0.00')
    total_fees: Decimal = Decimal('0.00')
    
    # Metadata
    calculation_method: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterestAccrual:
    """Interest accrual calculation"""
    accrual_date: date
    principal_balance: Decimal
    interest_rate: Decimal
    days: int
    accrued_interest: Decimal
    cumulative_accrual: Decimal


# ============================================================================
# Amortization Engine
# ============================================================================

class AmortizationEngine:
    """
    Amortization calculation engine
    Generates repayment schedules
    """
    
    def __init__(self):
        self.schedules: Dict[str, AmortizationSchedule] = {}
    
    async def generate_schedule(
        self,
        loan_account: LoanAccount
    ) -> AmortizationSchedule:
        """Generate amortization schedule for loan"""
        
        schedule_id = f"SCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        terms = loan_account.terms
        
        # Determine generation method
        if terms.repayment_type == RepaymentType.PRINCIPAL_AND_INTEREST:
            schedule = await self._generate_pi_schedule(
                schedule_id,
                loan_account
            )
        elif terms.repayment_type == RepaymentType.INTEREST_ONLY:
            schedule = await self._generate_io_schedule(
                schedule_id,
                loan_account
            )
        elif terms.repayment_type == RepaymentType.BALLOON:
            schedule = await self._generate_balloon_schedule(
                schedule_id,
                loan_account
            )
        else:
            schedule = await self._generate_pi_schedule(
                schedule_id,
                loan_account
            )
        
        self.schedules[schedule_id] = schedule
        
        return schedule
    
    async def _generate_pi_schedule(
        self,
        schedule_id: str,
        loan_account: LoanAccount
    ) -> AmortizationSchedule:
        """
        Generate Principal & Interest amortization schedule
        Uses standard amortization formula
        """
        
        terms = loan_account.terms
        
        # Calculate number of payments
        payments_per_year = self._get_payments_per_year(terms.repayment_frequency)
        total_payments = self._calculate_total_payments(
            terms.term_months,
            terms.repayment_frequency
        )
        
        # Calculate periodic interest rate
        periodic_rate = terms.interest_rate / Decimal('100') / Decimal(payments_per_year)
        
        # Calculate payment amount using amortization formula
        # PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
        if periodic_rate > 0:
            numerator = periodic_rate * ((1 + periodic_rate) ** total_payments)
            denominator = ((1 + periodic_rate) ** total_payments) - 1
            payment_amount = terms.principal_amount * (numerator / denominator)
        else:
            # No interest
            payment_amount = terms.principal_amount / Decimal(total_payments)
        
        payment_amount = payment_amount.quantize(Decimal('0.01'))
        
        # Generate schedule
        schedule = AmortizationSchedule(
            schedule_id=schedule_id,
            loan_account_id=loan_account.account_id,
            generated_date=datetime.now(timezone.utc),
            principal_amount=terms.principal_amount,
            interest_rate=terms.interest_rate,
            term_months=terms.term_months,
            payment_frequency=terms.repayment_frequency,
            calculation_method="PRINCIPAL_AND_INTEREST"
        )
        
        # Generate each payment
        principal_balance = terms.principal_amount
        cumulative_principal = Decimal('0.00')
        cumulative_interest = Decimal('0.00')
        payment_date = terms.first_payment_date
        
        for payment_num in range(1, total_payments + 1):
            # Calculate interest for this period
            days_in_period = self._calculate_days_in_period(
                payment_date,
                terms.repayment_frequency
            )
            
            interest_amount = principal_balance * periodic_rate
            interest_amount = interest_amount.quantize(Decimal('0.01'))
            
            # Principal portion
            if payment_num == total_payments:
                # Last payment - pay off remaining balance
                principal_amount = principal_balance
                actual_payment = principal_amount + interest_amount
            else:
                principal_amount = payment_amount - interest_amount
                actual_payment = payment_amount
            
            # Update balances
            principal_balance -= principal_amount
            principal_balance = principal_balance.quantize(Decimal('0.01'))
            
            cumulative_principal += principal_amount
            cumulative_interest += interest_amount
            
            # Create scheduled payment
            payment = ScheduledPayment(
                payment_number=payment_num,
                payment_date=payment_date,
                payment_amount=actual_payment,
                principal_amount=principal_amount,
                interest_amount=interest_amount,
                fee_amount=terms.monthly_fee if payment_num > 0 else Decimal('0.00'),
                principal_balance=principal_balance,
                cumulative_principal=cumulative_principal,
                cumulative_interest=cumulative_interest,
                days_in_period=days_in_period
            )
            
            schedule.payments.append(payment)
            
            # Next payment date
            payment_date = self._get_next_payment_date(
                payment_date,
                terms.repayment_frequency
            )
        
        # Calculate totals
        schedule.total_payments = sum(p.payment_amount for p in schedule.payments)
        schedule.total_principal = sum(p.principal_amount for p in schedule.payments)
        schedule.total_interest = sum(p.interest_amount for p in schedule.payments)
        schedule.total_fees = sum(p.fee_amount for p in schedule.payments)
        
        return schedule
    
    async def _generate_io_schedule(
        self,
        schedule_id: str,
        loan_account: LoanAccount
    ) -> AmortizationSchedule:
        """
        Generate Interest Only schedule
        Principal paid at end or separate schedule
        """
        
        terms = loan_account.terms
        
        # Calculate number of payments
        payments_per_year = self._get_payments_per_year(terms.repayment_frequency)
        io_payments = self._calculate_total_payments(
            terms.interest_only_months,
            terms.repayment_frequency
        )
        
        # Periodic interest rate
        periodic_rate = terms.interest_rate / Decimal('100') / Decimal(payments_per_year)
        
        # Interest only payment amount
        interest_payment = terms.principal_amount * periodic_rate
        interest_payment = interest_payment.quantize(Decimal('0.01'))
        
        # Generate schedule
        schedule = AmortizationSchedule(
            schedule_id=schedule_id,
            loan_account_id=loan_account.account_id,
            generated_date=datetime.now(timezone.utc),
            principal_amount=terms.principal_amount,
            interest_rate=terms.interest_rate,
            term_months=terms.term_months,
            payment_frequency=terms.repayment_frequency,
            calculation_method="INTEREST_ONLY"
        )
        
        # Generate interest-only payments
        principal_balance = terms.principal_amount
        cumulative_interest = Decimal('0.00')
        payment_date = terms.first_payment_date
        
        for payment_num in range(1, io_payments + 1):
            days_in_period = self._calculate_days_in_period(
                payment_date,
                terms.repayment_frequency
            )
            
            cumulative_interest += interest_payment
            
            payment = ScheduledPayment(
                payment_number=payment_num,
                payment_date=payment_date,
                payment_amount=interest_payment,
                principal_amount=Decimal('0.00'),
                interest_amount=interest_payment,
                fee_amount=terms.monthly_fee,
                principal_balance=principal_balance,
                cumulative_principal=Decimal('0.00'),
                cumulative_interest=cumulative_interest,
                days_in_period=days_in_period
            )
            
            schedule.payments.append(payment)
            
            payment_date = self._get_next_payment_date(
                payment_date,
                terms.repayment_frequency
            )
        
        # Add principal & interest period if term extends beyond IO period
        if terms.term_months > terms.interest_only_months:
            remaining_months = terms.term_months - terms.interest_only_months
            remaining_payments = self._calculate_total_payments(
                remaining_months,
                terms.repayment_frequency
            )
            
            # Calculate P&I payment for remaining term
            if periodic_rate > 0:
                numerator = periodic_rate * ((1 + periodic_rate) ** remaining_payments)
                denominator = ((1 + periodic_rate) ** remaining_payments) - 1
                pi_payment = terms.principal_amount * (numerator / denominator)
            else:
                pi_payment = terms.principal_amount / Decimal(remaining_payments)
            
            pi_payment = pi_payment.quantize(Decimal('0.01'))
            
            cumulative_principal = Decimal('0.00')
            
            for payment_num in range(io_payments + 1, io_payments + remaining_payments + 1):
                interest_amount = principal_balance * periodic_rate
                interest_amount = interest_amount.quantize(Decimal('0.01'))
                
                if payment_num == io_payments + remaining_payments:
                    # Last payment
                    principal_amount = principal_balance
                    actual_payment = principal_amount + interest_amount
                else:
                    principal_amount = pi_payment - interest_amount
                    actual_payment = pi_payment
                
                principal_balance -= principal_amount
                principal_balance = principal_balance.quantize(Decimal('0.01'))
                
                cumulative_principal += principal_amount
                cumulative_interest += interest_amount
                
                days_in_period = self._calculate_days_in_period(
                    payment_date,
                    terms.repayment_frequency
                )
                
                payment = ScheduledPayment(
                    payment_number=payment_num,
                    payment_date=payment_date,
                    payment_amount=actual_payment,
                    principal_amount=principal_amount,
                    interest_amount=interest_amount,
                    fee_amount=terms.monthly_fee,
                    principal_balance=principal_balance,
                    cumulative_principal=cumulative_principal,
                    cumulative_interest=cumulative_interest,
                    days_in_period=days_in_period
                )
                
                schedule.payments.append(payment)
                
                payment_date = self._get_next_payment_date(
                    payment_date,
                    terms.repayment_frequency
                )
        
        # Calculate totals
        schedule.total_payments = sum(p.payment_amount for p in schedule.payments)
        schedule.total_principal = sum(p.principal_amount for p in schedule.payments)
        schedule.total_interest = sum(p.interest_amount for p in schedule.payments)
        schedule.total_fees = sum(p.fee_amount for p in schedule.payments)
        
        return schedule
    
    async def _generate_balloon_schedule(
        self,
        schedule_id: str,
        loan_account: LoanAccount
    ) -> AmortizationSchedule:
        """
        Generate schedule with balloon payment at end
        """
        
        terms = loan_account.terms
        
        if not terms.balloon_amount:
            raise ValueError("Balloon amount not specified")
        
        # Amount to amortize (excluding balloon)
        amortize_amount = terms.principal_amount - terms.balloon_amount
        
        # Generate regular P&I schedule for amortized portion
        # Then add balloon payment at end
        
        payments_per_year = self._get_payments_per_year(terms.repayment_frequency)
        total_payments = self._calculate_total_payments(
            terms.term_months,
            terms.repayment_frequency
        )
        
        periodic_rate = terms.interest_rate / Decimal('100') / Decimal(payments_per_year)
        
        # Calculate payment for amortized portion
        if periodic_rate > 0 and amortize_amount > 0:
            numerator = periodic_rate * ((1 + periodic_rate) ** (total_payments - 1))
            denominator = ((1 + periodic_rate) ** (total_payments - 1)) - 1
            payment_amount = amortize_amount * (numerator / denominator)
        else:
            payment_amount = amortize_amount / Decimal(total_payments - 1) if total_payments > 1 else Decimal('0.00')
        
        payment_amount = payment_amount.quantize(Decimal('0.01'))
        
        schedule = AmortizationSchedule(
            schedule_id=schedule_id,
            loan_account_id=loan_account.account_id,
            generated_date=datetime.now(timezone.utc),
            principal_amount=terms.principal_amount,
            interest_rate=terms.interest_rate,
            term_months=terms.term_months,
            payment_frequency=terms.repayment_frequency,
            calculation_method="BALLOON"
        )
        
        principal_balance = terms.principal_amount
        cumulative_principal = Decimal('0.00')
        cumulative_interest = Decimal('0.00')
        payment_date = terms.first_payment_date
        
        # Regular payments
        for payment_num in range(1, total_payments):
            days_in_period = self._calculate_days_in_period(
                payment_date,
                terms.repayment_frequency
            )
            
            interest_amount = principal_balance * periodic_rate
            interest_amount = interest_amount.quantize(Decimal('0.01'))
            
            principal_amount = payment_amount - interest_amount
            
            principal_balance -= principal_amount
            principal_balance = principal_balance.quantize(Decimal('0.01'))
            
            cumulative_principal += principal_amount
            cumulative_interest += interest_amount
            
            payment = ScheduledPayment(
                payment_number=payment_num,
                payment_date=payment_date,
                payment_amount=payment_amount,
                principal_amount=principal_amount,
                interest_amount=interest_amount,
                fee_amount=terms.monthly_fee,
                principal_balance=principal_balance,
                cumulative_principal=cumulative_principal,
                cumulative_interest=cumulative_interest,
                days_in_period=days_in_period
            )
            
            schedule.payments.append(payment)
            
            payment_date = self._get_next_payment_date(
                payment_date,
                terms.repayment_frequency
            )
        
        # Final balloon payment
        days_in_period = self._calculate_days_in_period(
            payment_date,
            terms.repayment_frequency
        )
        
        interest_amount = principal_balance * periodic_rate
        interest_amount = interest_amount.quantize(Decimal('0.01'))
        
        balloon_payment = principal_balance + interest_amount
        
        cumulative_principal += principal_balance
        cumulative_interest += interest_amount
        
        payment = ScheduledPayment(
            payment_number=total_payments,
            payment_date=payment_date,
            payment_amount=balloon_payment,
            principal_amount=principal_balance,
            interest_amount=interest_amount,
            fee_amount=terms.monthly_fee,
            principal_balance=Decimal('0.00'),
            cumulative_principal=cumulative_principal,
            cumulative_interest=cumulative_interest,
            days_in_period=days_in_period
        )
        
        schedule.payments.append(payment)
        
        # Calculate totals
        schedule.total_payments = sum(p.payment_amount for p in schedule.payments)
        schedule.total_principal = sum(p.principal_amount for p in schedule.payments)
        schedule.total_interest = sum(p.interest_amount for p in schedule.payments)
        schedule.total_fees = sum(p.fee_amount for p in schedule.payments)
        
        return schedule
    
    def _get_payments_per_year(self, frequency: PaymentFrequency) -> int:
        """Get number of payments per year"""
        mapping = {
            PaymentFrequency.WEEKLY: 52,
            PaymentFrequency.FORTNIGHTLY: 26,
            PaymentFrequency.MONTHLY: 12,
            PaymentFrequency.QUARTERLY: 4,
            PaymentFrequency.ANNUALLY: 1
        }
        return mapping.get(frequency, 12)
    
    def _calculate_total_payments(
        self,
        term_months: int,
        frequency: PaymentFrequency
    ) -> int:
        """Calculate total number of payments"""
        payments_per_year = self._get_payments_per_year(frequency)
        return int((term_months / 12) * payments_per_year)
    
    def _get_next_payment_date(
        self,
        current_date: date,
        frequency: PaymentFrequency
    ) -> date:
        """Calculate next payment date"""
        if frequency == PaymentFrequency.WEEKLY:
            return current_date + timedelta(days=7)
        elif frequency == PaymentFrequency.FORTNIGHTLY:
            return current_date + timedelta(days=14)
        elif frequency == PaymentFrequency.MONTHLY:
            # Add one month
            if current_date.month == 12:
                return current_date.replace(year=current_date.year + 1, month=1)
            else:
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                next_month = current_date.month + 1
                try:
                    return current_date.replace(month=next_month)
                except ValueError:
                    # Day doesn't exist in next month, use last day of month
                    last_day = calendar.monthrange(current_date.year, next_month)[1]
                    return current_date.replace(month=next_month, day=last_day)
        elif frequency == PaymentFrequency.QUARTERLY:
            # Add 3 months
            new_month = current_date.month + 3
            new_year = current_date.year
            if new_month > 12:
                new_month -= 12
                new_year += 1
            try:
                return current_date.replace(year=new_year, month=new_month)
            except ValueError:
                last_day = calendar.monthrange(new_year, new_month)[1]
                return current_date.replace(year=new_year, month=new_month, day=last_day)
        elif frequency == PaymentFrequency.ANNUALLY:
            return current_date.replace(year=current_date.year + 1)
        
        return current_date
    
    def _calculate_days_in_period(
        self,
        payment_date: date,
        frequency: PaymentFrequency
    ) -> int:
        """Calculate days in payment period"""
        if frequency == PaymentFrequency.WEEKLY:
            return 7
        elif frequency == PaymentFrequency.FORTNIGHTLY:
            return 14
        elif frequency == PaymentFrequency.MONTHLY:
            return 30  # Simplified
        elif frequency == PaymentFrequency.QUARTERLY:
            return 90  # Simplified
        elif frequency == PaymentFrequency.ANNUALLY:
            return 365
        return 30
    
    async def get_schedule(self, schedule_id: str) -> Optional[AmortizationSchedule]:
        """Get amortization schedule by ID"""
        return self.schedules.get(schedule_id)
    
    async def recalculate_schedule(
        self,
        loan_account: LoanAccount,
        effective_date: date
    ) -> AmortizationSchedule:
        """
        Recalculate schedule from a specific date
        Used for rate changes, extra payments, etc.
        """
        # Would recalculate schedule based on current balance
        # and remaining term
        return await self.generate_schedule(loan_account)


# ============================================================================
# Global Amortization Engine
# ============================================================================

_amortization_engine: Optional[AmortizationEngine] = None

def get_amortization_engine() -> AmortizationEngine:
    """Get the singleton amortization engine"""
    global _amortization_engine
    if _amortization_engine is None:
        _amortization_engine = AmortizationEngine()
    return _amortization_engine

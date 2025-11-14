"""
Amortization Engine
Calculates loan schedules, repayment amounts, and amortization tables
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
import math


class RepaymentScheduleEntry(BaseModel):
    """Single entry in a repayment schedule"""
    installment_number: int
    due_date: date
    opening_balance: Decimal
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    closing_balance: Decimal
    cumulative_principal: Decimal
    cumulative_interest: Decimal
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class RepaymentSchedule(BaseModel):
    """Complete repayment schedule for a loan"""
    account_id: str
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    repayment_frequency: str
    repayment_amount: Decimal
    total_interest: Decimal
    total_repayable: Decimal
    schedule: List[RepaymentScheduleEntry]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class AmortizationEngine:
    """
    Amortization Engine
    
    Calculates loan schedules using various amortization methods:
    - Principal and Interest (P&I)
    - Interest Only
    - Reducing Balance
    - Balloon Payment
    """
    
    def __init__(self):
        self.DAYS_IN_YEAR = Decimal("365")
        
    def calculate_repayment_amount(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
        frequency: str = "monthly",
        amortization_type: str = "principal_and_interest"
    ) -> Decimal:
        """
        Calculate periodic repayment amount
        
        Args:
            principal: Loan principal
            annual_rate: Annual interest rate (e.g., 0.0650 for 6.50%)
            term_months: Loan term in months
            frequency: Repayment frequency
            amortization_type: Type of amortization
            
        Returns:
            Periodic repayment amount
        """
        
        if amortization_type == "interest_only":
            return self._calculate_interest_only_repayment(
                principal, annual_rate, frequency
            )
        
        # Convert annual rate to periodic rate
        periods_per_year = self._get_periods_per_year(frequency)
        periodic_rate = annual_rate / periods_per_year
        
        # Total number of payments
        total_periods = self._calculate_total_periods(term_months, frequency)
        
        # Calculate using standard amortization formula
        # PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
        
        if periodic_rate == 0:
            # No interest
            return principal / total_periods
        
        numerator = periodic_rate * ((1 + periodic_rate) ** total_periods)
        denominator = ((1 + periodic_rate) ** total_periods) - 1
        
        repayment = principal * (numerator / denominator)
        
        # Round to 2 decimal places
        return repayment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
    def _calculate_interest_only_repayment(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        frequency: str
    ) -> Decimal:
        """Calculate interest-only repayment"""
        periods_per_year = self._get_periods_per_year(frequency)
        periodic_rate = annual_rate / periods_per_year
        
        return (principal * periodic_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
    def generate_schedule(
        self,
        account_id: str,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
        start_date: date,
        frequency: str = "monthly",
        amortization_type: str = "principal_and_interest",
        balloon_amount: Optional[Decimal] = None
    ) -> RepaymentSchedule:
        """
        Generate complete repayment schedule
        
        Args:
            account_id: Loan account ID
            principal: Loan principal
            annual_rate: Annual interest rate
            term_months: Loan term in months
            start_date: First repayment date
            frequency: Repayment frequency
            amortization_type: Type of amortization
            balloon_amount: Final balloon payment (optional)
            
        Returns:
            Complete repayment schedule
        """
        
        # Calculate repayment amount
        repayment_amount = self.calculate_repayment_amount(
            principal, annual_rate, term_months, frequency, amortization_type
        )
        
        # Generate schedule entries
        schedule_entries = []
        
        if amortization_type == "principal_and_interest":
            schedule_entries = self._generate_pi_schedule(
                principal, annual_rate, term_months, start_date,
                frequency, repayment_amount, balloon_amount
            )
        elif amortization_type == "interest_only":
            schedule_entries = self._generate_io_schedule(
                principal, annual_rate, term_months, start_date,
                frequency, repayment_amount
            )
        
        # Calculate totals
        total_interest = sum(e.interest_due for e in schedule_entries)
        total_repayable = principal + total_interest
        
        return RepaymentSchedule(
            account_id=account_id,
            principal_amount=principal,
            interest_rate=annual_rate,
            term_months=term_months,
            repayment_frequency=frequency,
            repayment_amount=repayment_amount,
            total_interest=total_interest,
            total_repayable=total_repayable,
            schedule=schedule_entries
        )
        
    def _generate_pi_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
        start_date: date,
        frequency: str,
        repayment_amount: Decimal,
        balloon_amount: Optional[Decimal] = None
    ) -> List[RepaymentScheduleEntry]:
        """Generate Principal & Interest schedule"""
        
        entries = []
        balance = principal
        cumulative_principal = Decimal("0")
        cumulative_interest = Decimal("0")
        
        periods_per_year = self._get_periods_per_year(frequency)
        periodic_rate = annual_rate / periods_per_year
        total_periods = self._calculate_total_periods(term_months, frequency)
        
        current_date = start_date
        
        for i in range(1, total_periods + 1):
            # Calculate interest for this period
            interest_due = (balance * periodic_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            
            # Calculate principal for this period
            if i == total_periods and balloon_amount:
                # Last payment with balloon
                principal_due = balance - balloon_amount
                total_due = principal_due + interest_due + balloon_amount
            elif i == total_periods:
                # Last payment - pay off remaining balance
                principal_due = balance
                total_due = principal_due + interest_due
            else:
                principal_due = repayment_amount - interest_due
                total_due = repayment_amount
            
            # Update cumulative amounts
            cumulative_principal += principal_due
            cumulative_interest += interest_due
            
            # Create entry
            entry = RepaymentScheduleEntry(
                installment_number=i,
                due_date=current_date,
                opening_balance=balance,
                principal_due=principal_due,
                interest_due=interest_due,
                total_due=total_due,
                closing_balance=balance - principal_due,
                cumulative_principal=cumulative_principal,
                cumulative_interest=cumulative_interest
            )
            
            entries.append(entry)
            
            # Update balance and date
            balance -= principal_due
            current_date = self._get_next_payment_date(current_date, frequency)
        
        return entries
        
    def _generate_io_schedule(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
        start_date: date,
        frequency: str,
        repayment_amount: Decimal
    ) -> List[RepaymentScheduleEntry]:
        """Generate Interest Only schedule"""
        
        entries = []
        balance = principal
        cumulative_interest = Decimal("0")
        
        total_periods = self._calculate_total_periods(term_months, frequency)
        current_date = start_date
        
        for i in range(1, total_periods + 1):
            interest_due = repayment_amount
            
            if i == total_periods:
                # Last payment includes principal
                principal_due = principal
                total_due = principal + interest_due
            else:
                principal_due = Decimal("0")
                total_due = interest_due
            
            cumulative_interest += interest_due
            
            entry = RepaymentScheduleEntry(
                installment_number=i,
                due_date=current_date,
                opening_balance=balance,
                principal_due=principal_due,
                interest_due=interest_due,
                total_due=total_due,
                closing_balance=balance - principal_due,
                cumulative_principal=principal_due,
                cumulative_interest=cumulative_interest
            )
            
            entries.append(entry)
            
            balance -= principal_due
            current_date = self._get_next_payment_date(current_date, frequency)
        
        return entries
        
    def _get_periods_per_year(self, frequency: str) -> Decimal:
        """Get number of payment periods per year"""
        if frequency == "weekly":
            return Decimal("52")
        elif frequency == "fortnightly":
            return Decimal("26")
        elif frequency == "monthly":
            return Decimal("12")
        elif frequency == "quarterly":
            return Decimal("4")
        else:
            return Decimal("12")  # Default to monthly
            
    def _calculate_total_periods(self, term_months: int, frequency: str) -> int:
        """Calculate total number of payment periods"""
        if frequency == "weekly":
            return int((term_months * 52) / 12)
        elif frequency == "fortnightly":
            return int((term_months * 26) / 12)
        elif frequency == "monthly":
            return term_months
        elif frequency == "quarterly":
            return int(term_months / 3)
        else:
            return term_months
            
    def _get_next_payment_date(self, current_date: date, frequency: str) -> date:
        """Calculate next payment date based on frequency"""
        if frequency == "weekly":
            return current_date + timedelta(days=7)
        elif frequency == "fortnightly":
            return current_date + timedelta(days=14)
        elif frequency == "monthly":
            return current_date + relativedelta(months=1)
        elif frequency == "quarterly":
            return current_date + relativedelta(months=3)
        else:
            return current_date + relativedelta(months=1)
            
    def recalculate_schedule_after_payment(
        self,
        original_schedule: RepaymentSchedule,
        payment_number: int,
        actual_payment: Decimal,
        payment_date: date
    ) -> RepaymentSchedule:
        """
        Recalculate schedule after an actual payment
        
        Handles:
        - Extra payments
        - Underpayments
        - Late payments
        
        Args:
            original_schedule: Original schedule
            payment_number: Which payment was made
            actual_payment: Actual amount paid
            payment_date: Date payment was made
            
        Returns:
            Updated schedule
        """
        
        # Get the scheduled payment
        scheduled_entry = original_schedule.schedule[payment_number - 1]
        
        # Calculate difference
        payment_diff = actual_payment - scheduled_entry.total_due
        
        if payment_diff > 0:
            # Extra payment - reduce principal
            return self._recalculate_with_extra_payment(
                original_schedule, payment_number, payment_diff
            )
        elif payment_diff < 0:
            # Underpayment - may need to recalculate
            return self._recalculate_with_underpayment(
                original_schedule, payment_number, abs(payment_diff)
            )
        else:
            # Exact payment - no change needed
            return original_schedule
            
    def _recalculate_with_extra_payment(
        self,
        schedule: RepaymentSchedule,
        payment_number: int,
        extra_amount: Decimal
    ) -> RepaymentSchedule:
        """Recalculate schedule with extra principal payment"""
        
        # Reduce principal by extra amount
        new_principal = schedule.principal_amount - extra_amount
        
        # Regenerate schedule from this point
        remaining_months = schedule.term_months - payment_number
        next_date = schedule.schedule[payment_number].due_date
        
        return self.generate_schedule(
            account_id=schedule.account_id,
            principal=new_principal,
            annual_rate=schedule.interest_rate,
            term_months=remaining_months,
            start_date=next_date,
            frequency=schedule.repayment_frequency
        )
        
    def _recalculate_with_underpayment(
        self,
        schedule: RepaymentSchedule,
        payment_number: int,
        shortfall: Decimal
    ) -> RepaymentSchedule:
        """Recalculate schedule with underpayment"""
        
        # Add shortfall to principal
        new_principal = schedule.principal_amount + shortfall
        
        # May need to extend term or increase payments
        # For now, keep same term and recalculate payments
        remaining_months = schedule.term_months - payment_number
        next_date = schedule.schedule[payment_number].due_date
        
        return self.generate_schedule(
            account_id=schedule.account_id,
            principal=new_principal,
            annual_rate=schedule.interest_rate,
            term_months=remaining_months,
            start_date=next_date,
            frequency=schedule.repayment_frequency
        )
        
    def calculate_early_payoff_amount(
        self,
        schedule: RepaymentSchedule,
        current_installment: int,
        payoff_date: date
    ) -> Dict[str, Decimal]:
        """
        Calculate amount needed to pay off loan early
        
        Args:
            schedule: Current schedule
            current_installment: Current installment number
            payoff_date: Proposed payoff date
            
        Returns:
            Payoff details including principal, interest, fees
        """
        
        if current_installment >= len(schedule.schedule):
            return {
                "principal": Decimal("0"),
                "interest": Decimal("0"),
                "early_payoff_fee": Decimal("0"),
                "total": Decimal("0")
            }
        
        # Get remaining principal
        current_entry = schedule.schedule[current_installment - 1]
        remaining_principal = current_entry.closing_balance
        
        # Calculate accrued interest to payoff date
        days_since_last_payment = (payoff_date - current_entry.due_date).days
        daily_rate = schedule.interest_rate / self.DAYS_IN_YEAR
        accrued_interest = (remaining_principal * daily_rate * days_since_last_payment).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        # Early payoff fee (typically 1-2 months interest)
        early_payoff_fee = (remaining_principal * schedule.interest_rate / Decimal("12") * Decimal("2")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        total = remaining_principal + accrued_interest + early_payoff_fee
        
        return {
            "principal": remaining_principal,
            "interest": accrued_interest,
            "early_payoff_fee": early_payoff_fee,
            "total": total
        }

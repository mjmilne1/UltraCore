"""
Interest Calculation Service
Australian-compliant interest calculation for savings accounts
"""

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

from ultracore.domains.savings.models.savings_account import SavingsAccount
from ultracore.domains.savings.models.savings_product import (
    SavingsProduct,
    InterestCalculationMethod,
    InterestPostingFrequency,
)


class InterestCalculator:
    """
    Interest Calculation Engine
    
    Implements Australian banking standards for interest calculation:
    - Daily balance method (most common)
    - Minimum monthly balance method
    - Average daily balance method
    - Compound interest
    - TFN withholding tax deduction
    """
    
    DAYS_IN_YEAR = Decimal("365")
    
    @staticmethod
    def calculate_daily_interest(
        balance: Decimal,
        annual_rate: Decimal,
        withholding_tax_rate: Decimal = Decimal("0.00")
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate interest for one day
        
        Args:
            balance: Account balance
            annual_rate: Annual interest rate (%)
            withholding_tax_rate: Withholding tax rate (%)
        
        Returns:
            (gross_interest, withholding_tax, net_interest)
        """
        if balance <= 0 or annual_rate <= 0:
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        # Calculate daily interest
        daily_rate = annual_rate / Decimal("100") / InterestCalculator.DAYS_IN_YEAR
        gross_interest = (balance * daily_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Calculate withholding tax
        withholding_tax = (gross_interest * withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        # Net interest after tax
        net_interest = gross_interest - withholding_tax
        
        return gross_interest, withholding_tax, net_interest
    
    @staticmethod
    def calculate_period_interest(
        daily_balances: List[Tuple[date, Decimal]],
        annual_rate: Decimal,
        calculation_method: InterestCalculationMethod,
        withholding_tax_rate: Decimal = Decimal("0.00")
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate interest for a period using specified method
        
        Args:
            daily_balances: List of (date, balance) tuples
            annual_rate: Annual interest rate (%)
            calculation_method: Method to use for calculation
            withholding_tax_rate: Withholding tax rate (%)
        
        Returns:
            (gross_interest, withholding_tax, net_interest)
        """
        if not daily_balances or annual_rate <= 0:
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        if calculation_method == InterestCalculationMethod.DAILY_BALANCE:
            return InterestCalculator._calculate_daily_balance_method(
                daily_balances, annual_rate, withholding_tax_rate
            )
        
        elif calculation_method == InterestCalculationMethod.MINIMUM_MONTHLY_BALANCE:
            return InterestCalculator._calculate_minimum_balance_method(
                daily_balances, annual_rate, withholding_tax_rate
            )
        
        elif calculation_method == InterestCalculationMethod.AVERAGE_DAILY_BALANCE:
            return InterestCalculator._calculate_average_balance_method(
                daily_balances, annual_rate, withholding_tax_rate
            )
        
        else:
            raise ValueError(f"Unknown calculation method: {calculation_method}")
    
    @staticmethod
    def _calculate_daily_balance_method(
        daily_balances: List[Tuple[date, Decimal]],
        annual_rate: Decimal,
        withholding_tax_rate: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Daily Balance Method
        
        Interest = Σ(daily_balance * daily_rate) for each day
        Most accurate and commonly used in Australia
        """
        total_gross_interest = Decimal("0.00")
        daily_rate = annual_rate / Decimal("100") / InterestCalculator.DAYS_IN_YEAR
        
        for _, balance in daily_balances:
            if balance > 0:
                daily_interest = balance * daily_rate
                total_gross_interest += daily_interest
        
        total_gross_interest = total_gross_interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        withholding_tax = (total_gross_interest * withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        net_interest = total_gross_interest - withholding_tax
        
        return total_gross_interest, withholding_tax, net_interest
    
    @staticmethod
    def _calculate_minimum_balance_method(
        daily_balances: List[Tuple[date, Decimal]],
        annual_rate: Decimal,
        withholding_tax_rate: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Minimum Monthly Balance Method
        
        Interest = minimum_balance * rate * days / 365
        Less favorable to customers but simpler
        """
        if not daily_balances:
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        minimum_balance = min(balance for _, balance in daily_balances)
        days = len(daily_balances)
        
        daily_rate = annual_rate / Decimal("100") / InterestCalculator.DAYS_IN_YEAR
        gross_interest = (minimum_balance * daily_rate * Decimal(days)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        withholding_tax = (gross_interest * withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        net_interest = gross_interest - withholding_tax
        
        return gross_interest, withholding_tax, net_interest
    
    @staticmethod
    def _calculate_average_balance_method(
        daily_balances: List[Tuple[date, Decimal]],
        annual_rate: Decimal,
        withholding_tax_rate: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Average Daily Balance Method
        
        Interest = average_balance * rate * days / 365
        """
        if not daily_balances:
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        total_balance = sum(balance for _, balance in daily_balances)
        average_balance = total_balance / Decimal(len(daily_balances))
        days = len(daily_balances)
        
        daily_rate = annual_rate / Decimal("100") / InterestCalculator.DAYS_IN_YEAR
        gross_interest = (average_balance * daily_rate * Decimal(days)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        withholding_tax = (gross_interest * withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        net_interest = gross_interest - withholding_tax
        
        return gross_interest, withholding_tax, net_interest
    
    @staticmethod
    def calculate_bonus_interest(
        account: SavingsAccount,
        product: SavingsProduct,
        monthly_deposits: Decimal,
        withdrawal_count: int
    ) -> Tuple[bool, Decimal, Decimal, Decimal]:
        """
        Calculate bonus interest if conditions are met
        
        Args:
            account: Savings account
            product: Savings product
            monthly_deposits: Total deposits in the month
            withdrawal_count: Number of withdrawals in the month
        
        Returns:
            (eligible, gross_bonus, withholding_tax, net_bonus)
        """
        # Check bonus eligibility
        eligible, _ = product.check_bonus_eligibility(
            monthly_deposits=monthly_deposits,
            withdrawal_count=withdrawal_count,
            balance=account.balance
        )
        
        if not eligible or product.bonus_interest_rate == Decimal("0.00"):
            return False, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        # Calculate bonus interest for the month (assuming 30 days)
        days = 30
        daily_rate = product.bonus_interest_rate / Decimal("100") / InterestCalculator.DAYS_IN_YEAR
        gross_bonus = (account.balance * daily_rate * Decimal(days)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        withholding_tax = (gross_bonus * account.withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        net_bonus = gross_bonus - withholding_tax
        
        return True, gross_bonus, withholding_tax, net_bonus
    
    @staticmethod
    def project_interest(
        principal: Decimal,
        annual_rate: Decimal,
        months: int,
        posting_frequency: InterestPostingFrequency,
        withholding_tax_rate: Decimal = Decimal("0.00")
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Project future interest earnings
        
        Useful for customer projections and product comparisons.
        
        Args:
            principal: Initial balance
            annual_rate: Annual interest rate (%)
            months: Number of months to project
            posting_frequency: How often interest is compounded
            withholding_tax_rate: Withholding tax rate (%)
        
        Returns:
            (total_gross_interest, total_withholding_tax, total_net_interest)
        """
        if principal <= 0 or annual_rate <= 0 or months <= 0:
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        
        # Determine compounding frequency
        if posting_frequency == InterestPostingFrequency.MONTHLY:
            periods_per_year = 12
        elif posting_frequency == InterestPostingFrequency.QUARTERLY:
            periods_per_year = 4
        elif posting_frequency == InterestPostingFrequency.ANNUALLY:
            periods_per_year = 1
        else:  # DAILY or AT_MATURITY
            periods_per_year = 365
        
        # Calculate compound interest
        rate_per_period = annual_rate / Decimal("100") / Decimal(periods_per_year)
        total_periods = Decimal(months) * Decimal(periods_per_year) / Decimal("12")
        
        # A = P(1 + r)^n
        final_amount = principal * ((Decimal("1") + rate_per_period) ** int(total_periods))
        gross_interest = (final_amount - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        withholding_tax = (gross_interest * withholding_tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        net_interest = gross_interest - withholding_tax
        
        return gross_interest, withholding_tax, net_interest

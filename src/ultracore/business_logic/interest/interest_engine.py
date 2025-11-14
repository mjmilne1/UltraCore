"""
Interest Calculation Engine
Complex interest calculations with multiple methods

Features:
- Multiple interest types (simple, compound, daily, annual)
- Tiered interest rates
- Promotional rates
- Penalty interest
- Interest accrual and capitalization
- Tax calculation (TFN withholding)
- Event-sourced interest posting
"""
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from enum import Enum
import calendar

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.data_mesh.integration import DataMeshPublisher


class InterestType(str, Enum):
    SIMPLE = 'SIMPLE'
    COMPOUND = 'COMPOUND'
    DAILY_COMPOUND = 'DAILY_COMPOUND'


class AccrualFrequency(str, Enum):
    DAILY = 'DAILY'
    MONTHLY = 'MONTHLY'
    QUARTERLY = 'QUARTERLY'
    ANNUALLY = 'ANNUALLY'


class BalanceTier:
    """Balance tier for tiered interest rates"""
    
    def __init__(
        self,
        min_balance: Decimal,
        max_balance: Optional[Decimal],
        interest_rate: Decimal
    ):
        self.min_balance = min_balance
        self.max_balance = max_balance
        self.interest_rate = interest_rate
    
    def applies_to_balance(self, balance: Decimal) -> bool:
        """Check if tier applies to balance"""
        if self.max_balance:
            return self.min_balance <= balance < self.max_balance
        else:
            return balance >= self.min_balance


class InterestCalculator:
    """
    Enterprise interest calculation engine
    
    Supports:
    - Savings accounts (credit interest)
    - Loans (debit interest)
    - Tiered rates
    - Promotional rates
    - Tax withholding
    """
    
    @staticmethod
    def calculate_simple_interest(
        principal: Decimal,
        annual_rate: Decimal,
        days: int
    ) -> Decimal:
        """
        Calculate simple interest
        
        Formula: I = P × r × t
        Where:
        - P = Principal
        - r = Daily interest rate
        - t = Time in days
        """
        daily_rate = annual_rate / Decimal('365') / Decimal('100')
        interest = principal * daily_rate * Decimal(days)
        
        return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_compound_interest(
        principal: Decimal,
        annual_rate: Decimal,
        days: int,
        compounds_per_year: int = 365
    ) -> Decimal:
        """
        Calculate compound interest
        
        Formula: A = P(1 + r/n)^(nt)
        Where:
        - A = Final amount
        - P = Principal
        - r = Annual interest rate
        - n = Number of times interest compounds per year
        - t = Time in years
        
        Returns: Interest amount (A - P)
        """
        rate = annual_rate / Decimal('100')
        time_years = Decimal(days) / Decimal('365')
        
        # Calculate compound factor
        compound_factor = (
            1 + (rate / Decimal(compounds_per_year))
        ) ** (Decimal(compounds_per_year) * time_years)
        
        final_amount = principal * Decimal(str(compound_factor))
        interest = final_amount - principal
        
        return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_daily_compound_interest(
        principal: Decimal,
        annual_rate: Decimal,
        days: int
    ) -> Decimal:
        """
        Calculate daily compound interest
        
        Most common for Australian savings accounts
        """
        return InterestCalculator.calculate_compound_interest(
            principal,
            annual_rate,
            days,
            compounds_per_year=365
        )
    
    @staticmethod
    def calculate_tiered_interest(
        balance: Decimal,
        tiers: List[BalanceTier],
        days: int
    ) -> Decimal:
        """
        Calculate interest with tiered rates
        
        Example tiers:
        -  - ,000: 0.5%
        - ,000 - ,000: 1.5%
        - ,000+: 2.5%
        """
        total_interest = Decimal('0')
        remaining_balance = balance
        
        for tier in tiers:
            if remaining_balance <= 0:
                break
            
            # Calculate amount in this tier
            if tier.max_balance:
                tier_amount = min(
                    remaining_balance,
                    tier.max_balance - tier.min_balance
                )
            else:
                tier_amount = remaining_balance
            
            # Calculate interest for this tier
            tier_interest = InterestCalculator.calculate_daily_compound_interest(
                tier_amount,
                tier.interest_rate,
                days
            )
            
            total_interest += tier_interest
            remaining_balance -= tier_amount
        
        return total_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class InterestAccrualService:
    """
    Interest accrual service
    
    Manages:
    - Daily interest accrual
    - Monthly interest posting
    - Interest capitalization
    - Tax withholding (TFN)
    """
    
    def __init__(self):
        self.accrued_interest: Dict[str, Decimal] = {}
    
    async def accrue_daily_interest(
        self,
        account_id: str,
        balance: Decimal,
        annual_rate: Decimal,
        account_type: str
    ) -> Dict:
        """
        Accrue interest for one day
        
        Called by daily batch job
        """
        # Calculate daily interest
        daily_interest = InterestCalculator.calculate_simple_interest(
            principal=balance,
            annual_rate=annual_rate,
            days=1
        )
        
        # Add to accrued amount
        if account_id not in self.accrued_interest:
            self.accrued_interest[account_id] = Decimal('0')
        
        self.accrued_interest[account_id] += daily_interest
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='interest',
            event_type='interest_accrued',
            event_data={
                'account_id': account_id,
                'balance': str(balance),
                'daily_interest': str(daily_interest),
                'total_accrued': str(self.accrued_interest[account_id]),
                'accrual_date': datetime.now(timezone.utc).date().isoformat()
            },
            aggregate_id=account_id
        )
        
        return {
            'account_id': account_id,
            'daily_interest': str(daily_interest),
            'total_accrued': str(self.accrued_interest[account_id])
        }
    
    async def post_monthly_interest(
        self,
        account_id: str,
        has_tfn: bool = True
    ) -> Dict:
        """
        Post accrued interest to account
        
        Called on last day of month
        
        Handles:
        - TFN withholding (46.5% if no TFN)
        - GL entries
        - Capitalization
        """
        accrued = self.accrued_interest.get(account_id, Decimal('0'))
        
        if accrued <= 0:
            return {'success': False, 'reason': 'No interest to post'}
        
        # Calculate tax withholding if no TFN
        tax_withheld = Decimal('0')
        net_interest = accrued
        
        if not has_tfn:
            # Australian TFN withholding rate: 46.5%
            tax_withheld = (accrued * Decimal('0.465')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            net_interest = accrued - tax_withheld
        
        # Create GL entries
        from ultracore.modules.accounting.general_ledger.journal import get_journal_service
        
        journal_service = get_journal_service()
        
        entries = [
            {
                'account_code': '1100',  # Customer Account (Asset)
                'debit': str(net_interest),
                'credit': '0'
            },
            {
                'account_code': '5100',  # Interest Expense (Expense)
                'debit': '0',
                'credit': str(accrued)
            }
        ]
        
        # Add tax withholding entry if applicable
        if tax_withheld > 0:
            entries.append({
                'account_code': '2400',  # Tax Payable (Liability)
                'debit': str(tax_withheld),
                'credit': '0'
            })
        
        entry = await journal_service.create_entry(
            description=f"Interest payment - Account {account_id}",
            entries=entries
        )
        
        # Reset accrued interest
        self.accrued_interest[account_id] = Decimal('0')
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='interest',
            event_type='interest_posted',
            event_data={
                'account_id': account_id,
                'gross_interest': str(accrued),
                'tax_withheld': str(tax_withheld),
                'net_interest': str(net_interest),
                'has_tfn': has_tfn,
                'journal_entry_id': entry['entry_id'],
                'posted_date': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=account_id
        )
        
        # Publish to Data Mesh
        await DataMeshPublisher.publish_transaction_data(
            f"interest_{account_id}",
            {
                'data_product': 'interest_payments',
                'account_id': account_id,
                'gross_interest': str(accrued),
                'net_interest': str(net_interest),
                'posted_date': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            'success': True,
            'account_id': account_id,
            'gross_interest': str(accrued),
            'tax_withheld': str(tax_withheld),
            'net_interest': str(net_interest),
            'journal_entry_id': entry['entry_id']
        }


class InterestOptimizationAgent:
    """
    Agentic interest rate optimization
    
    Monitors:
    - RBA cash rate changes
    - Competitor rates
    - Customer behavior
    - Profit margins
    
    Recommends:
    - Rate adjustments
    - Promotional rates
    - Retention offers
    """
    
    @staticmethod
    async def monitor_market_rates():
        """
        Monitor market rates and recommend adjustments
        
        Agentic: Runs automatically, makes recommendations
        """
        # Track RBA rate
        # Monitor competitor rates
        # Calculate optimal rate
        # Recommend changes
        
        pass
    
    @staticmethod
    async def identify_rate_sensitive_customers() -> List[Dict]:
        """
        Identify customers likely to churn over rates
        
        ML-powered: Predicts rate sensitivity
        """
        # Use churn model
        # Identify high-balance, rate-sensitive customers
        # Recommend retention offers
        
        return []

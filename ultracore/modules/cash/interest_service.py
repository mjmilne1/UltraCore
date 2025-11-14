"""
Interest Calculation Module
Automated interest calculations and crediting
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

class InterestCalculationMethod(str, Enum):
    """Interest calculation methods"""
    SIMPLE = "simple"  # Simple interest
    DAILY_BALANCE = "daily_balance"  # Daily balance method
    AVERAGE_BALANCE = "average_balance"  # Average balance method

class InterestService:
    """
    Interest Calculation Service
    
    Features:
    - Daily interest calculations
    - Multiple calculation methods
    - Automatic crediting
    - Tiered interest rates
    - Minimum balance requirements
    """
    
    def __init__(self):
        self.interest_history = []
        self.tier_rates = self._initialize_tiers()
        
    def _initialize_tiers(self) -> List[Dict[str, Any]]:
        """Initialize tiered interest rates"""
        
        return [
            {"min_balance": 0, "max_balance": 10000, "rate": 2.0},
            {"min_balance": 10000, "max_balance": 50000, "rate": 3.0},
            {"min_balance": 50000, "max_balance": 100000, "rate": 3.5},
            {"min_balance": 100000, "max_balance": float("inf"), "rate": 4.0}
        ]
    
    def calculate_daily_interest(
        self,
        balance: Decimal,
        annual_rate: float,
        days: int = 1
    ) -> Decimal:
        """
        Calculate daily interest
        
        Formula: Balance × (Annual Rate / 100) × (Days / 365)
        """
        
        interest = balance * Decimal(str(annual_rate)) / Decimal("100") * Decimal(days) / Decimal("365")
        
        # Round to 2 decimal places
        interest = interest.quantize(Decimal("0.01"))
        
        return interest
    
    def calculate_tiered_interest(
        self,
        balance: Decimal,
        days: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate interest using tiered rates
        
        Different rates apply to different balance ranges
        """
        
        total_interest = Decimal("0.00")
        tier_breakdown = []
        
        remaining_balance = balance
        
        for tier in self.tier_rates:
            min_bal = Decimal(str(tier["min_balance"]))
            max_bal = Decimal(str(tier["max_balance"]))
            rate = tier["rate"]
            
            if remaining_balance <= 0:
                break
            
            # Amount in this tier
            if remaining_balance >= (max_bal - min_bal):
                tier_amount = max_bal - min_bal
            else:
                tier_amount = remaining_balance
            
            # Calculate interest for this tier
            tier_interest = self.calculate_daily_interest(tier_amount, rate, days)
            
            tier_breakdown.append({
                "tier_min": float(min_bal),
                "tier_max": float(max_bal),
                "rate": rate,
                "balance_in_tier": float(tier_amount),
                "interest": float(tier_interest)
            })
            
            total_interest += tier_interest
            remaining_balance -= tier_amount
        
        return {
            "total_interest": float(total_interest),
            "tier_breakdown": tier_breakdown
        }
    
    def calculate_average_balance_interest(
        self,
        daily_balances: List[Decimal],
        annual_rate: float
    ) -> Decimal:
        """
        Calculate interest based on average balance
        
        Used for monthly interest payments
        """
        
        if not daily_balances:
            return Decimal("0.00")
        
        # Calculate average balance
        average_balance = sum(daily_balances) / len(daily_balances)
        
        # Calculate interest for the period
        days = len(daily_balances)
        interest = self.calculate_daily_interest(average_balance, annual_rate, days)
        
        return interest
    
    def credit_interest_to_account(
        self,
        account_id: str,
        balance: Decimal,
        annual_rate: float,
        period_start: datetime,
        period_end: datetime,
        method: InterestCalculationMethod = InterestCalculationMethod.DAILY_BALANCE
    ) -> Dict[str, Any]:
        """
        Credit interest to account
        """
        
        days = (period_end - period_start).days
        
        if method == InterestCalculationMethod.SIMPLE:
            interest = self.calculate_daily_interest(balance, annual_rate, days)
            breakdown = None
        
        elif method == InterestCalculationMethod.DAILY_BALANCE:
            result = self.calculate_tiered_interest(balance, days)
            interest = Decimal(str(result["total_interest"]))
            breakdown = result["tier_breakdown"]
        
        else:
            interest = Decimal("0.00")
            breakdown = None
        
        # Record interest credit
        interest_record = {
            "account_id": account_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "days": days,
            "balance": float(balance),
            "annual_rate": annual_rate,
            "interest_amount": float(interest),
            "method": method.value,
            "breakdown": breakdown,
            "credited_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.interest_history.append(interest_record)
        
        return interest_record
    
    def get_interest_summary(
        self,
        account_id: str,
        year: int
    ) -> Dict[str, Any]:
        """Get annual interest summary"""
        
        account_history = [
            h for h in self.interest_history
            if h["account_id"] == account_id
            and datetime.fromisoformat(h["period_start"]).year == year
        ]
        
        total_interest = sum(h["interest_amount"] for h in account_history)
        
        return {
            "account_id": account_id,
            "year": year,
            "total_interest": total_interest,
            "payment_count": len(account_history),
            "history": account_history
        }

# Global interest service
interest_service = InterestService()

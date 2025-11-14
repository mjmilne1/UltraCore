"""Flexible Fee Calculation Engine - Maximum Flexibility"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional

class FeeCalculator:
    """Maximum flexibility fee calculation engine"""
    
    def calculate_management_fee(self, aum: Decimal, rate: Decimal,
                                 period_days: int = 365) -> Decimal:
        """Calculate management fee (% of AUM annually)"""
        annual_fee = aum * (rate / Decimal("100"))
        return (annual_fee / Decimal("365")) * Decimal(str(period_days))
    
    def calculate_performance_fee(self, gains: Decimal, rate: Decimal,
                                  high_water_mark: Optional[Decimal] = None) -> Decimal:
        """Calculate performance fee (% of gains above high water mark)"""
        if high_water_mark and gains <= high_water_mark:
            return Decimal("0")
        taxable_gains = gains - (high_water_mark or Decimal("0"))
        return taxable_gains * (rate / Decimal("100"))
    
    def calculate_tiered_fee(self, amount: Decimal, tiers: list) -> Decimal:
        """Calculate tiered fees (different rates for different brackets)
        Example: tiers = [
            {"threshold": 100000, "rate": 1.0},
            {"threshold": 500000, "rate": 0.75},
            {"threshold": None, "rate": 0.5}
        ]
        """
        total_fee = Decimal("0")
        remaining = amount
        prev_threshold = Decimal("0")
        
        for tier in tiers:
            threshold = Decimal(str(tier["threshold"])) if tier["threshold"] else None
            rate = Decimal(str(tier["rate"]))
            
            if threshold is None:
                # Final tier - all remaining
                total_fee += remaining * (rate / Decimal("100"))
                break
            elif remaining > (threshold - prev_threshold):
                # This tier is fully utilized
                tier_amount = threshold - prev_threshold
                total_fee += tier_amount * (rate / Decimal("100"))
                remaining -= tier_amount
                prev_threshold = threshold
            else:
                # Partial tier utilization
                total_fee += remaining * (rate / Decimal("100"))
                break
        
        return total_fee
    
    def apply_min_max(self, fee: Decimal, min_fee: Optional[Decimal],
                     max_fee: Optional[Decimal]) -> Decimal:
        """Apply min/max fee caps"""
        if min_fee and fee < min_fee:
            return min_fee
        if max_fee and fee > max_fee:
            return max_fee
        return fee
    
    def apply_discount(self, fee: Decimal, discount_pct: Optional[Decimal],
                      discount_amt: Optional[Decimal]) -> Decimal:
        """Apply promotional discount"""
        if discount_pct:
            fee = fee * (Decimal("100") - discount_pct) / Decimal("100")
        if discount_amt:
            fee = max(Decimal("0"), fee - discount_amt)
        return fee

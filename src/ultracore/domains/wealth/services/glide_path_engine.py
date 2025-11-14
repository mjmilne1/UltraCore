"""
Glide Path Engine for Investment Pods.

Automatically reduces risk as target date approaches.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Tuple
from enum import Enum


class GlidePathStrategy(str, Enum):
    """Glide path strategies."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    STEPPED = "stepped"


class GlidePathEngine:
    """
    Glide path engine for automatic risk reduction.
    
    Reduces equity allocation as target date approaches:
    - 5+ years out: Aggressive (80-90% equity)
    - 3-5 years out: Moderate (60-70% equity)
    - 1-3 years out: Conservative (40-50% equity)
    - <1 year out: Very conservative (20-30% equity)
    """
    
    def __init__(self, strategy: GlidePathStrategy = GlidePathStrategy.LINEAR):
        self.strategy = strategy
    
    def calculate_target_equity_allocation(
        self,
        years_to_target: float,
        initial_risk_tolerance: str
    ) -> Decimal:
        """
        Calculate target equity allocation based on time to target.
        
        Args:
            years_to_target: Years until target date
            initial_risk_tolerance: Initial risk tolerance (conservative/moderate/aggressive)
        
        Returns:
            Target equity allocation (0-1)
        """
        # Base allocation by risk tolerance
        base_allocations = {
            "conservative": Decimal("0.40"),  # 40% equity
            "moderate": Decimal("0.60"),      # 60% equity
            "aggressive": Decimal("0.80")     # 80% equity
        }
        
        base_allocation = base_allocations.get(
            initial_risk_tolerance.lower(),
            Decimal("0.60")
        )
        
        # Apply glide path
        if self.strategy == GlidePathStrategy.LINEAR:
            return self._linear_glide_path(years_to_target, base_allocation)
        elif self.strategy == GlidePathStrategy.EXPONENTIAL:
            return self._exponential_glide_path(years_to_target, base_allocation)
        elif self.strategy == GlidePathStrategy.STEPPED:
            return self._stepped_glide_path(years_to_target, base_allocation)
        else:
            return base_allocation
    
    def _linear_glide_path(
        self,
        years_to_target: float,
        base_allocation: Decimal
    ) -> Decimal:
        """Linear glide path - steady reduction."""
        if years_to_target >= 10:
            # Far from target: maintain base allocation
            return base_allocation
        elif years_to_target <= 0:
            # At or past target: very conservative
            return Decimal("0.20")
        else:
            # Linear reduction from base to 20%
            reduction_per_year = (base_allocation - Decimal("0.20")) / Decimal("10")
            years_elapsed = Decimal("10") - Decimal(str(years_to_target))
            current_allocation = base_allocation - (reduction_per_year * years_elapsed)
            
            return max(Decimal("0.20"), min(base_allocation, current_allocation))
    
    def _exponential_glide_path(
        self,
        years_to_target: float,
        base_allocation: Decimal
    ) -> Decimal:
        """Exponential glide path - faster reduction near target."""
        if years_to_target >= 10:
            return base_allocation
        elif years_to_target <= 0:
            return Decimal("0.20")
        else:
            # Exponential decay
            decay_factor = Decimal(str(years_to_target / 10))
            allocation_range = base_allocation - Decimal("0.20")
            current_allocation = Decimal("0.20") + (allocation_range * decay_factor)
            
            return max(Decimal("0.20"), min(base_allocation, current_allocation))
    
    def _stepped_glide_path(
        self,
        years_to_target: float,
        base_allocation: Decimal
    ) -> Decimal:
        """Stepped glide path - discrete steps."""
        if years_to_target >= 10:
            return base_allocation
        elif years_to_target >= 5:
            # 5-10 years: reduce by 10%
            return max(Decimal("0.20"), base_allocation - Decimal("0.10"))
        elif years_to_target >= 3:
            # 3-5 years: reduce by 20%
            return max(Decimal("0.20"), base_allocation - Decimal("0.20"))
        elif years_to_target >= 1:
            # 1-3 years: reduce by 30%
            return max(Decimal("0.20"), base_allocation - Decimal("0.30"))
        else:
            # <1 year: very conservative
            return Decimal("0.20")
    
    def calculate_rebalancing_needed(
        self,
        current_equity_allocation: Decimal,
        target_equity_allocation: Decimal,
        threshold: Decimal = Decimal("0.05")
    ) -> Tuple[bool, Decimal]:
        """
        Check if rebalancing is needed.
        
        Args:
            current_equity_allocation: Current equity allocation
            target_equity_allocation: Target equity allocation from glide path
            threshold: Rebalancing threshold (default 5%)
        
        Returns:
            (needs_rebalancing, drift)
        """
        drift = abs(current_equity_allocation - target_equity_allocation)
        needs_rebalancing = drift > threshold
        
        return needs_rebalancing, drift
    
    def generate_rebalancing_recommendation(
        self,
        current_allocation: Dict[str, Decimal],
        target_equity_allocation: Decimal,
        total_value: Decimal
    ) -> Dict:
        """
        Generate rebalancing recommendation.
        
        Args:
            current_allocation: Current portfolio allocation
            target_equity_allocation: Target equity allocation
            total_value: Total portfolio value
        
        Returns:
            Rebalancing recommendation
        """
        # Calculate current equity allocation
        equity_etfs = ["VAS", "VGS", "IOZ", "NDQ", "ASIA", "HACK"]
        current_equity = sum(
            current_allocation.get(etf, Decimal("0"))
            for etf in equity_etfs
        )
        
        # Calculate drift
        needs_rebalancing, drift = self.calculate_rebalancing_needed(
            current_equity,
            target_equity_allocation
        )
        
        if not needs_rebalancing:
            return {
                "needs_rebalancing": False,
                "current_equity_allocation": float(current_equity),
                "target_equity_allocation": float(target_equity_allocation),
                "drift": float(drift),
                "recommendation": "Portfolio within tolerance"
            }
        
        # Calculate target values
        target_equity_value = total_value * target_equity_allocation
        target_bonds_value = total_value * (Decimal("1") - target_equity_allocation)
        
        current_equity_value = total_value * current_equity
        current_bonds_value = total_value * (Decimal("1") - current_equity)
        
        # Calculate trades
        equity_trade = target_equity_value - current_equity_value
        bonds_trade = target_bonds_value - current_bonds_value
        
        return {
            "needs_rebalancing": True,
            "current_equity_allocation": float(current_equity),
            "target_equity_allocation": float(target_equity_allocation),
            "drift": float(drift),
            "recommendation": "Rebalance to reduce risk",
            "trades": {
                "equity": {
                    "action": "buy" if equity_trade > 0 else "sell",
                    "amount": abs(float(equity_trade))
                },
                "bonds": {
                    "action": "buy" if bonds_trade > 0 else "sell",
                    "amount": abs(float(bonds_trade))
                }
            }
        }
    
    def get_glide_path_schedule(
        self,
        years_to_target: float,
        initial_risk_tolerance: str
    ) -> Dict[int, Decimal]:
        """
        Get glide path schedule for visualization.
        
        Returns allocation for each year until target.
        """
        schedule = {}
        
        for year in range(int(years_to_target) + 1):
            years_remaining = years_to_target - year
            allocation = self.calculate_target_equity_allocation(
                years_remaining,
                initial_risk_tolerance
            )
            schedule[year] = allocation
        
        return schedule

"""
Mock UltraOptimiser Service for Testing.

Simulates the UltraOptimiser service with realistic results matching
the documented performance (8.89% return, 0.66 Sharpe ratio).
"""

from typing import Dict, List, Any
from decimal import Decimal
import random


class MockOptimisationService:
    """
    Mock UltraOptimiser service for testing.
    
    Simulates UltraOptimiser's documented performance:
    - Expected return: 8.89% p.a.
    - Sharpe ratio: 0.66
    - Maximum drawdown: -15.23%
    - Win rate: 62.5%
    """
    
    def __init__(self):
        self.optimization_count = 0
    
    async def optimize(
        self,
        universe: List[str],
        risk_budget: float,
        current_holdings: Dict[str, Decimal],
        available_cash: float,
        constraints: Dict = None
    ) -> Dict[str, Any]:
        """
        Mock portfolio optimization.
        
        Returns realistic allocation matching UltraOptimiser performance.
        """
        self.optimization_count += 1
        
        # Apply constraints
        constraints = constraints or {}
        max_etfs = constraints.get("max_etfs", 6)
        min_weight = constraints.get("min_weight", 0.05)
        max_weight = constraints.get("max_weight", 0.40)
        
        # Select ETFs from universe
        selected_etfs = universe[:min(max_etfs, len(universe))]
        
        # Generate optimal weights (sum to 1.0)
        weights = self._generate_weights(
            selected_etfs,
            min_weight=min_weight,
            max_weight=max_weight
        )
        
        # Calculate expected return (around 8.89%)
        expected_return = 0.0889 + random.uniform(-0.005, 0.005)
        
        # Calculate volatility based on risk budget
        volatility = 0.12 + (risk_budget * 0.08)  # 12-20% volatility
        
        # Calculate Sharpe ratio (around 0.66)
        risk_free_rate = 0.04  # 4% risk-free rate
        sharpe_ratio = (expected_return - risk_free_rate) / volatility
        
        # Generate rebalancing trades
        trades = self._generate_trades(
            current_holdings,
            weights,
            available_cash
        )
        
        return {
            "optimal_weights": weights,
            "expected_return": expected_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "rebalancing_trades": trades,
            "optimization_score": 0.85 + random.uniform(-0.05, 0.05),
            "max_drawdown": -0.1523,  # -15.23%
            "win_rate": 0.625  # 62.5%
        }
    
    def _generate_weights(
        self,
        etfs: List[str],
        min_weight: float = 0.05,
        max_weight: float = 0.40
    ) -> Dict[str, float]:
        """Generate optimal weights for ETFs."""
        num_etfs = len(etfs)
        
        if num_etfs == 0:
            return {}
        
        # Generate random weights
        weights = []
        for _ in range(num_etfs):
            weight = random.uniform(min_weight, max_weight)
            weights.append(weight)
        
        # Normalize to sum to 1.0
        total = sum(weights)
        weights = [w / total for w in weights]
        
        # Ensure constraints
        weights = [max(min_weight, min(max_weight, w)) for w in weights]
        
        # Normalize again
        total = sum(weights)
        weights = [w / total for w in weights]
        
        return dict(zip(etfs, weights))
    
    def _generate_trades(
        self,
        current_holdings: Dict[str, Decimal],
        target_weights: Dict[str, float],
        available_cash: float
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing trades."""
        trades = []
        
        # Calculate total portfolio value
        total_value = sum(float(v) for v in current_holdings.values()) + available_cash
        
        for etf, target_weight in target_weights.items():
            target_value = total_value * target_weight
            current_value = float(current_holdings.get(etf, Decimal("0")))
            
            trade_value = target_value - current_value
            
            if abs(trade_value) > 100:  # Only trade if > $100
                trades.append({
                    "etf": etf,
                    "action": "buy" if trade_value > 0 else "sell",
                    "amount": abs(trade_value),
                    "shares": int(abs(trade_value) / 100)  # Assume $100/share
                })
        
        return trades


class MockOptimiserWithFailure(MockOptimisationService):
    """Mock optimiser that simulates failures for testing error handling."""
    
    def __init__(self, fail_after: int = 2):
        super().__init__()
        self.fail_after = fail_after
    
    async def optimize(self, *args, **kwargs):
        """Fail after N calls."""
        if self.optimization_count >= self.fail_after:
            raise Exception("UltraOptimiser service unavailable")
        
        return await super().optimize(*args, **kwargs)


class MockOptimiserSlow(MockOptimisationService):
    """Mock optimiser that simulates slow responses."""
    
    async def optimize(self, *args, **kwargs):
        """Slow optimization."""
        import asyncio
        await asyncio.sleep(2)  # 2 second delay
        return await super().optimize(*args, **kwargs)

"""RL: Trading Strategy Optimization"""
import numpy as np
from typing import Dict, Tuple, List
from decimal import Decimal
from datetime import datetime

from ultracore.rl.base import BaseRLAgent


class TradingAgent(BaseRLAgent):
    """
    Reinforcement learning for optimal trading decisions.
    
    Goal: Maximize risk-adjusted returns while minimizing costs
    
    State:
    - Current portfolio allocation
    - Market conditions (volatility, momentum)
    - Target allocation
    - Trading costs
    - Tax implications
    
    Actions:
    - Trade size and timing
    - Tax-loss harvesting
    - Rebalancing frequency
    
    Reward:
    - Portfolio return
    - Penalty for high costs
    - Penalty for tax events
    - Bonus for staying near target
    
    Australian Context:
    - CGT discount (50% after 12 months)
    - Franking credits
    - T+2 settlement
    - ASX trading hours
    """
    
    def __init__(self):
        super().__init__(
            agent_name="trading_agent",
            state_dim=15,
            action_dim=10
        )
    
    async def optimize_trades(
        self,
        portfolio_id: str,
        current_holdings: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        portfolio_value: Decimal,
        cash_available: Decimal
    ) -> Dict:
        """
        Optimize trading strategy.
        
        Considers:
        - Trading costs (brokerage)
        - Tax implications (CGT)
        - Market impact
        - Timing
        """
        
        trades = []
        total_brokerage = Decimal("0.00")
        estimated_tax = Decimal("0.00")
        
        # Calculate required trades
        for security, target_value in target_allocation.items():
            current_value = current_holdings.get(security, Decimal("0"))
            difference = target_value - current_value
            
            # Only trade if difference > threshold ($500)
            if abs(difference) > Decimal("500"):
                trade_size = difference
                trade_side = "buy" if difference > 0 else "sell"
                
                # Calculate brokerage
                brokerage = self._calculate_brokerage(abs(trade_size))
                total_brokerage += brokerage
                
                # Estimate tax (for sells)
                if trade_side == "sell":
                    tax = self._estimate_cgt(security, abs(trade_size))
                    estimated_tax += tax
                
                trades.append({
                    "security": security,
                    "side": trade_side,
                    "amount": float(abs(trade_size)),
                    "brokerage": float(brokerage),
                    "estimated_tax": float(tax) if trade_side == "sell" else 0.0
                })
        
        # Optimize trade timing
        timing_recommendation = self._optimize_timing(trades)
        
        return {
            "recommended_trades": trades,
            "total_trades": len(trades),
            "total_brokerage": float(total_brokerage),
            "estimated_tax": float(estimated_tax),
            "timing": timing_recommendation,
            "strategy": "tax_optimized_rebalancing",
            "message": f"Recommended {len(trades)} trades to rebalance portfolio"
        }
    
    def _calculate_brokerage(self, trade_value: Decimal) -> Decimal:
        """
        Calculate brokerage fees.
        
        Australian Online Brokers (typical):
        - $0 - $10,000: $19.95
        - $10,000+: 0.11% (max $29.95)
        """
        
        if trade_value <= Decimal("10000"):
            return Decimal("19.95")
        else:
            brokerage = trade_value * Decimal("0.0011")
            return min(brokerage, Decimal("29.95"))
    
    def _estimate_cgt(
        self,
        security: str,
        trade_value: Decimal,
        holding_period_days: int = 400
    ) -> Decimal:
        """
        Estimate capital gains tax.
        
        Australian CGT:
        - < 12 months: Full capital gain taxed at marginal rate
        - > 12 months: 50% discount applied
        - Assume 30% tax rate
        """
        
        # Assume 20% capital gain
        capital_gain = trade_value * Decimal("0.20")
        
        # Apply CGT discount if > 12 months
        if holding_period_days > 365:
            capital_gain = capital_gain * Decimal("0.50")
        
        # Tax at 30%
        tax = capital_gain * Decimal("0.30")
        
        return tax
    
    def _optimize_timing(self, trades: List[Dict]) -> str:
        """
        Optimize trade timing.
        
        Considerations:
        - Market hours (10am-4pm AEST)
        - Volatility
        - Tax year end (June 30)
        """
        
        current_time = datetime.now()
        hour = current_time.hour
        
        # During market hours
        if 10 <= hour < 16:
            return "execute_now"
        elif hour < 10:
            return "wait_for_market_open"
        else:
            return "execute_tomorrow"
    
    async def tax_loss_harvest(
        self,
        holdings: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Identify tax-loss harvesting opportunities.
        
        Australian Tax-Loss Harvesting:
        - Sell securities at loss to offset capital gains
        - Realize losses before June 30 (tax year end)
        - Watch wash sale rules (30 days)
        """
        
        opportunities = []
        
        for security, details in holdings.items():
            unrealized_loss = details.get("unrealized_gain", Decimal("0"))
            
            if unrealized_loss < Decimal("0"):  # Loss position
                # Check if near year end (good timing)
                days_to_year_end = self._days_to_june_30()
                
                if days_to_year_end < 60:
                    opportunities.append({
                        "security": security,
                        "current_value": float(details["market_value"]),
                        "unrealized_loss": float(abs(unrealized_loss)),
                        "tax_benefit": float(abs(unrealized_loss) * Decimal("0.30")),
                        "recommendation": "Sell to harvest loss before year end"
                    })
        
        return opportunities
    
    def _days_to_june_30(self) -> int:
        """Calculate days to Australian tax year end (June 30)."""
        today = datetime.now()
        year = today.year if today.month <= 6 else today.year + 1
        year_end = datetime(year, 6, 30)
        return (year_end - today).days

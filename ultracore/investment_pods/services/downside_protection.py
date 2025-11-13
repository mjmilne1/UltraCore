"""
Downside Protection Service
Circuit breakers and risk monitoring for 15% drawdown limit
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from ..models import RiskMetrics, MarketConditions, CircuitBreakerEvent

logger = logging.getLogger(__name__)


@dataclass
class DrawdownAnalysis:
    """Drawdown analysis result"""
    current_drawdown: Decimal
    peak_value: Decimal
    current_value: Decimal
    drawdown_start_date: Optional[date]
    days_in_drawdown: int
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    circuit_breaker_distance: Decimal  # Percentage points to circuit breaker


class DownsideProtectionService:
    """
    Downside protection service with 15% circuit breaker
    
    Monitors portfolio drawdown and triggers defensive shifts
    when 15% threshold is breached
    """
    
    def __init__(self):
        self.circuit_breaker_threshold = Decimal("15.0")  # 15% max drawdown
        self.warning_threshold = Decimal("10.0")  # 10% warning level
        self.recovery_threshold = Decimal("5.0")  # 5% recovery before resuming normal allocation
    
    def calculate_drawdown(
        self,
        current_value: Decimal,
        historical_values: List[Dict]  # [{"date": "2024-01-01", "value": 100000}]
    ) -> DrawdownAnalysis:
        """
        Calculate current drawdown from peak
        """
        if not historical_values:
            return DrawdownAnalysis(
                current_drawdown=Decimal("0"),
                peak_value=current_value,
                current_value=current_value,
                drawdown_start_date=None,
                days_in_drawdown=0,
                risk_level="LOW",
                circuit_breaker_distance=self.circuit_breaker_threshold
            )
        
        # Find peak value
        peak_value = max(Decimal(str(v["value"])) for v in historical_values)
        peak_value = max(peak_value, current_value)
        
        # Calculate drawdown
        if peak_value == 0:
            current_drawdown = Decimal("0")
        else:
            current_drawdown = ((peak_value - current_value) / peak_value) * Decimal("100")
        
        # Find drawdown start date
        drawdown_start_date = None
        days_in_drawdown = 0
        
        for i, value_record in enumerate(reversed(historical_values)):
            if Decimal(str(value_record["value"])) >= peak_value * Decimal("0.99"):  # Within 1% of peak
                break
            drawdown_start_date = datetime.fromisoformat(value_record["date"]).date()
            days_in_drawdown = i + 1
        
        # Determine risk level
        if current_drawdown >= self.circuit_breaker_threshold:
            risk_level = "CRITICAL"
        elif current_drawdown >= self.warning_threshold:
            risk_level = "HIGH"
        elif current_drawdown >= Decimal("5.0"):
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
        
        # Distance to circuit breaker
        circuit_breaker_distance = self.circuit_breaker_threshold - current_drawdown
        
        logger.info(f"Drawdown analysis: current={current_drawdown}%, risk_level={risk_level}")
        
        return DrawdownAnalysis(
            current_drawdown=current_drawdown,
            peak_value=peak_value,
            current_value=current_value,
            drawdown_start_date=drawdown_start_date,
            days_in_drawdown=days_in_drawdown,
            risk_level=risk_level,
            circuit_breaker_distance=circuit_breaker_distance
        )
    
    def should_trigger_circuit_breaker(
        self,
        drawdown_analysis: DrawdownAnalysis
    ) -> Tuple[bool, str]:
        """
        Check if circuit breaker should be triggered
        
        Returns (should_trigger, reason)
        """
        if drawdown_analysis.current_drawdown >= self.circuit_breaker_threshold:
            return True, f"Drawdown breach: {drawdown_analysis.current_drawdown}% >= {self.circuit_breaker_threshold}%"
        
        return False, ""
    
    def calculate_defensive_shift(
        self,
        current_allocation: Dict[str, Decimal],
        drawdown_severity: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate defensive allocation shift based on drawdown severity
        
        More severe drawdown = more defensive shift
        """
        # Base defensive shift: move to 70% defensive, 30% equity
        base_defensive_allocation = {
            "equity": Decimal("30"),
            "defensive": Decimal("70")
        }
        
        # If drawdown is very severe (>20%), go even more defensive
        if drawdown_severity >= Decimal("20.0"):
            return {
                "equity": Decimal("20"),
                "defensive": Decimal("80")
            }
        
        return base_defensive_allocation
    
    def calculate_defensive_shift_trades(
        self,
        current_holdings: List[Dict],
        target_allocation: Dict[str, Decimal],
        total_value: Decimal
    ) -> List[Dict]:
        """
        Calculate trades for defensive shift
        Similar to glide path but more aggressive
        """
        trades = []
        
        # Calculate current allocation by asset class
        current_by_class = {}
        for holding in current_holdings:
            asset_class = holding.get("asset_class", "equity")
            class_key = "equity" if asset_class in ["australian_equity", "international_equity"] else "defensive"
            
            current_value = current_by_class.get(class_key, Decimal("0"))
            current_by_class[class_key] = current_value + holding["current_value"]
        
        # Calculate target values
        target_equity_value = total_value * target_allocation["equity"] / Decimal("100")
        target_defensive_value = total_value * target_allocation["defensive"] / Decimal("100")
        
        current_equity_value = current_by_class.get("equity", Decimal("0"))
        current_defensive_value = current_by_class.get("defensive", Decimal("0"))
        
        # Calculate rebalancing needs
        equity_diff = target_equity_value - current_equity_value
        defensive_diff = target_defensive_value - current_defensive_value
        
        logger.info(f"Defensive shift: equity_diff={equity_diff}, defensive_diff={defensive_diff}")
        
        # Sell equity holdings
        if equity_diff < 0:
            equity_holdings = [h for h in current_holdings if self._is_equity(h["asset_class"])]
            sell_amount = abs(equity_diff)
            
            for holding in equity_holdings:
                proportion = holding["current_value"] / current_equity_value if current_equity_value > 0 else 0
                sell_value = sell_amount * proportion
                units_to_sell = sell_value / holding["current_price"] if holding["current_price"] > 0 else 0
                
                if units_to_sell > 0:
                    trades.append({
                        "etf_code": holding["etf_code"],
                        "action": "SELL",
                        "units": int(units_to_sell),
                        "value": sell_value,
                        "price": holding["current_price"]
                    })
        
        # Buy defensive holdings
        if defensive_diff > 0:
            defensive_holdings = [h for h in current_holdings if not self._is_equity(h["asset_class"])]
            
            if defensive_holdings:
                buy_per_holding = abs(defensive_diff) / len(defensive_holdings)
                
                for holding in defensive_holdings:
                    units_to_buy = buy_per_holding / holding["current_price"] if holding["current_price"] > 0 else 0
                    
                    if units_to_buy > 0:
                        trades.append({
                            "etf_code": holding["etf_code"],
                            "action": "BUY",
                            "units": int(units_to_buy),
                            "value": buy_per_holding,
                            "price": holding["current_price"]
                        })
            else:
                # No defensive holdings - need to add cash/bonds ETF
                logger.warning("No defensive holdings available for circuit breaker shift")
        
        return trades
    
    def _is_equity(self, asset_class: str) -> bool:
        """Check if asset class is equity"""
        return asset_class in ["australian_equity", "international_equity"]
    
    def should_resume_normal_allocation(
        self,
        current_drawdown: Decimal,
        circuit_breaker_triggered_at: datetime
    ) -> bool:
        """
        Check if portfolio should resume normal allocation
        
        Requires:
        1. Drawdown recovered to < 5%
        2. At least 30 days since circuit breaker triggered
        """
        # Check drawdown recovery
        if current_drawdown >= self.recovery_threshold:
            return False
        
        # Check time elapsed
        days_since_trigger = (datetime.utcnow() - circuit_breaker_triggered_at).days
        if days_since_trigger < 30:
            return False
        
        logger.info(f"Circuit breaker recovery: drawdown={current_drawdown}%, days={days_since_trigger}")
        return True
    
    def calculate_risk_metrics(
        self,
        current_value: Decimal,
        historical_values: List[Dict],
        expected_volatility: Decimal
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        drawdown_analysis = self.calculate_drawdown(current_value, historical_values)
        
        # Calculate returns for volatility
        if len(historical_values) >= 2:
            returns = []
            for i in range(1, len(historical_values)):
                prev_value = Decimal(str(historical_values[i-1]["value"]))
                curr_value = Decimal(str(historical_values[i]["value"]))
                if prev_value > 0:
                    ret = (curr_value - prev_value) / prev_value
                    returns.append(float(ret))
            
            # Calculate volatility from returns
            if returns:
                import numpy as np
                actual_volatility = Decimal(str(np.std(returns) * np.sqrt(252)))  # Annualized
            else:
                actual_volatility = expected_volatility
        else:
            actual_volatility = expected_volatility
        
        # Sharpe ratio (simplified)
        risk_free_rate = Decimal("0.04")
        if actual_volatility > 0:
            sharpe_ratio = (Decimal("0.08") - risk_free_rate) / actual_volatility  # Assume 8% return
        else:
            sharpe_ratio = Decimal("0")
        
        # Value at Risk (95% confidence)
        var_95 = current_value * actual_volatility * Decimal("1.645") / Decimal("100")  # 1.645 = 95% z-score
        
        # Conditional VaR (expected loss beyond VaR)
        cvar = var_95 * Decimal("1.3")  # Simplified estimate
        
        # Downside deviation (simplified)
        downside_deviation = actual_volatility * Decimal("0.7")  # Typically 70% of total volatility
        
        # Beta (simplified - assume 1.0 for balanced portfolio)
        beta = Decimal("1.0")
        
        return RiskMetrics(
            volatility=actual_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=drawdown_analysis.current_drawdown,
            current_drawdown=drawdown_analysis.current_drawdown,
            value_at_risk_95=var_95,
            conditional_var=cvar,
            downside_deviation=downside_deviation,
            beta=beta,
            risk_level=drawdown_analysis.risk_level,
            circuit_breaker_distance=drawdown_analysis.circuit_breaker_distance
        )
    
    def generate_risk_alert_message(
        self,
        goal_name: str,
        drawdown_analysis: DrawdownAnalysis,
        action_required: str
    ) -> str:
        """Generate risk alert message for client"""
        if action_required == "monitor":
            message = f"""
⚠️ Risk Alert: {goal_name}

Your portfolio has experienced a {drawdown_analysis.current_drawdown}% decline from its peak value.

Current Status:
• Risk Level: {drawdown_analysis.risk_level}
• Distance to Circuit Breaker: {drawdown_analysis.circuit_breaker_distance}%
• Days in Drawdown: {drawdown_analysis.days_in_drawdown}

Anya is monitoring your portfolio closely. No action needed at this time.
"""
        else:  # defensive_shift
            message = f"""
🛡️ Circuit Breaker Activated: {goal_name}

Your portfolio has declined {drawdown_analysis.current_drawdown}% from its peak, triggering our downside protection.

Protective Action Taken:
• Automatically shifted to defensive allocation (70% defensive, 30% equity)
• This helps protect your capital during market volatility
• Your goal timeline and target remain unchanged

What This Means:
• Your portfolio is now more conservative to limit further losses
• Once markets stabilize, we'll gradually return to your optimal allocation
• You can continue making contributions as normal

Anya will keep you updated on recovery progress. 💙
"""
        
        return message.strip()
    
    def generate_recovery_message(
        self,
        goal_name: str,
        current_drawdown: Decimal
    ) -> str:
        """Generate recovery notification message"""
        message = f"""
🎉 Recovery Update: {goal_name}

Great news! Your portfolio has recovered from the recent market decline.

Recovery Status:
• Current Drawdown: {current_drawdown}% (below 5% threshold)
• Circuit Breaker: Deactivated
• Allocation: Resuming optimal allocation

Next Steps:
• Anya will gradually transition back to your goal-optimized allocation
• This ensures you're positioned for growth while markets are stable
• Your goal remains on track!

Keep up the great work! 🚀
"""
        return message.strip()
    
    def estimate_downside_protection_value(
        self,
        portfolio_value: Decimal,
        without_protection_drawdown: Decimal,
        with_protection_drawdown: Decimal
    ) -> Decimal:
        """
        Estimate value of downside protection
        
        Calculates how much capital was preserved by circuit breaker
        """
        # Without protection
        value_without_protection = portfolio_value * (Decimal("100") - without_protection_drawdown) / Decimal("100")
        
        # With protection
        value_with_protection = portfolio_value * (Decimal("100") - with_protection_drawdown) / Decimal("100")
        
        # Value preserved
        value_preserved = value_with_protection - value_without_protection
        
        return value_preserved

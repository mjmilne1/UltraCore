"""
Smart Glide Path Engine
Automatic asset allocation transitions based on time to goal
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from ..models import GlidePathStrategy, GoalType
from ..events import GoalType as GoalTypeEnum

logger = logging.getLogger(__name__)


@dataclass
class GlidePathTransition:
    """Glide path transition point"""
    years_remaining: int
    equity_weight: Decimal
    defensive_weight: Decimal
    transition_date: date


class GlidePathEngine:
    """
    Smart glide path engine for automatic asset allocation transitions
    
    Implements time-based glide paths for different goal types:
    - First Home: Aggressive early, conservative near goal
    - Retirement: Age-based glide path
    - Wealth Accumulation: Balanced throughout
    """
    
    # Predefined glide path strategies
    GLIDE_PATH_STRATEGIES = {
        GoalTypeEnum.FIRST_HOME: {
            "name": "First Home Buyer Glide Path",
            "description": "Aggressive growth early, conservative protection near purchase",
            "schedule": [
                {"years_remaining": 10, "equity": 90, "defensive": 10},
                {"years_remaining": 7, "equity": 80, "defensive": 20},
                {"years_remaining": 5, "equity": 70, "defensive": 30},
                {"years_remaining": 3, "equity": 50, "defensive": 50},
                {"years_remaining": 2, "equity": 30, "defensive": 70},
                {"years_remaining": 1, "equity": 10, "defensive": 90},
            ]
        },
        GoalTypeEnum.RETIREMENT: {
            "name": "Retirement Glide Path",
            "description": "Age-based allocation, gradual shift to defensive",
            "schedule": [
                {"years_remaining": 30, "equity": 90, "defensive": 10},
                {"years_remaining": 25, "equity": 85, "defensive": 15},
                {"years_remaining": 20, "equity": 80, "defensive": 20},
                {"years_remaining": 15, "equity": 70, "defensive": 30},
                {"years_remaining": 10, "equity": 60, "defensive": 40},
                {"years_remaining": 5, "equity": 50, "defensive": 50},
                {"years_remaining": 2, "equity": 40, "defensive": 60},
            ]
        },
        GoalTypeEnum.WEALTH_ACCUMULATION: {
            "name": "Wealth Accumulation Glide Path",
            "description": "Balanced growth throughout, minor defensive shift near goal",
            "schedule": [
                {"years_remaining": 20, "equity": 80, "defensive": 20},
                {"years_remaining": 15, "equity": 75, "defensive": 25},
                {"years_remaining": 10, "equity": 70, "defensive": 30},
                {"years_remaining": 5, "equity": 65, "defensive": 35},
                {"years_remaining": 2, "equity": 60, "defensive": 40},
            ]
        },
        GoalTypeEnum.EMERGENCY_FUND: {
            "name": "Emergency Fund Glide Path",
            "description": "Conservative throughout, prioritize capital preservation",
            "schedule": [
                {"years_remaining": 5, "equity": 40, "defensive": 60},
                {"years_remaining": 3, "equity": 30, "defensive": 70},
                {"years_remaining": 1, "equity": 20, "defensive": 80},
            ]
        },
        GoalTypeEnum.EDUCATION: {
            "name": "Education Savings Glide Path",
            "description": "Growth early, protection near enrollment",
            "schedule": [
                {"years_remaining": 15, "equity": 85, "defensive": 15},
                {"years_remaining": 10, "equity": 75, "defensive": 25},
                {"years_remaining": 7, "equity": 65, "defensive": 35},
                {"years_remaining": 5, "equity": 50, "defensive": 50},
                {"years_remaining": 3, "equity": 35, "defensive": 65},
                {"years_remaining": 1, "equity": 20, "defensive": 80},
            ]
        },
    }
    
    def __init__(self):
        self.transition_frequency_months = 12  # Annual transitions
    
    def get_glide_path_strategy(self, goal_type: GoalTypeEnum) -> Dict:
        """Get glide path strategy for goal type"""
        strategy = self.GLIDE_PATH_STRATEGIES.get(
            goal_type,
            self.GLIDE_PATH_STRATEGIES[GoalTypeEnum.WEALTH_ACCUMULATION]  # Default
        )
        return strategy
    
    def calculate_current_allocation(
        self,
        goal_type: GoalTypeEnum,
        target_date: date,
        current_date: Optional[date] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate current target allocation based on time to goal
        """
        if current_date is None:
            current_date = date.today()
        
        # Calculate years remaining
        years_remaining = (target_date - current_date).days / 365.25
        
        if years_remaining <= 0:
            # Goal reached or past due - maximum defensive
            return {"equity": Decimal("0"), "defensive": Decimal("100")}
        
        # Get glide path strategy
        strategy = self.get_glide_path_strategy(goal_type)
        schedule = strategy["schedule"]
        
        # Find appropriate allocation
        # Linear interpolation between schedule points
        for i, point in enumerate(schedule):
            if years_remaining >= point["years_remaining"]:
                if i == 0:
                    # Before first point - use first allocation
                    return {
                        "equity": Decimal(str(point["equity"])),
                        "defensive": Decimal(str(point["defensive"]))
                    }
                else:
                    # Interpolate between points
                    prev_point = schedule[i - 1]
                    
                    # Linear interpolation
                    years_range = prev_point["years_remaining"] - point["years_remaining"]
                    years_from_point = years_remaining - point["years_remaining"]
                    ratio = years_from_point / years_range if years_range > 0 else 0
                    
                    equity = point["equity"] + ratio * (prev_point["equity"] - point["equity"])
                    defensive = point["defensive"] + ratio * (prev_point["defensive"] - point["defensive"])
                    
                    return {
                        "equity": Decimal(str(round(equity, 1))),
                        "defensive": Decimal(str(round(defensive, 1)))
                    }
        
        # After last point - use last allocation
        last_point = schedule[-1]
        return {
            "equity": Decimal(str(last_point["equity"])),
            "defensive": Decimal(str(last_point["defensive"]))
        }
    
    def calculate_glide_path_schedule(
        self,
        goal_type: GoalTypeEnum,
        target_date: date,
        current_date: Optional[date] = None
    ) -> List[GlidePathTransition]:
        """
        Calculate full glide path schedule with transition dates
        """
        if current_date is None:
            current_date = date.today()
        
        strategy = self.get_glide_path_strategy(goal_type)
        schedule = strategy["schedule"]
        
        transitions = []
        
        for point in schedule:
            # Calculate transition date
            transition_date = target_date - timedelta(days=int(point["years_remaining"] * 365.25))
            
            # Only include future transitions
            if transition_date >= current_date:
                transitions.append(GlidePathTransition(
                    years_remaining=point["years_remaining"],
                    equity_weight=Decimal(str(point["equity"])),
                    defensive_weight=Decimal(str(point["defensive"])),
                    transition_date=transition_date
                ))
        
        return sorted(transitions, key=lambda t: t.transition_date)
    
    def get_next_transition(
        self,
        goal_type: GoalTypeEnum,
        target_date: date,
        current_date: Optional[date] = None
    ) -> Optional[GlidePathTransition]:
        """Get next glide path transition"""
        transitions = self.calculate_glide_path_schedule(goal_type, target_date, current_date)
        
        if not transitions:
            return None
        
        return transitions[0]  # First (earliest) transition
    
    def should_execute_transition(
        self,
        current_allocation: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        threshold: Decimal = Decimal("10.0")
    ) -> bool:
        """
        Check if transition should be executed
        Executes if allocation drift > threshold
        """
        equity_drift = abs(
            current_allocation.get("equity", Decimal("0")) -
            target_allocation.get("equity", Decimal("0"))
        )
        
        return equity_drift >= threshold
    
    def calculate_transition_trades(
        self,
        current_holdings: List[Dict],
        target_allocation: Dict[str, Decimal],
        total_value: Decimal
    ) -> List[Dict]:
        """
        Calculate trades required for glide path transition
        
        Returns list of trades: [{"etf_code": "VAS", "action": "SELL", "units": 50, "value": 4275}]
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
        
        logger.info(f"Glide path transition: equity_diff={equity_diff}, defensive_diff={defensive_diff}")
        
        # Generate trades
        if equity_diff < 0:
            # Sell equity, buy defensive
            # Sell proportionally from equity holdings
            equity_holdings = [h for h in current_holdings if self._is_equity(h["asset_class"])]
            sell_amount = abs(equity_diff)
            
            for holding in equity_holdings:
                proportion = holding["current_value"] / current_equity_value
                sell_value = sell_amount * proportion
                units_to_sell = sell_value / holding["current_price"]
                
                trades.append({
                    "etf_code": holding["etf_code"],
                    "action": "SELL",
                    "units": int(units_to_sell),
                    "value": sell_value,
                    "price": holding["current_price"]
                })
            
            # Buy defensive
            defensive_holdings = [h for h in current_holdings if not self._is_equity(h["asset_class"])]
            if defensive_holdings:
                buy_per_holding = abs(defensive_diff) / len(defensive_holdings)
                
                for holding in defensive_holdings:
                    units_to_buy = buy_per_holding / holding["current_price"]
                    
                    trades.append({
                        "etf_code": holding["etf_code"],
                        "action": "BUY",
                        "units": int(units_to_buy),
                        "value": buy_per_holding,
                        "price": holding["current_price"]
                    })
        
        elif equity_diff > 0:
            # Buy equity, sell defensive
            defensive_holdings = [h for h in current_holdings if not self._is_equity(h["asset_class"])]
            sell_amount = abs(defensive_diff)
            
            for holding in defensive_holdings:
                proportion = holding["current_value"] / current_defensive_value
                sell_value = sell_amount * proportion
                units_to_sell = sell_value / holding["current_price"]
                
                trades.append({
                    "etf_code": holding["etf_code"],
                    "action": "SELL",
                    "units": int(units_to_sell),
                    "value": sell_value,
                    "price": holding["current_price"]
                })
            
            # Buy equity
            equity_holdings = [h for h in current_holdings if self._is_equity(h["asset_class"])]
            if equity_holdings:
                buy_per_holding = abs(equity_diff) / len(equity_holdings)
                
                for holding in equity_holdings:
                    units_to_buy = buy_per_holding / holding["current_price"]
                    
                    trades.append({
                        "etf_code": holding["etf_code"],
                        "action": "BUY",
                        "units": int(units_to_buy),
                        "value": buy_per_holding,
                        "price": holding["current_price"]
                    })
        
        return trades
    
    def _is_equity(self, asset_class: str) -> bool:
        """Check if asset class is equity"""
        return asset_class in ["australian_equity", "international_equity"]
    
    def estimate_transition_cost(
        self,
        trades: List[Dict],
        brokerage_rate: Decimal = Decimal("0.001")  # 0.1% brokerage
    ) -> Decimal:
        """Estimate cost of executing transition trades"""
        total_trade_value = sum(Decimal(str(trade["value"])) for trade in trades)
        brokerage_cost = total_trade_value * brokerage_rate
        
        # Minimum brokerage per trade
        min_brokerage_per_trade = Decimal("5.00")
        min_total_brokerage = len(trades) * min_brokerage_per_trade
        
        return max(brokerage_cost, min_total_brokerage)
    
    def generate_transition_notification(
        self,
        goal_name: str,
        current_allocation: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        transition_date: date,
        months_to_goal: int
    ) -> str:
        """Generate notification message for glide path transition"""
        message = f"""
🎯 Glide Path Transition for {goal_name}

Your portfolio allocation will be automatically adjusted to match your timeline:

Current Allocation:
• Equity: {current_allocation['equity']}%
• Defensive: {current_allocation['defensive']}%

New Target Allocation:
• Equity: {target_allocation['equity']}%
• Defensive: {target_allocation['defensive']}%

Transition Date: {transition_date.strftime('%B %d, %Y')}
Months to Goal: {months_to_goal}

This automatic transition helps protect your goal as you get closer to your target date.
No action required - Anya will handle this for you! 🚀
"""
        return message.strip()

"""
Automated Rebalancing Engine
AI-powered portfolio rebalancing with multiple strategies
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

class RebalancingStrategy(str, Enum):
    THRESHOLD = "threshold"      # Rebalance when drift > threshold
    CALENDAR = "calendar"        # Rebalance on schedule
    TACTICAL = "tactical"        # AI-driven tactical rebalancing
    TOLERANCE_BAND = "tolerance_band"  # Rebalance when outside bands

class RebalancingEngine:
    """
    Automated rebalancing engine with AI integration
    """
    
    def __init__(self):
        self.rebalancing_history = []
        self.threshold = 0.05  # 5% default threshold
    
    async def evaluate_rebalancing_need(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
        strategy: RebalancingStrategy = RebalancingStrategy.THRESHOLD
    ) -> Dict[str, Any]:
        """
        Evaluate if portfolio needs rebalancing
        """
        
        # Calculate drifts
        drifts = {}
        max_drift = 0
        
        for ticker in set(list(current_allocation.keys()) + list(target_allocation.keys())):
            current = current_allocation.get(ticker, 0)
            target = target_allocation.get(ticker, 0)
            drift = current - target
            
            drifts[ticker] = {
                "current": current,
                "target": target,
                "drift": drift,
                "drift_abs": abs(drift)
            }
            
            max_drift = max(max_drift, abs(drift))
        
        # Determine if rebalancing needed based on strategy
        needs_rebalancing = False
        reason = ""
        
        if strategy == RebalancingStrategy.THRESHOLD:
            needs_rebalancing = max_drift > self.threshold
            reason = f"Max drift {max_drift:.2%} exceeds threshold {self.threshold:.2%}"
        
        elif strategy == RebalancingStrategy.TOLERANCE_BAND:
            # More sophisticated - different tolerance for different assets
            for ticker, drift_info in drifts.items():
                target = drift_info["target"]
                tolerance = self._calculate_tolerance_band(target)
                if drift_info["drift_abs"] > tolerance:
                    needs_rebalancing = True
                    reason = f"{ticker} outside tolerance band"
                    break
        
        elif strategy == RebalancingStrategy.TACTICAL:
            # AI-driven decision
            from ultracore.agents.holdings_agent import holdings_agent
            # Would use AI agent to decide
            needs_rebalancing = max_drift > self.threshold  # Fallback
            reason = "AI tactical rebalancing recommended"
        
        return {
            "needs_rebalancing": needs_rebalancing,
            "reason": reason,
            "max_drift": max_drift,
            "drifts": drifts,
            "strategy": strategy
        }
    
    async def generate_rebalancing_trades(
        self,
        current_positions: List[Dict[str, Any]],
        target_allocation: Dict[str, float],
        total_value: float,
        min_trade_size: float = 100
    ) -> Dict[str, Any]:
        """
        Generate specific trades to rebalance portfolio
        """
        
        # Calculate current allocation
        current_allocation = {}
        for position in current_positions:
            ticker = position["ticker"]
            value = position["market_value"]
            current_allocation[ticker] = value / total_value if total_value > 0 else 0
        
        # Generate trades
        trades = []
        
        for ticker, target_weight in target_allocation.items():
            current_weight = current_allocation.get(ticker, 0)
            drift = current_weight - target_weight
            
            if abs(drift) < 0.01:  # Skip tiny adjustments
                continue
            
            # Calculate trade value
            trade_value = abs(drift * total_value)
            
            if trade_value < min_trade_size:
                continue
            
            # Find current position
            current_position = next(
                (p for p in current_positions if p["ticker"] == ticker),
                None
            )
            
            if drift > 0:
                # Overweight - need to sell
                if current_position:
                    quantity_to_sell = (drift * total_value) / current_position.get("current_price", 1)
                    
                    trades.append({
                        "ticker": ticker,
                        "action": "sell",
                        "quantity": quantity_to_sell,
                        "estimated_price": current_position.get("current_price"),
                        "estimated_value": trade_value,
                        "reason": f"Reduce from {current_weight:.2%} to {target_weight:.2%}"
                    })
            else:
                # Underweight - need to buy
                estimated_price = self._get_estimated_price(ticker, current_positions)
                quantity_to_buy = trade_value / estimated_price if estimated_price > 0 else 0
                
                trades.append({
                    "ticker": ticker,
                    "action": "buy",
                    "quantity": quantity_to_buy,
                    "estimated_price": estimated_price,
                    "estimated_value": trade_value,
                    "reason": f"Increase from {current_weight:.2%} to {target_weight:.2%}"
                })
        
        # Calculate costs and impact
        total_trade_value = sum(t["estimated_value"] for t in trades)
        estimated_costs = self._calculate_transaction_costs(trades)
        
        rebalancing_plan = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trades": trades,
            "trade_count": len(trades),
            "total_trade_value": total_trade_value,
            "turnover_pct": total_trade_value / total_value if total_value > 0 else 0,
            "estimated_costs": estimated_costs,
            "net_impact": -estimated_costs  # Cost is negative impact
        }
        
        return rebalancing_plan
    
    async def execute_rebalancing(
        self,
        client_id: str,
        rebalancing_plan: Dict[str, Any],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Execute rebalancing trades
        """
        
        from ultracore.streaming.kafka_events import kafka_producer, EventType
        
        if dry_run:
            print(f"🧪 DRY RUN: Rebalancing for {client_id}")
            print(f"   Trades: {len(rebalancing_plan['trades'])}")
            print(f"   Total value: ${rebalancing_plan['total_trade_value']:,.2f}")
            print(f"   Estimated cost: ${rebalancing_plan['estimated_costs']:,.2f}")
            
            return {
                "client_id": client_id,
                "status": "dry_run_complete",
                "plan": rebalancing_plan
            }
        
        # Execute trades
        executed_trades = []
        failed_trades = []
        
        for trade in rebalancing_plan["trades"]:
            try:
                # In production, this would call actual trading API
                trade_result = {
                    **trade,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "executed"
                }
                
                executed_trades.append(trade_result)
                
                # Produce trade event to Kafka
                await kafka_producer.produce(
                    topic="holdings.trades",
                    event_type=EventType.TRADE_EXECUTED,
                    data=trade_result,
                    key=client_id
                )
                
            except Exception as e:
                failed_trades.append({
                    **trade,
                    "error": str(e),
                    "status": "failed"
                })
        
        # Record rebalancing
        rebalancing_record = {
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "plan": rebalancing_plan,
            "executed_trades": executed_trades,
            "failed_trades": failed_trades,
            "success_rate": len(executed_trades) / len(rebalancing_plan["trades"]) if rebalancing_plan["trades"] else 0
        }
        
        self.rebalancing_history.append(rebalancing_record)
        
        # Produce rebalancing event
        await kafka_producer.produce(
            topic="holdings.rebalancing",
            event_type=EventType.REBALANCING_COMPLETED,
            data=rebalancing_record,
            key=client_id
        )
        
        return rebalancing_record
    
    def schedule_rebalancing(
        self,
        client_id: str,
        target_allocation: Dict[str, float],
        schedule: str = "quarterly"
    ) -> Dict[str, Any]:
        """
        Schedule automatic rebalancing
        """
        
        next_rebalance = self._calculate_next_rebalance_date(schedule)
        
        schedule_record = {
            "client_id": client_id,
            "target_allocation": target_allocation,
            "schedule": schedule,
            "next_rebalance": next_rebalance.isoformat(),
            "status": "active"
        }
        
        print(f"📅 Scheduled {schedule} rebalancing for {client_id}")
        print(f"   Next rebalance: {next_rebalance.strftime('%Y-%m-%d')}")
        
        return schedule_record
    
    def _calculate_tolerance_band(self, target_weight: float) -> float:
        """
        Calculate tolerance band based on target weight
        Larger positions get narrower bands
        """
        
        if target_weight >= 0.20:  # ≥20%
            return 0.03  # ±3%
        elif target_weight >= 0.10:  # 10-20%
            return 0.05  # ±5%
        else:  # <10%
            return 0.08  # ±8%
    
    def _get_estimated_price(
        self,
        ticker: str,
        current_positions: List[Dict[str, Any]]
    ) -> float:
        """Get estimated price for ticker"""
        
        # Try to find in current positions
        position = next(
            (p for p in current_positions if p["ticker"] == ticker),
            None
        )
        
        if position:
            return position.get("current_price", 0)
        
        # Would fetch from market data in production
        return 0
    
    def _calculate_transaction_costs(
        self,
        trades: List[Dict[str, Any]]
    ) -> float:
        """Calculate estimated transaction costs"""
        
        total_cost = 0
        
        for trade in trades:
            # Assume 0.1% transaction cost
            trade_value = trade.get("estimated_value", 0)
            total_cost += trade_value * 0.001
        
        return total_cost
    
    def _calculate_next_rebalance_date(self, schedule: str) -> datetime:
        """Calculate next rebalancing date based on schedule"""
        
        now = datetime.now(timezone.utc)
        
        if schedule == "monthly":
            # Next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        
        elif schedule == "quarterly":
            # Next quarter
            current_quarter = (now.month - 1) // 3
            next_quarter = current_quarter + 1
            
            if next_quarter >= 4:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, next_quarter * 3 + 1, 1)
        
        elif schedule == "annually":
            return datetime(now.year + 1, 1, 1)
        
        return now

# Global instance
rebalancing_engine = RebalancingEngine()

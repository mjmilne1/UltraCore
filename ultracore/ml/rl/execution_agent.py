"""
Reinforcement Learning for Optimal Trade Execution
Learns to minimize market impact and execution costs
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from enum import Enum

class ExecutionAction(str, Enum):
    EXECUTE_ALL = "execute_all"           # Execute entire order immediately
    EXECUTE_HALF = "execute_half"         # Execute 50% now
    EXECUTE_QUARTER = "execute_quarter"   # Execute 25% now
    EXECUTE_TENTH = "execute_tenth"       # Execute 10% now
    WAIT_SHORT = "wait_short"             # Wait 1 minute
    WAIT_MEDIUM = "wait_medium"           # Wait 5 minutes
    WAIT_LONG = "wait_long"               # Wait 15 minutes
    CANCEL = "cancel"                     # Cancel remaining order

class ExecutionRLAgent:
    """
    RL Agent for optimal trade execution
    
    Learns to:
    - Minimize market impact
    - Reduce execution costs
    - Adapt to market conditions
    - Balance urgency vs cost
    """
    
    def __init__(self):
        self.learning_rate = 0.001
        self.gamma = 0.95
        self.epsilon = 0.15  # Higher exploration for execution
        
        # Q-table for execution decisions
        self.q_table = {}
        
        # Experience replay
        self.memory = []
        self.memory_size = 5000
        
        # Training history
        self.episodes = []
        self.execution_history = []
    
    def get_state(
        self,
        order: Dict[str, Any],
        market: Dict[str, Any],
        execution_progress: Dict[str, Any]
    ) -> str:
        """
        Create state representation for execution
        
        State includes:
        - Remaining quantity
        - Market volatility
        - Spread
        - Volume
        - Time urgency
        """
        
        features = []
        
        # 1. Execution progress (0-100%)
        remaining_pct = execution_progress.get("remaining_quantity", 100) / 100
        features.append(round(remaining_pct, 1))
        
        # 2. Market volatility (bucketed)
        volatility = market.get("volatility", 0.02)
        vol_bucket = int(volatility * 100) // 10  # 0-9
        features.append(vol_bucket)
        
        # 3. Spread (basis points)
        spread = market.get("spread", 0.001)
        spread_bp = int(spread * 10000)
        features.append(min(spread_bp, 50))  # Cap at 50bp
        
        # 4. Volume percentage (order size vs avg volume)
        order_qty = order.get("quantity", 0)
        avg_volume = market.get("avg_volume", 1000000)
        volume_pct = (order_qty / avg_volume) * 100 if avg_volume > 0 else 0
        features.append(round(volume_pct, 1))
        
        # 5. Time urgency (0-10)
        time_in_force = order.get("time_in_force", "day")
        urgency_map = {"ioc": 10, "fok": 10, "day": 5, "gtc": 2}
        urgency = urgency_map.get(time_in_force, 5)
        features.append(urgency)
        
        return "-".join(str(f) for f in features)
    
    def select_action(
        self,
        state: str,
        order: Dict[str, Any],
        market: Dict[str, Any]
    ) -> ExecutionAction:
        """
        Select execution action using epsilon-greedy
        """
        
        # Exploration
        if np.random.random() < self.epsilon:
            return np.random.choice(list(ExecutionAction))
        
        # Exploitation
        if state in self.q_table:
            q_values = self.q_table[state]
            best_action = max(q_values, key=q_values.get)
            return ExecutionAction(best_action)
        
        # Default to moderate execution
        return ExecutionAction.EXECUTE_HALF
    
    def calculate_reward(
        self,
        action: ExecutionAction,
        execution_result: Dict[str, Any],
        market_before: Dict[str, Any],
        market_after: Dict[str, Any]
    ) -> float:
        """
        Calculate reward for execution action
        
        Reward components:
        - Execution price (vs benchmark)
        - Market impact
        - Speed of execution
        - Completion percentage
        """
        
        # 1. Price improvement/slippage
        executed_price = execution_result.get("avg_price", 0)
        benchmark_price = market_before.get("mid_price", executed_price)
        
        side = execution_result.get("side", "buy")
        if side == "buy":
            price_diff = benchmark_price - executed_price  # Positive = good
        else:
            price_diff = executed_price - benchmark_price  # Positive = good
        
        price_reward = price_diff * execution_result.get("quantity", 0)
        
        # 2. Market impact penalty
        price_movement = abs(market_after.get("mid_price", 0) - market_before.get("mid_price", 0))
        impact_penalty = -price_movement * execution_result.get("quantity", 0) * 0.5
        
        # 3. Speed bonus (for completing execution)
        completion_pct = execution_result.get("filled_quantity", 0) / execution_result.get("total_quantity", 1)
        speed_bonus = completion_pct * 10
        
        # 4. Spread cost
        spread = market_before.get("spread", 0.001)
        spread_cost = -spread * executed_price * execution_result.get("quantity", 0)
        
        # Total reward
        reward = (
            price_reward * 1000 +      # Scale up price improvement
            impact_penalty * 1000 +    # Penalize market impact
            speed_bonus +              # Bonus for completion
            spread_cost * 1000         # Penalize spread crossing
        )
        
        return round(reward, 4)
    
    def update_q_value(
        self,
        state: str,
        action: ExecutionAction,
        reward: float,
        next_state: str
    ):
        """Update Q-value using Q-learning"""
        
        # Initialize if needed
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in ExecutionAction}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in ExecutionAction}
        
        # Q-learning update
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        new_q = current_q + self.learning_rate * (
            reward + self.gamma * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def train_execution(
        self,
        order: Dict[str, Any],
        market_scenarios: List[Dict[str, Any]],
        steps: int = 50
    ) -> Dict[str, Any]:
        """
        Train agent on execution scenarios
        """
        
        total_reward = 0
        actions_taken = []
        
        remaining_quantity = order.get("quantity", 0)
        total_quantity = remaining_quantity
        
        for step in range(min(steps, len(market_scenarios))):
            if remaining_quantity <= 0:
                break
            
            market = market_scenarios[step]
            
            # Get state
            execution_progress = {
                "remaining_quantity": (remaining_quantity / total_quantity) * 100,
                "filled_quantity": total_quantity - remaining_quantity
            }
            
            state = self.get_state(order, market, execution_progress)
            
            # Select action
            action = self.select_action(state, order, market)
            
            # Execute action (simulate)
            execution_result = self._simulate_execution(
                action,
                remaining_quantity,
                market
            )
            
            executed_qty = execution_result.get("quantity", 0)
            remaining_quantity -= executed_qty
            
            # Calculate reward
            market_after = market_scenarios[min(step + 1, len(market_scenarios) - 1)]
            
            reward = self.calculate_reward(
                action,
                {
                    **execution_result,
                    "side": order.get("side"),
                    "total_quantity": total_quantity,
                    "filled_quantity": total_quantity - remaining_quantity
                },
                market,
                market_after
            )
            
            total_reward += reward
            
            # Get next state
            next_execution_progress = {
                "remaining_quantity": (remaining_quantity / total_quantity) * 100,
                "filled_quantity": total_quantity - remaining_quantity
            }
            
            next_state = self.get_state(order, market_after, next_execution_progress)
            
            # Update Q-value
            self.update_q_value(state, action, reward, next_state)
            
            actions_taken.append({
                "step": step,
                "action": action,
                "quantity": executed_qty,
                "reward": reward
            })
        
        episode_result = {
            "episode": len(self.episodes) + 1,
            "total_reward": total_reward,
            "actions_taken": actions_taken,
            "fill_rate": (total_quantity - remaining_quantity) / total_quantity,
            "q_table_size": len(self.q_table)
        }
        
        self.episodes.append(episode_result)
        
        return episode_result
    
    def get_optimal_execution_plan(
        self,
        order: Dict[str, Any],
        market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get optimal execution plan (exploitation only)
        """
        
        plan = []
        remaining_quantity = order.get("quantity", 0)
        total_quantity = remaining_quantity
        
        max_steps = 20
        step = 0
        
        while remaining_quantity > 0 and step < max_steps:
            execution_progress = {
                "remaining_quantity": (remaining_quantity / total_quantity) * 100,
                "filled_quantity": total_quantity - remaining_quantity
            }
            
            state = self.get_state(order, market, execution_progress)
            
            # Get best action from Q-table
            if state in self.q_table:
                q_values = self.q_table[state]
                best_action = max(q_values, key=q_values.get)
                confidence = q_values[best_action]
            else:
                best_action = ExecutionAction.EXECUTE_HALF
                confidence = 0.5
            
            # Calculate execution quantity
            exec_qty = self._get_execution_quantity(best_action, remaining_quantity)
            
            plan.append({
                "step": step + 1,
                "action": best_action,
                "quantity": exec_qty,
                "confidence": confidence,
                "remaining": remaining_quantity - exec_qty
            })
            
            remaining_quantity -= exec_qty
            step += 1
        
        return {
            "order_id": order.get("order_id"),
            "total_quantity": total_quantity,
            "execution_steps": len(plan),
            "plan": plan,
            "estimated_duration": self._estimate_duration(plan)
        }
    
    def _simulate_execution(
        self,
        action: ExecutionAction,
        remaining_quantity: float,
        market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate execution of action"""
        
        exec_qty = self._get_execution_quantity(action, remaining_quantity)
        
        # Simulate price (with some randomness)
        base_price = market.get("mid_price", 100)
        spread = market.get("spread", 0.001)
        
        # Add noise and market impact
        impact = (exec_qty / market.get("avg_volume", 1000000)) * base_price * 0.1
        noise = np.random.normal(0, spread * base_price)
        
        executed_price = base_price + impact + noise
        
        return {
            "quantity": exec_qty,
            "avg_price": executed_price,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_execution_quantity(
        self,
        action: ExecutionAction,
        remaining: float
    ) -> float:
        """Get quantity to execute for action"""
        
        if action == ExecutionAction.EXECUTE_ALL:
            return remaining
        elif action == ExecutionAction.EXECUTE_HALF:
            return remaining * 0.5
        elif action == ExecutionAction.EXECUTE_QUARTER:
            return remaining * 0.25
        elif action == ExecutionAction.EXECUTE_TENTH:
            return remaining * 0.1
        else:  # Wait or cancel
            return 0
    
    def _estimate_duration(self, plan: List[Dict[str, Any]]) -> str:
        """Estimate execution duration"""
        
        total_minutes = 0
        
        for step in plan:
            action = step["action"]
            
            if action in [ExecutionAction.WAIT_SHORT]:
                total_minutes += 1
            elif action in [ExecutionAction.WAIT_MEDIUM]:
                total_minutes += 5
            elif action in [ExecutionAction.WAIT_LONG]:
                total_minutes += 15
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            mins = total_minutes % 60
            return f"{hours}h {mins}m"

# Global instance
execution_rl_agent = ExecutionRLAgent()

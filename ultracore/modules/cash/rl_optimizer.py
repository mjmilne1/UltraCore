"""
Reinforcement Learning for Cash Management
Optimize liquidity, interest earnings, and cash allocation
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import random

class CashOptimizationAction(str, Enum):
    """RL agent actions"""
    MAINTAIN_CURRENT = "maintain_current"
    TRANSFER_TO_INTEREST = "transfer_to_interest"
    TRANSFER_TO_OPERATING = "transfer_to_operating"
    REDUCE_RESERVES = "reduce_reserves"
    INCREASE_RESERVES = "increase_reserves"

class CashOptimizationRL:
    """
    Reinforcement Learning for Cash Optimization
    
    Learns to:
    - Optimize cash allocation across accounts
    - Maximize interest earnings
    - Maintain adequate liquidity
    - Minimize opportunity cost
    - Balance risk and return
    """
    
    def __init__(self):
        # Q-table: state -> action -> Q-value
        self.q_table = {}
        
        # RL hyperparameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.exploration_rate = 0.2
        
        # Performance tracking
        self.episodes = []
        self.rewards_history = []
        
    def get_state(
        self,
        operating_balance: float,
        interest_bearing_balance: float,
        reserved_balance: float,
        expected_outflows_24h: float,
        interest_rate: float
    ) -> str:
        """
        Get current state representation
        
        State includes:
        - Operating balance level (low/medium/high)
        - Interest-bearing balance level
        - Reserved balance level
        - Expected outflows
        - Interest rate tier
        """
        
        total_balance = operating_balance + interest_bearing_balance + reserved_balance
        
        # Categorize operating balance
        if operating_balance < expected_outflows_24h * 1.5:
            op_level = "low"
        elif operating_balance < expected_outflows_24h * 3:
            op_level = "medium"
        else:
            op_level = "high"
        
        # Categorize interest-bearing balance
        if interest_bearing_balance < total_balance * 0.3:
            ib_level = "low"
        elif interest_bearing_balance < total_balance * 0.6:
            ib_level = "medium"
        else:
            ib_level = "high"
        
        # Categorize interest rate
        if interest_rate < 2.0:
            rate_tier = "low"
        elif interest_rate < 4.0:
            rate_tier = "medium"
        else:
            rate_tier = "high"
        
        state = f"{op_level}_{ib_level}_{rate_tier}"
        
        return state
    
    def choose_action(
        self,
        state: str,
        available_actions: List[CashOptimizationAction]
    ) -> CashOptimizationAction:
        """
        Choose action using epsilon-greedy policy
        """
        
        # Exploration vs exploitation
        if random.random() < self.exploration_rate:
            # Explore: random action
            return random.choice(available_actions)
        else:
            # Exploit: best known action
            if state not in self.q_table:
                self.q_table[state] = {action: 0.0 for action in available_actions}
            
            # Get Q-values for available actions
            q_values = {
                action: self.q_table[state].get(action, 0.0)
                for action in available_actions
            }
            
            # Choose action with highest Q-value
            best_action = max(q_values, key=q_values.get)
            
            return best_action
    
    def calculate_reward(
        self,
        action: CashOptimizationAction,
        result: Dict[str, Any]
    ) -> float:
        """
        Calculate reward for action
        
        Reward factors:
        + Interest earned
        + Adequate liquidity maintained
        - Insufficient liquidity penalty
        - Opportunity cost of idle cash
        """
        
        reward = 0.0
        
        # Interest earnings (positive reward)
        interest_earned = result.get("interest_earned", 0)
        reward += interest_earned * 100  # Scale up
        
        # Liquidity maintenance
        liquidity_ratio = result.get("liquidity_ratio", 0)
        
        if liquidity_ratio < 1.0:
            # Penalty for insufficient liquidity
            reward -= 50 * (1.0 - liquidity_ratio)
        elif liquidity_ratio > 3.0:
            # Penalty for excess idle cash
            reward -= 10 * (liquidity_ratio - 3.0)
        else:
            # Reward for optimal liquidity
            reward += 20
        
        # Transaction costs (if any)
        transaction_cost = result.get("transaction_cost", 0)
        reward -= transaction_cost * 10
        
        # Opportunity cost
        idle_cash = result.get("idle_cash", 0)
        opportunity_cost = idle_cash * 0.0001  # Small penalty per dollar idle
        reward -= opportunity_cost
        
        return reward
    
    def update_q_value(
        self,
        state: str,
        action: CashOptimizationAction,
        reward: float,
        next_state: str,
        available_next_actions: List[CashOptimizationAction]
    ):
        """
        Update Q-value using Q-learning algorithm
        
        Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        """
        
        # Initialize Q-table entries if needed
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in CashOptimizationAction}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in available_next_actions}
        
        # Current Q-value
        current_q = self.q_table[state][action]
        
        # Max Q-value for next state
        max_next_q = max(
            self.q_table[next_state].get(a, 0.0)
            for a in available_next_actions
        )
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def optimize_cash_allocation(
        self,
        account_balances: Dict[str, float],
        expected_outflows: float,
        interest_rate: float
    ) -> Dict[str, Any]:
        """
        Recommend optimal cash allocation
        """
        
        # Get current state
        state = self.get_state(
            operating_balance=account_balances.get("operating", 0),
            interest_bearing_balance=account_balances.get("interest_bearing", 0),
            reserved_balance=account_balances.get("reserved", 0),
            expected_outflows_24h=expected_outflows,
            interest_rate=interest_rate
        )
        
        # Available actions
        available_actions = list(CashOptimizationAction)
        
        # Choose action
        action = self.choose_action(state, available_actions)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            action,
            account_balances,
            expected_outflows,
            interest_rate
        )
        
        return {
            "state": state,
            "recommended_action": action,
            "recommendation": recommendation,
            "confidence": self._get_action_confidence(state, action),
            "reasoning": self._explain_recommendation(action, account_balances, expected_outflows)
        }
    
    def _generate_recommendation(
        self,
        action: CashOptimizationAction,
        balances: Dict[str, float],
        expected_outflows: float,
        interest_rate: float
    ) -> Dict[str, Any]:
        """Generate specific recommendation based on action"""
        
        operating = balances.get("operating", 0)
        interest_bearing = balances.get("interest_bearing", 0)
        
        if action == CashOptimizationAction.TRANSFER_TO_INTEREST:
            # Transfer excess operating cash to interest-bearing
            min_operating = expected_outflows * 2  # Keep 2x expected outflows
            transferable = max(0, operating - min_operating)
            
            return {
                "action": "Transfer to interest-bearing account",
                "from_account": "operating",
                "to_account": "interest_bearing",
                "amount": transferable,
                "expected_benefit": f"Earn ${transferable * interest_rate / 100 / 365:.2f} per day"
            }
        
        elif action == CashOptimizationAction.TRANSFER_TO_OPERATING:
            # Transfer from interest-bearing to operating
            needed = max(0, (expected_outflows * 2) - operating)
            transferable = min(needed, interest_bearing)
            
            return {
                "action": "Transfer to operating account",
                "from_account": "interest_bearing",
                "to_account": "operating",
                "amount": transferable,
                "expected_benefit": "Ensure adequate liquidity"
            }
        
        elif action == CashOptimizationAction.MAINTAIN_CURRENT:
            return {
                "action": "Maintain current allocation",
                "reason": "Current allocation is optimal"
            }
        
        else:
            return {
                "action": action.value,
                "details": "Adjust reserves as needed"
            }
    
    def _get_action_confidence(self, state: str, action: CashOptimizationAction) -> float:
        """Get confidence in recommended action"""
        
        if state not in self.q_table:
            return 0.5  # Low confidence if never seen
        
        q_value = self.q_table[state].get(action, 0.0)
        
        # Normalize Q-value to confidence score (0-1)
        # Higher Q-value = higher confidence
        confidence = min(1.0, max(0.0, (q_value + 50) / 100))
        
        return confidence
    
    def _explain_recommendation(
        self,
        action: CashOptimizationAction,
        balances: Dict[str, float],
        expected_outflows: float
    ) -> str:
        """Explain recommendation in natural language"""
        
        operating = balances.get("operating", 0)
        liquidity_ratio = operating / expected_outflows if expected_outflows > 0 else 0
        
        if action == CashOptimizationAction.TRANSFER_TO_INTEREST:
            return f"Operating balance (${operating:,.2f}) exceeds requirements ({liquidity_ratio:.1f}x expected outflows). Transfer excess to interest-bearing account to maximize returns while maintaining adequate liquidity."
        
        elif action == CashOptimizationAction.TRANSFER_TO_OPERATING:
            return f"Operating balance (${operating:,.2f}) is below optimal level ({liquidity_ratio:.1f}x expected outflows). Transfer from interest-bearing account to ensure sufficient liquidity for upcoming obligations."
        
        elif action == CashOptimizationAction.MAINTAIN_CURRENT:
            return f"Current allocation is optimal with {liquidity_ratio:.1f}x liquidity coverage. No changes recommended at this time."
        
        else:
            return f"Consider adjusting cash allocation based on current market conditions and liquidity needs."
    
    def train_episode(
        self,
        initial_balances: Dict[str, float],
        transaction_sequence: List[Dict[str, Any]],
        interest_rate: float
    ):
        """Train agent on historical episode"""
        
        balances = initial_balances.copy()
        total_reward = 0.0
        
        for i, transaction in enumerate(transaction_sequence):
            # Get current state
            state = self.get_state(
                operating_balance=balances.get("operating", 0),
                interest_bearing_balance=balances.get("interest_bearing", 0),
                reserved_balance=balances.get("reserved", 0),
                expected_outflows_24h=transaction.get("expected_outflows", 0),
                interest_rate=interest_rate
            )
            
            # Choose action
            available_actions = list(CashOptimizationAction)
            action = self.choose_action(state, available_actions)
            
            # Simulate action result
            result = self._simulate_action(action, balances, transaction)
            
            # Calculate reward
            reward = self.calculate_reward(action, result)
            total_reward += reward
            
            # Update balances
            balances = result.get("new_balances", balances)
            
            # Get next state
            next_transaction = transaction_sequence[i+1] if i+1 < len(transaction_sequence) else transaction
            next_state = self.get_state(
                operating_balance=balances.get("operating", 0),
                interest_bearing_balance=balances.get("interest_bearing", 0),
                reserved_balance=balances.get("reserved", 0),
                expected_outflows_24h=next_transaction.get("expected_outflows", 0),
                interest_rate=interest_rate
            )
            
            # Update Q-value
            self.update_q_value(state, action, reward, next_state, available_actions)
        
        # Record episode
        self.episodes.append({
            "episode_id": len(self.episodes) + 1,
            "total_reward": total_reward,
            "final_balances": balances,
            "trained_at": datetime.now(timezone.utc).isoformat()
        })
        
        self.rewards_history.append(total_reward)
    
    def _simulate_action(
        self,
        action: CashOptimizationAction,
        balances: Dict[str, float],
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate action and return result"""
        
        new_balances = balances.copy()
        interest_earned = 0.0
        transaction_cost = 0.0
        
        # Simulate action effects
        if action == CashOptimizationAction.TRANSFER_TO_INTEREST:
            transfer_amount = min(10000, balances.get("operating", 0) * 0.2)
            new_balances["operating"] = balances.get("operating", 0) - transfer_amount
            new_balances["interest_bearing"] = balances.get("interest_bearing", 0) + transfer_amount
            transaction_cost = 0  # Internal transfer - no cost
        
        # Calculate metrics
        expected_outflows = transaction.get("expected_outflows", 0)
        liquidity_ratio = new_balances.get("operating", 0) / expected_outflows if expected_outflows > 0 else 0
        
        # Calculate interest
        interest_rate = transaction.get("interest_rate", 0)
        interest_earned = new_balances.get("interest_bearing", 0) * interest_rate / 100 / 365
        
        # Calculate idle cash
        idle_cash = max(0, new_balances.get("operating", 0) - (expected_outflows * 2))
        
        return {
            "new_balances": new_balances,
            "interest_earned": interest_earned,
            "liquidity_ratio": liquidity_ratio,
            "transaction_cost": transaction_cost,
            "idle_cash": idle_cash
        }
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        
        if not self.rewards_history:
            return {
                "episodes_completed": 0,
                "average_reward": 0,
                "improvement": 0
            }
        
        recent_rewards = self.rewards_history[-10:] if len(self.rewards_history) >= 10 else self.rewards_history
        early_rewards = self.rewards_history[:10] if len(self.rewards_history) >= 10 else self.rewards_history
        
        avg_recent = sum(recent_rewards) / len(recent_rewards)
        avg_early = sum(early_rewards) / len(early_rewards)
        
        improvement = ((avg_recent - avg_early) / abs(avg_early) * 100) if avg_early != 0 else 0
        
        return {
            "episodes_completed": len(self.episodes),
            "total_states_learned": len(self.q_table),
            "average_reward": sum(self.rewards_history) / len(self.rewards_history),
            "recent_average_reward": avg_recent,
            "improvement_percentage": improvement,
            "exploration_rate": self.exploration_rate
        }

# Global RL optimizer
cash_optimizer_rl = CashOptimizationRL()

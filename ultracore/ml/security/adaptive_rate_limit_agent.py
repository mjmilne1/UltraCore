"""
Adaptive Rate Limiting RL Agent

Reinforcement Learning agent that dynamically adjusts rate limits based on traffic patterns.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pickle
import os


@dataclass
class TrafficState:
    """State representation for rate limiting decisions"""
    current_request_rate: float  # Requests per second
    user_reputation: float  # 0-1
    endpoint_sensitivity: int  # 1-5
    recent_errors: int
    time_of_day: int  # 0-23
    is_authenticated: bool
    burst_detected: bool
    
    def to_tuple(self) -> Tuple:
        """Convert to hashable state tuple"""
        return (
            int(self.current_request_rate // 10),  # Discretize to buckets of 10
            int(self.user_reputation * 10),
            self.endpoint_sensitivity,
            min(self.recent_errors, 10),
            self.time_of_day // 6,  # 4 time blocks
            int(self.is_authenticated),
            int(self.burst_detected)
        )


@dataclass
class RateLimitAction:
    """Rate limiting actions"""
    ALLOW_NORMAL = 0
    ALLOW_REDUCED = 1
    THROTTLE_50 = 2
    THROTTLE_75 = 3
    BLOCK_TEMPORARY = 4
    BLOCK_PERMANENT = 5
    
    @staticmethod
    def get_all_actions() -> List[int]:
        return [0, 1, 2, 3, 4, 5]
    
    @staticmethod
    def get_action_name(action: int) -> str:
        names = {
            0: "allow_normal",
            1: "allow_reduced",
            2: "throttle_50",
            3: "throttle_75",
            4: "block_temporary",
            5: "block_permanent"
        }
        return names.get(action, "unknown")
    
    @staticmethod
    def get_rate_multiplier(action: int) -> float:
        """Get rate limit multiplier for action"""
        multipliers = {
            0: 1.0,    # Normal
            1: 0.75,   # Reduced
            2: 0.5,    # 50% throttle
            3: 0.25,   # 75% throttle
            4: 0.0,    # Temporary block
            5: 0.0     # Permanent block
        }
        return multipliers.get(action, 1.0)


class AdaptiveRateLimitAgent:
    """
    Q-Learning agent for adaptive rate limiting.
    
    Learns to:
    - Prevent DDoS attacks
    - Allow legitimate bursts
    - Minimize false positives
    - Adapt to traffic patterns
    
    Reward structure:
    - Allow legitimate traffic: +10
    - Block attack: +20
    - False positive (block legitimate): -30
    - False negative (allow attack): -50
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/tmp/adaptive_rate_limit.pkl"
        
        # Q-learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.15
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        # Q-table
        self.q_table: Dict[Tuple, np.ndarray] = {}
        
        # Performance tracking
        self.total_decisions = 0
        self.attacks_blocked = 0
        self.false_positives = 0
        self.false_negatives = 0
        
        if os.path.exists(self.model_path):
            self.load()
    
    def get_q_values(self, state: TrafficState) -> np.ndarray:
        """Get Q-values for all actions"""
        state_tuple = state.to_tuple()
        
        if state_tuple not in self.q_table:
            self.q_table[state_tuple] = np.zeros(len(RateLimitAction.get_all_actions()))
        
        return self.q_table[state_tuple]
    
    def select_action(self, state: TrafficState, training: bool = False) -> int:
        """Select action using epsilon-greedy policy"""
        if training and np.random.random() < self.epsilon:
            return np.random.choice(RateLimitAction.get_all_actions())
        else:
            q_values = self.get_q_values(state)
            return int(np.argmax(q_values))
    
    def update(self, state: TrafficState, action: int, reward: float, next_state: TrafficState):
        """Update Q-values"""
        state_tuple = state.to_tuple()
        
        current_q = self.get_q_values(state)[action]
        next_q_values = self.get_q_values(next_state)
        max_next_q = np.max(next_q_values)
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_tuple][action] = new_q
        
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def decide_rate_limit(
        self,
        current_request_rate: float,
        user_reputation: float,
        endpoint_sensitivity: int,
        recent_errors: int,
        time_of_day: int,
        is_authenticated: bool,
        burst_detected: bool,
        training: bool = False
    ) -> Dict:
        """
        Make rate limiting decision.
        
        Returns:
            Decision dict with action, rate multiplier, and reasoning
        """
        state = TrafficState(
            current_request_rate=current_request_rate,
            user_reputation=user_reputation,
            endpoint_sensitivity=endpoint_sensitivity,
            recent_errors=recent_errors,
            time_of_day=time_of_day,
            is_authenticated=is_authenticated,
            burst_detected=burst_detected
        )
        
        action = self.select_action(state, training=training)
        q_values = self.get_q_values(state)
        confidence = float(q_values[action] / (np.max(q_values) + 1e-6))
        
        self.total_decisions += 1
        
        return {
            "action": RateLimitAction.get_action_name(action),
            "action_code": action,
            "rate_multiplier": RateLimitAction.get_rate_multiplier(action),
            "confidence": confidence,
            "reasoning": self._generate_reasoning(state, action),
            "q_values": {
                RateLimitAction.get_action_name(i): float(q_values[i])
                for i in range(len(q_values))
            }
        }
    
    def provide_feedback(
        self,
        state_dict: Dict,
        action: int,
        was_attack: bool,
        was_blocked: bool
    ):
        """Provide feedback for learning"""
        state = TrafficState(
            current_request_rate=state_dict["current_request_rate"],
            user_reputation=state_dict["user_reputation"],
            endpoint_sensitivity=state_dict["endpoint_sensitivity"],
            recent_errors=state_dict["recent_errors"],
            time_of_day=state_dict["time_of_day"],
            is_authenticated=state_dict["is_authenticated"],
            burst_detected=state_dict["burst_detected"]
        )
        
        reward = self._calculate_reward(action, was_attack, was_blocked)
        
        # Update metrics
        if was_attack and was_blocked:
            self.attacks_blocked += 1
        elif not was_attack and was_blocked:
            self.false_positives += 1
        elif was_attack and not was_blocked:
            self.false_negatives += 1
        
        # Create next state
        next_state = TrafficState(
            current_request_rate=state.current_request_rate * 0.8 if was_blocked else state.current_request_rate,
            user_reputation=state.user_reputation * 0.9 if was_attack else min(state.user_reputation * 1.05, 1.0),
            endpoint_sensitivity=state.endpoint_sensitivity,
            recent_errors=state.recent_errors,
            time_of_day=state.time_of_day,
            is_authenticated=state.is_authenticated,
            burst_detected=False
        )
        
        self.update(state, action, reward, next_state)
    
    def _calculate_reward(self, action: int, was_attack: bool, was_blocked: bool) -> float:
        """Calculate reward"""
        if not was_attack and not was_blocked:
            # Correct allow
            return 10.0
        elif was_attack and was_blocked:
            # Correct block
            return 20.0
        elif not was_attack and was_blocked:
            # False positive
            return -30.0
        else:
            # False negative
            return -50.0
    
    def _generate_reasoning(self, state: TrafficState, action: int) -> str:
        """Generate reasoning for decision"""
        reasons = []
        
        if state.current_request_rate > 100:
            reasons.append(f"high request rate ({state.current_request_rate:.1f} req/s)")
        if state.user_reputation < 0.5:
            reasons.append("low user reputation")
        if state.endpoint_sensitivity >= 4:
            reasons.append("sensitive endpoint")
        if state.recent_errors > 5:
            reasons.append(f"{state.recent_errors} recent errors")
        if state.burst_detected:
            reasons.append("burst detected")
        if not state.is_authenticated:
            reasons.append("unauthenticated")
        
        action_name = RateLimitAction.get_action_name(action)
        
        if reasons:
            return f"Action '{action_name}' due to: {', '.join(reasons)}"
        else:
            return f"Action '{action_name}' - normal traffic pattern"
    
    def get_metrics(self) -> Dict:
        """Get agent metrics"""
        if self.total_decisions == 0:
            return {
                "total_decisions": 0,
                "attacks_blocked": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "exploration_rate": self.epsilon
            }
        
        return {
            "total_decisions": self.total_decisions,
            "attacks_blocked": self.attacks_blocked,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "block_rate": self.attacks_blocked / self.total_decisions,
            "false_positive_rate": self.false_positives / self.total_decisions,
            "false_negative_rate": self.false_negatives / self.total_decisions,
            "exploration_rate": self.epsilon,
            "states_learned": len(self.q_table)
        }
    
    def save(self):
        """Save agent"""
        agent_data = {
            "q_table": self.q_table,
            "epsilon": self.epsilon,
            "total_decisions": self.total_decisions,
            "attacks_blocked": self.attacks_blocked,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(agent_data, f)
    
    def load(self):
        """Load agent"""
        try:
            with open(self.model_path, 'rb') as f:
                agent_data = pickle.load(f)
            
            self.q_table = agent_data["q_table"]
            self.epsilon = agent_data["epsilon"]
            self.total_decisions = agent_data.get("total_decisions", 0)
            self.attacks_blocked = agent_data.get("attacks_blocked", 0)
            self.false_positives = agent_data.get("false_positives", 0)
            self.false_negatives = agent_data.get("false_negatives", 0)
        except Exception as e:
            print(f"Error loading agent: {e}")

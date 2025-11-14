"""
Adaptive Access Control RL Agent

Reinforcement Learning agent that learns optimal access control policies.
Uses Q-learning to adapt security policies based on threat landscape.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pickle
import os


@dataclass
class AccessState:
    """State representation for access control decisions"""
    user_risk_score: float  # 0-1
    resource_sensitivity: int  # 1-5
    time_of_day: int  # 0-23
    recent_violations: int
    authentication_strength: int  # 1-3 (password, 2FA, biometric)
    location_trust: float  # 0-1
    device_trust: float  # 0-1
    
    def to_tuple(self) -> Tuple:
        """Convert to hashable state tuple for Q-table"""
        return (
            int(self.user_risk_score * 10),  # Discretize to 0-10
            self.resource_sensitivity,
            self.time_of_day // 6,  # 4 time blocks
            min(self.recent_violations, 5),
            self.authentication_strength,
            int(self.location_trust * 10),
            int(self.device_trust * 10)
        )


@dataclass
class AccessAction:
    """Possible access control actions"""
    ALLOW = 0
    ALLOW_WITH_MFA = 1
    ALLOW_WITH_MONITORING = 2
    DENY_WITH_ALERT = 3
    DENY_SILENT = 4
    
    @staticmethod
    def get_all_actions() -> List[int]:
        return [0, 1, 2, 3, 4]
    
    @staticmethod
    def get_action_name(action: int) -> str:
        names = {
            0: "allow",
            1: "allow_with_mfa",
            2: "allow_with_monitoring",
            3: "deny_with_alert",
            4: "deny_silent"
        }
        return names.get(action, "unknown")


class AdaptiveAccessControlAgent:
    """
    Q-Learning agent for adaptive access control.
    
    Learns to:
    - Balance security and usability
    - Adapt to changing threat patterns
    - Minimize false positives while maintaining security
    
    Reward structure:
    - Correct allow: +10
    - Correct deny: +15
    - False positive (deny legitimate): -20
    - False negative (allow malicious): -50
    - MFA when needed: +5
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/tmp/adaptive_access_control.pkl"
        
        # Q-learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        # Q-table: state -> action -> Q-value
        self.q_table: Dict[Tuple, np.ndarray] = {}
        
        # Performance tracking
        self.total_decisions = 0
        self.correct_decisions = 0
        self.false_positives = 0
        self.false_negatives = 0
        
        if os.path.exists(self.model_path):
            self.load()
    
    def get_q_values(self, state: AccessState) -> np.ndarray:
        """Get Q-values for all actions in given state"""
        state_tuple = state.to_tuple()
        
        if state_tuple not in self.q_table:
            # Initialize with optimistic values
            self.q_table[state_tuple] = np.zeros(len(AccessAction.get_all_actions()))
        
        return self.q_table[state_tuple]
    
    def select_action(self, state: AccessState, training: bool = False) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current access state
            training: If True, use exploration; if False, use pure exploitation
        """
        if training and np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.choice(AccessAction.get_all_actions())
        else:
            # Exploit: best action
            q_values = self.get_q_values(state)
            return int(np.argmax(q_values))
    
    def update(self, state: AccessState, action: int, reward: float, next_state: AccessState):
        """
        Update Q-values using Q-learning update rule.
        
        Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        """
        state_tuple = state.to_tuple()
        next_state_tuple = next_state.to_tuple()
        
        # Get current Q-value
        current_q = self.get_q_values(state)[action]
        
        # Get max Q-value for next state
        next_q_values = self.get_q_values(next_state)
        max_next_q = np.max(next_q_values)
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        
        # Update Q-table
        self.q_table[state_tuple][action] = new_q
        
        # Decay exploration rate
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def decide_access(
        self,
        user_risk_score: float,
        resource_sensitivity: int,
        time_of_day: int,
        recent_violations: int,
        authentication_strength: int,
        location_trust: float,
        device_trust: float,
        training: bool = False
    ) -> Dict:
        """
        Make access control decision.
        
        Returns:
            Decision dict with action, confidence, and reasoning
        """
        state = AccessState(
            user_risk_score=user_risk_score,
            resource_sensitivity=resource_sensitivity,
            time_of_day=time_of_day,
            recent_violations=recent_violations,
            authentication_strength=authentication_strength,
            location_trust=location_trust,
            device_trust=device_trust
        )
        
        action = self.select_action(state, training=training)
        q_values = self.get_q_values(state)
        confidence = float(q_values[action] / (np.max(q_values) + 1e-6))
        
        self.total_decisions += 1
        
        return {
            "action": AccessAction.get_action_name(action),
            "action_code": action,
            "confidence": confidence,
            "reasoning": self._generate_reasoning(state, action),
            "q_values": {
                AccessAction.get_action_name(i): float(q_values[i])
                for i in range(len(q_values))
            }
        }
    
    def provide_feedback(
        self,
        state_dict: Dict,
        action: int,
        was_legitimate: bool,
        was_allowed: bool
    ):
        """
        Provide feedback on access decision for learning.
        
        Args:
            state_dict: State information
            action: Action taken
            was_legitimate: Whether access attempt was legitimate
            was_allowed: Whether access was granted
        """
        state = AccessState(
            user_risk_score=state_dict["user_risk_score"],
            resource_sensitivity=state_dict["resource_sensitivity"],
            time_of_day=state_dict["time_of_day"],
            recent_violations=state_dict["recent_violations"],
            authentication_strength=state_dict["authentication_strength"],
            location_trust=state_dict["location_trust"],
            device_trust=state_dict["device_trust"]
        )
        
        # Calculate reward
        reward = self._calculate_reward(action, was_legitimate, was_allowed)
        
        # Update metrics
        if was_legitimate and was_allowed:
            self.correct_decisions += 1
        elif not was_legitimate and not was_allowed:
            self.correct_decisions += 1
        elif was_legitimate and not was_allowed:
            self.false_positives += 1
        else:
            self.false_negatives += 1
        
        # Create next state (simplified - in practice would come from environment)
        next_state = AccessState(
            user_risk_score=state.user_risk_score * 0.9 if was_legitimate else state.user_risk_score * 1.1,
            resource_sensitivity=state.resource_sensitivity,
            time_of_day=state.time_of_day,
            recent_violations=state.recent_violations if was_legitimate else state.recent_violations + 1,
            authentication_strength=state.authentication_strength,
            location_trust=state.location_trust,
            device_trust=state.device_trust
        )
        
        # Update Q-values
        self.update(state, action, reward, next_state)
    
    def _calculate_reward(self, action: int, was_legitimate: bool, was_allowed: bool) -> float:
        """Calculate reward for the action taken"""
        if was_legitimate and was_allowed:
            # Correct allow
            if action == AccessAction.ALLOW:
                return 10.0
            elif action == AccessAction.ALLOW_WITH_MFA:
                return 8.0  # Slightly lower for extra friction
            elif action == AccessAction.ALLOW_WITH_MONITORING:
                return 9.0
            else:
                return -20.0  # False positive
        
        elif not was_legitimate and not was_allowed:
            # Correct deny
            if action in [AccessAction.DENY_WITH_ALERT, AccessAction.DENY_SILENT]:
                return 15.0
            else:
                return -50.0  # False negative - very bad!
        
        elif was_legitimate and not was_allowed:
            # False positive
            return -20.0
        
        else:
            # False negative
            return -50.0
    
    def _generate_reasoning(self, state: AccessState, action: int) -> str:
        """Generate human-readable reasoning for decision"""
        reasons = []
        
        if state.user_risk_score > 0.7:
            reasons.append("high user risk score")
        if state.resource_sensitivity >= 4:
            reasons.append("highly sensitive resource")
        if state.recent_violations > 0:
            reasons.append(f"{state.recent_violations} recent violations")
        if state.authentication_strength < 2:
            reasons.append("weak authentication")
        if state.location_trust < 0.5:
            reasons.append("untrusted location")
        if state.device_trust < 0.5:
            reasons.append("untrusted device")
        
        action_name = AccessAction.get_action_name(action)
        
        if reasons:
            return f"Action '{action_name}' due to: {', '.join(reasons)}"
        else:
            return f"Action '{action_name}' - normal access pattern"
    
    def get_metrics(self) -> Dict:
        """Get agent performance metrics"""
        if self.total_decisions == 0:
            return {
                "total_decisions": 0,
                "accuracy": 0.0,
                "false_positive_rate": 0.0,
                "false_negative_rate": 0.0,
                "exploration_rate": self.epsilon
            }
        
        accuracy = self.correct_decisions / self.total_decisions
        fpr = self.false_positives / self.total_decisions
        fnr = self.false_negatives / self.total_decisions
        
        return {
            "total_decisions": self.total_decisions,
            "correct_decisions": self.correct_decisions,
            "accuracy": accuracy,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "exploration_rate": self.epsilon,
            "states_learned": len(self.q_table)
        }
    
    def save(self):
        """Save agent to disk"""
        agent_data = {
            "q_table": self.q_table,
            "epsilon": self.epsilon,
            "total_decisions": self.total_decisions,
            "correct_decisions": self.correct_decisions,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(agent_data, f)
    
    def load(self):
        """Load agent from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                agent_data = pickle.load(f)
            
            self.q_table = agent_data["q_table"]
            self.epsilon = agent_data["epsilon"]
            self.total_decisions = agent_data.get("total_decisions", 0)
            self.correct_decisions = agent_data.get("correct_decisions", 0)
            self.false_positives = agent_data.get("false_positives", 0)
            self.false_negatives = agent_data.get("false_negatives", 0)
        except Exception as e:
            print(f"Error loading agent: {e}")

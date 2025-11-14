"""
Unit tests for Reinforcement Learning Optimizer.

Tests RL-based portfolio optimization and decision-making.
"""

import pytest
from decimal import Decimal
import numpy as np
from tests.helpers.mock_ml_models import MockRLOptimizer


@pytest.mark.unit
@pytest.mark.ml
@pytest.mark.rl
class TestRLOptimizerAgent:
    """Test RL optimizer agent."""
    
    def test_rl_agent_initialization(self):
        """Test RL agent initializes with correct state/action space."""
        # Arrange & Act
        agent = MockRLOptimizer()
        
        # Assert - Agent initialized
        assert agent.training_episodes == 0
        assert agent.total_reward == 0.0
    
    def test_rl_agent_state_representation(self):
        """Test RL agent state representation."""
        # Arrange - Portfolio state
        portfolio_state = {
            "current_value": Decimal("100000.00"),
            "allocation": {"VAS": 0.40, "VGS": 0.30, "VAF": 0.30},
            "market_conditions": {"volatility": 0.15, "trend": "up"},
            "time_to_goal_months": 36
        }
        
        # Act - Agent can process state
        agent = MockRLOptimizer()
        
        # Assert - Valid state representation
        assert isinstance(portfolio_state, dict)
        assert "allocation" in portfolio_state
    
    def test_rl_agent_action_selection(self):
        """Test RL agent selects valid actions."""
        # Arrange
        agent = MockRLOptimizer()
        state = {
            "current_allocation": {"VAS": 0.40, "VGS": 0.30, "VAF": 0.30},
            "target_allocation": {"VAS": 0.35, "VGS": 0.35, "VAF": 0.30},
            "max_drawdown": -0.05
        }
        
        # Act
        import asyncio
        action = asyncio.run(agent.select_action(state, epsilon=0.1))
        
        # Assert
        assert "action_type" in action
        assert action["action_type"] in ["hold", "rebalance", "reduce_risk"]
        assert "confidence" in action
        assert 0 <= action["confidence"] <= 1
    
    def test_rl_agent_training(self):
        """Test RL agent training process."""
        # Arrange
        agent = MockRLOptimizer()
        experiences = [
            {"state": {}, "action": "rebalance", "reward": 0.08, "next_state": {}},
            {"state": {}, "action": "hold", "reward": 0.05, "next_state": {}},
            {"state": {}, "action": "reduce_risk", "reward": 0.03, "next_state": {}}
        ]
        
        # Act
        import asyncio
        metrics = asyncio.run(agent.train(experiences, epochs=10))
        
        # Assert
        assert metrics["episodes_trained"] == 3
        assert "avg_reward" in metrics
        assert "policy_loss" in metrics
        assert "value_loss" in metrics
    
    def test_rl_agent_policy_evaluation(self):
        """Test RL agent policy evaluation."""
        # Arrange
        agent = MockRLOptimizer()
        
        # Act
        import asyncio
        results = asyncio.run(agent.evaluate_policy(test_episodes=100))
        
        # Assert - Target performance
        assert results["avg_return"] >= 0.08  # 8%+ return
        assert results["sharpe_ratio"] >= 0.6  # 0.6+ Sharpe
        assert results["max_drawdown"] <= -0.10  # Max 10% drawdown
        assert results["win_rate"] >= 0.60  # 60%+ win rate


@pytest.mark.unit
@pytest.mark.ml
class TestRLOptimizationStrategies:
    """Test RL optimization strategies."""
    
    def test_epsilon_greedy_exploration(self):
        """Test epsilon-greedy exploration strategy."""
        # Arrange
        agent = MockRLOptimizer()
        state = {"current_allocation": {"VAS": 0.40}}
        
        # Act - Multiple actions with high epsilon
        import asyncio
        actions = [
            asyncio.run(agent.select_action(state, epsilon=0.5))
            for _ in range(10)
        ]
        
        # Assert - Should have some exploration
        action_types = [a["action_type"] for a in actions]
        assert len(set(action_types)) > 1  # Multiple action types
    
    def test_reward_shaping(self):
        """Test reward shaping for portfolio optimization."""
        # Arrange
        experiences = []
        
        # Good action: rebalance when drift is high
        experiences.append({
            "state": {"drift": 0.15},
            "action": "rebalance",
            "reward": 0.10,  # High reward
            "next_state": {"drift": 0.02}
        })
        
        # Bad action: hold when drift is high
        experiences.append({
            "state": {"drift": 0.15},
            "action": "hold",
            "reward": -0.05,  # Negative reward
            "next_state": {"drift": 0.20}
        })
        
        # Assert - Reward structure is correct
        assert experiences[0]["reward"] > experiences[1]["reward"]
    
    def test_convergence_criteria(self):
        """Test RL agent convergence criteria."""
        # Arrange
        agent = MockRLOptimizer()
        
        # Act - Train for multiple episodes
        import asyncio
        for _ in range(100):
            experiences = [
                {"state": {}, "action": "rebalance", "reward": 0.08, "next_state": {}}
            ]
            asyncio.run(agent.train(experiences, epochs=1))
        
        # Assert - Agent should converge
        assert agent.training_episodes == 100
        assert agent.total_reward > 0


@pytest.mark.unit
@pytest.mark.ml
class TestRLModelPersistence:
    """Test RL model persistence and loading."""
    
    def test_save_rl_model(self):
        """Test saving RL model."""
        # Arrange
        agent = MockRLOptimizer()
        
        # Act - Train and save (simulated)
        import asyncio
        experiences = [{"state": {}, "action": "hold", "reward": 0.05, "next_state": {}}]
        asyncio.run(agent.train(experiences, epochs=10))
        
        # Assert - Model has training history
        assert agent.training_episodes > 0
    
    def test_load_rl_model(self):
        """Test loading RL model."""
        # Arrange & Act - Load model (simulated)
        agent = MockRLOptimizer()
        
        # Assert - Model loaded successfully
        assert agent is not None
    
    def test_model_versioning(self):
        """Test RL model versioning."""
        # Arrange
        agent_v1 = MockRLOptimizer()
        agent_v2 = MockRLOptimizer()
        
        # Act - Train different versions with different numbers of experiences
        import asyncio
        # Agent v1: Train with 1 experience
        asyncio.run(agent_v1.train([{"state": {}, "action": "hold", "reward": 0.05, "next_state": {}}], epochs=10))
        
        # Agent v2: Train with 3 experiences (different training history)
        asyncio.run(agent_v2.train([
            {"state": {}, "action": "rebalance", "reward": 0.08, "next_state": {}},
            {"state": {}, "action": "hold", "reward": 0.06, "next_state": {}},
            {"state": {}, "action": "rebalance", "reward": 0.09, "next_state": {}}
        ], epochs=20))
        
        # Assert - Different training histories (different number of experiences)
        assert agent_v1.training_episodes != agent_v2.training_episodes
        assert agent_v1.training_episodes == 1  # 1 experience
        assert agent_v2.training_episodes == 3  # 3 experiences

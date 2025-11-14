"""
Mock ML Models for Testing.

Simulates ML models with realistic behavior for testing.
"""

import random
from typing import Dict, List, Any
from decimal import Decimal
import numpy as np


class MockCreditScoringModel:
    """
    Mock credit scoring model.
    
    Target accuracy: >85%
    """
    
    def __init__(self, accuracy: float = 0.87):
        self.accuracy = accuracy
        self.predictions_made = 0
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict credit score.
        
        Args:
            features: Customer features (income, debt, history, etc.)
        
        Returns:
            Prediction with score and probability
        """
        self.predictions_made += 1
        
        # Simulate realistic credit scoring
        income = features.get("income", 50000)
        debt = features.get("debt", 10000)
        credit_history_years = features.get("credit_history_years", 5)
        
        # Simple scoring logic
        debt_to_income = debt / income if income > 0 else 1.0
        
        base_score = 650
        base_score += min(credit_history_years * 10, 100)
        base_score -= int(debt_to_income * 200)
        base_score = max(300, min(850, base_score))
        
        # Add some randomness based on accuracy
        if random.random() > self.accuracy:
            # Simulate error
            base_score += random.randint(-100, 100)
        
        # Classify
        if base_score >= 700:
            risk_category = "low"
            approval_probability = 0.9
        elif base_score >= 600:
            risk_category = "medium"
            approval_probability = 0.6
        else:
            risk_category = "high"
            approval_probability = 0.3
        
        return {
            "credit_score": base_score,
            "risk_category": risk_category,
            "approval_probability": approval_probability,
            "confidence": self.accuracy
        }
    
    def evaluate(self, test_data: List[Dict]) -> Dict[str, float]:
        """Evaluate model on test data."""
        correct = int(len(test_data) * self.accuracy)
        
        return {
            "accuracy": self.accuracy,
            "precision": self.accuracy + 0.02,
            "recall": self.accuracy - 0.02,
            "f1_score": self.accuracy
        }


class MockFraudDetectionModel:
    """
    Mock fraud detection model.
    
    Target accuracy: >95%
    """
    
    def __init__(self, accuracy: float = 0.96):
        self.accuracy = accuracy
        self.predictions_made = 0
    
    def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict fraud probability.
        
        Args:
            transaction: Transaction features
        
        Returns:
            Fraud prediction
        """
        self.predictions_made += 1
        
        # Simulate fraud detection
        amount = transaction.get("amount", 100)
        merchant_category = transaction.get("merchant_category", "retail")
        time_of_day = transaction.get("time_of_day", 12)
        location_distance = transaction.get("location_distance_km", 0)
        
        # Simple fraud scoring
        fraud_score = 0.0
        
        # Large amounts are suspicious
        if amount > 5000:
            fraud_score += 0.3
        
        # Unusual merchant categories
        if merchant_category in ["gambling", "crypto"]:
            fraud_score += 0.2
        
        # Late night transactions
        if time_of_day < 6 or time_of_day > 22:
            fraud_score += 0.1
        
        # Distant locations
        if location_distance > 1000:
            fraud_score += 0.3
        
        # Add randomness based on accuracy
        if random.random() > self.accuracy:
            fraud_score = random.random()
        
        is_fraud = fraud_score > 0.5
        
        return {
            "is_fraud": is_fraud,
            "fraud_probability": min(1.0, fraud_score),
            "confidence": self.accuracy,
            "risk_factors": [
                f for f in [
                    "high_amount" if amount > 5000 else None,
                    "unusual_merchant" if merchant_category in ["gambling", "crypto"] else None,
                    "unusual_time" if time_of_day < 6 or time_of_day > 22 else None,
                    "distant_location" if location_distance > 1000 else None
                ]
                if f
            ]
        }
    
    def evaluate(self, test_data: List[Dict]) -> Dict[str, float]:
        """Evaluate model on test data."""
        return {
            "accuracy": self.accuracy,
            "precision": self.accuracy + 0.01,
            "recall": self.accuracy - 0.01,
            "f1_score": self.accuracy,
            "auc_roc": self.accuracy + 0.02
        }


class MockPricePredictionModel:
    """
    Mock price prediction model (LSTM).
    
    Predicts next-day asset prices.
    """
    
    def __init__(self):
        self.predictions_made = 0
    
    def predict(
        self,
        historical_prices: List[float],
        horizon: int = 1
    ) -> Dict[str, Any]:
        """
        Predict future prices.
        
        Args:
            historical_prices: Historical price data
            horizon: Number of days to predict
        
        Returns:
            Price predictions
        """
        self.predictions_made += 1
        
        if len(historical_prices) < 2:
            raise ValueError("Need at least 2 historical prices")
        
        # Simple prediction: trend + noise
        recent_trend = historical_prices[-1] - historical_prices[-2]
        last_price = historical_prices[-1]
        
        predictions = []
        for i in range(horizon):
            # Trend + random walk
            noise = random.gauss(0, abs(last_price) * 0.02)  # 2% volatility
            predicted_price = last_price + (recent_trend * 0.5) + noise
            predictions.append(max(0, predicted_price))
            last_price = predicted_price
        
        return {
            "predictions": predictions,
            "confidence_intervals": [
                (p * 0.95, p * 1.05) for p in predictions
            ],
            "model_type": "LSTM"
        }
    
    def evaluate(self, test_data: List[Dict]) -> Dict[str, float]:
        """Evaluate model on test data."""
        return {
            "mae": 2.5,  # Mean Absolute Error
            "rmse": 3.2,  # Root Mean Squared Error
            "mape": 0.03,  # Mean Absolute Percentage Error (3%)
            "r2_score": 0.85
        }


class MockRLOptimizer:
    """
    Mock RL optimizer for portfolio management.
    
    Uses policy network and value network.
    """
    
    def __init__(self):
        self.training_episodes = 0
        self.total_reward = 0.0
    
    async def select_action(
        self,
        state: Dict[str, Any],
        epsilon: float = 0.1
    ) -> Dict[str, Any]:
        """
        Select portfolio action using policy network.
        
        Args:
            state: Current portfolio state
            epsilon: Exploration rate
        
        Returns:
            Action (rebalancing decision)
        """
        # Epsilon-greedy exploration
        if random.random() < epsilon:
            # Explore: random action
            action_type = random.choice(["hold", "rebalance", "reduce_risk"])
        else:
            # Exploit: use policy
            current_allocation = state.get("current_allocation", {})
            target_allocation = state.get("target_allocation", {})
            
            # Calculate drift
            drift = sum(
                abs(current_allocation.get(k, 0) - target_allocation.get(k, 0))
                for k in set(list(current_allocation.keys()) + list(target_allocation.keys()))
            )
            
            if drift > 0.1:
                action_type = "rebalance"
            elif state.get("max_drawdown", 0) < -0.10:
                action_type = "reduce_risk"
            else:
                action_type = "hold"
        
        return {
            "action_type": action_type,
            "confidence": 0.85,
            "expected_reward": random.uniform(0.05, 0.15)
        }
    
    async def train(
        self,
        experiences: List[Dict],
        epochs: int = 100
    ) -> Dict[str, Any]:
        """
        Train RL optimizer.
        
        Args:
            experiences: Training experiences (state, action, reward, next_state)
            epochs: Number of training epochs
        
        Returns:
            Training metrics
        """
        self.training_episodes += len(experiences)
        
        # Simulate training
        avg_reward = sum(exp.get("reward", 0) for exp in experiences) / len(experiences)
        self.total_reward += avg_reward * len(experiences)
        
        # Simulate convergence
        loss = max(0.1, 1.0 - (self.training_episodes / 10000))
        
        return {
            "episodes_trained": self.training_episodes,
            "avg_reward": avg_reward,
            "total_reward": self.total_reward,
            "policy_loss": loss,
            "value_loss": loss * 0.8,
            "convergence": min(1.0, self.training_episodes / 10000)
        }
    
    async def evaluate_policy(self, test_episodes: int = 100) -> Dict[str, float]:
        """Evaluate trained policy."""
        return {
            "avg_return": 0.089,  # 8.9% return
            "sharpe_ratio": 0.66,
            "max_drawdown": -0.1523,
            "win_rate": 0.625,
            "episodes_evaluated": test_episodes
        }


class MockModelExplainer:
    """Mock model explainer using SHAP values."""
    
    def explain_prediction(
        self,
        model: Any,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Explain model prediction using SHAP values.
        
        Args:
            model: Model to explain
            features: Input features
        
        Returns:
            SHAP values and explanation
        """
        # Generate mock SHAP values
        shap_values = {}
        
        for feature, value in features.items():
            # Random SHAP value between -1 and 1
            shap_values[feature] = random.uniform(-1, 1)
        
        # Sort by absolute value
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return {
            "shap_values": shap_values,
            "top_features": [f[0] for f in sorted_features[:5]],
            "explanation": f"Top feature: {sorted_features[0][0]} (impact: {sorted_features[0][1]:.3f})"
        }

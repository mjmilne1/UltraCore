"""
Fraud Detection ML Model

Production-grade fraud detection using ensemble methods with online learning capability.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import pickle
import os


@dataclass
class TransactionFeatures:
    """Features extracted from a transaction for fraud detection"""
    amount: float
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    is_night: bool  # 22:00 - 06:00
    amount_zscore: float  # Z-score relative to user's history
    velocity_1h: int  # Number of transactions in last hour
    velocity_24h: int  # Number of transactions in last 24 hours
    new_device: bool
    new_location: bool
    distance_from_last_km: float
    time_since_last_minutes: float
    amount_deviation_pct: float  # Deviation from user's average
    
    def to_array(self) -> np.ndarray:
        """Convert features to numpy array for model input"""
        return np.array([
            self.amount,
            self.hour_of_day,
            self.day_of_week,
            float(self.is_weekend),
            float(self.is_night),
            self.amount_zscore,
            self.velocity_1h,
            self.velocity_24h,
            float(self.new_device),
            float(self.new_location),
            self.distance_from_last_km,
            self.time_since_last_minutes,
            self.amount_deviation_pct
        ])


class FraudDetectionModel:
    """
    Ensemble fraud detection model using multiple algorithms.
    
    Combines:
    - Isolation Forest for anomaly detection
    - Logistic Regression for pattern matching
    - Online learning for adaptation
    
    Performance targets:
    - Accuracy: >98%
    - False positive rate: <0.5%
    - Latency: <50ms
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/tmp/fraud_detection_model.pkl"
        self.isolation_forest = None
        self.logistic_model = None
        self.feature_means = None
        self.feature_stds = None
        self.training_data = []
        self.training_labels = []
        self.is_trained = False
        
        # Performance metrics
        self.total_predictions = 0
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        
        # Load model if exists
        if os.path.exists(self.model_path):
            self.load()
    
    def extract_features(
        self,
        amount: float,
        timestamp: datetime,
        user_history: Dict,
        device_info: Dict,
        location_info: Dict
    ) -> TransactionFeatures:
        """Extract features from transaction data"""
        
        # Time features
        hour_of_day = timestamp.hour
        day_of_week = timestamp.weekday()
        is_weekend = day_of_week >= 5
        is_night = hour_of_day >= 22 or hour_of_day < 6
        
        # User history features
        user_avg = user_history.get("avg_amount", amount)
        user_std = user_history.get("std_amount", 1.0)
        amount_zscore = (amount - user_avg) / max(user_std, 1.0)
        amount_deviation_pct = ((amount - user_avg) / max(user_avg, 1.0)) * 100
        
        # Velocity features
        velocity_1h = user_history.get("transactions_1h", 0)
        velocity_24h = user_history.get("transactions_24h", 0)
        
        # Device and location features
        new_device = device_info.get("is_new", False)
        new_location = location_info.get("is_new", False)
        distance_from_last_km = location_info.get("distance_km", 0.0)
        
        # Time since last transaction
        last_transaction_time = user_history.get("last_transaction_time")
        if last_transaction_time:
            time_since_last_minutes = (timestamp - last_transaction_time).total_seconds() / 60
        else:
            time_since_last_minutes = 1440.0  # 24 hours
        
        return TransactionFeatures(
            amount=amount,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            is_night=is_night,
            amount_zscore=amount_zscore,
            velocity_1h=velocity_1h,
            velocity_24h=velocity_24h,
            new_device=new_device,
            new_location=new_location,
            distance_from_last_km=distance_from_last_km,
            time_since_last_minutes=time_since_last_minutes,
            amount_deviation_pct=amount_deviation_pct
        )
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Train the fraud detection model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (0 = legitimate, 1 = fraud)
        """
        from sklearn.ensemble import IsolationForest
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.feature_means = scaler.mean_
        self.feature_stds = scaler.scale_
        
        # Train Isolation Forest (unsupervised anomaly detection)
        self.isolation_forest = IsolationForest(
            contamination=0.01,  # Expect 1% fraud rate
            random_state=42,
            n_estimators=100
        )
        self.isolation_forest.fit(X_scaled)
        
        # Train Logistic Regression (supervised classification)
        self.logistic_model = LogisticRegression(
            class_weight='balanced',  # Handle imbalanced data
            random_state=42,
            max_iter=1000
        )
        self.logistic_model.fit(X_scaled, y)
        
        self.is_trained = True
        self.save()
    
    def predict(self, features: TransactionFeatures) -> Tuple[float, Dict]:
        """
        Predict fraud probability for a transaction.
        
        Returns:
            (fraud_score, details) where fraud_score is 0.0-1.0
        """
        if not self.is_trained:
            # Use rule-based scoring if model not trained
            return self._rule_based_score(features)
        
        X = features.to_array().reshape(1, -1)
        
        # Normalize
        X_scaled = (X - self.feature_means) / self.feature_stds
        
        # Get anomaly score from Isolation Forest (-1 to 1, lower = more anomalous)
        anomaly_score = self.isolation_forest.score_samples(X_scaled)[0]
        anomaly_prob = 1 / (1 + np.exp(anomaly_score))  # Convert to 0-1
        
        # Get fraud probability from Logistic Regression
        fraud_prob = self.logistic_model.predict_proba(X_scaled)[0][1]
        
        # Ensemble: weighted average
        fraud_score = 0.4 * anomaly_prob + 0.6 * fraud_prob
        
        details = {
            "anomaly_score": float(anomaly_prob),
            "pattern_score": float(fraud_prob),
            "ensemble_score": float(fraud_score),
            "high_risk_factors": self._identify_risk_factors(features, fraud_score)
        }
        
        self.total_predictions += 1
        
        return fraud_score, details
    
    def _rule_based_score(self, features: TransactionFeatures) -> Tuple[float, Dict]:
        """Fallback rule-based scoring when ML model not available"""
        score = 0.0
        risk_factors = []
        
        # High amount deviation
        if abs(features.amount_deviation_pct) > 200:
            score += 0.3
            risk_factors.append("high_amount_deviation")
        
        # High velocity
        if features.velocity_1h > 5:
            score += 0.2
            risk_factors.append("high_velocity")
        
        # New device and location
        if features.new_device and features.new_location:
            score += 0.25
            risk_factors.append("new_device_and_location")
        
        # Night transaction with high amount
        if features.is_night and features.amount > 10000:
            score += 0.15
            risk_factors.append("night_high_amount")
        
        # Large distance from last transaction
        if features.distance_from_last_km > 500:
            score += 0.1
            risk_factors.append("large_distance")
        
        score = min(score, 1.0)
        
        return score, {
            "rule_based": True,
            "fraud_score": score,
            "risk_factors": risk_factors
        }
    
    def _identify_risk_factors(self, features: TransactionFeatures, score: float) -> List[str]:
        """Identify which factors contributed to high fraud score"""
        factors = []
        
        if abs(features.amount_deviation_pct) > 150:
            factors.append("unusual_amount")
        if features.velocity_1h > 3:
            factors.append("high_velocity")
        if features.new_device:
            factors.append("new_device")
        if features.new_location:
            factors.append("new_location")
        if features.distance_from_last_km > 300:
            factors.append("large_distance")
        if features.is_night and features.amount > 5000:
            factors.append("night_transaction")
        
        return factors
    
    def update_feedback(self, features: TransactionFeatures, is_fraud: bool, predicted_fraud: bool):
        """Update model with feedback (online learning)"""
        if is_fraud and predicted_fraud:
            self.true_positives += 1
        elif is_fraud and not predicted_fraud:
            self.false_negatives += 1
        elif not is_fraud and predicted_fraud:
            self.false_positives += 1
        else:
            self.true_negatives += 1
        
        # Store for retraining
        self.training_data.append(features.to_array())
        self.training_labels.append(1 if is_fraud else 0)
        
        # Retrain periodically (every 1000 samples)
        if len(self.training_data) >= 1000:
            X = np.array(self.training_data)
            y = np.array(self.training_labels)
            self.train(X, y)
            self.training_data = []
            self.training_labels = []
    
    def get_metrics(self) -> Dict:
        """Get model performance metrics"""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        if total == 0:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "false_positive_rate": 0.0
            }
        
        accuracy = (self.true_positives + self.true_negatives) / total
        precision = self.true_positives / max(self.true_positives + self.false_positives, 1)
        recall = self.true_positives / max(self.true_positives + self.false_negatives, 1)
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        fpr = self.false_positives / max(self.false_positives + self.true_negatives, 1)
        
        return {
            "total_predictions": self.total_predictions,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "false_positive_rate": fpr,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives
        }
    
    def save(self):
        """Save model to disk"""
        model_data = {
            "isolation_forest": self.isolation_forest,
            "logistic_model": self.logistic_model,
            "feature_means": self.feature_means,
            "feature_stds": self.feature_stds,
            "is_trained": self.is_trained,
            "metrics": {
                "total_predictions": self.total_predictions,
                "true_positives": self.true_positives,
                "false_positives": self.false_positives,
                "true_negatives": self.true_negatives,
                "false_negatives": self.false_negatives
            }
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self):
        """Load model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data["isolation_forest"]
            self.logistic_model = model_data["logistic_model"]
            self.feature_means = model_data["feature_means"]
            self.feature_stds = model_data["feature_stds"]
            self.is_trained = model_data["is_trained"]
            
            metrics = model_data.get("metrics", {})
            self.total_predictions = metrics.get("total_predictions", 0)
            self.true_positives = metrics.get("true_positives", 0)
            self.false_positives = metrics.get("false_positives", 0)
            self.true_negatives = metrics.get("true_negatives", 0)
            self.false_negatives = metrics.get("false_negatives", 0)
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_trained = False

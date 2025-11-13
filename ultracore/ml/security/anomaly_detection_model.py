"""
Anomaly Detection ML Model

Behavioral anomaly detection using unsupervised learning.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import pickle
import os


@dataclass
class BehaviorFeatures:
    """Features for behavioral anomaly detection"""
    login_hour: int
    login_day_of_week: int
    api_calls_per_minute: float
    unique_endpoints_accessed: int
    data_volume_mb: float
    failed_attempts: int
    session_duration_minutes: float
    ip_reputation_score: float  # 0-100
    device_fingerprint_match: bool
    location_match: bool
    
    def to_array(self) -> np.ndarray:
        return np.array([
            self.login_hour,
            self.login_day_of_week,
            self.api_calls_per_minute,
            self.unique_endpoints_accessed,
            self.data_volume_mb,
            self.failed_attempts,
            self.session_duration_minutes,
            self.ip_reputation_score,
            float(self.device_fingerprint_match),
            float(self.location_match)
        ])


class AnomalyDetectionModel:
    """
    Behavioral anomaly detection using Isolation Forest.
    
    Detects:
    - Unusual login patterns
    - Abnormal API usage
    - Data exfiltration attempts
    - Account takeover indicators
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/tmp/anomaly_detection_model.pkl"
        self.isolation_forest = None
        self.feature_means = None
        self.feature_stds = None
        self.is_trained = False
        
        # User behavior baselines
        self.user_baselines = {}
        
        if os.path.exists(self.model_path):
            self.load()
    
    def train(self, X: np.ndarray):
        """Train anomaly detection model (unsupervised)"""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.feature_means = scaler.mean_
        self.feature_stds = scaler.scale_
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_estimators=100
        )
        self.isolation_forest.fit(X_scaled)
        
        self.is_trained = True
        self.save()
    
    def predict(self, features: BehaviorFeatures, user_id: str) -> Tuple[float, Dict]:
        """
        Predict anomaly score for user behavior.
        
        Returns:
            (anomaly_score, details) where anomaly_score is 0.0-1.0
        """
        if not self.is_trained:
            return self._rule_based_score(features, user_id)
        
        X = features.to_array().reshape(1, -1)
        X_scaled = (X - self.feature_means) / self.feature_stds
        
        # Get anomaly score
        score = self.isolation_forest.score_samples(X_scaled)[0]
        anomaly_prob = 1 / (1 + np.exp(score))  # Convert to 0-1
        
        # Compare with user baseline
        baseline_deviation = self._calculate_baseline_deviation(features, user_id)
        
        # Combine scores
        final_score = 0.6 * anomaly_prob + 0.4 * baseline_deviation
        
        details = {
            "anomaly_score": float(anomaly_prob),
            "baseline_deviation": float(baseline_deviation),
            "final_score": float(final_score),
            "anomaly_indicators": self._identify_anomalies(features, user_id)
        }
        
        return final_score, details
    
    def _rule_based_score(self, features: BehaviorFeatures, user_id: str) -> Tuple[float, Dict]:
        """Fallback rule-based scoring"""
        score = 0.0
        indicators = []
        
        # High API call rate
        if features.api_calls_per_minute > 100:
            score += 0.3
            indicators.append("high_api_rate")
        
        # Large data volume
        if features.data_volume_mb > 1000:
            score += 0.2
            indicators.append("large_data_volume")
        
        # Failed attempts
        if features.failed_attempts > 3:
            score += 0.25
            indicators.append("multiple_failed_attempts")
        
        # Device/location mismatch
        if not features.device_fingerprint_match or not features.location_match:
            score += 0.15
            indicators.append("device_location_mismatch")
        
        # Low IP reputation
        if features.ip_reputation_score < 30:
            score += 0.1
            indicators.append("low_ip_reputation")
        
        score = min(score, 1.0)
        
        return score, {
            "rule_based": True,
            "anomaly_score": score,
            "indicators": indicators
        }
    
    def _calculate_baseline_deviation(self, features: BehaviorFeatures, user_id: str) -> float:
        """Calculate deviation from user's normal behavior"""
        if user_id not in self.user_baselines:
            return 0.5  # Unknown user, moderate score
        
        baseline = self.user_baselines[user_id]
        deviations = []
        
        # Check each feature against baseline
        if "avg_api_calls" in baseline:
            deviation = abs(features.api_calls_per_minute - baseline["avg_api_calls"]) / max(baseline["avg_api_calls"], 1.0)
            deviations.append(min(deviation, 1.0))
        
        if "avg_data_volume" in baseline:
            deviation = abs(features.data_volume_mb - baseline["avg_data_volume"]) / max(baseline["avg_data_volume"], 1.0)
            deviations.append(min(deviation, 1.0))
        
        return np.mean(deviations) if deviations else 0.5
    
    def update_baseline(self, user_id: str, features: BehaviorFeatures):
        """Update user's behavior baseline"""
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {
                "avg_api_calls": features.api_calls_per_minute,
                "avg_data_volume": features.data_volume_mb,
                "sample_count": 1
            }
        else:
            baseline = self.user_baselines[user_id]
            n = baseline["sample_count"]
            
            # Running average
            baseline["avg_api_calls"] = (baseline["avg_api_calls"] * n + features.api_calls_per_minute) / (n + 1)
            baseline["avg_data_volume"] = (baseline["avg_data_volume"] * n + features.data_volume_mb) / (n + 1)
            baseline["sample_count"] = n + 1
    
    def _identify_anomalies(self, features: BehaviorFeatures, user_id: str) -> List[str]:
        """Identify specific anomaly indicators"""
        indicators = []
        
        if features.api_calls_per_minute > 50:
            indicators.append("high_api_rate")
        if features.data_volume_mb > 500:
            indicators.append("high_data_volume")
        if features.failed_attempts > 2:
            indicators.append("failed_attempts")
        if not features.device_fingerprint_match:
            indicators.append("device_mismatch")
        if not features.location_match:
            indicators.append("location_mismatch")
        if features.ip_reputation_score < 40:
            indicators.append("suspicious_ip")
        
        return indicators
    
    def save(self):
        """Save model to disk"""
        model_data = {
            "isolation_forest": self.isolation_forest,
            "feature_means": self.feature_means,
            "feature_stds": self.feature_stds,
            "is_trained": self.is_trained,
            "user_baselines": self.user_baselines
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self):
        """Load model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data["isolation_forest"]
            self.feature_means = model_data["feature_means"]
            self.feature_stds = model_data["feature_stds"]
            self.is_trained = model_data["is_trained"]
            self.user_baselines = model_data.get("user_baselines", {})
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_trained = False

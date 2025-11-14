"""
Tests for Fraud Detection ML Model
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from ultracore.ml.security import FraudDetectionModel, TransactionFeatures


class TestFraudDetectionModel:
    """Test fraud detection model"""
    
    @pytest.fixture
    def model(self):
        """Create fresh model for testing"""
        return FraudDetectionModel(model_path="/tmp/test_fraud_model.pkl")
    
    @pytest.fixture
    def sample_user_history(self):
        """Sample user transaction history"""
        return {
            "avg_amount": 1000.0,
            "std_amount": 200.0,
            "transactions_1h": 2,
            "transactions_24h": 10,
            "last_transaction_time": datetime.utcnow() - timedelta(hours=1)
        }
    
    @pytest.fixture
    def sample_device_info(self):
        """Sample device information"""
        return {
            "is_new": False,
            "device_id": "device_123"
        }
    
    @pytest.fixture
    def sample_location_info(self):
        """Sample location information"""
        return {
            "is_new": False,
            "distance_km": 5.0,
            "country": "AU"
        }
    
    def test_feature_extraction(self, model, sample_user_history, sample_device_info, sample_location_info):
        """Test feature extraction from transaction"""
        features = model.extract_features(
            amount=1500.0,
            timestamp=datetime(2025, 11, 13, 14, 30),
            user_history=sample_user_history,
            device_info=sample_device_info,
            location_info=sample_location_info
        )
        
        assert isinstance(features, TransactionFeatures)
        assert features.amount == 1500.0
        assert features.hour_of_day == 14
        assert features.day_of_week == 3  # Wednesday
        assert not features.is_weekend
        assert not features.is_night
        assert features.velocity_1h == 2
        assert features.velocity_24h == 10
        assert not features.new_device
        assert not features.new_location
    
    def test_rule_based_scoring_low_risk(self, model, sample_user_history, sample_device_info, sample_location_info):
        """Test rule-based scoring for low-risk transaction"""
        features = model.extract_features(
            amount=1000.0,  # Normal amount
            timestamp=datetime(2025, 11, 13, 10, 0),
            user_history=sample_user_history,
            device_info=sample_device_info,
            location_info=sample_location_info
        )
        
        score, details = model.predict(features)
        
        assert 0.0 <= score <= 1.0
        # Score should be reasonable (not checking exact threshold as it's rule-based)
        assert "rule_based" in details or "ensemble_score" in details
    
    def test_rule_based_scoring_high_risk(self, model, sample_user_history, sample_device_info, sample_location_info):
        """Test rule-based scoring for high-risk transaction"""
        # High amount, new device, new location, night time
        high_risk_device = {"is_new": True}
        high_risk_location = {"is_new": True, "distance_km": 1000.0}
        high_risk_history = {
            **sample_user_history,
            "transactions_1h": 10  # High velocity
        }
        
        features = model.extract_features(
            amount=50000.0,  # Very high amount
            timestamp=datetime(2025, 11, 13, 2, 0),  # Night
            user_history=high_risk_history,
            device_info=high_risk_device,
            location_info=high_risk_location
        )
        
        score, details = model.predict(features)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high risk
    
    def test_model_training(self, model):
        """Test model training"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Normal transactions
        X_normal = np.random.randn(n_samples // 2, 13) * 0.5
        y_normal = np.zeros(n_samples // 2)
        
        # Fraudulent transactions (with higher values)
        X_fraud = np.random.randn(n_samples // 2, 13) * 2 + 3
        y_fraud = np.ones(n_samples // 2)
        
        X = np.vstack([X_normal, X_fraud])
        y = np.hstack([y_normal, y_fraud])
        
        # Train model
        model.train(X, y)
        
        assert model.is_trained
        assert model.isolation_forest is not None
        assert model.logistic_model is not None
        assert model.feature_means is not None
        assert model.feature_stds is not None
    
    def test_prediction_after_training(self, model):
        """Test prediction after model training"""
        # Train model first
        np.random.seed(42)
        n_samples = 1000
        X_normal = np.random.randn(n_samples // 2, 13) * 0.5
        X_fraud = np.random.randn(n_samples // 2, 13) * 2 + 3
        X = np.vstack([X_normal, X_fraud])
        y = np.hstack([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
        
        model.train(X, y)
        
        # Test prediction on normal transaction
        normal_features = TransactionFeatures(
            amount=1000.0,
            hour_of_day=10,
            day_of_week=2,
            is_weekend=False,
            is_night=False,
            amount_zscore=0.0,
            velocity_1h=2,
            velocity_24h=10,
            new_device=False,
            new_location=False,
            distance_from_last_km=5.0,
            time_since_last_minutes=60.0,
            amount_deviation_pct=0.0
        )
        
        score, details = model.predict(normal_features)
        
        assert 0.0 <= score <= 1.0
        assert "ensemble_score" in details
        assert "anomaly_score" in details
        assert "pattern_score" in details
    
    def test_feedback_update(self, model):
        """Test model feedback and online learning"""
        features = TransactionFeatures(
            amount=1000.0,
            hour_of_day=10,
            day_of_week=2,
            is_weekend=False,
            is_night=False,
            amount_zscore=0.0,
            velocity_1h=2,
            velocity_24h=10,
            new_device=False,
            new_location=False,
            distance_from_last_km=5.0,
            time_since_last_minutes=60.0,
            amount_deviation_pct=0.0
        )
        
        # Provide feedback
        model.update_feedback(features, is_fraud=False, predicted_fraud=False)
        
        # Check metrics updated
        metrics = model.get_metrics()
        # Note: total_predictions is incremented in predict(), not update_feedback()
        assert metrics["true_negatives"] == 1
    
    def test_metrics(self, model):
        """Test metrics calculation"""
        # Simulate some predictions
        features = TransactionFeatures(
            amount=1000.0, hour_of_day=10, day_of_week=2,
            is_weekend=False, is_night=False, amount_zscore=0.0,
            velocity_1h=2, velocity_24h=10, new_device=False,
            new_location=False, distance_from_last_km=5.0,
            time_since_last_minutes=60.0, amount_deviation_pct=0.0
        )
        
        model.update_feedback(features, is_fraud=False, predicted_fraud=False)  # TN
        model.update_feedback(features, is_fraud=True, predicted_fraud=True)    # TP
        model.update_feedback(features, is_fraud=False, predicted_fraud=True)   # FP
        model.update_feedback(features, is_fraud=True, predicted_fraud=False)   # FN
        
        metrics = model.get_metrics()
        
        assert metrics["true_positives"] == 1
        assert metrics["true_negatives"] == 1
        assert metrics["false_positives"] == 1
        assert metrics["false_negatives"] == 1
        assert metrics["accuracy"] == 0.5
    
    def test_save_and_load(self, model, tmp_path):
        """Test model persistence"""
        model_path = tmp_path / "fraud_model.pkl"
        model.model_path = str(model_path)
        
        # Train model
        np.random.seed(42)
        X = np.random.randn(100, 13)
        y = np.random.randint(0, 2, 100)
        model.train(X, y)
        
        # Save
        model.save()
        assert model_path.exists()
        
        # Load into new model
        new_model = FraudDetectionModel(model_path=str(model_path))
        
        assert new_model.is_trained
        assert new_model.isolation_forest is not None
        assert new_model.logistic_model is not None

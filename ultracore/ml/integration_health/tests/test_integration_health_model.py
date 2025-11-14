"""Tests for Integration Health ML Model"""
import pytest
from ultracore.ml.integration_health.integration_health_model import IntegrationHealthModel

def test_predict_failure_probability():
    """Test failure probability prediction"""
    model = IntegrationHealthModel()
    
    features = {
        "success_rate": 92.0,
        "avg_response_time_ms": 500,
        "error_count_last_hour": 15,
        "uptime_percent_7d": 98.5
    }
    
    probability = model.predict_failure_probability(features)
    
    assert 0 <= probability <= 1

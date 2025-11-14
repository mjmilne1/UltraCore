"""Tests for Template Recommender ML Model"""
import pytest
from ultracore.ml.template_recommender.template_recommender_model import TemplateRecommenderModel

def test_predict_template_usage():
    """Test template usage prediction"""
    model = TemplateRecommenderModel()
    
    user_features = {
        "age": 35,
        "risk_score": 7,
        "portfolio_value": 500000,
        "country": "AU"
    }
    
    result = model.predict_template_usage(user_features)
    
    assert "predictions" in result
    assert "top_recommendation" in result
    assert result["confidence"] > 0

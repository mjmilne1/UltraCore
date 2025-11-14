"""Tests for Template Recommender Agent"""
import pytest
from ultracore.agents.template_recommender.template_recommender_agent import TemplateRecommenderAgent

@pytest.mark.asyncio
async def test_recommend_portfolio_template():
    """Test portfolio template recommendation"""
    agent = TemplateRecommenderAgent(llm_client=None)
    
    client_profile = {
        "age": 30,
        "risk_tolerance": "high",
        "investment_horizon_years": 20,
        "country": "AU"
    }
    
    result = await agent.recommend_portfolio_template(client_profile)
    
    assert "recommended_template" in result
    assert result["confidence"] > 0.8

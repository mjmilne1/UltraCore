"""Tests for Integration Monitor Agent"""
import pytest
from ultracore.agents.integration_monitor.integration_monitor_agent import IntegrationMonitorAgent

@pytest.mark.asyncio
async def test_monitor_integration_health():
    """Test integration health monitoring"""
    agent = IntegrationMonitorAgent(llm_client=None)
    
    metrics = {
        "success_rate": 98.5,
        "avg_response_time_ms": 250,
        "error_count_last_hour": 2
    }
    
    result = await agent.monitor_integration_health("integration_001", metrics)
    
    assert "health_score" in result
    assert result["health_status"] in ["healthy", "degraded", "unhealthy"]

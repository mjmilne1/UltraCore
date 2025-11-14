"""Tests for Tenant Optimizer Agent"""
import pytest
from ultracore.agents.tenant_optimizer.tenant_optimizer_agent import TenantOptimizerAgent

@pytest.mark.asyncio
async def test_optimize_tenant_resources():
    """Test tenant resource optimization"""
    agent = TenantOptimizerAgent(llm_client=None)
    
    resource_usage = {
        "database": {"current_connections": 5, "max_connections": 20},
        "storage": {"used_gb": 125.7}
    }
    cost_data = {"total_cost_aud": 900.70}
    
    result = await agent.optimize_tenant_resources("tenant_001", resource_usage, cost_data)
    
    assert "recommendations" in result
    assert "total_estimated_savings_aud" in result

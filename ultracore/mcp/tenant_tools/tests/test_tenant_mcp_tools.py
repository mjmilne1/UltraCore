"""Tests for Tenant MCP Tools"""
import pytest
from ultracore.mcp.tenant_tools.tenant_mcp_tools import (
    provision_tenant,
    get_tenant_status,
    upgrade_tenant_tier
)

@pytest.mark.asyncio
async def test_provision_tenant():
    """Test tenant provisioning"""
    result = await provision_tenant(
        tenant_name="Test Corp",
        tier="ENTERPRISE",
        isolation_strategy="database_per_tenant",
        admin_email="admin@testcorp.com"
    )
    
    assert result["tenant_name"] == "Test Corp"
    assert result["tier"] == "ENTERPRISE"
    assert "tenant_id" in result

@pytest.mark.asyncio
async def test_upgrade_tenant_tier():
    """Test tenant tier upgrade"""
    result = await upgrade_tenant_tier("tenant_001", "ENTERPRISE")
    
    assert result["new_tier"] == "ENTERPRISE"
    assert "cost_impact" in result

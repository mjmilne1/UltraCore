"""Tests for Permissions MCP Tools"""
import pytest
from ultracore.mcp.permissions_tools.permissions_mcp_tools import (
    create_role,
    assign_permission,
    check_access,
    get_user_permissions,
    revoke_permission,
    audit_access
)

@pytest.mark.asyncio
async def test_create_role():
    """Test role creation"""
    result = await create_role(
        name="Portfolio Manager",
        description="Can manage client portfolios",
        permissions=["portfolio.read", "portfolio.update"]
    )
    
    assert result["status"] == "created"
    assert result["role"]["name"] == "Portfolio Manager"
    assert "role_id" in result["role"]

@pytest.mark.asyncio
async def test_assign_permission():
    """Test permission assignment"""
    result = await assign_permission(
        role_id="role_abc123",
        permission="portfolio.update"
    )
    
    assert result["status"] == "assigned"
    assert result["assignment"]["permission"] == "portfolio.update"

@pytest.mark.asyncio
async def test_check_access():
    """Test access check"""
    result = await check_access(
        user_id="user_123",
        resource="portfolio",
        action="update"
    )
    
    assert "allowed" in result
    assert "reason" in result

@pytest.mark.asyncio
async def test_get_user_permissions():
    """Test get user permissions"""
    result = await get_user_permissions(user_id="user_123")
    
    assert "permissions" in result
    assert "permissions_by_resource" in result
    assert result["total_permissions"] > 0

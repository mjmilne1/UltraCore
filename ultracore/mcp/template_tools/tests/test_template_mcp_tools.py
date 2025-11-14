"""Tests for Template MCP Tools"""
import pytest
from ultracore.mcp.template_tools.template_mcp_tools import (
    create_custom_template,
    apply_template,
    get_template_recommendations
)

@pytest.mark.asyncio
async def test_create_custom_template():
    """Test custom template creation"""
    result = await create_custom_template(
        name="My Custom Portfolio",
        template_type="portfolio",
        configuration={"allocation": {"stocks": 60, "bonds": 40}},
        description="Custom balanced portfolio"
    )
    
    assert result["name"] == "My Custom Portfolio"
    assert "template_id" in result

@pytest.mark.asyncio
async def test_get_template_recommendations():
    """Test template recommendations"""
    context = {"age": 30, "risk_tolerance": "high", "country": "AU"}
    
    result = await get_template_recommendations("user_123", context)
    
    assert isinstance(result, list)
    assert all("match_score" in r for r in result)

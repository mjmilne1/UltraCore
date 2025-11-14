"""Tests for Business Rules MCP Tools"""
import pytest
from ultracore.mcp.rules_tools.rules_mcp_tools import (
    create_rule,
    evaluate_rule,
    update_rule,
    get_rule_violations,
    simulate_rule
)

@pytest.mark.asyncio
async def test_create_rule():
    """Test rule creation"""
    result = await create_rule(
        name="High Risk Transaction Alert",
        rule_type="compliance",
        condition={"field": "transaction_amount", "operator": "greater_than", "value": 10000},
        action={"type": "alert", "recipients": ["compliance@example.com"]},
        priority=900
    )
    
    assert result["status"] == "created"
    assert result["rule"]["name"] == "High Risk Transaction Alert"
    assert "rule_id" in result["rule"]

@pytest.mark.asyncio
async def test_evaluate_rule():
    """Test rule evaluation"""
    result = await evaluate_rule(
        rule_id="rule_abc123",
        data={"transaction_amount": 15000}
    )
    
    assert "evaluation_id" in result
    assert result["matched"] is True

@pytest.mark.asyncio
async def test_simulate_rule():
    """Test rule simulation"""
    result = await simulate_rule(
        rule_id="rule_abc123",
        test_data=[
            {"transaction_amount": 5000},
            {"transaction_amount": 15000}
        ]
    )
    
    assert result["total_test_cases"] == 2
    assert result["matched_cases"] == 1

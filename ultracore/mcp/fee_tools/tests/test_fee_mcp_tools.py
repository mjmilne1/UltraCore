"""Tests for Fee MCP Tools"""
import pytest
from decimal import Decimal
from ultracore.mcp.fee_tools.fee_mcp_tools import (
    calculate_fee,
    get_fee_schedule,
    optimize_fee_structure,
    calculate_australian_gst
)

@pytest.mark.asyncio
async def test_calculate_management_fee():
    """Test management fee calculation"""
    result = await calculate_fee(
        fee_type="management",
        amount=Decimal("1000000"),
        parameters={"annual_rate": 1.0, "billing_frequency": "monthly"},
        tenant_id="tenant_001"
    )
    
    assert result["fee_type"] == "management"
    assert result["fee_amount"] == pytest.approx(833.33, rel=0.01)

@pytest.mark.asyncio
async def test_calculate_performance_fee():
    """Test performance fee calculation"""
    result = await calculate_fee(
        fee_type="performance",
        amount=Decimal("100000"),  # Gains
        parameters={
            "performance_rate": 20.0,
            "hurdle_rate": 8.0,
            "high_water_mark": 0
        },
        tenant_id="tenant_001"
    )
    
    assert result["fee_type"] == "performance"
    assert "gains_above_hurdle" in result

@pytest.mark.asyncio
async def test_calculate_australian_gst():
    """Test Australian GST calculation"""
    result = await calculate_australian_gst(
        fee_amount=Decimal("1000"),
        gst_registered=True
    )
    
    assert result["gst_rate_percent"] == 10.0
    assert result["gst_amount"] == 100.0
    assert result["total_amount_inc_gst"] == 1100.0
    assert result["input_tax_credit_available"] is True

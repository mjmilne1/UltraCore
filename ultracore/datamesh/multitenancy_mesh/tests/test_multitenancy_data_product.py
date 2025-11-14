"""Tests for Multi-Tenancy Data Product"""
import pytest
from datetime import datetime, timedelta
from ultracore.datamesh.multitenancy_mesh.multitenancy_data_product import MultiTenancyDataProduct

@pytest.mark.asyncio
async def test_get_tenant_analytics():
    """Test tenant analytics retrieval"""
    product = MultiTenancyDataProduct()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    analytics = await product.get_tenant_analytics(
        tenant_id="tenant_001",
        date_range_start=start_date,
        date_range_end=end_date
    )
    
    assert analytics["tenant_id"] == "tenant_001"
    assert "resource_usage" in analytics
    assert "cost_allocation" in analytics
    assert analytics["tier"] in ["SMALL", "STANDARD", "ENTERPRISE"]

@pytest.mark.asyncio
async def test_get_cost_optimization_opportunities():
    """Test cost optimization recommendations"""
    product = MultiTenancyDataProduct()
    
    opportunities = await product.get_cost_optimization_opportunities("tenant_001")
    
    assert isinstance(opportunities, list)
    assert all("savings_aud" in opp for opp in opportunities)

"""Tests for Trading Data Product"""
import pytest
from datetime import datetime, timedelta
from ultracore.datamesh.trading_mesh.trading_data_product import TradingDataProduct

@pytest.mark.asyncio
async def test_get_trade_analytics():
    """Test trade analytics retrieval"""
    product = TradingDataProduct()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    analytics = await product.get_trade_analytics(
        tenant_id="tenant_001",
        date_range_start=start_date,
        date_range_end=end_date
    )
    
    assert analytics["tenant_id"] == "tenant_001"
    assert "total_orders" in analytics
    assert "execution_rate" in analytics
    assert analytics["asic_compliant"] is True

@pytest.mark.asyncio
async def test_get_asic_trade_report():
    """Test ASIC trade report generation"""
    product = TradingDataProduct()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    report = await product.get_asic_trade_report(
        tenant_id="tenant_001",
        date_range_start=start_date,
        date_range_end=end_date
    )
    
    assert report["report_type"] == "ASIC_TRADE_REPORT"
    assert report["asic_compliant"] is True
    assert "best_execution_compliance" in report
    assert report["best_execution_compliance"]["status"] == "compliant"

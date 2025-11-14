"""
Integration tests for Data Mesh.

Tests data product functionality, quality monitoring, and catalog API.
"""

import pytest
from datetime import datetime, timedelta
from ultracore.data_mesh import (
    DataProductRegistry,
    QualityMonitor,
    DataCatalogAPI,
)
from ultracore.data_mesh.products import (
    Customer360,
    AccountBalances,
    TransactionHistory,
)


class TestDataProductRegistry:
    """Test data product registry."""
    
    def test_register_product(self):
        """Test product registration."""
        registry = DataProductRegistry()
        product = Customer360()
        
        registry.register(product)
        
        assert registry.get_product("customer_360") is not None
        assert len(registry.list_products()) == 1
    
    def test_list_products_by_domain(self):
        """Test listing products by domain."""
        registry = DataProductRegistry()
        
        registry.register(Customer360())
        registry.register(AccountBalances())
        
        customer_products = registry.list_products(domain="customers")
        assert len(customer_products) == 1
        assert customer_products[0].metadata.name == "Customer360"
    
    def test_get_product_by_id(self):
        """Test getting product by ID."""
        registry = DataProductRegistry()
        product = Customer360()
        registry.register(product)
        
        retrieved = registry.get_product("customer_360")
        assert retrieved is not None
        assert retrieved.metadata.name == "Customer360"


class TestDataProducts:
    """Test individual data products."""
    
    @pytest.mark.asyncio
    async def test_customer360_query(self):
        """Test Customer360 query."""
        product = Customer360()
        
        result = await product.query(filters={"customer_id": "CUST001"})
        
        assert result is not None
        assert "customers" in result
        assert len(result["customers"]) > 0
    
    @pytest.mark.asyncio
    async def test_account_balances_query(self):
        """Test AccountBalances query."""
        product = AccountBalances()
        
        result = await product.query(filters={"customer_id": "CUST001"})
        
        assert result is not None
        assert "accounts" in result
    
    @pytest.mark.asyncio
    async def test_transaction_history_query(self):
        """Test TransactionHistory query."""
        product = TransactionHistory()
        
        result = await product.query(
            filters={
                "account_id": "ACC001",
                "start_date": datetime.utcnow() - timedelta(days=30)
            }
        )
        
        assert result is not None
        assert "transactions" in result
    
    @pytest.mark.asyncio
    async def test_product_refresh(self):
        """Test product refresh."""
        product = Customer360()
        
        result = await product.refresh()
        
        assert result is True
        assert product.metadata.last_updated is not None
    
    @pytest.mark.asyncio
    async def test_product_schema(self):
        """Test product schema."""
        product = Customer360()
        
        schema = await product.get_schema()
        
        assert schema is not None
        assert "fields" in schema
        assert len(schema["fields"]) > 0


class TestQualityMonitoring:
    """Test quality monitoring system."""
    
    @pytest.mark.asyncio
    async def test_measure_quality(self):
        """Test quality measurement."""
        monitor = QualityMonitor()
        product = Customer360()
        
        metrics = await monitor.measure_quality(product)
        
        assert metrics is not None
        assert 0 <= metrics.completeness <= 1
        assert 0 <= metrics.accuracy <= 1
        assert 0 <= metrics.consistency <= 1
        assert 0 <= metrics.timeliness <= 1
        assert 0 <= metrics.uniqueness <= 1
    
    @pytest.mark.asyncio
    async def test_quality_alerts(self):
        """Test quality alert generation."""
        monitor = QualityMonitor()
        product = Customer360()
        
        # Measure quality
        await monitor.measure_quality(product)
        
        # Get alerts
        alerts = monitor.get_alerts(product_id="customer_360")
        
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_quality_report(self):
        """Test quality report generation."""
        monitor = QualityMonitor()
        product = Customer360()
        
        # Measure quality
        await monitor.measure_quality(product)
        
        # Get report
        report = monitor.get_quality_report(product_id="customer_360")
        
        assert report is not None
        assert "average_score" in report
        assert "measurements" in report
    
    def test_alert_resolution(self):
        """Test alert resolution."""
        monitor = QualityMonitor()
        
        # Create a mock alert
        alert_id = "alert_001"
        # In real implementation, this would resolve an actual alert
        
        result = monitor.resolve_alert(alert_id, resolved_by="test_user")
        
        # Alert resolution logic would be tested here
        assert result is not None


class TestDataCatalogAPI:
    """Test Data Catalog API."""
    
    def test_list_products_endpoint(self):
        """Test list products endpoint."""
        api = DataCatalogAPI()
        registry = DataProductRegistry()
        
        # Register products
        registry.register(Customer360())
        registry.register(AccountBalances())
        
        api.registry = registry
        
        # List products
        products = api.list_products()
        
        assert len(products) == 2
    
    def test_get_product_endpoint(self):
        """Test get product endpoint."""
        api = DataCatalogAPI()
        registry = DataProductRegistry()
        
        registry.register(Customer360())
        api.registry = registry
        
        product = api.get_product("customer_360")
        
        assert product is not None
        assert product["name"] == "Customer360"
    
    def test_list_domains_endpoint(self):
        """Test list domains endpoint."""
        api = DataCatalogAPI()
        registry = DataProductRegistry()
        
        registry.register(Customer360())
        registry.register(AccountBalances())
        registry.register(TransactionHistory())
        
        api.registry = registry
        
        domains = api.list_domains()
        
        assert len(domains) > 0
        assert any(d["domain"] == "customers" for d in domains)
        assert any(d["domain"] == "accounts" for d in domains)


class TestDataLineage:
    """Test data lineage tracking."""
    
    def test_lineage_tracking(self):
        """Test lineage tracking."""
        product = Customer360()
        
        lineage = product.metadata.lineage
        
        assert lineage is not None
        assert "upstream" in lineage
        assert "downstream" in lineage
    
    def test_upstream_dependencies(self):
        """Test upstream dependency tracking."""
        product = Customer360()
        
        upstream = product.metadata.lineage.get("upstream", [])
        
        # Customer360 depends on multiple sources
        assert len(upstream) > 0
    
    def test_downstream_consumers(self):
        """Test downstream consumer tracking."""
        product = Customer360()
        
        downstream = product.metadata.lineage.get("downstream", [])
        
        # Customer360 is consumed by other products
        assert isinstance(downstream, list)


class TestCrossProductIntegration:
    """Test integration between data products."""
    
    @pytest.mark.asyncio
    async def test_customer_account_integration(self):
        """Test Customer360 and AccountBalances integration."""
        customer_product = Customer360()
        account_product = AccountBalances()
        
        # Query customer
        customer_result = await customer_product.query(
            filters={"customer_id": "CUST001"}
        )
        
        # Query accounts for same customer
        account_result = await account_product.query(
            filters={"customer_id": "CUST001"}
        )
        
        assert customer_result is not None
        assert account_result is not None
    
    @pytest.mark.asyncio
    async def test_account_transaction_integration(self):
        """Test AccountBalances and TransactionHistory integration."""
        account_product = AccountBalances()
        transaction_product = TransactionHistory()
        
        # Query account
        account_result = await account_product.query(
            filters={"account_id": "ACC001"}
        )
        
        # Query transactions for same account
        transaction_result = await transaction_product.query(
            filters={"account_id": "ACC001"}
        )
        
        assert account_result is not None
        assert transaction_result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

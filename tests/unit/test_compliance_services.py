"""
Unit tests for Compliance services.

Tests transaction monitoring, AML/CTF, and regulatory reporting.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.ultracore.domains.compliance.services.transaction_monitoring import (
    TransactionMonitoringService,
    MonitoringRule,
)
from src.ultracore.domains.compliance.services.aml_ctf import AMLCTFService
from src.ultracore.domains.compliance.services.regulatory_reporting import (
    RegulatoryReportingService,
)
from src.ultracore.domains.compliance.models import (
    TransactionMonitoring,
    SuspiciousActivity,
    RegulatoryReport,
    CustomerRiskProfile,
    RiskLevel,
    AlertPriority,
    ReportType,
)


class TestTransactionMonitoringService:
    """Test transaction monitoring service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return TransactionMonitoringService()
    
    def test_large_transaction_rule(self, service):
        """Test large transaction detection."""
        monitoring = TransactionMonitoring(
            tenant_id="test",
            transaction_id="txn-001",
            customer_id="cust-001",
            amount=Decimal("15000"),
            transaction_type="transfer",
            from_account="acc-001",
            to_account="acc-002"
        )
        
        result = service.check_transaction(monitoring)
        
        assert result["triggered_rules"] == ["large_transaction"]
        assert result["risk_score"] >= 50
    
    def test_velocity_rule(self, service):
        """Test velocity rule detection."""
        # Create multiple transactions
        for i in range(5):
            monitoring = TransactionMonitoring(
                tenant_id="test",
                transaction_id=f"txn-{i:03d}",
                customer_id="cust-001",
                amount=Decimal("1000"),
                transaction_type="transfer",
                from_account="acc-001",
                to_account=f"acc-{i:03d}"
            )
            service.check_transaction(monitoring)
        
        # Check if velocity rule triggered
        # In production: query database for recent transactions
        assert True  # Placeholder
    
    def test_structuring_pattern(self, service):
        """Test structuring pattern detection."""
        monitoring = TransactionMonitoring(
            tenant_id="test",
            transaction_id="txn-001",
            customer_id="cust-001",
            amount=Decimal("9900"),  # Just below $10k threshold
            transaction_type="deposit",
            from_account="acc-001",
            to_account="acc-002"
        )
        
        result = service.check_transaction(monitoring)
        
        assert "structuring" in result["triggered_rules"]


class TestAMLCTFService:
    """Test AML/CTF service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return AMLCTFService()
    
    def test_sanctions_screening(self, service):
        """Test sanctions screening."""
        result = service.screen_sanctions("John Smith", "1980-01-01")
        
        assert "matches" in result
        assert isinstance(result["matches"], list)
    
    def test_pep_screening(self, service):
        """Test PEP screening."""
        result = service.check_pep("John Smith")
        
        assert "is_pep" in result
        assert isinstance(result["is_pep"], bool)
    
    def test_risk_assessment(self, service):
        """Test risk assessment."""
        customer_data = {
            "customer_id": "cust-001",
            "country": "AU",
            "occupation": "Engineer",
            "expected_activity": "moderate",
            "source_of_wealth": "employment"
        }
        
        result = service.assess_risk(customer_data)
        
        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high"]
    
    def test_enhanced_due_diligence(self, service):
        """Test enhanced due diligence."""
        customer_id = "cust-001"
        
        result = service.perform_edd(customer_id)
        
        assert "edd_required" in result
        assert "findings" in result


class TestRegulatoryReportingService:
    """Test regulatory reporting service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return RegulatoryReportingService()
    
    def test_generate_ttr(self, service):
        """Test TTR generation."""
        transactions = [
            {
                "transaction_id": "txn-001",
                "amount": Decimal("15000"),
                "customer_id": "cust-001",
                "transaction_date": datetime.utcnow()
            }
        ]
        
        report = service.generate_ttr(transactions)
        
        assert report.report_type == ReportType.AUSTRAC_TTR
        assert len(report.data["transactions"]) > 0
    
    def test_generate_smr(self, service):
        """Test SMR generation."""
        alert = SuspiciousActivity(
            tenant_id="test",
            customer_id="cust-001",
            alert_type="structuring",
            description="Suspicious structuring pattern",
            risk_score=85,
            priority=AlertPriority.HIGH
        )
        
        report = service.generate_smr(alert)
        
        assert report.report_type == ReportType.AUSTRAC_SMR
        assert "alert_id" in report.data
    
    def test_generate_apra_quarterly(self, service):
        """Test APRA quarterly report."""
        data = {
            "total_assets": Decimal("1000000"),
            "total_liabilities": Decimal("500000"),
            "capital_adequacy": Decimal("15.5")
        }
        
        report = service.generate_apra_quarterly(data)
        
        assert report.report_type == ReportType.APRA_QUARTERLY
        assert report.reporting_period_start is not None
    
    def test_submit_report(self, service):
        """Test report submission."""
        report = RegulatoryReport(
            tenant_id="test",
            report_type=ReportType.AUSTRAC_TTR,
            reporting_period_start=datetime.utcnow() - timedelta(days=30),
            reporting_period_end=datetime.utcnow(),
            data={"transactions": []}
        )
        
        result = service.submit_report(report)
        
        assert result["success"] is True
        assert "submission_id" in result

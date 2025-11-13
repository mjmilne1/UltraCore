"""
Reporting System Integration Tests
Comprehensive tests for reporting system with full UltraCore architecture
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from ultracore.reporting.events import ReportType, ReportFormat, ReportFrequency, TaxReportType
from ultracore.reporting.aggregates import (
    ReportTemplateAggregate,
    ScheduledReportAggregate,
    ReportAggregate,
    TaxReportAggregate
)
from ultracore.agentic_ai.agents.reporting import get_report_generation_agent
from ultracore.ml.reporting import get_performance_prediction_model, get_tax_optimization_model
from ultracore.datamesh.reporting_mesh import get_reporting_data_product
from ultracore.mcp.reporting_tools import get_reporting_tools


class TestReportingEventSourcing:
    """Test event-sourced aggregates"""
    
    def test_create_report_template(self):
        """Test creating report template"""
        tenant_id = "test_tenant"
        template_id = str(uuid4())
        
        template = ReportTemplateAggregate(
            tenant_id=tenant_id,
            template_id=template_id
        )
        
        template.create(
            name="Monthly Performance Report",
            report_type=ReportType.PORTFOLIO_PERFORMANCE,
            description="Standard monthly performance report",
            sections=["executive_summary", "performance_overview", "holdings"],
            metrics=["total_return", "sharpe_ratio", "alpha", "beta"],
            filters={"period": "1_month"},
            format_options={"include_charts": True},
            created_by="user_123"
        )
        
        assert template.name == "Monthly Performance Report"
        assert template.report_type == ReportType.PORTFOLIO_PERFORMANCE
        assert len(template.sections) == 3
        assert template.is_active
        
        # Test events
        events = template.get_uncommitted_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "ReportTemplateCreated"
    
    def test_schedule_report(self):
        """Test scheduling recurring report"""
        tenant_id = "test_tenant"
        schedule_id = str(uuid4())
        
        schedule = ScheduledReportAggregate(
            tenant_id=tenant_id,
            schedule_id=schedule_id
        )
        
        schedule.create(
            client_id="client_123",
            template_id="template_456",
            frequency=ReportFrequency.WEEKLY,
            delivery_channels=["email", "portal"],
            recipients=["client@example.com"],
            parameters={"include_detailed_holdings": True}
        )
        
        assert schedule.frequency == ReportFrequency.WEEKLY
        assert schedule.is_active
        assert schedule.next_run_at is not None
        assert len(schedule.delivery_channels) == 2
    
    def test_generate_report(self):
        """Test report generation workflow"""
        tenant_id = "test_tenant"
        report_id = str(uuid4())
        
        report = ReportAggregate(
            tenant_id=tenant_id,
            report_id=report_id
        )
        
        # Request report
        report.request(
            client_id="client_123",
            report_type=ReportType.PORTFOLIO_PERFORMANCE,
            format=ReportFormat.PDF,
            template_id="template_456",
            parameters={"period": "1_month"},
            requested_by="user_123"
        )
        
        assert report.status == "pending"
        
        # Start generation
        report.start_generation()
        assert report.status == "generating"
        
        # Complete generation
        report.complete_generation(
            file_url="https://storage.example.com/reports/report_123.pdf",
            file_size_bytes=1024 * 150,
            page_count=8
        )
        
        assert report.status == "completed"
        assert report.file_url is not None
        assert report.file_size_bytes == 1024 * 150
    
    def test_generate_tax_report(self):
        """Test tax report generation"""
        tenant_id = "test_tenant"
        report_id = str(uuid4())
        
        tax_report = TaxReportAggregate(
            tenant_id=tenant_id,
            report_id=report_id
        )
        
        tax_report.generate(
            client_id="client_123",
            tax_year=2024,
            tax_report_type=TaxReportType.CAPITAL_GAINS,
            total_capital_gains=15000.00,
            total_dividends=3000.00,
            total_interest=500.00,
            wash_sales_count=2,
            file_url="https://storage.example.com/tax_reports/tax_2024.pdf",
            cgt_discount_applied=True,
            franking_credits=1200.00
        )
        
        assert tax_report.tax_year == 2024
        assert tax_report.total_capital_gains == 15000.00
        assert tax_report.cgt_discount_applied
        assert tax_report.franking_credits == 1200.00


class TestReportingDataMesh:
    """Test data mesh reporting domain"""
    
    def test_calculate_capital_gains(self):
        """Test Australian CGT calculation"""
        data_product = get_reporting_data_product()
        
        cgt_data = data_product.calculate_capital_gains(
            tenant_id="test_tenant",
            client_id="client_123",
            tax_year=2024
        )
        
        assert "short_term_gains" in cgt_data
        assert "long_term_gains" in cgt_data
        assert "cgt_discount_amount" in cgt_data
        assert "net_capital_gain" in cgt_data
    
    def test_calculate_dividend_income(self):
        """Test Australian dividend income with franking credits"""
        data_product = get_reporting_data_product()
        
        dividend_data = data_product.calculate_dividend_income(
            tenant_id="test_tenant",
            client_id="client_123",
            tax_year=2024
        )
        
        assert "total_dividends" in dividend_data
        assert "franking_credits" in dividend_data
        assert "grossed_up_dividends" in dividend_data
    
    def test_calculate_performance_metrics(self):
        """Test performance metrics calculation"""
        data_product = get_reporting_data_product()
        
        metrics = data_product.calculate_performance_metrics(
            tenant_id="test_tenant",
            client_id="client_123",
            portfolio_id="portfolio_456",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "alpha" in metrics
        assert "beta" in metrics
        assert "max_drawdown" in metrics
    
    def test_generate_ato_report(self):
        """Test ATO-compliant report generation"""
        data_product = get_reporting_data_product()
        
        ato_report = data_product.generate_ato_report(
            tenant_id="test_tenant",
            client_id="client_123",
            tax_year=2024
        )
        
        assert ato_report["tax_year"] == 2024
        assert ato_report["ato_compliant"] is True
        assert "capital_gains" in ato_report
        assert "dividend_income" in ato_report


class TestReportingAI:
    """Test AI agents for reporting"""
    
    def test_select_optimal_template(self):
        """Test AI template selection"""
        agent = get_report_generation_agent()
        
        result = agent.select_optimal_template(
            report_type=ReportType.PORTFOLIO_PERFORMANCE,
            client_data={"sophistication_level": "high"},
            historical_preferences=[]
        )
        
        assert "template_id" in result
        assert "confidence" in result
        assert result["confidence"] > 0.5
    
    def test_generate_insights(self):
        """Test AI insights generation"""
        agent = get_report_generation_agent()
        
        insights = agent.generate_insights(
            portfolio_data={"allocation": {"cash": 0.20}},
            performance_data={"total_return": 0.12, "volatility": 0.15},
            market_data={"benchmark_return": 0.10}
        )
        
        assert isinstance(insights, list)
        assert all("type" in i and "priority" in i for i in insights)
    
    def test_generate_tax_optimization_recommendations(self):
        """Test AI tax optimization"""
        agent = get_report_generation_agent()
        
        recommendations = agent.generate_tax_optimization_recommendations(
            portfolio_data={"holdings": [
                {"symbol": "AAPL", "days_held": 350, "unrealized_gain": 5000}
            ]},
            tax_data={},
            client_data={"marginal_tax_rate": 0.37}
        )
        
        assert isinstance(recommendations, list)


class TestReportingML:
    """Test ML models for reporting"""
    
    def test_performance_prediction(self):
        """Test performance prediction model"""
        model = get_performance_prediction_model()
        
        prediction = model.predict_performance(
            portfolio_data={"sharpe_ratio": 1.5, "beta": 1.1, "allocation": {}},
            historical_performance=[{"return": 0.01} for _ in range(30)],
            market_data={"market_return": 0.02, "market_volatility": 0.15}
        )
        
        assert "predicted_return" in prediction
        assert "confidence_interval" in prediction
        assert "confidence" in prediction
    
    def test_tax_loss_harvesting(self):
        """Test tax loss harvesting ML"""
        model = get_tax_optimization_model()
        
        opportunities = model.identify_tax_loss_harvesting_opportunities(
            holdings=[
                {"symbol": "AAPL", "unrealized_loss": -1500, "days_since_last_trade": 60}
            ],
            client_tax_data={"marginal_tax_rate": 0.37},
            market_data={}
        )
        
        assert isinstance(opportunities, list)
        if opportunities:
            assert "tax_savings" in opportunities[0]
            assert "score" in opportunities[0]
    
    def test_cgt_timing_optimization(self):
        """Test CGT timing optimization"""
        model = get_tax_optimization_model()
        
        recommendations = model.optimize_cgt_timing(
            holdings=[
                {"symbol": "AAPL", "days_held": 350, "unrealized_gain": 5000}
            ],
            client_tax_data={"marginal_tax_rate": 0.37}
        )
        
        assert isinstance(recommendations, list)
        if recommendations:
            assert "potential_saving" in recommendations[0]


class TestReportingMCP:
    """Test MCP tools for reporting"""
    
    def test_create_report_template_tool(self):
        """Test create report template MCP tool"""
        tools = get_reporting_tools()
        
        result = tools.create_report_template(
            tenant_id="test_tenant",
            name="Test Template",
            report_type="portfolio_performance",
            description="Test description",
            sections=["summary", "performance"],
            metrics=["total_return"],
            filters={},
            format_options={},
            created_by="user_123"
        )
        
        assert result["success"] is True
        assert "template_id" in result
    
    def test_schedule_report_tool(self):
        """Test schedule report MCP tool"""
        tools = get_reporting_tools()
        
        result = tools.schedule_report(
            tenant_id="test_tenant",
            client_id="client_123",
            template_id="template_456",
            frequency="weekly",
            delivery_channels=["email"],
            recipients=["client@example.com"],
            parameters={}
        )
        
        assert result["success"] is True
        assert "schedule_id" in result
    
    def test_generate_report_tool(self):
        """Test generate report MCP tool"""
        tools = get_reporting_tools()
        
        result = tools.generate_report(
            tenant_id="test_tenant",
            client_id="client_123",
            report_type="portfolio_performance",
            format="pdf"
        )
        
        assert result["success"] is True
        assert "report_id" in result
        assert "file_url" in result
    
    def test_generate_tax_report_tool(self):
        """Test generate tax report MCP tool"""
        tools = get_reporting_tools()
        
        result = tools.generate_tax_report(
            tenant_id="test_tenant",
            client_id="client_123",
            tax_year=2024,
            tax_report_type="capital_gains"
        )
        
        assert result["success"] is True
        assert "total_capital_gains" in result
    
    def test_export_formats(self):
        """Test multi-format export"""
        tools = get_reporting_tools()
        
        # PDF export
        pdf_result = tools.export_to_pdf("test_tenant", "report_123")
        assert pdf_result["success"] is True
        assert "page_count" in pdf_result
        
        # Excel export
        excel_result = tools.export_to_excel("test_tenant", "report_123")
        assert excel_result["success"] is True
        assert "sheet_count" in excel_result
        
        # CSV export
        csv_result = tools.export_to_csv("test_tenant", "report_123")
        assert csv_result["success"] is True
        assert "row_count" in csv_result


class TestReportingCompliance:
    """Test Australian compliance"""
    
    def test_ato_compliance(self):
        """Test ATO compliance"""
        data_product = get_reporting_data_product()
        
        assert data_product.ato_compliant is True
        assert data_product.data_retention_days >= 2555  # 7 years
    
    def test_asic_compliance(self):
        """Test ASIC compliance"""
        data_product = get_reporting_data_product()
        
        assert data_product.asic_compliant is True
    
    def test_privacy_act_compliance(self):
        """Test Privacy Act compliance"""
        data_product = get_reporting_data_product()
        
        assert data_product.privacy_act_compliant is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

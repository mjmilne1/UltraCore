"""
Compliance Integration Tests
Tests for Kafka-first event sourcing, data mesh, AI agents, ML models, and MCP tools
"""

import pytest
from datetime import datetime
from uuid import uuid4

from ultracore.compliance.events import (
    CustomerIdentifiedEvent,
    ComplaintSubmittedEvent,
    ComplianceTopic
)
from ultracore.compliance.aggregates import CustomerAggregate, ComplaintAggregate
from ultracore.agentic_ai.agents.compliance import AMLMonitoringAgent
from ultracore.ml.compliance import FraudDetectionModel
from ultracore.mcp.compliance_tools import get_compliance_tools
from ultracore.datamesh.compliance_mesh import get_compliance_data_product


class TestEventSourcing:
    """Test event sourcing with Kafka"""
    
    def test_customer_aggregate_identify(self):
        """Test customer identification creates event"""
        customer_id = str(uuid4())
        customer = CustomerAggregate(customer_id, "tenant1")
        
        customer.identify(
            user_id="user1",
            full_name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            residential_address="123 Main St",
            identification_type="passport",
            identification_number="P1234567",
            risk_level="low"
        )
        
        assert len(customer.uncommitted_events) == 1
        event = customer.uncommitted_events[0]
        assert isinstance(event, CustomerIdentifiedEvent)
        assert event.aggregate_id == customer_id
        assert event.event_data["full_name"] == "John Doe"
    
    def test_customer_aggregate_verify(self):
        """Test customer verification creates event"""
        customer_id = str(uuid4())
        customer = CustomerAggregate(customer_id, "tenant1")
        
        customer.verify(
            user_id="user1",
            verification_method="document_check",
            pep_check_result=True,
            sanctions_check_result=True
        )
        
        assert len(customer.uncommitted_events) == 1
        assert customer.is_verified == False  # Not applied yet
    
    def test_complaint_aggregate_submit(self):
        """Test complaint submission creates event"""
        complaint_id = str(uuid4())
        complaint = ComplaintAggregate(complaint_id, "tenant1")
        
        complaint.submit(
            user_id="user1",
            category="service",
            subject="Poor service",
            description="Service was below expectations",
            priority="high"
        )
        
        assert len(complaint.uncommitted_events) == 1
        event = complaint.uncommitted_events[0]
        assert isinstance(event, ComplaintSubmittedEvent)
        assert complaint.status == "submitted"
        assert complaint.complaint_reference is not None


class TestAIAgents:
    """Test AI agents for compliance automation"""
    
    def test_aml_agent_monitor_transaction(self):
        """Test AML agent monitors transaction"""
        agent = AMLMonitoringAgent()
        
        result = agent.monitor_transaction(
            transaction_id="txn123",
            user_id="user1",
            transaction_type="withdrawal",
            amount=15000.00,
            currency="AUD",
            user_history=[]
        )
        
        assert "risk_score" in result
        assert "is_suspicious" in result
        assert "recommendation" in result
        assert result["risk_score"] >= 0
    
    def test_aml_agent_large_transaction_detection(self):
        """Test AML agent detects large transactions"""
        agent = AMLMonitoringAgent()
        
        result = agent.monitor_transaction(
            transaction_id="txn123",
            user_id="user1",
            transaction_type="withdrawal",
            amount=60000.00,  # Very large
            currency="AUD",
            user_history=[]
        )
        
        assert result["risk_score"] >= 50
        assert "large_transaction" in result["triggered_rules"] or \
               "very_large_transaction" in result["triggered_rules"]
    
    def test_aml_agent_customer_risk_assessment(self):
        """Test AML agent assesses customer risk"""
        agent = AMLMonitoringAgent()
        
        customer_data = {
            "country": "AU",
            "is_pep": False,
            "on_sanctions_list": False
        }
        
        result = agent.assess_customer_risk(
            customer_data=customer_data,
            transaction_history=[]
        )
        
        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high", "very_high"]


class TestMLModels:
    """Test ML models for fraud detection"""
    
    def test_fraud_model_feature_extraction(self):
        """Test fraud model extracts features"""
        model = FraudDetectionModel()
        
        transaction = {
            "id": "txn123",
            "amount": 10000.00,
            "type": "withdrawal",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        features = model.extract_features(
            transaction=transaction,
            user_history=[],
            customer_risk_score=30
        )
        
        assert len(features) == len(model.feature_names)
        assert features[0] == 10000.00  # amount
    
    def test_fraud_model_prediction(self):
        """Test fraud model predicts fraud probability"""
        model = FraudDetectionModel()
        
        transaction = {
            "id": "txn123",
            "amount": 50000.00,
            "type": "withdrawal",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = model.predict_fraud_probability(
            transaction=transaction,
            user_history=[],
            customer_risk_score=50
        )
        
        assert "fraud_probability" in result
        assert 0 <= result["fraud_probability"] <= 1
        assert result["risk_level"] in ["low", "medium", "high", "very_high"]


class TestMCPTools:
    """Test MCP tools for compliance operations"""
    
    def test_mcp_check_aml_status(self):
        """Test MCP check AML status tool"""
        tools = get_compliance_tools()
        
        result = tools.check_aml_status(
            user_id="user1",
            tenant_id="tenant1"
        )
        
        assert "aml_status" in result
        assert "risk_level" in result
    
    def test_mcp_monitor_transaction(self):
        """Test MCP monitor transaction tool"""
        tools = get_compliance_tools()
        
        result = tools.monitor_transaction(
            transaction_id="txn123",
            user_id="user1",
            tenant_id="tenant1",
            transaction_type="withdrawal",
            amount=50000.00
        )
        
        assert "aml_monitoring" in result
        assert "fraud_detection" in result
        assert "overall_risk" in result
    
    def test_mcp_file_smr(self):
        """Test MCP file SMR tool"""
        tools = get_compliance_tools()
        
        result = tools.file_smr(
            user_id="user1",
            tenant_id="tenant1",
            transaction_ids=["txn123"],
            reason="Suspicious activity detected"
        )
        
        assert "smr_reference" in result
        assert result["smr_reference"].startswith("SMR-")
        assert result["filed_with_austrac"] == True
    
    def test_mcp_submit_complaint(self):
        """Test MCP submit complaint tool"""
        tools = get_compliance_tools()
        
        result = tools.submit_complaint(
            user_id="user1",
            tenant_id="tenant1",
            category="service",
            subject="Poor service",
            description="Service was below expectations"
        )
        
        assert "complaint_id" in result
        assert "complaint_reference" in result
        assert result["status"] == "submitted"


class TestDataMesh:
    """Test data mesh compliance domain"""
    
    def test_get_compliance_data_product(self):
        """Test get compliance data product"""
        data_product = get_compliance_data_product()
        
        assert data_product.domain == "compliance"
        assert data_product.owner == "compliance_team"
        assert data_product.metadata["sla"]["availability"] == 0.999
    
    def test_get_aml_data(self):
        """Test get AML data from data product"""
        data_product = get_compliance_data_product()
        
        result = data_product.get_aml_data(tenant_id="tenant1")
        
        assert result["domain"] == "aml"
        assert "data" in result
        assert "metadata" in result
    
    def test_get_compliance_dashboard(self):
        """Test get compliance dashboard"""
        data_product = get_compliance_data_product()
        
        dashboard = data_product.get_compliance_dashboard(tenant_id="tenant1")
        
        assert "dashboard" in dashboard
        assert "aml" in dashboard["dashboard"]
        assert "disputes" in dashboard["dashboard"]
        assert "compliance_score" in dashboard
    
    def test_validate_data_quality(self):
        """Test data quality validation"""
        data_product = get_compliance_data_product()
        
        validation = data_product.validate_data_quality()
        
        assert "quality_checks" in validation
        assert validation["quality_checks"]["completeness"]["passed"] == True
        assert validation["sla_compliance"]["availability"] == True


class TestIntegration:
    """End-to-end integration tests"""
    
    def test_full_aml_workflow(self):
        """Test complete AML workflow: identify → verify → monitor → SMR"""
        # 1. Create customer
        customer_id = str(uuid4())
        customer = CustomerAggregate(customer_id, "tenant1")
        
        # 2. Identify customer
        customer.identify(
            user_id="user1",
            full_name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            residential_address="123 Main St",
            identification_type="passport",
            identification_number="P1234567",
            risk_level="low"
        )
        
        # 3. Verify customer
        customer.verify(
            user_id="user1",
            verification_method="document_check",
            pep_check_result=True,
            sanctions_check_result=True
        )
        
        # 4. Monitor transaction
        tools = get_compliance_tools()
        monitoring_result = tools.monitor_transaction(
            transaction_id="txn123",
            user_id="user1",
            tenant_id="tenant1",
            transaction_type="withdrawal",
            amount=100000.00  # Very large
        )
        
        # 5. File SMR if needed
        if monitoring_result["action_required"]:
            smr_result = tools.file_smr(
                user_id="user1",
                tenant_id="tenant1",
                transaction_ids=["txn123"],
                reason="Large suspicious transaction"
            )
            assert smr_result["filed_with_austrac"] == True
    
    def test_full_dispute_workflow(self):
        """Test complete dispute workflow: submit → acknowledge → resolve"""
        tools = get_compliance_tools()
        
        # 1. Submit complaint
        submit_result = tools.submit_complaint(
            user_id="user1",
            tenant_id="tenant1",
            category="service",
            subject="Poor service",
            description="Service was below expectations",
            priority="high"
        )
        
        complaint_id = submit_result["complaint_id"]
        
        # 2. Acknowledge complaint
        ack_result = tools.acknowledge_complaint(
            complaint_id=complaint_id,
            tenant_id="tenant1",
            user_id="compliance_officer"
        )
        
        assert ack_result["status"] == "acknowledged"
        
        # 3. Resolve complaint
        resolve_result = tools.resolve_complaint(
            complaint_id=complaint_id,
            tenant_id="tenant1",
            user_id="compliance_officer",
            resolution="Issue resolved with compensation",
            compensation_amount=500.00
        )
        
        assert resolve_result["status"] == "resolved"
        assert resolve_result["compensation_amount"] == 500.00


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Audit Trail Integration Tests

Tests for comprehensive audit trail system.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from ultracore.audit.audit_trail import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditTrail,
    ComplianceReporter
)


class TestAuditEvent:
    """Test audit event"""
    
    def test_create_audit_event(self):
        """Test creating audit event"""
        event = AuditEvent(
            event_id="evt_123",
            event_type=AuditEventType.LOGIN,
            timestamp=datetime.utcnow(),
            tenant_id="tenant_1",
            user_id="user_123",
            severity=AuditSeverity.INFO,
            description="User logged in",
            result="success"
        )
        
        assert event.event_id == "evt_123"
        assert event.event_type == AuditEventType.LOGIN
        assert event.tenant_id == "tenant_1"
        assert event.user_id == "user_123"
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        event = AuditEvent(
            event_id="evt_123",
            event_type=AuditEventType.LOGIN,
            timestamp=datetime.utcnow(),
            tenant_id="tenant_1",
            description="Test event"
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt_123"
        assert data["event_type"] == "login"
        assert data["severity"] == "info"
        assert isinstance(data["timestamp"], str)
    
    def test_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "event_id": "evt_123",
            "event_type": "login",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": "tenant_1",
            "severity": "info",
            "description": "Test event"
        }
        
        event = AuditEvent.from_dict(data)
        
        assert event.event_id == "evt_123"
        assert event.event_type == AuditEventType.LOGIN
        assert isinstance(event.timestamp, datetime)


class TestAuditTrail:
    """Test audit trail"""
    
    @pytest.fixture
    def mock_event_producer(self):
        """Create mock event producer"""
        producer = AsyncMock()
        producer.publish_audit_event = AsyncMock()
        return producer
    
    @pytest.fixture
    def mock_cache(self):
        """Create mock cache manager"""
        cache = AsyncMock()
        cache.list_push = AsyncMock()
        cache.list_range = AsyncMock(return_value=[])
        return cache
    
    @pytest.fixture
    def audit_trail(self, mock_event_producer, mock_cache):
        """Create audit trail"""
        return AuditTrail(
            event_producer=mock_event_producer,
            cache_manager=mock_cache
        )
    
    @pytest.mark.asyncio
    async def test_log_event(self, audit_trail, mock_event_producer, mock_cache):
        """Test logging audit event"""
        event = await audit_trail.log_event(
            event_type=AuditEventType.LOGIN,
            tenant_id="tenant_1",
            user_id="user_123",
            description="User logged in",
            result="success",
            ip_address="192.168.1.1"
        )
        
        assert event.event_type == AuditEventType.LOGIN
        assert event.tenant_id == "tenant_1"
        assert event.user_id == "user_123"
        assert event.ip_address == "192.168.1.1"
        
        # Verify event was published
        mock_event_producer.publish_audit_event.assert_called_once()
        
        # Verify event was cached
        mock_cache.list_push.assert_called()
    
    @pytest.mark.asyncio
    async def test_log_login(self, audit_trail):
        """Test logging login"""
        event = await audit_trail.log_login(
            tenant_id="tenant_1",
            user_id="user_123",
            success=True,
            ip_address="192.168.1.1"
        )
        
        assert event.event_type == AuditEventType.LOGIN
        assert event.result == "success"
        assert event.severity == AuditSeverity.INFO
        assert "authentication" in event.compliance_tags
    
    @pytest.mark.asyncio
    async def test_log_login_failed(self, audit_trail):
        """Test logging failed login"""
        event = await audit_trail.log_login(
            tenant_id="tenant_1",
            user_id="user_123",
            success=False,
            ip_address="192.168.1.1"
        )
        
        assert event.event_type == AuditEventType.LOGIN_FAILED
        assert event.result == "failure"
        assert event.severity == AuditSeverity.WARNING
    
    @pytest.mark.asyncio
    async def test_log_transaction(self, audit_trail):
        """Test logging transaction"""
        event = await audit_trail.log_transaction(
            tenant_id="tenant_1",
            user_id="user_123",
            transaction_type="deposit",
            transaction_id="txn_123",
            amount=1000.0,
            account_id="acc_456"
        )
        
        assert event.event_type == AuditEventType.TRANSACTION_CREATED
        assert event.resource_type == "transaction"
        assert event.resource_id == "txn_123"
        assert event.metadata["amount"] == 1000.0
        assert "financial" in event.compliance_tags
    
    @pytest.mark.asyncio
    async def test_log_fraud_detection(self, audit_trail):
        """Test logging fraud detection"""
        event = await audit_trail.log_fraud_detection(
            tenant_id="tenant_1",
            user_id="user_123",
            transaction_id="txn_123",
            fraud_score=0.85,
            decision="review",
            risk_factors=["new_device", "unusual_amount"]
        )
        
        assert event.event_type == AuditEventType.FRAUD_DETECTED
        assert event.severity == AuditSeverity.WARNING
        assert event.metadata["fraud_score"] == 0.85
        assert "fraud" in event.compliance_tags
    
    @pytest.mark.asyncio
    async def test_log_access_control(self, audit_trail):
        """Test logging access control"""
        # Access granted
        event = await audit_trail.log_access_control(
            tenant_id="tenant_1",
            user_id="user_123",
            resource_type="account",
            resource_id="acc_456",
            action="read",
            granted=True
        )
        
        assert event.event_type == AuditEventType.PERMISSION_GRANTED
        assert event.result == "granted"
        assert event.severity == AuditSeverity.INFO
        
        # Access denied
        event = await audit_trail.log_access_control(
            tenant_id="tenant_1",
            user_id="user_123",
            resource_type="account",
            resource_id="acc_456",
            action="delete",
            granted=False,
            reason="insufficient_permissions"
        )
        
        assert event.event_type == AuditEventType.PERMISSION_DENIED
        assert event.result == "denied"
        assert event.severity == AuditSeverity.WARNING
    
    @pytest.mark.asyncio
    async def test_log_data_access(self, audit_trail):
        """Test logging data access"""
        # Regular data access
        event = await audit_trail.log_data_access(
            tenant_id="tenant_1",
            user_id="user_123",
            resource_type="account",
            resource_id="acc_456",
            action="read",
            pii_accessed=False
        )
        
        assert event.event_type == AuditEventType.DATA_ACCESSED
        assert event.severity == AuditSeverity.INFO
        assert "data_access" in event.compliance_tags
        
        # PII access
        event = await audit_trail.log_data_access(
            tenant_id="tenant_1",
            user_id="user_123",
            resource_type="customer",
            resource_id="cust_789",
            action="read",
            pii_accessed=True
        )
        
        assert event.severity == AuditSeverity.WARNING
        assert "privacy" in event.compliance_tags
    
    @pytest.mark.asyncio
    async def test_log_ml_prediction(self, audit_trail):
        """Test logging ML prediction"""
        event = await audit_trail.log_ml_prediction(
            tenant_id="tenant_1",
            model_name="fraud_detector",
            prediction="fraud",
            confidence=0.92,
            user_id="user_123"
        )
        
        assert event.event_type == AuditEventType.AI_PREDICTION
        assert event.resource_type == "ml_model"
        assert event.resource_id == "fraud_detector"
        assert event.metadata["confidence"] == 0.92
        assert "ml" in event.compliance_tags
    
    @pytest.mark.asyncio
    async def test_log_compliance_check(self, audit_trail):
        """Test logging compliance check"""
        # Passed
        event = await audit_trail.log_compliance_check(
            tenant_id="tenant_1",
            check_type="kyc",
            passed=True,
            details={"verified": True}
        )
        
        assert event.event_type == AuditEventType.COMPLIANCE_CHECK
        assert event.result == "passed"
        assert event.severity == AuditSeverity.INFO
        
        # Failed
        event = await audit_trail.log_compliance_check(
            tenant_id="tenant_1",
            check_type="aml",
            passed=False,
            details={"reason": "high_risk_country"}
        )
        
        assert event.event_type == AuditEventType.COMPLIANCE_VIOLATION
        assert event.result == "failed"
        assert event.severity == AuditSeverity.ERROR
    
    @pytest.mark.asyncio
    async def test_get_recent_events(self, audit_trail, mock_cache):
        """Test getting recent events"""
        # Mock cached events
        mock_cache.list_range.return_value = [
            {
                "event_id": "evt_1",
                "event_type": "login",
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": "tenant_1",
                "severity": "info",
                "description": "Login"
            }
        ]
        
        events = await audit_trail.get_recent_events("tenant_1")
        
        assert len(events) == 1
        assert events[0].event_id == "evt_1"


class TestComplianceReporter:
    """Test compliance reporter"""
    
    @pytest.fixture
    def audit_trail(self):
        """Create audit trail"""
        return AuditTrail()
    
    @pytest.fixture
    def reporter(self, audit_trail):
        """Create compliance reporter"""
        return ComplianceReporter(audit_trail)
    
    @pytest.mark.asyncio
    async def test_generate_access_report(self, reporter):
        """Test generating access report"""
        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)
        
        report = await reporter.generate_access_report(
            "tenant_1",
            start_date,
            end_date
        )
        
        assert report["report_type"] == "access_control"
        assert report["tenant_id"] == "tenant_1"
        assert "summary" in report
    
    @pytest.mark.asyncio
    async def test_generate_transaction_report(self, reporter):
        """Test generating transaction report"""
        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)
        
        report = await reporter.generate_transaction_report(
            "tenant_1",
            start_date,
            end_date
        )
        
        assert report["report_type"] == "transactions"
        assert "summary" in report
    
    @pytest.mark.asyncio
    async def test_generate_security_report(self, reporter):
        """Test generating security report"""
        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)
        
        report = await reporter.generate_security_report(
            "tenant_1",
            start_date,
            end_date
        )
        
        assert report["report_type"] == "security"
        assert "summary" in report
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, reporter):
        """Test generating compliance report"""
        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)
        
        report = await reporter.generate_compliance_report(
            "tenant_1",
            start_date,
            end_date,
            compliance_type="all"
        )
        
        assert report["report_type"] == "compliance"
        assert "checks" in report
        assert "violations" in report

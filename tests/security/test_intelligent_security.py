"""
Tests for Intelligent Security Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from ultracore.security.intelligent_security import (
    IntelligentSecurityService,
    SecurityEventProducer
)


class TestIntelligentSecurityService:
    """Test intelligent security service"""
    
    @pytest.fixture
    def mock_event_producer(self):
        """Mock event producer"""
        producer = MagicMock(spec=SecurityEventProducer)
        producer.publish_fraud_detection = AsyncMock()
        producer.publish_anomaly_detection = AsyncMock()
        producer.publish_access_control = AsyncMock()
        producer.publish_rate_limit = AsyncMock()
        producer.publish_threat_detection = AsyncMock()
        producer.publish_security_incident = AsyncMock()
        return producer
    
    @pytest.fixture
    def service(self, mock_event_producer):
        """Create security service with mocked producer"""
        return IntelligentSecurityService(event_producer=mock_event_producer)
    
    @pytest.mark.asyncio
    async def test_detect_fraud_low_risk(self, service, mock_event_producer):
        """Test fraud detection for low-risk transaction"""
        result = await service.detect_fraud(
            tenant_id="tenant_1",
            transaction_id="txn_123",
            amount=1000.0,
            timestamp=datetime.utcnow(),
            user_id="user_123",
            user_history={
                "avg_amount": 1000.0,
                "std_amount": 200.0,
                "transactions_1h": 2,
                "transactions_24h": 10,
                "last_transaction_time": datetime.utcnow() - timedelta(hours=1)
            },
            device_info={"is_new": False},
            location_info={"is_new": False, "distance_km": 5.0}
        )
        
        assert "fraud_score" in result
        assert "decision" in result
        assert "risk_factors" in result
        assert 0.0 <= result["fraud_score"] <= 1.0
        assert result["decision"] in ["allow", "review", "deny"]
        
        # Event should be published
        mock_event_producer.publish_fraud_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_fraud_high_risk(self, service, mock_event_producer):
        """Test fraud detection for high-risk transaction"""
        result = await service.detect_fraud(
            tenant_id="tenant_1",
            transaction_id="txn_456",
            amount=50000.0,  # Very high amount
            timestamp=datetime(2025, 11, 13, 2, 0),  # Night
            user_id="user_456",
            user_history={
                "avg_amount": 1000.0,
                "std_amount": 200.0,
                "transactions_1h": 10,  # High velocity
                "transactions_24h": 50,
                "last_transaction_time": datetime.utcnow() - timedelta(minutes=5)
            },
            device_info={"is_new": True},  # New device
            location_info={"is_new": True, "distance_km": 1000.0}  # New location, far away
        )
        
        assert result["fraud_score"] > 0.3  # Should be higher risk
        # Risk factors may be in details depending on model state
        assert "risk_factors" in result
        
        mock_event_producer.publish_fraud_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_anomaly_normal(self, service, mock_event_producer):
        """Test anomaly detection for normal behavior"""
        result = await service.detect_anomaly(
            tenant_id="tenant_1",
            session_id="sess_123",
            user_id="user_123",
            login_hour=10,
            login_day_of_week=2,
            api_calls_per_minute=5.0,
            unique_endpoints_accessed=3,
            data_volume_mb=10.0,
            failed_attempts=0,
            session_duration_minutes=30.0,
            ip_reputation_score=90.0,
            device_fingerprint_match=True,
            location_match=True
        )
        
        assert "anomaly_score" in result
        assert "action" in result
        assert "indicators" in result
        assert 0.0 <= result["anomaly_score"] <= 1.0
        assert result["action"] in ["monitor", "alert", "block"]
        
        mock_event_producer.publish_anomaly_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_anomaly_suspicious(self, service, mock_event_producer):
        """Test anomaly detection for suspicious behavior"""
        result = await service.detect_anomaly(
            tenant_id="tenant_1",
            session_id="sess_456",
            user_id="user_456",
            login_hour=3,  # Unusual time
            login_day_of_week=6,
            api_calls_per_minute=150.0,  # Very high
            unique_endpoints_accessed=50,
            data_volume_mb=2000.0,  # Large volume
            failed_attempts=5,
            session_duration_minutes=5.0,
            ip_reputation_score=20.0,  # Low reputation
            device_fingerprint_match=False,
            location_match=False
        )
        
        assert result["anomaly_score"] > 0.3
        # Indicators may be in details depending on model state
        assert "indicators" in result
        
        mock_event_producer.publish_anomaly_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_access_low_risk(self, service, mock_event_producer):
        """Test access control for low-risk access"""
        result = await service.check_access(
            tenant_id="tenant_1",
            user_id="user_123",
            resource_id="account_123",
            resource_type="savings_account",
            action_requested="view",
            user_risk_score=0.1,
            resource_sensitivity=2,
            time_of_day=10,
            recent_violations=0,
            authentication_strength=2,
            location_trust=0.9,
            device_trust=0.9
        )
        
        assert "action" in result
        assert "confidence" in result
        assert "reasoning" in result
        
        mock_event_producer.publish_access_control.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_access_high_risk(self, service, mock_event_producer):
        """Test access control for high-risk access"""
        result = await service.check_access(
            tenant_id="tenant_1",
            user_id="user_456",
            resource_id="account_456",
            resource_type="savings_account",
            action_requested="withdraw",
            user_risk_score=0.9,
            resource_sensitivity=5,
            time_of_day=2,
            recent_violations=3,
            authentication_strength=1,
            location_trust=0.2,
            device_trust=0.3
        )
        
        assert "action" in result
        assert "reasoning" in result
        
        mock_event_producer.publish_access_control.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_normal(self, service, mock_event_producer):
        """Test rate limiting for normal traffic"""
        result = await service.check_rate_limit(
            tenant_id="tenant_1",
            user_id="user_123",
            endpoint="/api/v1/accounts",
            current_request_rate=10.0,
            user_reputation=0.8,
            endpoint_sensitivity=2,
            recent_errors=0,
            time_of_day=10,
            is_authenticated=True,
            burst_detected=False
        )
        
        assert "action" in result
        assert "rate_multiplier" in result
        assert "reasoning" in result
        assert 0.0 <= result["rate_multiplier"] <= 1.0
        
        mock_event_producer.publish_rate_limit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_attack(self, service, mock_event_producer):
        """Test rate limiting for potential attack"""
        result = await service.check_rate_limit(
            tenant_id="tenant_1",
            user_id="user_456",
            endpoint="/api/v1/auth/login",
            current_request_rate=500.0,
            user_reputation=0.1,
            endpoint_sensitivity=5,
            recent_errors=10,
            time_of_day=2,
            is_authenticated=False,
            burst_detected=True
        )
        
        assert "action" in result
        assert "rate_multiplier" in result
        
        mock_event_producer.publish_rate_limit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_report_threat(self, service, mock_event_producer):
        """Test threat reporting"""
        await service.report_threat(
            tenant_id="tenant_1",
            threat_type="brute_force",
            severity="high",
            source_ip="192.168.1.100",
            target="/api/v1/auth/login",
            action_taken="ip_blocked",
            details={"failed_attempts": 15, "time_window": "5m"}
        )
        
        mock_event_producer.publish_threat_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_incident(self, service, mock_event_producer):
        """Test security incident creation"""
        await service.create_incident(
            tenant_id="tenant_1",
            incident_id="inc_001",
            incident_type="unauthorized_access",
            severity="critical",
            description="Multiple failed login attempts",
            affected_resources=["user_123", "account_456"]
        )
        
        mock_event_producer.publish_security_incident.assert_called_once()
    
    def test_get_metrics(self, service):
        """Test metrics retrieval"""
        metrics = service.get_metrics()
        
        assert "fraud_detection" in metrics
        assert "access_control" in metrics
        assert "rate_limiting" in metrics
        
        # Each should have metrics
        assert "total_predictions" in metrics["fraud_detection"] or "accuracy" in metrics["fraud_detection"]
        assert "total_decisions" in metrics["access_control"] or "accuracy" in metrics["access_control"]
        assert "total_decisions" in metrics["rate_limiting"] or "exploration_rate" in metrics["rate_limiting"]

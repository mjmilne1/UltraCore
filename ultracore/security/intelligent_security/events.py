"""
Intelligent Security Events

Event definitions for security event sourcing.
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class SecurityEvent(BaseModel):
    """Base security event"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str
    user_id: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class FraudDetectionEvent(SecurityEvent):
    """Fraud detection event"""
    event_type: str = "security.fraud_detection"
    transaction_id: str
    fraud_score: float
    risk_factors: list[str]
    decision: str  # allow, deny, review
    amount: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123",
                "fraud_score": 0.85,
                "risk_factors": ["high_amount_deviation", "new_device"],
                "decision": "review",
                "amount": 15000.0,
                "tenant_id": "tenant_1",
                "user_id": "user_123"
            }
        }


class AnomalyDetectionEvent(SecurityEvent):
    """Behavioral anomaly detection event"""
    event_type: str = "security.anomaly_detection"
    session_id: str
    anomaly_score: float
    anomaly_indicators: list[str]
    action_taken: str  # monitor, alert, block
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_456",
                "anomaly_score": 0.72,
                "anomaly_indicators": ["high_api_rate", "device_mismatch"],
                "action_taken": "alert",
                "tenant_id": "tenant_1",
                "user_id": "user_456"
            }
        }


class AccessControlEvent(SecurityEvent):
    """Access control decision event"""
    event_type: str = "security.access_control"
    resource_id: str
    resource_type: str
    action_requested: str
    decision: str  # allow, deny, allow_with_mfa
    risk_score: float
    reasoning: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "account_789",
                "resource_type": "savings_account",
                "action_requested": "withdraw",
                "decision": "allow_with_mfa",
                "risk_score": 0.45,
                "reasoning": "High value transaction requires MFA",
                "tenant_id": "tenant_1",
                "user_id": "user_789"
            }
        }


class RateLimitEvent(SecurityEvent):
    """Rate limiting event"""
    event_type: str = "security.rate_limit"
    endpoint: str
    request_rate: float
    action: str  # allow, throttle, block
    rate_multiplier: float
    reasoning: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/v1/accounts",
                "request_rate": 150.5,
                "action": "throttle_50",
                "rate_multiplier": 0.5,
                "reasoning": "High request rate detected",
                "tenant_id": "tenant_1",
                "user_id": "user_999"
            }
        }


class ThreatDetectionEvent(SecurityEvent):
    """Threat detection event"""
    event_type: str = "security.threat_detection"
    threat_type: str  # brute_force, sql_injection, xss, ddos
    severity: str  # low, medium, high, critical
    source_ip: str
    target: str
    action_taken: str
    details: Dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "threat_type": "brute_force",
                "severity": "high",
                "source_ip": "192.168.1.100",
                "target": "/api/v1/auth/login",
                "action_taken": "ip_blocked",
                "details": {"failed_attempts": 15, "time_window": "5m"},
                "tenant_id": "tenant_1"
            }
        }


class SecurityIncidentEvent(SecurityEvent):
    """Security incident event"""
    event_type: str = "security.incident"
    incident_id: str
    incident_type: str
    severity: str
    status: str  # open, investigating, resolved, closed
    description: str
    affected_resources: list[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc_001",
                "incident_type": "unauthorized_access",
                "severity": "critical",
                "status": "investigating",
                "description": "Multiple failed login attempts followed by successful login from new location",
                "affected_resources": ["user_123", "account_456"],
                "tenant_id": "tenant_1"
            }
        }


class ModelUpdateEvent(SecurityEvent):
    """ML/RL model update event"""
    event_type: str = "security.model_update"
    model_name: str
    model_version: str
    update_type: str  # retrain, parameter_update, deployment
    metrics: Dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "fraud_detection",
                "model_version": "v2.1",
                "update_type": "retrain",
                "metrics": {
                    "accuracy": 0.985,
                    "precision": 0.92,
                    "recall": 0.88
                },
                "tenant_id": "tenant_1"
            }
        }

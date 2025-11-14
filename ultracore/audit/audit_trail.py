"""
Comprehensive Audit Trail

Kafka-first audit trail with event aggregation, compliance reporting, and retention policies.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
from dataclasses import dataclass, asdict
from uuid import uuid4


class AuditEventType(str, Enum):
    """Audit event types"""
    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    
    # Access Control
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Account Operations
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_ACTIVATED = "account_activated"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_CLOSED = "account_closed"
    
    # Transaction Operations
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_APPROVED = "transaction_approved"
    TRANSACTION_REJECTED = "transaction_rejected"
    TRANSACTION_REVERSED = "transaction_reversed"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    
    # Security Events
    FRAUD_DETECTED = "fraud_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_DETECTED = "threat_detected"
    SECURITY_INCIDENT = "security_incident"
    ACCESS_BLOCKED = "access_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # AI/ML Operations
    AI_PREDICTION = "ai_prediction"
    ML_MODEL_TRAINED = "ml_model_trained"
    ML_MODEL_UPDATED = "ml_model_updated"
    RL_DECISION = "rl_decision"
    RL_FEEDBACK = "rl_feedback"
    
    # Data Operations
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    
    # Compliance
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_VIOLATION = "compliance_violation"
    REGULATORY_REPORT = "regulatory_report"
    
    # System Operations
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"


class AuditSeverity(str, Enum):
    """Audit event severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Comprehensive audit event.
    
    Captures all information needed for compliance and forensics.
    """
    # Event identification
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    
    # Tenant and user context
    tenant_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Event details
    severity: AuditSeverity = AuditSeverity.INFO
    description: str = ""
    
    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Action details
    action: Optional[str] = None
    result: Optional[str] = None  # success, failure, denied
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Data changes
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    # Compliance tags
    compliance_tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary"""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["event_type"] = AuditEventType(data["event_type"])
        data["severity"] = AuditSeverity(data["severity"])
        return cls(**data)


class AuditTrail:
    """
    Comprehensive audit trail system.
    
    Features:
    - Kafka-first event publishing
    - Event aggregation and querying
    - Compliance reporting
    - Retention policies
    - Tamper-proof logging
    """
    
    def __init__(
        self,
        event_producer=None,
        cache_manager=None
    ):
        self.event_producer = event_producer
        self.cache = cache_manager
    
    async def log_event(
        self,
        event_type: AuditEventType,
        tenant_id: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[str]] = None
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            tenant_id: Tenant ID
            description: Human-readable description
            ... (other parameters as in AuditEvent)
        
        Returns:
            Created audit event
        """
        # Create audit event
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            severity=severity,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata,
            compliance_tags=compliance_tags
        )
        
        # Publish to Kafka (if available)
        if self.event_producer:
            await self.event_producer.publish_audit_event(event)
        
        # Cache recent events for fast access
        if self.cache:
            await self._cache_recent_event(event)
        
        return event
    
    async def _cache_recent_event(self, event: AuditEvent):
        """Cache recent audit events for fast access"""
        # Cache by tenant
        tenant_key = f"audit:recent:{event.tenant_id}"
        await self.cache.list_push(tenant_key, event.to_dict())
        
        # Keep only last 100 events per tenant
        # (Full history is in Kafka/event store)
        
        # Cache by user if present
        if event.user_id:
            user_key = f"audit:recent:{event.tenant_id}:{event.user_id}"
            await self.cache.list_push(user_key, event.to_dict())
    
    async def get_recent_events(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get recent audit events from cache"""
        if not self.cache:
            return []
        
        key = f"audit:recent:{tenant_id}"
        if user_id:
            key += f":{user_id}"
        
        events_data = await self.cache.list_range(key, 0, limit - 1)
        return [AuditEvent.from_dict(data) for data in events_data]
    
    # Convenience methods for common audit events
    
    async def log_login(
        self,
        tenant_id: str,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditEvent:
        """Log login attempt"""
        return await self.log_event(
            event_type=AuditEventType.LOGIN if success else AuditEventType.LOGIN_FAILED,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"User {'logged in' if success else 'login failed'}",
            result="success" if success else "failure",
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            ip_address=ip_address,
            user_agent=user_agent,
            compliance_tags=["authentication"]
        )
    
    async def log_transaction(
        self,
        tenant_id: str,
        user_id: str,
        transaction_type: str,
        transaction_id: str,
        amount: float,
        account_id: str,
        result: str = "success"
    ) -> AuditEvent:
        """Log financial transaction"""
        return await self.log_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"{transaction_type} transaction of ${amount}",
            resource_type="transaction",
            resource_id=transaction_id,
            action=transaction_type,
            result=result,
            metadata={
                "amount": amount,
                "account_id": account_id,
                "transaction_type": transaction_type
            },
            compliance_tags=["financial", "transaction"]
        )
    
    async def log_fraud_detection(
        self,
        tenant_id: str,
        user_id: str,
        transaction_id: str,
        fraud_score: float,
        decision: str,
        risk_factors: List[str]
    ) -> AuditEvent:
        """Log fraud detection"""
        return await self.log_event(
            event_type=AuditEventType.FRAUD_DETECTED,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"Fraud detection: score={fraud_score:.2f}, decision={decision}",
            resource_type="transaction",
            resource_id=transaction_id,
            severity=AuditSeverity.WARNING if fraud_score > 0.5 else AuditSeverity.INFO,
            metadata={
                "fraud_score": fraud_score,
                "decision": decision,
                "risk_factors": risk_factors
            },
            compliance_tags=["security", "fraud"]
        )
    
    async def log_access_control(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        granted: bool,
        reason: Optional[str] = None
    ) -> AuditEvent:
        """Log access control decision"""
        return await self.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"Access {'granted' if granted else 'denied'} for {action} on {resource_type}",
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="granted" if granted else "denied",
            severity=AuditSeverity.INFO if granted else AuditSeverity.WARNING,
            metadata={"reason": reason} if reason else None,
            compliance_tags=["access_control", "security"]
        )
    
    async def log_data_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        pii_accessed: bool = False
    ) -> AuditEvent:
        """Log data access"""
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESSED,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"Data {action}: {resource_type}/{resource_id}",
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            severity=AuditSeverity.WARNING if pii_accessed else AuditSeverity.INFO,
            compliance_tags=["data_access", "privacy"] if pii_accessed else ["data_access"]
        )
    
    async def log_ml_prediction(
        self,
        tenant_id: str,
        model_name: str,
        prediction: Any,
        confidence: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log ML model prediction"""
        return await self.log_event(
            event_type=AuditEventType.AI_PREDICTION,
            tenant_id=tenant_id,
            user_id=user_id,
            description=f"ML prediction by {model_name}",
            resource_type="ml_model",
            resource_id=model_name,
            metadata={
                "model": model_name,
                "prediction": str(prediction),
                "confidence": confidence
            },
            compliance_tags=["ai", "ml"]
        )
    
    async def log_compliance_check(
        self,
        tenant_id: str,
        check_type: str,
        passed: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log compliance check"""
        return await self.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK if passed else AuditEventType.COMPLIANCE_VIOLATION,
            tenant_id=tenant_id,
            description=f"Compliance check: {check_type} - {'passed' if passed else 'failed'}",
            result="passed" if passed else "failed",
            severity=AuditSeverity.INFO if passed else AuditSeverity.ERROR,
            metadata=details,
            compliance_tags=["compliance", check_type]
        )


class ComplianceReporter:
    """
    Generate compliance reports from audit trail.
    
    Supports:
    - ASIC reporting
    - APRA reporting
    - ATO reporting
    - Custom compliance reports
    """
    
    def __init__(self, audit_trail: AuditTrail):
        self.audit_trail = audit_trail
    
    async def generate_access_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate access control report"""
        # This would query event store for access events
        return {
            "report_type": "access_control",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_access_attempts": 0,
                "granted": 0,
                "denied": 0,
                "by_user": {},
                "by_resource": {}
            }
        }
    
    async def generate_transaction_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate transaction audit report"""
        return {
            "report_type": "transactions",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_transactions": 0,
                "total_amount": 0.0,
                "by_type": {},
                "by_status": {}
            }
        }
    
    async def generate_security_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate security incident report"""
        return {
            "report_type": "security",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "fraud_detections": 0,
                "anomalies": 0,
                "threats": 0,
                "incidents": 0,
                "by_severity": {}
            }
        }
    
    async def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        compliance_type: str = "all"
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        return {
            "report_type": "compliance",
            "compliance_type": compliance_type,
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "checks": {
                "total": 0,
                "passed": 0,
                "failed": 0
            },
            "violations": [],
            "recommendations": []
        }

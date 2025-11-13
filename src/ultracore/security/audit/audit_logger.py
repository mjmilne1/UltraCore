"""
Audit Logging System
CloudTrail-style comprehensive logging for compliance

Zero-trust: Log everything, assume breach
"""
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class AuditEventType(str, Enum):
    # Authentication events
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILURE = 'LOGIN_FAILURE'
    LOGOUT = 'LOGOUT'
    MFA_ENABLED = 'MFA_ENABLED'
    MFA_DISABLED = 'MFA_DISABLED'
    PASSWORD_CHANGED = 'PASSWORD_CHANGED'
    
    # Authorization events
    ACCESS_DENIED = 'ACCESS_DENIED'
    PERMISSION_GRANTED = 'PERMISSION_GRANTED'
    ROLE_ASSIGNED = 'ROLE_ASSIGNED'
    ROLE_REVOKED = 'ROLE_REVOKED'
    
    # API Key events
    API_KEY_CREATED = 'API_KEY_CREATED'
    API_KEY_REVOKED = 'API_KEY_REVOKED'
    API_KEY_USED = 'API_KEY_USED'
    
    # Data access events
    ACCOUNT_VIEWED = 'ACCOUNT_VIEWED'
    ACCOUNT_MODIFIED = 'ACCOUNT_MODIFIED'
    PAYMENT_INITIATED = 'PAYMENT_INITIATED'
    PAYMENT_APPROVED = 'PAYMENT_APPROVED'
    GL_ENTRY_POSTED = 'GL_ENTRY_POSTED'
    
    # Security events
    SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY'
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'
    IP_BLOCKED = 'IP_BLOCKED'
    BRUTE_FORCE_DETECTED = 'BRUTE_FORCE_DETECTED'
    
    # Admin events
    USER_CREATED = 'USER_CREATED'
    USER_DELETED = 'USER_DELETED'
    CONFIG_CHANGED = 'CONFIG_CHANGED'


class AuditSeverity(str, Enum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class AuditLogger:
    """
    Comprehensive audit logging
    
    CloudTrail-style: Who did what, when, where, and why
    """
    
    @staticmethod
    async def log_event(
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        result: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log audit event
        
        Immutable, event-sourced to Kafka for compliance
        """
        event_data = {
            'event_type': event_type.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'result': result,
            'severity': severity.value,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata': metadata or {}
        }
        
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='audit',
            event_type='audit_log',
            event_data=event_data,
            aggregate_id=f"{user_id or 'system'}_{datetime.now(timezone.utc).timestamp()}"
        )
        
        # Also publish to Data Mesh for analytics
        from ultracore.data_mesh.integration import DataMeshPublisher
        await DataMeshPublisher.publish_transaction_data(
            f"AUDIT-{datetime.now(timezone.utc).timestamp()}",
            {
                **event_data,
                'data_classification': 'CONFIDENTIAL'
            }
        )
    
    @staticmethod
    async def log_authentication(
        event_type: AuditEventType,
        user_id: Optional[str],
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log authentication event"""
        await AuditLogger.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type='USER',
            resource_id=user_id,
            action='AUTHENTICATE',
            result='SUCCESS' if success else 'FAILURE',
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            ip_address=ip_address,
            metadata={
                'username': username,
                'reason': reason
            }
        )
    
    @staticmethod
    async def log_data_access(
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None
    ):
        """Log data access for compliance"""
        await AuditLogger.log_event(
            event_type=AuditEventType.ACCOUNT_VIEWED if 'VIEW' in action else AuditEventType.ACCOUNT_MODIFIED,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result='SUCCESS',
            severity=AuditSeverity.INFO,
            ip_address=ip_address
        )
    
    @staticmethod
    async def log_security_event(
        event_type: AuditEventType,
        severity: AuditSeverity,
        description: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log security event"""
        await AuditLogger.log_event(
            event_type=event_type,
            user_id=None,
            resource_type='SYSTEM',
            resource_id=None,
            action='SECURITY_EVENT',
            result='DETECTED',
            severity=severity,
            ip_address=ip_address,
            metadata={'description': description, **(metadata or {})}
        )

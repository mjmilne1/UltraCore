"""
Security Domain Events
Event-sourced security events for authentication, authorization, and encryption
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ultracore.event_sourcing.base import EventType, EventMetadata, Event


# Extend EventType with security events
class SecurityEventType(str, Enum):
    """Security-specific event types"""

    # Authentication events
    USER_AUTHENTICATED = "security.user.authenticated"
    USER_AUTHENTICATION_FAILED = "security.user.authentication_failed"
    USER_LOGGED_OUT = "security.user.logged_out"
    PASSWORD_CHANGED = "security.password.changed"
    PASSWORD_RESET_REQUESTED = "security.password.reset_requested"
    PASSWORD_RESET_COMPLETED = "security.password.reset_completed"
    TOKEN_CREATED = "security.token.created"
    TOKEN_REFRESHED = "security.token.refreshed"
    TOKEN_REVOKED = "security.token.revoked"
    MFA_ENABLED = "security.mfa.enabled"
    MFA_DISABLED = "security.mfa.disabled"
    MFA_VERIFIED = "security.mfa.verified"

    # Authorization events
    ROLE_ASSIGNED = "security.role.assigned"
    ROLE_REVOKED = "security.role.revoked"
    PERMISSION_GRANTED = "security.permission.granted"
    PERMISSION_REVOKED = "security.permission.revoked"
    ACCESS_GRANTED = "security.access.granted"
    ACCESS_DENIED = "security.access.denied"

    # Encryption events
    DATA_ENCRYPTED = "security.data.encrypted"
    DATA_DECRYPTED = "security.data.decrypted"
    ENCRYPTION_KEY_ROTATED = "security.encryption_key.rotated"

    # Audit events
    SECURITY_AUDIT_LOGGED = "security.audit.logged"
    SUSPICIOUS_ACTIVITY_DETECTED = "security.suspicious_activity.detected"


# Authentication Events


def create_user_authenticated_event(
    user_id: str,
    tenant_id: str,
    authentication_method: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[UUID] = None,
) -> Event:
    """Create UserAuthenticated event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.CUSTOMER_CREATED,  # Using existing type, should add to EventType
        aggregate_id=user_id,
        aggregate_type="User",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "authentication_method": authentication_method,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


def create_password_changed_event(
    user_id: str, tenant_id: str, changed_by: str, correlation_id: Optional[UUID] = None
) -> Event:
    """Create PasswordChanged event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.CUSTOMER_UPDATED,
        aggregate_id=user_id,
        aggregate_type="User",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=changed_by,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "changed_by": changed_by,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


def create_token_created_event(
    user_id: str,
    tenant_id: str,
    token_type: str,
    expires_at: datetime,
    correlation_id: Optional[UUID] = None,
) -> Event:
    """Create TokenCreated event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.CUSTOMER_UPDATED,
        aggregate_id=user_id,
        aggregate_type="Token",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "token_type": token_type,
        "expires_at": expires_at.isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


# Authorization Events


def create_role_assigned_event(
    user_id: str, tenant_id: str, role: str, assigned_by: str, correlation_id: Optional[UUID] = None
) -> Event:
    """Create RoleAssigned event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.CUSTOMER_UPDATED,
        aggregate_id=user_id,
        aggregate_type="User",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=assigned_by,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "assigned_by": assigned_by,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


def create_permission_granted_event(
    user_id: str,
    tenant_id: str,
    permission: str,
    granted_by: str,
    resource_id: Optional[str] = None,
    correlation_id: Optional[UUID] = None,
) -> Event:
    """Create PermissionGranted event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.CUSTOMER_UPDATED,
        aggregate_id=user_id,
        aggregate_type="User",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=granted_by,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "permission": permission,
        "granted_by": granted_by,
        "resource_id": resource_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


def create_access_denied_event(
    user_id: str,
    tenant_id: str,
    resource_id: str,
    required_permission: str,
    reason: str,
    correlation_id: Optional[UUID] = None,
) -> Event:
    """Create AccessDenied event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.AUDIT_LOG_CREATED,
        aggregate_id=user_id,
        aggregate_type="AccessControl",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "resource_id": resource_id,
        "required_permission": required_permission,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)


# Encryption Events


def create_data_encrypted_event(
    user_id: str,
    tenant_id: str,
    data_type: str,
    field_name: str,
    encryption_algorithm: str = "Fernet",
    correlation_id: Optional[UUID] = None,
) -> Event:
    """Create DataEncrypted event"""
    metadata = EventMetadata(
        event_id=uuid4(),
        event_type=EventType.AUDIT_LOG_CREATED,
        aggregate_id=f"{data_type}-{field_name}",
        aggregate_type="EncryptedData",
        version=1,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "data_type": data_type,
        "field_name": field_name,
        "encryption_algorithm": encryption_algorithm,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return Event(metadata=metadata, data=data)

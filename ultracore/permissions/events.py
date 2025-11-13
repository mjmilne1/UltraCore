"""
Permissions & Roles Events
Kafka event schemas for RBAC system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class PermissionAction(str, Enum):
    """Permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"


class RoleType(str, Enum):
    """Role types"""
    SYSTEM = "system"  # Built-in roles
    CUSTOM = "custom"  # User-defined roles
    ADVISOR = "advisor"  # Financial advisor role
    CLIENT = "client"  # Client role
    ADMIN = "admin"  # Administrator role


# Role Events
@dataclass
class RoleCreated:
    tenant_id: str
    role_id: str
    name: str
    role_type: RoleType
    description: Optional[str]
    permissions: List[str]
    is_system_role: bool
    created_by: str
    created_at: datetime


@dataclass
class RoleUpdated:
    tenant_id: str
    role_id: str
    permissions: List[str]
    updated_by: str
    updated_at: datetime


@dataclass
class RoleAssigned:
    tenant_id: str
    user_id: str
    role_id: str
    granted_by: str
    expires_at: Optional[datetime]
    granted_at: datetime


@dataclass
class RoleRevoked:
    tenant_id: str
    user_id: str
    role_id: str
    revoked_by: str
    reason: Optional[str]
    revoked_at: datetime


# Permission Events
@dataclass
class PermissionCreated:
    tenant_id: str
    permission_id: str
    resource: str
    action: PermissionAction
    description: Optional[str]
    created_by: str
    created_at: datetime


@dataclass
class PermissionChecked:
    tenant_id: str
    user_id: str
    resource: str
    action: PermissionAction
    granted: bool
    reason: Optional[str]
    checked_at: datetime


# API Key Events
@dataclass
class ApiKeyCreated:
    tenant_id: str
    api_key_id: str
    user_id: str
    name: str
    key_hash: str
    permissions: List[str]
    expires_at: Optional[datetime]
    created_by: str
    created_at: datetime


@dataclass
class ApiKeyUsed:
    tenant_id: str
    api_key_id: str
    resource: str
    action: str
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]
    used_at: datetime


@dataclass
class ApiKeyRevoked:
    tenant_id: str
    api_key_id: str
    revoked_by: str
    reason: Optional[str]
    revoked_at: datetime


# Access Control Events
@dataclass
class AccessDenied:
    tenant_id: str
    user_id: str
    resource: str
    action: PermissionAction
    reason: str
    ip_address: Optional[str]
    denied_at: datetime


@dataclass
class SuspiciousAccessDetected:
    tenant_id: str
    user_id: str
    anomaly_type: str
    severity: str
    details: Dict[str, Any]
    detected_at: datetime

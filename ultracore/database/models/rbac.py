"""
RBAC Database Models
Role-Based Access Control with hierarchical roles and fine-grained permissions
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index, Table, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ultracore.database.base import Base


# ============================================================================
# Association Tables (Many-to-Many)
# ============================================================================

# Role-Permission association
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('granted_by', UUID(as_uuid=True)),  # User who granted this permission
)

# User-Role association
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('assigned_by', UUID(as_uuid=True)),  # User who assigned this role
    Column('expires_at', DateTime),  # Optional expiration for temporary roles
)


# ============================================================================
# Core RBAC Tables
# ============================================================================

class Role(Base):
    """
    Role definition with hierarchical structure
    
    Hierarchy:
    - super_admin (level 0) - System administrator
    - admin (level 1) - Organization administrator
    - manager (level 2) - Department manager
    - officer (level 3) - Bank officer/staff
    - customer (level 4) - End customer
    """
    __tablename__ = "roles"
    
    # Primary key
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Role details
    name = Column(String(100), nullable=False, index=True)  # e.g., "admin", "manager"
    display_name = Column(String(255), nullable=False)  # e.g., "System Administrator"
    description = Column(Text)
    
    # Hierarchy
    level = Column(String(20), nullable=False, index=True)  # 0=highest, 4=lowest
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    
    # Metadata
    metadata_json = Column('metadata', JSON)  # Additional role configuration
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
    parent_role = relationship("Role", remote_side=[role_id], backref="child_roles")
    
    # Indexes
    __table_args__ = (
        Index("idx_roles_tenant_name", "tenant_id", "name", unique=True),
        Index("idx_roles_level", "level"),
    )


class Permission(Base):
    """
    Fine-grained permission definition
    
    Format: <resource>:<action>
    Examples:
    - accounts:read
    - accounts:write
    - accounts:delete
    - transactions:approve
    - loans:create
    """
    __tablename__ = "permissions"
    
    # Primary key
    permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Permission details
    name = Column(String(255), nullable=False, unique=True, index=True)  # e.g., "accounts:read"
    resource = Column(String(100), nullable=False, index=True)  # e.g., "accounts"
    action = Column(String(100), nullable=False, index=True)  # e.g., "read", "write", "delete"
    description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    metadata_json = Column('metadata', JSON)  # Additional permission configuration
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_permissions_resource_action", "resource", "action"),
        Index("idx_permissions_tenant", "tenant_id"),
    )


class ResourcePolicy(Base):
    """
    Resource-level access policies
    
    Defines who can access specific resources with conditions
    """
    __tablename__ = "resource_policies"
    
    # Primary key
    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Policy details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Resource
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., "account", "loan"
    resource_id = Column(UUID(as_uuid=True), index=True)  # Specific resource or NULL for all
    
    # Access control
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))  # User-specific policy
    
    # Permissions
    allowed_actions = Column(ARRAY(String))  # ["read", "write", "delete"]
    denied_actions = Column(ARRAY(String))  # Explicit denials (take precedence)
    
    # Conditions (JSON-based policy conditions)
    conditions = Column(JSON)  # e.g., {"ip_range": "10.0.0.0/8", "time_range": "09:00-17:00"}
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(String(20), default=0)  # Higher priority = evaluated first
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    # Indexes
    __table_args__ = (
        Index("idx_resource_policies_resource", "resource_type", "resource_id"),
        Index("idx_resource_policies_role", "role_id"),
        Index("idx_resource_policies_user", "user_id"),
        Index("idx_resource_policies_priority", "priority"),
    )


class AccessLog(Base):
    """
    Access log for audit trail and compliance
    """
    __tablename__ = "access_logs"
    
    # Primary key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # User and role
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'))
    
    # Access details
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), index=True)
    action = Column(String(100), nullable=False, index=True)
    
    # Result
    access_granted = Column(Boolean, nullable=False, index=True)
    denial_reason = Column(Text)  # Why access was denied
    
    # Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    request_id = Column(UUID(as_uuid=True), index=True)  # Correlation ID
    
    # AI-powered decision
    risk_score = Column(String(20))  # 0-100
    ai_decision = Column(String(50))  # "allow", "deny", "challenge"
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_access_logs_user_timestamp", "user_id", "timestamp"),
        Index("idx_access_logs_resource", "resource_type", "resource_id"),
        Index("idx_access_logs_denied", "access_granted", "timestamp"),
    )

"""Multi-Tenancy Event Schemas (Kafka-First)"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, Optional, List

class TenantTier(Enum):
    """Tenant isolation tier"""
    ENTERPRISE = "enterprise"  # Database per tenant
    STANDARD = "standard"      # Schema per tenant
    SMALL = "small"            # Row-level isolation

class TenantStatus(Enum):
    """Tenant lifecycle status"""
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

# Tenant Lifecycle Events

@dataclass
class TenantCreatedEvent:
    """Tenant created"""
    event_id: str
    tenant_id: str
    tenant_name: str
    tier: TenantTier
    owner_email: str
    created_at: datetime
    created_by: str

@dataclass
class TenantProvisioningStartedEvent:
    """Tenant provisioning started"""
    event_id: str
    tenant_id: str
    tier: TenantTier
    db_name: Optional[str]
    schema_name: Optional[str]
    started_at: datetime

@dataclass
class TenantDatabaseCreatedEvent:
    """Tenant database created (Enterprise tier)"""
    event_id: str
    tenant_id: str
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    created_at: datetime

@dataclass
class TenantSchemaCreatedEvent:
    """Tenant schema created (Standard tier)"""
    event_id: str
    tenant_id: str
    db_name: str
    schema_name: str
    created_at: datetime

@dataclass
class TenantMigrationsCompletedEvent:
    """Tenant database migrations completed"""
    event_id: str
    tenant_id: str
    migration_version: str
    tables_created: int
    completed_at: datetime

@dataclass
class TenantActivatedEvent:
    """Tenant activated and ready for use"""
    event_id: str
    tenant_id: str
    tier: TenantTier
    activated_at: datetime

@dataclass
class TenantSuspendedEvent:
    """Tenant suspended"""
    event_id: str
    tenant_id: str
    reason: str
    suspended_at: datetime
    suspended_by: str

@dataclass
class TenantReactivatedEvent:
    """Tenant reactivated"""
    event_id: str
    tenant_id: str
    reactivated_at: datetime
    reactivated_by: str

@dataclass
class TenantTerminatedEvent:
    """Tenant terminated"""
    event_id: str
    tenant_id: str
    reason: str
    data_retention_days: int
    terminated_at: datetime
    terminated_by: str

# Configuration Events

@dataclass
class TenantConfigUpdatedEvent:
    """Tenant configuration updated"""
    event_id: str
    tenant_id: str
    config_key: str
    old_value: Any
    new_value: Any
    updated_at: datetime
    updated_by: str

@dataclass
class TenantConnectionPoolResizedEvent:
    """Tenant connection pool resized"""
    event_id: str
    tenant_id: str
    old_min_connections: int
    old_max_connections: int
    new_min_connections: int
    new_max_connections: int
    reason: str
    resized_at: datetime

@dataclass
class TenantReadReplicaAddedEvent:
    """Read replica added for tenant"""
    event_id: str
    tenant_id: str
    replica_host: str
    replica_port: int
    added_at: datetime

# Resource Events

@dataclass
class TenantResourceUsageRecordedEvent:
    """Tenant resource usage recorded"""
    event_id: str
    tenant_id: str
    cpu_usage_percent: Decimal
    memory_usage_mb: Decimal
    storage_usage_gb: Decimal
    connection_count: int
    query_count: int
    recorded_at: datetime

@dataclass
class TenantResourceLimitExceededEvent:
    """Tenant exceeded resource limits"""
    event_id: str
    tenant_id: str
    resource_type: str  # cpu, memory, storage, connections
    current_usage: Decimal
    limit: Decimal
    exceeded_at: datetime

@dataclass
class TenantScaledUpEvent:
    """Tenant resources scaled up"""
    event_id: str
    tenant_id: str
    resource_type: str
    old_limit: Decimal
    new_limit: Decimal
    reason: str
    scaled_at: datetime

@dataclass
class TenantScaledDownEvent:
    """Tenant resources scaled down"""
    event_id: str
    tenant_id: str
    resource_type: str
    old_limit: Decimal
    new_limit: Decimal
    reason: str
    scaled_at: datetime

# Security Events

@dataclass
class TenantPasswordRotatedEvent:
    """Tenant database password rotated"""
    event_id: str
    tenant_id: str
    rotated_at: datetime
    rotated_by: str

@dataclass
class TenantAccessGrantedEvent:
    """Access granted to tenant"""
    event_id: str
    tenant_id: str
    user_id: str
    role: str
    granted_at: datetime
    granted_by: str

@dataclass
class TenantAccessRevokedEvent:
    """Access revoked from tenant"""
    event_id: str
    tenant_id: str
    user_id: str
    reason: str
    revoked_at: datetime
    revoked_by: str

# Kafka Topics
TENANT_LIFECYCLE_TOPIC = "multitenancy.lifecycle"
TENANT_CONFIG_TOPIC = "multitenancy.config"
TENANT_RESOURCES_TOPIC = "multitenancy.resources"
TENANT_SECURITY_TOPIC = "multitenancy.security"

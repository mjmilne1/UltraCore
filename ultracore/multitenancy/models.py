"""Multi-Tenancy Models"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from .events import TenantTier, TenantStatus

@dataclass
class TenantConfig:
    """Tenant configuration"""
    tenant_id: str
    tenant_name: str
    tier: TenantTier
    status: TenantStatus
    owner_email: str
    
    # Database connection (for enterprise/standard tiers)
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_username: Optional[str] = None
    db_password_encrypted: Optional[str] = None
    schema_name: Optional[str] = None  # For standard tier
    
    # Read replica (optional)
    readonly_db_host: Optional[str] = None
    readonly_db_port: Optional[int] = None
    readonly_db_username: Optional[str] = None
    readonly_db_password_encrypted: Optional[str] = None
    
    # Connection pool configuration
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout_seconds: int = 30
    idle_timeout_seconds: int = 600
    
    # Resource limits
    max_cpu_percent: Decimal = Decimal("80")
    max_memory_mb: Decimal = Decimal("2048")
    max_storage_gb: Decimal = Decimal("100")
    max_concurrent_queries: int = 100
    
    # Configuration
    timezone: str = "UTC"
    locale: str = "en_US"
    auto_update: bool = True
    auto_scale: bool = False
    
    # Encryption
    master_password_hash: str = ""
    encryption_algorithm: str = "AES-256-GCM"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "tier": self.tier.value,
            "status": self.status.value,
            "owner_email": self.owner_email,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_username": self.db_username,
            "schema_name": self.schema_name,
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat(),
        }

@dataclass
class TenantResourceUsage:
    """Tenant resource usage metrics"""
    tenant_id: str
    timestamp: datetime
    cpu_usage_percent: Decimal
    memory_usage_mb: Decimal
    storage_usage_gb: Decimal
    connection_count: int
    active_query_count: int
    total_queries_last_hour: int
    avg_query_time_ms: Decimal

@dataclass
class ConnectionPoolStats:
    """Connection pool statistics"""
    tenant_id: str
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    pool_utilization_percent: Decimal
    avg_wait_time_ms: Decimal

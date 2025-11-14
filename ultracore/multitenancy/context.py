"""Tenant Context Manager"""
from contextvars import ContextVar
from typing import Optional, Dict

# Thread-safe tenant context
_tenant_context: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)

class TenantContext:
    """Manage tenant context for current request/event"""
    
    @staticmethod
    def set_tenant(tenant_id: str):
        """Set current tenant ID"""
        _tenant_context.set(tenant_id)
    
    @staticmethod
    def get_tenant() -> Optional[str]:
        """Get current tenant ID"""
        return _tenant_context.get()
    
    @staticmethod
    def clear():
        """Clear tenant context"""
        _tenant_context.set(None)
    
    @classmethod
    def from_http_header(cls, headers: Dict[str, str]) -> Optional[str]:
        """Extract tenant ID from HTTP header"""
        tenant_id = headers.get('X-UltraCore-Tenant-Id') or headers.get('x-ultracore-tenant-id')
        if tenant_id:
            cls.set_tenant(tenant_id)
        return tenant_id
    
    @classmethod
    def from_kafka_event(cls, event: Dict) -> Optional[str]:
        """Extract tenant ID from Kafka event"""
        tenant_id = event.get('tenant_id')
        if tenant_id:
            cls.set_tenant(tenant_id)
        return tenant_id
    
    @classmethod
    def require_tenant(cls) -> str:
        """Get tenant ID or raise error"""
        tenant_id = cls.get_tenant()
        if not tenant_id:
            raise ValueError("No tenant context set")
        return tenant_id

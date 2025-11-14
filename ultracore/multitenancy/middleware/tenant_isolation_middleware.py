"""Tenant Isolation Middleware"""
from typing import Callable, Dict
from ..context import TenantContext

class TenantIsolationMiddleware:
    """Ensure tenant isolation for all requests"""
    
    def __init__(self, tenant_registry):
        """Initialize with tenant registry"""
        self.tenant_registry = tenant_registry
    
    async def __call__(self, request: Dict, call_next: Callable):
        """Process request with tenant isolation"""
        # Extract tenant ID from header
        headers = request.get('headers', {})
        tenant_id = TenantContext.from_http_header(headers)
        
        if not tenant_id:
            raise ValueError("Tenant ID required in X-UltraCore-Tenant-Id header")
        
        # Validate tenant exists and is active
        tenant_config = await self.tenant_registry.get_tenant(tenant_id)
        if not tenant_config:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        if tenant_config.status.value != "active":
            raise ValueError(f"Tenant {tenant_id} is not active")
        
        try:
            # Process request
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context
            TenantContext.clear()

"""Tenant Connection Pool Manager"""
from typing import Dict, Optional
import asyncpg
from ..models import TenantConfig
from ..encryption import PasswordEncryption
from ..context import TenantContext

class TenantConnectionPoolManager:
    """Manage connection pools per tenant"""
    
    def __init__(self, master_password: str):
        """Initialize with master password for decryption"""
        self._pools: Dict[str, asyncpg.Pool] = {}
        self._readonly_pools: Dict[str, asyncpg.Pool] = {}
        self._encryption = PasswordEncryption(master_password)
        self._tenant_configs: Dict[str, TenantConfig] = {}
    
    async def register_tenant(self, config: TenantConfig):
        """Register tenant configuration"""
        self._tenant_configs[config.tenant_id] = config
    
    async def get_pool(self, tenant_id: Optional[str] = None, 
                      readonly: bool = False) -> asyncpg.Pool:
        """Get connection pool for tenant"""
        if tenant_id is None:
            tenant_id = TenantContext.require_tenant()
        
        cache = self._readonly_pools if readonly else self._pools
        
        if tenant_id not in cache:
            config = self._tenant_configs.get(tenant_id)
            if not config:
                raise ValueError(f"Tenant {tenant_id} not registered")
            
            cache[tenant_id] = await self._create_pool(config, readonly)
        
        return cache[tenant_id]
    
    async def _create_pool(self, config: TenantConfig, 
                          readonly: bool) -> asyncpg.Pool:
        """Create connection pool for tenant"""
        if readonly and config.readonly_db_host:
            host = config.readonly_db_host
            port = config.readonly_db_port
            username = config.readonly_db_username
            password_encrypted = config.readonly_db_password_encrypted
        else:
            host = config.db_host
            port = config.db_port
            username = config.db_username
            password_encrypted = config.db_password_encrypted
        
        if not password_encrypted:
            raise ValueError(f"No password configured for tenant {config.tenant_id}")
        
        password = self._encryption.decrypt(password_encrypted)
        
        return await asyncpg.create_pool(
            host=host,
            port=port,
            user=username,
            password=password,
            database=config.db_name,
            min_size=config.min_connections,
            max_size=config.max_connections,
            command_timeout=config.connection_timeout_seconds
        )
    
    async def resize_pool(self, tenant_id: str, min_size: int, max_size: int):
        """Resize connection pool for tenant"""
        # Close existing pools
        if tenant_id in self._pools:
            await self._pools[tenant_id].close()
            del self._pools[tenant_id]
        
        if tenant_id in self._readonly_pools:
            await self._readonly_pools[tenant_id].close()
            del self._readonly_pools[tenant_id]
        
        # Update config
        config = self._tenant_configs[tenant_id]
        config.min_connections = min_size
        config.max_connections = max_size
        
        # Pools will be recreated on next access
    
    async def get_pool_stats(self, tenant_id: str) -> Dict:
        """Get connection pool statistics"""
        pool = await self.get_pool(tenant_id, readonly=False)
        
        return {
            "tenant_id": tenant_id,
            "total_connections": pool.get_size(),
            "idle_connections": pool.get_idle_size(),
            "min_size": pool.get_min_size(),
            "max_size": pool.get_max_size(),
        }
    
    async def close_tenant_pools(self, tenant_id: str):
        """Close all pools for a tenant"""
        if tenant_id in self._pools:
            await self._pools[tenant_id].close()
            del self._pools[tenant_id]
        
        if tenant_id in self._readonly_pools:
            await self._readonly_pools[tenant_id].close()
            del self._readonly_pools[tenant_id]
    
    async def close_all(self):
        """Close all connection pools"""
        for pool in self._pools.values():
            await pool.close()
        for pool in self._readonly_pools.values():
            await pool.close()
        
        self._pools.clear()
        self._readonly_pools.clear()

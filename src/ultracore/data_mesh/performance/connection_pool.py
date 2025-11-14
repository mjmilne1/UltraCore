"""Database Connection Pooling"""
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """Simple connection pool for database access."""
    
    def __init__(self, min_size: int = 5, max_size: int = 20):
        self.min_size = min_size
        self.max_size = max_size
        self.pool = []
        self.in_use = set()
        self.stats = {"acquired": 0, "released": 0, "created": 0}
        logger.info(f"Connection pool initialized (min={min_size}, max={max_size})")
    
    async def acquire(self):
        """Acquire a connection from pool."""
        # Try to get from pool
        if self.pool:
            conn = self.pool.pop()
            self.in_use.add(conn)
            self.stats["acquired"] += 1
            return conn
        
        # Create new if under max
        if len(self.in_use) < self.max_size:
            conn = await self._create_connection()
            self.in_use.add(conn)
            self.stats["created"] += 1
            self.stats["acquired"] += 1
            return conn
        
        # Wait for available connection
        while not self.pool:
            await asyncio.sleep(0.1)
        
        conn = self.pool.pop()
        self.in_use.add(conn)
        self.stats["acquired"] += 1
        return conn
    
    async def release(self, conn):
        """Release connection back to pool."""
        if conn in self.in_use:
            self.in_use.remove(conn)
            self.pool.append(conn)
            self.stats["released"] += 1
    
    async def _create_connection(self):
        """Create new database connection."""
        # Placeholder - would create actual DB connection
        return {"id": len(self.in_use) + len(self.pool) + 1}
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        return {
            **self.stats,
            "pool_size": len(self.pool),
            "in_use": len(self.in_use),
            "available": len(self.pool)
        }

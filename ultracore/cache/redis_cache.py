"""
Redis Cache Manager

Production-grade Redis caching with:
- Session management
- Data caching with TTL
- ML model prediction caching
- Cache invalidation strategies
- Distributed locking
"""

import os
import json
import pickle
from typing import Any, Optional, Dict, List, Callable
from datetime import timedelta
import asyncio
from functools import wraps

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache:
    """
    Production-grade Redis cache manager.
    
    Features:
    - Async operations
    - Automatic serialization (JSON/pickle)
    - TTL support
    - Namespace isolation
    - Cache invalidation patterns
    - Distributed locking
    - Connection pooling
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: Optional[str] = None,
        namespace: str = "ultracore",
        default_ttl: int = 3600  # 1 hour
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Install with: pip install redis")
        
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.namespace = namespace
        self.default_ttl = default_ttl
        
        # Connection pool
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=False,  # We handle encoding ourselves
            max_connections=50
        )
        
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection"""
        if not self.client:
            self.client = redis.Redis(connection_pool=self.pool)
            # Test connection
            await self.client.ping()
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.client = None
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"
    
    async def get(
        self,
        key: str,
        deserialize: str = "json"
    ) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            deserialize: Deserialization method ("json" or "pickle")
        
        Returns:
            Cached value or None if not found
        """
        await self.connect()
        
        namespaced_key = self._make_key(key)
        value = await self.client.get(namespaced_key)
        
        if value is None:
            return None
        
        # Deserialize
        if deserialize == "json":
            return json.loads(value)
        elif deserialize == "pickle":
            return pickle.loads(value)
        else:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: str = "json"
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = default_ttl)
            serialize: Serialization method ("json" or "pickle")
        
        Returns:
            True if successful
        """
        await self.connect()
        
        namespaced_key = self._make_key(key)
        
        # Serialize
        if serialize == "json":
            serialized = json.dumps(value)
        elif serialize == "pickle":
            serialized = pickle.dumps(value)
        else:
            serialized = value
        
        # Set with TTL
        ttl = ttl or self.default_ttl
        return await self.client.setex(namespaced_key, ttl, serialized)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.delete(namespaced_key) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.exists(namespaced_key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.expire(namespaced_key, ttl)
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.ttl(namespaced_key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
        
        Returns:
            Number of keys deleted
        """
        await self.connect()
        namespaced_pattern = self._make_key(pattern)
        
        # Scan for matching keys
        keys = []
        async for key in self.client.scan_iter(match=namespaced_pattern):
            keys.append(key)
        
        # Delete in batches
        if keys:
            return await self.client.delete(*keys)
        return 0
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
        serialize: str = "json"
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
            serialize: Serialization method
        
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key, deserialize=serialize)
        
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache it
        await self.set(key, value, ttl=ttl, serialize=serialize)
        
        return value
    
    async def lock(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking_timeout: Optional[int] = None
    ):
        """
        Acquire distributed lock.
        
        Args:
            lock_name: Lock name
            timeout: Lock timeout in seconds
            blocking_timeout: How long to wait for lock (None = wait forever)
        
        Returns:
            Lock context manager
        """
        await self.connect()
        namespaced_lock = self._make_key(f"lock:{lock_name}")
        return self.client.lock(
            namespaced_lock,
            timeout=timeout,
            blocking_timeout=blocking_timeout
        )
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.incrby(namespaced_key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.decrby(namespaced_key, amount)
    
    async def list_push(self, key: str, *values: Any) -> int:
        """Push values to list (right push)"""
        await self.connect()
        namespaced_key = self._make_key(key)
        serialized = [json.dumps(v) for v in values]
        return await self.client.rpush(namespaced_key, *serialized)
    
    async def list_pop(self, key: str) -> Optional[Any]:
        """Pop value from list (left pop)"""
        await self.connect()
        namespaced_key = self._make_key(key)
        value = await self.client.lpop(namespaced_key)
        return json.loads(value) if value else None
    
    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get range of values from list"""
        await self.connect()
        namespaced_key = self._make_key(key)
        values = await self.client.lrange(namespaced_key, start, end)
        return [json.loads(v) for v in values]
    
    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.hset(namespaced_key, field, json.dumps(value))
    
    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        await self.connect()
        namespaced_key = self._make_key(key)
        value = await self.client.hget(namespaced_key, field)
        return json.loads(value) if value else None
    
    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        await self.connect()
        namespaced_key = self._make_key(key)
        data = await self.client.hgetall(namespaced_key)
        return {k.decode(): json.loads(v) for k, v in data.items()}
    
    async def hash_delete(self, key: str, *fields: str) -> int:
        """Delete hash fields"""
        await self.connect()
        namespaced_key = self._make_key(key)
        return await self.client.hdel(namespaced_key, *fields)


class CacheManager:
    """
    High-level cache manager with domain-specific caching strategies.
    """
    
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
    
    # Session Management
    async def set_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Set user session"""
        session_data = {
            "user_id": user_id,
            "created_at": str(asyncio.get_event_loop().time()),
            **data
        }
        return await self.cache.set(
            f"session:{session_id}",
            session_data,
            ttl=ttl
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session"""
        return await self.cache.get(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        return await self.cache.delete(f"session:{session_id}")
    
    # Account Caching
    async def cache_account(
        self,
        tenant_id: str,
        account_id: str,
        account_data: Dict[str, Any],
        ttl: int = 300  # 5 minutes
    ) -> bool:
        """Cache account data"""
        return await self.cache.set(
            f"account:{tenant_id}:{account_id}",
            account_data,
            ttl=ttl
        )
    
    async def get_cached_account(
        self,
        tenant_id: str,
        account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached account"""
        return await self.cache.get(f"account:{tenant_id}:{account_id}")
    
    async def invalidate_account(self, tenant_id: str, account_id: str) -> bool:
        """Invalidate account cache"""
        return await self.cache.delete(f"account:{tenant_id}:{account_id}")
    
    # ML Prediction Caching
    async def cache_ml_prediction(
        self,
        model_name: str,
        input_hash: str,
        prediction: Any,
        ttl: int = 600  # 10 minutes
    ) -> bool:
        """Cache ML model prediction"""
        return await self.cache.set(
            f"ml:{model_name}:{input_hash}",
            prediction,
            ttl=ttl,
            serialize="pickle"
        )
    
    async def get_cached_prediction(
        self,
        model_name: str,
        input_hash: str
    ) -> Optional[Any]:
        """Get cached ML prediction"""
        return await self.cache.get(
            f"ml:{model_name}:{input_hash}",
            deserialize="pickle"
        )
    
    # RL Agent Q-Table Caching
    async def cache_q_table(
        self,
        agent_name: str,
        q_table: Dict,
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache RL agent Q-table"""
        return await self.cache.set(
            f"rl:{agent_name}:q_table",
            q_table,
            ttl=ttl,
            serialize="pickle"
        )
    
    async def get_cached_q_table(self, agent_name: str) -> Optional[Dict]:
        """Get cached Q-table"""
        return await self.cache.get(
            f"rl:{agent_name}:q_table",
            deserialize="pickle"
        )
    
    # User Profile Caching
    async def cache_user_profile(
        self,
        tenant_id: str,
        user_id: str,
        profile: Dict[str, Any],
        ttl: int = 600
    ) -> bool:
        """Cache user profile"""
        return await self.cache.set(
            f"user:{tenant_id}:{user_id}",
            profile,
            ttl=ttl
        )
    
    async def get_cached_user_profile(
        self,
        tenant_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        return await self.cache.get(f"user:{tenant_id}:{user_id}")
    
    # Rate Limiting
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """
        Check rate limit.
        
        Args:
            key: Rate limit key (e.g., "api:user_123")
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            True if under limit, False if exceeded
        """
        rate_key = f"rate:{key}"
        
        # Increment counter
        count = await self.cache.increment(rate_key)
        
        # Set expiration on first request
        if count == 1:
            await self.cache.expire(rate_key, window)
        
        return count <= limit


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    serialize: str = "json"
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
        serialize: Serialization method
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache from first argument (assumed to be self with cache attribute)
            if args and hasattr(args[0], 'cache'):
                cache = args[0].cache
            else:
                return await func(*args, **kwargs)
            
            # Create cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args[1:])  # Skip self
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = await cache.get(cache_key, deserialize=serialize)
            if result is not None:
                return result
            
            # Compute and cache
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl, serialize=serialize)
            
            return result
        
        return wrapper
    return decorator

"""
Data Mesh Query Caching
Implements Redis-based caching for data product queries.
"""

from typing import Optional, Any, Dict
import json
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataProductCache:
    """Cache for data product queries with Redis backend."""
    
    def __init__(self, redis_client=None, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            redis_client: Redis client instance (optional, will use in-memory if None)
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, tuple] = {}  # Fallback in-memory cache
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0
        }
        
        logger.info(f"DataProductCache initialized (TTL: {default_ttl}s)")
    
    def _generate_cache_key(
        self,
        product_id: str,
        filters: Optional[Dict] = None,
        fields: Optional[list] = None
    ) -> str:
        """Generate cache key from query parameters."""
        key_parts = [product_id]
        
        if filters:
            # Sort filters for consistent keys
            filter_str = json.dumps(filters, sort_keys=True)
            key_parts.append(hashlib.md5(filter_str.encode()).hexdigest())
        
        if fields:
            # Sort fields for consistent keys
            fields_str = ",".join(sorted(fields))
            key_parts.append(hashlib.md5(fields_str.encode()).hexdigest())
        
        return f"product:{':'.join(key_parts)}"
    
    def get(
        self,
        product_id: str,
        filters: Optional[Dict] = None,
        fields: Optional[list] = None
    ) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            product_id: Data product ID
            filters: Query filters
            fields: Requested fields
            
        Returns:
            Cached result or None if not found
        """
        cache_key = self._generate_cache_key(product_id, filters, fields)
        
        try:
            if self.redis:
                # Try Redis first
                cached = self.redis.get(cache_key)
                if cached:
                    self.stats["hits"] += 1
                    logger.debug(f"Cache HIT: {cache_key}")
                    return json.loads(cached)
            else:
                # Use in-memory cache
                if cache_key in self.memory_cache:
                    value, expiry = self.memory_cache[cache_key]
                    if datetime.utcnow() < expiry:
                        self.stats["hits"] += 1
                        logger.debug(f"Cache HIT (memory): {cache_key}")
                        return value
                    else:
                        # Expired
                        del self.memory_cache[cache_key]
            
            self.stats["misses"] += 1
            logger.debug(f"Cache MISS: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(
        self,
        product_id: str,
        value: Any,
        filters: Optional[Dict] = None,
        fields: Optional[list] = None,
        ttl: Optional[int] = None
    ):
        """
        Set cached query result.
        
        Args:
            product_id: Data product ID
            value: Result to cache
            filters: Query filters
            fields: Requested fields
            ttl: TTL in seconds (uses default if None)
        """
        cache_key = self._generate_cache_key(product_id, filters, fields)
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis:
                # Store in Redis
                self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(value)
                )
            else:
                # Store in memory
                expiry = datetime.utcnow() + timedelta(seconds=ttl)
                self.memory_cache[cache_key] = (value, expiry)
            
            self.stats["sets"] += 1
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def invalidate(self, product_id: str):
        """
        Invalidate all cache entries for a product.
        
        Args:
            product_id: Data product ID
        """
        try:
            if self.redis:
                # Delete all keys matching pattern
                pattern = f"product:{product_id}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    self.stats["invalidations"] += len(keys)
                    logger.info(f"Invalidated {len(keys)} cache entries for {product_id}")
            else:
                # Delete from memory cache
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if k.startswith(f"product:{product_id}:")
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                
                self.stats["invalidations"] += len(keys_to_delete)
                logger.info(f"Invalidated {len(keys_to_delete)} memory cache entries for {product_id}")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        try:
            if self.redis:
                pattern = "product:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Cleared {len(keys)} cache entries")
            else:
                count = len(self.memory_cache)
                self.memory_cache.clear()
                logger.info(f"Cleared {count} memory cache entries")
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "cache_type": "redis" if self.redis else "memory"
        }
    
    def warm_cache(self, product_id: str, common_queries: list):
        """
        Warm cache with common queries.
        
        Args:
            product_id: Data product ID
            common_queries: List of (filters, fields) tuples
        """
        logger.info(f"Warming cache for {product_id} with {len(common_queries)} queries")
        
        # This would be called after product refresh
        # Implementation depends on data product interface
        pass


class CacheWarmer:
    """Automatic cache warming on product refresh."""
    
    def __init__(self, cache: DataProductCache, registry):
        self.cache = cache
        self.registry = registry
        self.common_queries = {}  # Track common query patterns
    
    def track_query(
        self,
        product_id: str,
        filters: Optional[Dict] = None,
        fields: Optional[list] = None
    ):
        """Track query for cache warming."""
        if product_id not in self.common_queries:
            self.common_queries[product_id] = []
        
        query = (filters, fields)
        if query not in self.common_queries[product_id]:
            self.common_queries[product_id].append(query)
    
    async def warm_on_refresh(self, product_id: str):
        """Warm cache after product refresh."""
        if product_id not in self.common_queries:
            return
        
        logger.info(f"Warming cache for {product_id}")
        
        for filters, fields in self.common_queries[product_id][:10]:  # Top 10 queries
            try:
                # Query product and cache result
                result = await self.registry.query_product(
                    product_id,
                    filters=filters,
                    fields=fields
                )
                
                self.cache.set(
                    product_id,
                    result,
                    filters=filters,
                    fields=fields
                )
                
            except Exception as e:
                logger.error(f"Cache warming error: {e}")


# Global cache instance
_cache_instance: Optional[DataProductCache] = None


def get_cache() -> DataProductCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataProductCache()
    return _cache_instance


def init_cache(redis_client=None, default_ttl: int = 3600):
    """Initialize global cache with Redis client."""
    global _cache_instance
    _cache_instance = DataProductCache(redis_client, default_ttl)
    return _cache_instance

"""
Redis Cache Integration Tests

Tests for Redis caching layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
import pickle

from ultracore.cache.redis_cache import RedisCache, CacheManager


class TestRedisCache:
    """Test Redis cache (mocked)"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        client = AsyncMock()
        client.ping.return_value = True
        client.get.return_value = None
        client.setex.return_value = True
        client.delete.return_value = 1
        client.exists.return_value = True
        client.expire.return_value = True
        client.ttl.return_value = 3600
        return client
    
    @pytest.fixture
    @patch('ultracore.cache.redis_cache.redis')
    def cache(self, mock_redis_module, mock_redis):
        """Create Redis cache with mock client"""
        mock_redis_module.ConnectionPool.return_value = Mock()
        mock_redis_module.Redis.return_value = mock_redis
        
        cache = RedisCache(namespace="test")
        cache.client = mock_redis
        return cache
    
    @pytest.mark.asyncio
    async def test_connect(self, cache, mock_redis):
        """Test Redis connection"""
        # Connection is already established in fixture
        assert cache.client is not None
    
    @pytest.mark.asyncio
    async def test_set_and_get_json(self, cache, mock_redis):
        """Test set and get with JSON serialization"""
        test_data = {"key": "value", "number": 123}
        
        # Mock get to return serialized data
        mock_redis.get.return_value = json.dumps(test_data).encode()
        
        # Set
        await cache.set("test_key", test_data, ttl=300)
        mock_redis.setex.assert_called_once()
        
        # Get
        result = await cache.get("test_key")
        assert result == test_data
    
    @pytest.mark.asyncio
    async def test_set_and_get_pickle(self, cache, mock_redis):
        """Test set and get with pickle serialization"""
        test_data = {"complex": object(), "list": [1, 2, 3]}
        
        # Mock get to return pickled data
        mock_redis.get.return_value = pickle.dumps(test_data)
        
        # Set
        await cache.set("test_key", test_data, serialize="pickle")
        
        # Get
        result = await cache.get("test_key", deserialize="pickle")
        # Can't compare objects directly, just check type
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_delete(self, cache, mock_redis):
        """Test delete"""
        result = await cache.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exists(self, cache, mock_redis):
        """Test exists"""
        result = await cache.exists("test_key")
        assert result is True
        mock_redis.exists.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_expire(self, cache, mock_redis):
        """Test expire"""
        result = await cache.expire("test_key", 600)
        assert result is True
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ttl(self, cache, mock_redis):
        """Test TTL"""
        result = await cache.ttl("test_key")
        assert result == 3600
        mock_redis.ttl.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache, mock_redis):
        """Test pattern invalidation"""
        # Mock scan_iter to return AsyncMock that can be async iterated
        async def mock_scan_iter(*args, **kwargs):
            for key in [b"test:key1", b"test:key2"]:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2
        
        result = await cache.invalidate_pattern("key*")
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_get_or_set(self, cache, mock_redis):
        """Test get_or_set"""
        # First call - not in cache
        mock_redis.get.return_value = None
        
        def factory():
            return {"computed": True}
        
        result = await cache.get_or_set("test_key", factory)
        assert result == {"computed": True}
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_increment(self, cache, mock_redis):
        """Test increment"""
        mock_redis.incrby.return_value = 5
        
        result = await cache.increment("counter", 1)
        assert result == 5
        mock_redis.incrby.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_operations(self, cache, mock_redis):
        """Test list operations"""
        # Push
        mock_redis.rpush.return_value = 1
        await cache.list_push("list_key", "value1", "value2")
        mock_redis.rpush.assert_called_once()
        
        # Pop
        mock_redis.lpop.return_value = json.dumps("value1").encode()
        result = await cache.list_pop("list_key")
        assert result == "value1"
        
        # Range
        mock_redis.lrange.return_value = [
            json.dumps("value1").encode(),
            json.dumps("value2").encode()
        ]
        result = await cache.list_range("list_key")
        assert result == ["value1", "value2"]
    
    @pytest.mark.asyncio
    async def test_hash_operations(self, cache, mock_redis):
        """Test hash operations"""
        # Set
        mock_redis.hset.return_value = True
        await cache.hash_set("hash_key", "field1", "value1")
        mock_redis.hset.assert_called_once()
        
        # Get
        mock_redis.hget.return_value = json.dumps("value1").encode()
        result = await cache.hash_get("hash_key", "field1")
        assert result == "value1"
        
        # Get all
        mock_redis.hgetall.return_value = {
            b"field1": json.dumps("value1").encode(),
            b"field2": json.dumps("value2").encode()
        }
        result = await cache.hash_get_all("hash_key")
        assert result == {"field1": "value1", "field2": "value2"}
        
        # Delete
        mock_redis.hdel.return_value = 1
        result = await cache.hash_delete("hash_key", "field1")
        assert result == 1


class TestCacheManager:
    """Test cache manager"""
    
    @pytest.fixture
    def mock_cache(self):
        """Create mock Redis cache"""
        cache = AsyncMock()
        cache.get.return_value = None
        cache.set.return_value = True
        cache.delete.return_value = True
        cache.increment.return_value = 1
        cache.expire.return_value = True
        return cache
    
    @pytest.fixture
    def manager(self, mock_cache):
        """Create cache manager"""
        return CacheManager(mock_cache)
    
    @pytest.mark.asyncio
    async def test_session_management(self, manager, mock_cache):
        """Test session management"""
        # Set session
        await manager.set_session(
            "sess_123",
            "user_456",
            {"role": "admin"},
            ttl=3600
        )
        mock_cache.set.assert_called_once()
        
        # Get session
        mock_cache.get.return_value = {
            "user_id": "user_456",
            "role": "admin"
        }
        result = await manager.get_session("sess_123")
        assert result["user_id"] == "user_456"
        
        # Delete session
        await manager.delete_session("sess_123")
        mock_cache.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_account_caching(self, manager, mock_cache):
        """Test account caching"""
        account_data = {
            "account_id": "acc_123",
            "balance": 10000.0,
            "status": "active"
        }
        
        # Cache account
        await manager.cache_account("tenant_1", "acc_123", account_data)
        mock_cache.set.assert_called_once()
        
        # Get cached account
        mock_cache.get.return_value = account_data
        result = await manager.get_cached_account("tenant_1", "acc_123")
        assert result["account_id"] == "acc_123"
        
        # Invalidate
        await manager.invalidate_account("tenant_1", "acc_123")
        mock_cache.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ml_prediction_caching(self, manager, mock_cache):
        """Test ML prediction caching"""
        prediction = {"score": 0.85, "label": "fraud"}
        
        # Cache prediction
        await manager.cache_ml_prediction(
            "fraud_detector",
            "input_hash_123",
            prediction
        )
        mock_cache.set.assert_called_once()
        
        # Get cached prediction
        mock_cache.get.return_value = prediction
        result = await manager.get_cached_prediction(
            "fraud_detector",
            "input_hash_123"
        )
        assert result["score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_q_table_caching(self, manager, mock_cache):
        """Test RL Q-table caching"""
        q_table = {(0, 0): 0.5, (0, 1): 0.3}
        
        # Cache Q-table
        await manager.cache_q_table("access_control_agent", q_table)
        mock_cache.set.assert_called_once()
        
        # Get cached Q-table
        mock_cache.get.return_value = q_table
        result = await manager.get_cached_q_table("access_control_agent")
        assert result == q_table
    
    @pytest.mark.asyncio
    async def test_user_profile_caching(self, manager, mock_cache):
        """Test user profile caching"""
        profile = {
            "user_id": "user_123",
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        # Cache profile
        await manager.cache_user_profile("tenant_1", "user_123", profile)
        mock_cache.set.assert_called_once()
        
        # Get cached profile
        mock_cache.get.return_value = profile
        result = await manager.get_cached_user_profile("tenant_1", "user_123")
        assert result["user_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, manager, mock_cache):
        """Test rate limiting"""
        # First request - under limit
        mock_cache.increment.return_value = 1
        result = await manager.check_rate_limit("api:user_123", 100, 60)
        assert result is True
        
        # 101st request - over limit
        mock_cache.increment.return_value = 101
        result = await manager.check_rate_limit("api:user_123", 100, 60)
        assert result is False

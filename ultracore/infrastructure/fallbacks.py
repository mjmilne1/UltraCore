"""
Infrastructure Fallbacks and Mock System
Provides graceful degradation when external services are unavailable
"""

import logging
from typing import Optional, Any, Dict
from contextlib import contextmanager
import asyncio

logger = logging.getLogger(__name__)

class InfrastructureManager:
    """
    Manages infrastructure dependencies with fallback support
    """
    
    def __init__(self):
        self.kafka_available = False
        self.redis_available = False
        self.postgres_available = False
        self.mock_mode = False
        
    async def check_kafka(self) -> bool:
        """Check if Kafka is available"""
        try:
            # Try to connect to Kafka
            from aiokafka import AIOKafkaProducer
            producer = AIOKafkaProducer(
                bootstrap_servers='localhost:9092',
                request_timeout_ms=5000
            )
            await asyncio.wait_for(producer.start(), timeout=5.0)
            await producer.stop()
            self.kafka_available = True
            logger.info("Kafka is available")
            return True
        except Exception as e:
            logger.warning(f"Kafka unavailable: {e}. Using mock mode.")
            self.kafka_available = False
            self.mock_mode = True
            return False
    
    async def check_redis(self) -> bool:
        """Check if Redis is available"""
        try:
            import redis.asyncio as redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
            await r.ping()
            await r.close()
            self.redis_available = True
            logger.info("Redis is available")
            return True
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Using in-memory cache.")
            self.redis_available = False
            return False
    
    async def check_postgres(self) -> bool:
        """Check if PostgreSQL is available"""
        try:
            import asyncpg
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host='localhost',
                    port=5432,
                    user='ultracore',
                    password='ultracore',
                    database='ultracore'
                ),
                timeout=5.0
            )
            await conn.close()
            self.postgres_available = True
            logger.info("PostgreSQL is available")
            return True
        except Exception as e:
            logger.warning(f"PostgreSQL unavailable: {e}. Using in-memory storage.")
            self.postgres_available = False
            return False
    
    async def check_all(self) -> Dict[str, bool]:
        """Check all infrastructure components"""
        results = {
            'kafka': await self.check_kafka(),
            'redis': await self.check_redis(),
            'postgres': await self.check_postgres()
        }
        
        if not all(results.values()):
            logger.warning("Some infrastructure components unavailable. Running in degraded mode.")
        else:
            logger.info("All infrastructure components available")
        
        return results

# Global infrastructure manager
infra_manager = InfrastructureManager()

class MockKafkaProducer:
    """Mock Kafka producer for offline operation"""
    
    def __init__(self, *args, **kwargs):
        self.messages = []
        logger.info("Using MockKafkaProducer (Kafka unavailable)")
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    async def send_and_wait(self, topic: str, value: Any, key: Optional[str] = None):
        """Mock send - stores message in memory"""
        self.messages.append({
            'topic': topic,
            'value': value,
            'key': key
        })
        logger.debug(f"Mock Kafka: Stored message to topic '{topic}'")
        return None
    
    def get_messages(self, topic: Optional[str] = None):
        """Get stored messages"""
        if topic:
            return [m for m in self.messages if m['topic'] == topic]
        return self.messages

class MockRedisClient:
    """Mock Redis client for offline operation"""
    
    def __init__(self, *args, **kwargs):
        self.data = {}
        logger.info("Using MockRedisClient (Redis unavailable)")
    
    async def get(self, key: str):
        return self.data.get(key)
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        self.data[key] = value
        logger.debug(f"Mock Redis: Set key '{key}'")
    
    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
    
    async def ping(self):
        return True
    
    async def close(self):
        pass

class MockDatabaseConnection:
    """Mock database connection for offline operation"""
    
    def __init__(self):
        self.data = {}
        logger.info("Using MockDatabaseConnection (PostgreSQL unavailable)")
    
    async def execute(self, query: str, *args):
        logger.debug(f"Mock DB: Execute query: {query[:100]}")
        return "OK"
    
    async def fetch(self, query: str, *args):
        logger.debug(f"Mock DB: Fetch query: {query[:100]}")
        return []
    
    async def fetchrow(self, query: str, *args):
        logger.debug(f"Mock DB: Fetchrow query: {query[:100]}")
        return None
    
    async def close(self):
        pass

@contextmanager
def kafka_fallback():
    """Context manager for Kafka with fallback to mock"""
    if infra_manager.kafka_available:
        from aiokafka import AIOKafkaProducer
        yield AIOKafkaProducer
    else:
        yield MockKafkaProducer

@contextmanager
def redis_fallback():
    """Context manager for Redis with fallback to mock"""
    if infra_manager.redis_available:
        import redis.asyncio as redis
        yield redis.Redis
    else:
        yield MockRedisClient

@contextmanager
def database_fallback():
    """Context manager for database with fallback to mock"""
    if infra_manager.postgres_available:
        import asyncpg
        yield asyncpg.connect
    else:
        async def mock_connect(*args, **kwargs):
            return MockDatabaseConnection()
        yield mock_connect

async def get_kafka_producer():
    """Get Kafka producer with automatic fallback"""
    if infra_manager.kafka_available:
        try:
            from aiokafka import AIOKafkaProducer
            producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
            await producer.start()
            return producer
        except Exception as e:
            logger.warning(f"Failed to create Kafka producer: {e}. Using mock.")
            return MockKafkaProducer()
    else:
        return MockKafkaProducer()

async def get_redis_client():
    """Get Redis client with automatic fallback"""
    if infra_manager.redis_available:
        try:
            import redis.asyncio as redis
            client = redis.Redis(host='localhost', port=6379)
            await client.ping()
            return client
        except Exception as e:
            logger.warning(f"Failed to create Redis client: {e}. Using mock.")
            return MockRedisClient()
    else:
        return MockRedisClient()

async def get_database_connection():
    """Get database connection with automatic fallback"""
    if infra_manager.postgres_available:
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='ultracore',
                password='ultracore',
                database='ultracore'
            )
            return conn
        except Exception as e:
            logger.warning(f"Failed to create database connection: {e}. Using mock.")
            return MockDatabaseConnection()
    else:
        return MockDatabaseConnection()

class HealthCheck:
    """Health check for all infrastructure components"""
    
    @staticmethod
    async def check() -> Dict[str, Any]:
        """Perform health check on all components"""
        results = await infra_manager.check_all()
        
        return {
            'status': 'healthy' if all(results.values()) else 'degraded',
            'components': {
                'kafka': {
                    'status': 'up' if results['kafka'] else 'down',
                    'mock': not results['kafka']
                },
                'redis': {
                    'status': 'up' if results['redis'] else 'down',
                    'mock': not results['redis']
                },
                'postgres': {
                    'status': 'up' if results['postgres'] else 'down',
                    'mock': not results['postgres']
                }
            },
            'mock_mode': infra_manager.mock_mode
        }

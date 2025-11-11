"""
UltraCore Database Configuration

Multi-database setup:
- PostgreSQL: Relational data (customers, accounts, loans, transactions)
- Redis: Caching, sessions, distributed locks (OPTIONAL)
- Neo4j: Graph data (relationships, fraud detection) (OPTIONAL)
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncGenerator, Generator, Optional
import logging

# Optional imports (graceful degradation)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None

from ultracore.api.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# SQLAlchemy Base
# ============================================================================

Base = declarative_base()

# Metadata for explicit schema separation (Data Mesh)
metadata_customers = Base.metadata
metadata_accounts = Base.metadata
metadata_lending = Base.metadata
metadata_events = Base.metadata


# ============================================================================
# PostgreSQL Configuration
# ============================================================================

class DatabaseManager:
    """
    Central database manager
    
    Features:
    - Connection pooling
    - Async support
    - Transaction management
    - Event sourcing support
    - Multi-tenant support
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Sync engine (for migrations, admin tasks)
        self.engine = None
        self.SessionLocal = None
        
        # Async engine (for API operations)
        self.async_engine = None
        self.AsyncSessionLocal = None
        
        # Redis (optional)
        self.redis_client = None
        
        # Neo4j (optional)
        self.neo4j_driver = None
        
        self._initialized = False
    
    def initialize(self):
        """Initialize all database connections"""
        if self._initialized:
            return
        
        logger.info("Initializing database connections...")
        
        # PostgreSQL (required)
        self._init_postgresql()
        
        # Redis (optional)
        if REDIS_AVAILABLE:
            self._init_redis()
        else:
            logger.info("⊘ Redis not installed (optional - install with: pip install redis)")
        
        # Neo4j (optional)
        if NEO4J_AVAILABLE:
            self._init_neo4j()
        else:
            logger.info("⊘ Neo4j not installed (optional - install with: pip install neo4j)")
        
        self._initialized = True
        logger.info("✓ Database connections initialized")
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connections"""
        database_url = self.settings.database_url or "sqlite:///./ultracore.db"
        
        # Sync engine
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool if "postgresql" in database_url else NullPool,
            pool_size=20 if "postgresql" in database_url else 5,
            max_overflow=40 if "postgresql" in database_url else 10,
            pool_pre_ping=True,
            echo=False,
            connect_args={"options": "-c timezone=utc"} if "postgresql" in database_url else {}
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Async engine
        if "postgresql" in database_url:
            async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            async_database_url = database_url
        
        self.async_engine = create_async_engine(
            async_database_url,
            poolclass=QueuePool if "postgresql" in database_url else NullPool,
            pool_size=20 if "postgresql" in database_url else 5,
            max_overflow=40 if "postgresql" in database_url else 10,
            pool_pre_ping=True,
            echo=False
        )
        
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        db_type = "SQLite" if "sqlite" in database_url else database_url.split('@')[-1] if '@' in database_url else database_url
        logger.info(f"✓ Database connected: {db_type}")
    
    def _init_redis(self):
        """Initialize Redis connection"""
        redis_url = self.settings.redis_url
        
        if redis_url and redis is not None:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✓ Redis connected: {redis_url.split('@')[-1]}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        else:
            logger.info("⊘ Redis not configured (optional)")
    
    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        neo4j_uri = getattr(self.settings, 'neo4j_uri', None)
        neo4j_user = getattr(self.settings, 'neo4j_user', None)
        neo4j_password = getattr(self.settings, 'neo4j_password', None)
        
        if neo4j_uri and neo4j_user and neo4j_password and GraphDatabase is not None:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=120
                )
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                logger.info(f"✓ Neo4j connected: {neo4j_uri}")
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}")
                self.neo4j_driver = None
        else:
            logger.info("⊘ Neo4j not configured (optional)")
    
    def create_tables(self):
        """Create all tables (for initial setup)"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✓ Database tables created")
    
    def close(self):
        """Close all connections"""
        if self.engine:
            self.engine.dispose()
        
        if self.redis_client:
            self.redis_client.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        logger.info("✓ Database connections closed")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get sync database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# Global Database Manager Instance
# ============================================================================

_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get singleton database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints"""
    db_manager = get_db_manager()
    async with db_manager.get_async_session() as session:
        yield session


# ============================================================================
# Redis Cache Helper
# ============================================================================

class CacheManager:
    """Redis cache manager with graceful degradation"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.db_manager.redis_client:
            return None
        try:
            return self.db_manager.redis_client.get(key)
        except Exception:
            return None
    
    async def set(self, key: str, value: str, expiry: int = 3600):
        """Set value in cache"""
        if not self.db_manager.redis_client:
            return
        try:
            self.db_manager.redis_client.setex(key, expiry, value)
        except Exception:
            pass
    
    async def delete(self, key: str):
        """Delete from cache"""
        if not self.db_manager.redis_client:
            return
        try:
            self.db_manager.redis_client.delete(key)
        except Exception:
            pass
    
    async def get_or_set(self, key: str, func, expiry: int = 3600):
        """Get from cache or execute function and cache result"""
        cached = await self.get(key)
        if cached:
            return cached
        
        result = await func()
        await self.set(key, result, expiry)
        return result


def get_cache_manager() -> CacheManager:
    """Get cache manager"""
    return CacheManager()

"""
Database Base Configuration
SQLAlchemy async setup for PostgreSQL
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, DateTime, String
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name"""
        return cls.__name__.lower()
    
    # Common columns for all tables (can be overridden in subclasses)
    pass


class DatabaseConfig:
    """Database configuration and session management"""
    
    def __init__(
        self,
        database_url: str = "postgresql+asyncpg://ultracore:ultracore_password@localhost:5432/ultracore",
        echo: bool = False
    ):
        self.database_url = database_url
        self.echo = echo
        
        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info(f"✓ Database configured: {database_url}")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_all_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ All tables created")
    
    async def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("✓ All tables dropped")
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("✓ Database connections closed")


# ============================================================================
# Singleton
# ============================================================================

_db_config: DatabaseConfig | None = None


def get_database_config(
    database_url: str = "postgresql+asyncpg://ultracore:ultracore_password@localhost:5432/ultracore",
    echo: bool = False
) -> DatabaseConfig:
    """Get singleton database configuration"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig(database_url, echo)
    return _db_config


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (dependency injection helper)"""
    db_config = get_database_config()
    async for session in db_config.get_session():
        yield session


# Alias for consistency
get_async_session = get_db_session

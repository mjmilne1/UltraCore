"""
Database Initialization for UltraWealth

Creates all tables and sets up database schema
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from ultrawealth.models.wealth_models import Base


def get_database_url() -> str:
    """Get database URL from environment or use default"""
    return os.getenv(
        'ULTRAWEALTH_DATABASE_URL',
        'postgresql://ultracore:ultracore_password@localhost:5432/ultracore'
    )


def init_database():
    """Initialize database with all tables"""
    
    database_url = get_database_url()
    
    print(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url, echo=True)
    
    # Create all tables
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    
    print("✅ Database initialized successfully!")
    
    return engine


def get_session():
    """Get database session"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()


if __name__ == "__main__":
    init_database()

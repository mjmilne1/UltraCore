"""
UltraCore Database Initialization

Script to initialize the database:
1. Create schemas
2. Create tables
3. Create indexes
4. Insert initial data (if needed)
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ultracore.database.config import get_db_manager
from ultracore.database.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database"""
    
    logger.info("🗄️  Initializing UltraCore Database...")
    logger.info("=" * 70)
    
    # Get database manager
    db_manager = get_db_manager()
    
    logger.info(f"Database: {db_manager.settings.database_url or 'SQLite (default)'}")
    
    # Create all tables
    logger.info("\n📊 Creating tables...")
    Base.metadata.create_all(bind=db_manager.engine)
    
    logger.info("✅ Tables created:")
    for table in Base.metadata.sorted_tables:
        logger.info(f"  ✓ {table.name}")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Database initialization complete!")
    logger.info("\n💡 Next steps:")
    logger.info("  1. Run migrations: alembic upgrade head")
    logger.info("  2. Start API: python run.py")
    logger.info("  3. Access docs: http://localhost:8000/api/v1/docs")


if __name__ == "__main__":
    init_database()

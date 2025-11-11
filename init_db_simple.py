"""
Simple database initialization (bypasses import issues)
"""
import os
os.environ['PYTHONPATH'] = r'C:\Users\mjmil\ultracore-working\src'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "postgresql://ultracore:ultracore_password@localhost:5432/ultracore"

print("🗄️  Connecting to PostgreSQL...")
engine = create_engine(DATABASE_URL)

print("📊 Creating tables...")

# Create basic tables
with engine.connect() as conn:
    # Create processed_events table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS processed_events (
            id BIGSERIAL PRIMARY KEY,
            event_id VARCHAR(50) UNIQUE NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            aggregate_id VARCHAR(100) NOT NULL,
            tenant_id VARCHAR(50) NOT NULL,
            processed_at TIMESTAMP NOT NULL,
            consumer_group VARCHAR(100)
        )
    """))
    
    # Create customers schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS customers"))
    
    # Create accounts schema  
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS accounts"))
    
    # Create lending schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS lending"))
    
    conn.commit()

print("✅ Database initialized (basic tables)")
print("")
print("💡 You can now:")
print("   1. pip install kafka-python")
print("   2. python run.py")
print("   3. Test at http://localhost:8000/api/v1/docs")

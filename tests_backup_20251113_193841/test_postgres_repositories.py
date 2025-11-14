"""
PostgreSQL Integration Tests for Database Repositories
Tests the repository pattern with actual PostgreSQL database
"""

import pytest
import asyncio
import os
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ultracore.database.base import Base
from ultracore.database.models.security import (
    User, SecurityEvent, ThreatEvent, SecurityIncident,
    RefreshToken, TrustedDevice, MFABackupCode, AuditLog
)
from ultracore.database.repositories import (
    UserRepository,
    SecurityEventRepository,
    ThreatEventRepository,
    SecurityIncidentRepository,
    AuditLogRepository
)


# ============================================================================
# Database Configuration
# ============================================================================

# PostgreSQL connection string from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ultracore:ultracore_password@localhost:5432/ultracore_test"
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def engine():
    """Create PostgreSQL database engine"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create database session"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return uuid4()


# ============================================================================
# User Repository Tests
# ============================================================================

@pytest.mark.asyncio
async def test_user_repository_create(session, tenant_id):
    """Test creating a user"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="customer",
        first_name="Test",
        last_name="User"
    )
    
    created_user = await repo.create(user)
    await session.commit()
    
    assert created_user.user_id is not None
    assert created_user.username == "testuser"
    assert created_user.email == "test@example.com"
    assert created_user.is_active == True
    assert created_user.trust_score == 50.0
    
    print(f"✓ Created user: {created_user.user_id}")


@pytest.mark.asyncio
async def test_user_repository_get_by_username(session, tenant_id):
    """Test getting user by username"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser2",
        email="test2@example.com",
        password_hash="hashed_password",
        role="customer"
    )
    
    await repo.create(user)
    await session.commit()
    
    found_user = await repo.get_by_username("testuser2")
    
    assert found_user is not None
    assert found_user.username == "testuser2"
    
    print(f"✓ Found user by username: {found_user.user_id}")


@pytest.mark.asyncio
async def test_user_repository_verify_credentials(session, tenant_id):
    """Test verifying user credentials"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser3",
        email="test3@example.com",
        password_hash="correct_password",
        role="customer"
    )
    
    await repo.create(user)
    await session.commit()
    
    # Correct password
    verified_user = await repo.verify_credentials("testuser3", "correct_password")
    assert verified_user is not None
    assert verified_user.username == "testuser3"
    
    # Incorrect password
    verified_user = await repo.verify_credentials("testuser3", "wrong_password")
    assert verified_user is None
    
    print("✓ Verified user credentials")


@pytest.mark.asyncio
async def test_user_repository_mfa(session, tenant_id):
    """Test MFA management"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser4",
        email="test4@example.com",
        password_hash="hashed_password",
        role="customer"
    )
    
    created_user = await repo.create(user)
    await session.commit()
    
    # Enable MFA
    await repo.enable_mfa(created_user.user_id, "secret_key")
    await session.commit()
    
    updated_user = await repo.get(created_user.user_id)
    assert updated_user.mfa_enabled == True
    assert updated_user.mfa_secret == "secret_key"
    
    # Create backup codes
    code_hashes = ["hash1", "hash2", "hash3"]
    backup_codes = await repo.create_backup_codes(created_user.user_id, code_hashes)
    await session.commit()
    
    assert len(backup_codes) == 3
    
    # Use backup code
    success = await repo.use_backup_code(created_user.user_id, "hash1")
    await session.commit()
    assert success == True
    
    # Try to use same code again
    success = await repo.use_backup_code(created_user.user_id, "hash1")
    assert success == False
    
    print("✓ MFA management working")


@pytest.mark.asyncio
async def test_user_repository_refresh_tokens(session, tenant_id):
    """Test refresh token management"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser5",
        email="test5@example.com",
        password_hash="hashed_password",
        role="customer"
    )
    
    created_user = await repo.create(user)
    await session.commit()
    
    # Create refresh token
    expires_at = datetime.utcnow() + timedelta(days=7)
    token = await repo.create_refresh_token(
        created_user.user_id,
        "token_hash_123",
        expires_at,
        device_fingerprint="device123",
        ip_address="192.168.1.1"
    )
    await session.commit()
    
    assert token.token_id is not None
    assert token.token_hash == "token_hash_123"
    
    # Get refresh token
    found_token = await repo.get_refresh_token("token_hash_123")
    assert found_token is not None
    
    # Revoke token
    await repo.revoke_refresh_token("token_hash_123")
    await session.commit()
    
    revoked_token = await repo.get_refresh_token("token_hash_123")
    assert revoked_token.revoked_at is not None
    
    print("✓ Refresh token management working")


@pytest.mark.asyncio
async def test_user_repository_trusted_devices(session, tenant_id):
    """Test trusted device management"""
    repo = UserRepository(session)
    
    user = User(
        tenant_id=tenant_id,
        username="testuser6",
        email="test6@example.com",
        password_hash="hashed_password",
        role="customer"
    )
    
    created_user = await repo.create(user)
    await session.commit()
    
    # Get or create device
    device = await repo.get_or_create_device(
        created_user.user_id,
        "device_fingerprint_123",
        device_name="iPhone 13 Pro",
        device_type="mobile",
        ip_address="192.168.1.1"
    )
    await session.commit()
    
    assert device.device_id is not None
    assert device.device_fingerprint == "device_fingerprint_123"
    assert device.is_trusted == False
    
    # Trust device
    await repo.trust_device(device.device_id)
    await session.commit()
    
    # Get device again (should update last_seen)
    device2 = await repo.get_or_create_device(
        created_user.user_id,
        "device_fingerprint_123",
        ip_address="192.168.1.2"
    )
    await session.commit()
    
    assert device2.device_id == device.device_id
    assert device2.is_trusted == True
    
    print("✓ Trusted device management working")


@pytest.mark.asyncio
async def test_security_event_repository(session, tenant_id):
    """Test security event repository"""
    repo = SecurityEventRepository(session)
    
    # Create multiple events
    events = [
        SecurityEvent(
            tenant_id=tenant_id,
            event_type="login_attempt",
            event_category="authentication",
            severity="low"
        ),
        SecurityEvent(
            tenant_id=tenant_id,
            event_type="login_failure",
            event_category="authentication",
            severity="medium"
        ),
        SecurityEvent(
            tenant_id=tenant_id,
            event_type="fraud_detected",
            event_category="threat",
            severity="high",
            risk_score=85.0
        ),
    ]
    
    await repo.create_many(events)
    await session.commit()
    
    # Count by type
    counts_by_type = await repo.count_by_type(tenant_id)
    assert counts_by_type["login_attempt"] == 1
    assert counts_by_type["login_failure"] == 1
    assert counts_by_type["fraud_detected"] == 1
    
    # Count by severity
    counts_by_severity = await repo.count_by_severity(tenant_id)
    assert counts_by_severity["low"] == 1
    assert counts_by_severity["medium"] == 1
    assert counts_by_severity["high"] == 1
    
    # Get high-risk events
    high_risk_events = await repo.get_high_risk_events(tenant_id, min_risk_score=70.0)
    assert len(high_risk_events) == 1
    assert high_risk_events[0].event_type == "fraud_detected"
    
    print("✓ Security event repository working")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PostgreSQL Repository Integration Tests")
    print("=" * 80)
    print(f"Database URL: {DATABASE_URL}")
    print()
    print("Run with: pytest tests/test_postgres_repositories.py -v")
    print("=" * 80)

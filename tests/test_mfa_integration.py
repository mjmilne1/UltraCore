"""
MFA Integration Tests with PostgreSQL
Tests TOTP service, event sourcing, and API endpoints
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
import pyotp

from ultracore.database.base import create_async_engine, Base
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from ultracore.database.repositories.user_repository import UserRepository
from ultracore.database.models.security import User
from ultracore.security.mfa.totp_service import create_totp_service
from ultracore.security.mfa.event_producer import create_mfa_event_producer


# ============================================================================
# Test Configuration
# ============================================================================

DATABASE_URL = "postgresql+asyncpg://ultracore:ultracore_password@localhost:5432/ultracore_test"


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
    )
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(engine):
    """Create database session"""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def user_repo(session):
    """Create user repository"""
    return UserRepository(session)


@pytest.fixture(scope="function")
async def totp_service(user_repo):
    """Create TOTP service"""
    return create_totp_service(user_repo)


@pytest.fixture(scope="function")
async def event_producer():
    """Create MFA event producer"""
    return create_mfa_event_producer()


@pytest.fixture(scope="function")
async def test_user(user_repo, session):
    """Create test user"""
    user = User(
        user_id=uuid4(),
        tenant_id=uuid4(),
        username=f"testuser_{uuid4().hex[:8]}",
        email=f"test_{uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
        role="user",
        mfa_enabled=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    created_user = await user_repo.create(user)
    await session.commit()
    
    yield created_user
    
    # Cleanup
    await session.delete(created_user)
    await session.commit()


# ============================================================================
# TOTP Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_generate_secret(totp_service):
    """Test TOTP secret generation"""
    secret = totp_service.generate_secret()
    
    assert secret is not None
    assert len(secret) == 32  # Base32 encoded
    assert secret.isalnum()  # Only alphanumeric characters
    
    print(f"✓ Generated secret: {secret[:8]}...")


@pytest.mark.asyncio
async def test_generate_qr_code(totp_service, test_user):
    """Test QR code generation"""
    secret = totp_service.generate_secret()
    uri = totp_service.generate_provisioning_uri(test_user, secret)
    qr_code = totp_service.generate_qr_code(uri)
    
    assert qr_code.startswith("data:image/png;base64,")
    assert len(qr_code) > 100  # Should be substantial
    
    print(f"✓ Generated QR code ({len(qr_code)} bytes)")


@pytest.mark.asyncio
async def test_verify_totp(totp_service):
    """Test TOTP verification"""
    secret = totp_service.generate_secret()
    totp = pyotp.TOTP(secret)
    
    # Generate valid token
    valid_token = totp.now()
    
    # Verify token
    is_valid, timestamp = totp_service.verify_totp(secret, valid_token)
    
    assert is_valid is True
    assert timestamp is not None
    
    print(f"✓ TOTP verification successful (timestamp: {timestamp})")


@pytest.mark.asyncio
async def test_verify_totp_invalid_token(totp_service):
    """Test TOTP verification with invalid token"""
    secret = totp_service.generate_secret()
    
    # Invalid token
    invalid_token = "000000"
    
    # Verify token
    is_valid, timestamp = totp_service.verify_totp(secret, invalid_token)
    
    assert is_valid is False
    assert timestamp is None
    
    print("✓ Invalid TOTP correctly rejected")


@pytest.mark.asyncio
async def test_verify_totp_replay_protection(totp_service):
    """Test TOTP replay attack protection"""
    secret = totp_service.generate_secret()
    totp = pyotp.TOTP(secret)
    
    # Generate valid token
    valid_token = totp.now()
    
    # First verification
    is_valid1, timestamp1 = totp_service.verify_totp(secret, valid_token)
    assert is_valid1 is True
    
    # Second verification with same timestamp (replay attack)
    is_valid2, timestamp2 = totp_service.verify_totp(secret, valid_token, timestamp1)
    assert is_valid2 is False
    assert timestamp2 is None
    
    print("✓ TOTP replay attack correctly blocked")


# ============================================================================
# Backup Code Tests
# ============================================================================

@pytest.mark.asyncio
async def test_generate_backup_codes(totp_service):
    """Test backup code generation"""
    codes = totp_service.generate_backup_codes()
    
    assert len(codes) == 10
    assert all(len(code) == 8 for code in codes)
    assert all(code.isalnum() for code in codes)
    assert len(set(codes)) == 10  # All unique
    
    print(f"✓ Generated {len(codes)} backup codes")


@pytest.mark.asyncio
async def test_create_backup_codes(totp_service, test_user, session):
    """Test backup code creation and storage"""
    codes = await totp_service.create_backup_codes(test_user.user_id)
    await session.commit()
    
    assert len(codes) == 10
    
    # Verify codes are stored in database
    from ultracore.database.models.security import MFABackupCode
    from sqlalchemy import select, func
    
    result = await session.execute(
        select(func.count()).select_from(MFABackupCode).where(
            MFABackupCode.user_id == test_user.user_id
        )
    )
    count = result.scalar()
    
    assert count == 10
    
    print(f"✓ Created and stored {count} backup codes")


@pytest.mark.asyncio
async def test_verify_backup_code(totp_service, test_user, session):
    """Test backup code verification"""
    # Create backup codes
    codes = await totp_service.create_backup_codes(test_user.user_id)
    await session.commit()
    
    # Verify first code
    is_valid = await totp_service.verify_backup_code(test_user.user_id, codes[0])
    await session.commit()
    
    assert is_valid is True
    
    # Try to use same code again (should fail)
    is_valid_again = await totp_service.verify_backup_code(test_user.user_id, codes[0])
    await session.commit()
    
    assert is_valid_again is False
    
    print("✓ Backup code verification and single-use enforcement working")


# ============================================================================
# MFA Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
async def test_enable_mfa(totp_service, test_user, session):
    """Test MFA enable"""
    secret, qr_code, backup_codes = await totp_service.enable_mfa(test_user.user_id)
    await session.commit()
    
    assert secret is not None
    assert len(secret) == 32
    assert qr_code.startswith("data:image/png;base64,")
    assert len(backup_codes) == 10
    
    # Verify user MFA is enabled
    updated_user = await totp_service.user_repo.get(test_user.user_id)
    assert updated_user.mfa_enabled is True
    assert updated_user.mfa_secret == secret
    
    print("✓ MFA enabled successfully")


@pytest.mark.asyncio
async def test_verify_user_totp(totp_service, test_user, session):
    """Test user TOTP verification"""
    # Enable MFA
    secret, _, _ = await totp_service.enable_mfa(test_user.user_id)
    await session.commit()
    
    # Generate valid token
    totp = pyotp.TOTP(secret)
    valid_token = totp.now()
    
    # Verify token
    is_valid = await totp_service.verify_user_totp(test_user.user_id, valid_token)
    await session.commit()
    
    assert is_valid is True
    
    # Verify timestamp was updated
    updated_user = await totp_service.user_repo.get(test_user.user_id)
    assert updated_user.mfa_last_used_timestamp is not None
    
    print("✓ User TOTP verification successful")


@pytest.mark.asyncio
async def test_disable_mfa(totp_service, test_user, session):
    """Test MFA disable"""
    # Enable MFA
    secret, _, _ = await totp_service.enable_mfa(test_user.user_id)
    await session.commit()
    
    # Generate verification token
    totp = pyotp.TOTP(secret)
    token = totp.now()
    
    # Disable MFA
    success = await totp_service.disable_mfa(test_user.user_id, token)
    await session.commit()
    
    assert success is True
    
    # Verify user MFA is disabled
    updated_user = await totp_service.user_repo.get(test_user.user_id)
    assert updated_user.mfa_enabled is False
    assert updated_user.mfa_secret is None
    
    print("✓ MFA disabled successfully")


@pytest.mark.asyncio
async def test_regenerate_backup_codes(totp_service, test_user, session):
    """Test backup code regeneration"""
    # Enable MFA
    secret, _, old_codes = await totp_service.enable_mfa(test_user.user_id)
    await session.commit()
    
    # Generate verification token
    totp = pyotp.TOTP(secret)
    token = totp.now()
    
    # Regenerate backup codes
    new_codes = await totp_service.regenerate_backup_codes(test_user.user_id, token)
    await session.commit()
    
    assert len(new_codes) == 10
    assert set(new_codes) != set(old_codes)  # Different codes
    
    # Verify old codes don't work
    is_valid = await totp_service.verify_backup_code(test_user.user_id, old_codes[0])
    await session.commit()
    assert is_valid is False
    
    # Verify new codes work
    is_valid = await totp_service.verify_backup_code(test_user.user_id, new_codes[0])
    await session.commit()
    assert is_valid is True
    
    print("✓ Backup codes regenerated successfully")


@pytest.mark.asyncio
async def test_get_mfa_status(totp_service, test_user, session):
    """Test MFA status retrieval"""
    # Enable MFA
    await totp_service.enable_mfa(test_user.user_id)
    await session.commit()
    
    # Get status
    status = await totp_service.get_mfa_status(test_user.user_id)
    
    assert status["mfa_enabled"] is True
    assert status["backup_codes_remaining"] == 10
    
    # Use a backup code
    codes = await totp_service.create_backup_codes(test_user.user_id)
    await session.commit()
    await totp_service.verify_backup_code(test_user.user_id, codes[0])
    await session.commit()
    
    # Check status again
    status = await totp_service.get_mfa_status(test_user.user_id)
    assert status["backup_codes_remaining"] == 9
    
    print("✓ MFA status retrieval working")


# ============================================================================
# Event Producer Tests
# ============================================================================

@pytest.mark.asyncio
async def test_event_producer_mfa_enabled(event_producer, test_user):
    """Test MFA enabled event publishing"""
    await event_producer.publish_mfa_enabled(
        user_id=test_user.user_id,
        tenant_id=test_user.tenant_id,
        backup_codes_generated=10
    )
    
    print("✓ MFA enabled event published")


@pytest.mark.asyncio
async def test_event_producer_verification_success(event_producer, test_user):
    """Test MFA verification success event publishing"""
    await event_producer.publish_verification_success(
        user_id=test_user.user_id,
        tenant_id=test_user.tenant_id,
        verification_method="totp",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    
    print("✓ Verification success event published")


@pytest.mark.asyncio
async def test_event_producer_verification_failed(event_producer, test_user):
    """Test MFA verification failed event publishing"""
    await event_producer.publish_verification_failed(
        user_id=test_user.user_id,
        tenant_id=test_user.tenant_id,
        verification_method="totp",
        failure_reason="invalid_token",
        ip_address="192.168.1.1"
    )
    
    print("✓ Verification failed event published")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

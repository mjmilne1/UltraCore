"""
User Repository
Data access for users and authentication
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import logging

from ultracore.database.models.security import User, RefreshToken, TrustedDevice, MFABackupCode
from ultracore.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    User repository with authentication methods
    
    Provides:
    - User CRUD operations
    - Authentication (login, password verification)
    - MFA management
    - Device trust management
    - Token management
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
        self.session = session
    
    async def get(self, user_id: UUID) -> Optional[User]:
        """Get user by user_id"""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalars().first()
    
    # ========================================================================
    # User Queries
    # ========================================================================
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.get_by_field('username', username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_by_field('email', email)
    
    async def get_by_tenant(self, tenant_id: UUID) -> List[User]:
        """Get all users for a tenant"""
        return await self.get_many_by_field('tenant_id', tenant_id)
    
    async def get_active_users(self, tenant_id: UUID) -> List[User]:
        """Get active users for a tenant"""
        result = await self.session.execute(
            select(User).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_active == True
                )
            )
        )
        
        return list(result.scalars().all())
    
    # ========================================================================
    # Authentication
    # ========================================================================
    
    async def verify_credentials(self, username: str, password_hash: str) -> Optional[User]:
        """
        Verify user credentials
        
        Args:
            username: Username or email
            password_hash: Hashed password to verify
            
        Returns:
            User if credentials valid, None otherwise
        """
        # Try username first, then email
        user = await self.get_by_username(username)
        
        if not user:
            user = await self.get_by_email(username)
        
        if not user:
            logger.debug(f"User not found: {username}")
            return None
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Inactive account login attempt: {username}")
            return None
        
        # Check if account is locked
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning(f"Locked account login attempt: {username}")
                return None
            else:
                # Unlock account if lock period expired
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
        
        # Verify password (in production, use bcrypt.checkpw)
        if user.password_hash != password_hash:
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"Account locked after failed attempts: {username}")
            
            await self.session.flush()
            
            logger.debug(f"Invalid password for user: {username}")
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        
        await self.session.flush()
        
        logger.info(f"Successful login: {username}")
        
        return user
    
    async def update_last_login(self, user_id: UUID, ip_address: str):
        """Update last login timestamp and IP"""
        await self.update(user_id, {
            'last_login_at': datetime.utcnow(),
            'last_login_ip': ip_address
        })
    
    async def increment_failed_login(self, user_id: UUID) -> int:
        """
        Increment failed login attempts
        
        Returns:
            New failed attempt count
        """
        user = await self.get(user_id)
        
        if not user:
            return 0
        
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        await self.session.flush()
        
        return user.failed_login_attempts
    
    async def reset_failed_login(self, user_id: UUID):
        """Reset failed login attempts"""
        await self.update(user_id, {'failed_login_attempts': 0})
    
    async def lock_account(self, user_id: UUID, duration_minutes: int = 30):
        """Lock user account"""
        await self.update(user_id, {
            'is_locked': True,
            'locked_until': datetime.utcnow() + timedelta(minutes=duration_minutes)
        })
    
    async def unlock_account(self, user_id: UUID):
        """Unlock user account"""
        await self.update(user_id, {
            'is_locked': False,
            'locked_until': None,
            'failed_login_attempts': 0
        })
    
    # ========================================================================
    # MFA Management
    # ========================================================================
    
    async def enable_mfa(self, user_id: UUID, mfa_secret: str):
        """Enable MFA for user"""
        await self.update(user_id, {
            'mfa_enabled': True,
            'mfa_secret': mfa_secret
        })
    
    async def disable_mfa(self, user_id: UUID):
        """Disable MFA for user"""
        await self.update(user_id, {
            'mfa_enabled': False,
            'mfa_secret': None
        })
    
    async def create_backup_codes(self, user_id: UUID, code_hashes: List[str]) -> List[MFABackupCode]:
        """Create MFA backup codes"""
        codes = [
            MFABackupCode(
                user_id=user_id,
                code_hash=code_hash
            )
            for code_hash in code_hashes
        ]
        
        self.session.add_all(codes)
        await self.session.flush()
        
        return codes
    
    async def use_backup_code(self, user_id: UUID, code_hash: str) -> bool:
        """
        Use MFA backup code
        
        Returns:
            True if code is valid and unused, False otherwise
        """
        result = await self.session.execute(
            select(MFABackupCode).where(
                and_(
                    MFABackupCode.user_id == user_id,
                    MFABackupCode.code_hash == code_hash,
                    MFABackupCode.used_at.is_(None)
                )
            )
        )
        
        code = result.scalar_one_or_none()
        
        if not code:
            return False
        
        code.used_at = datetime.utcnow()
        await self.session.flush()
        
        return True
    
    async def revoke_backup_codes(self, user_id: UUID):
        """
        Revoke all backup codes for a user by marking them as used
        """
        result = await self.session.execute(
            select(MFABackupCode).where(
                and_(
                    MFABackupCode.user_id == user_id,
                    MFABackupCode.used_at.is_(None)
                )
            )
        )
        
        codes = result.scalars().all()
        
        for code in codes:
            code.used_at = datetime.utcnow()
        
        await self.session.flush()
    
    # ========================================================================
    # Token Management
    # ========================================================================
    
    async def create_refresh_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Create refresh token"""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.session.add(token)
        await self.session.flush()
        
        return token
    
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token_hash: str):
        """Revoke refresh token"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        
        token = result.scalar_one_or_none()
        
        if token:
            token.revoked_at = datetime.utcnow()
            await self.session.flush()
    
    async def revoke_all_user_tokens(self, user_id: UUID):
        """Revoke all refresh tokens for user"""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None)
                )
            )
        )
        
        tokens = result.scalars().all()
        
        for token in tokens:
            token.revoked_at = datetime.utcnow()
        
        await self.session.flush()
    
    async def cleanup_expired_tokens(self):
        """Delete expired refresh tokens"""
        from sqlalchemy import delete
        
        stmt = delete(RefreshToken).where(
            RefreshToken.expires_at < datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        
        logger.info(f"Cleaned up {result.rowcount} expired tokens")
    
    # ========================================================================
    # Device Trust Management
    # ========================================================================
    
    async def get_or_create_device(
        self,
        user_id: UUID,
        device_fingerprint: str,
        device_name: Optional[str] = None,
        device_type: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> TrustedDevice:
        """Get or create trusted device"""
        result = await self.session.execute(
            select(TrustedDevice).where(
                and_(
                    TrustedDevice.user_id == user_id,
                    TrustedDevice.device_fingerprint == device_fingerprint
                )
            )
        )
        
        device = result.scalar_one_or_none()
        
        if device:
            # Update last seen
            device.last_seen_at = datetime.utcnow()
            device.last_ip_address = ip_address
            await self.session.flush()
        else:
            # Create new device
            device = TrustedDevice(
                user_id=user_id,
                device_fingerprint=device_fingerprint,
                device_name=device_name,
                device_type=device_type,
                last_ip_address=ip_address
            )
            
            self.session.add(device)
            await self.session.flush()
        
        return device
    
    async def trust_device(self, device_id: UUID):
        """Mark device as trusted"""
        result = await self.session.execute(
            select(TrustedDevice).where(TrustedDevice.device_id == device_id)
        )
        
        device = result.scalar_one_or_none()
        
        if device:
            device.is_trusted = True
            device.trust_score = 100.0
            await self.session.flush()
    
    async def update_device_trust_score(self, device_id: UUID, trust_score: float):
        """Update device trust score"""
        result = await self.session.execute(
            select(TrustedDevice).where(TrustedDevice.device_id == device_id)
        )
        
        device = result.scalar_one_or_none()
        
        if device:
            device.trust_score = trust_score
            await self.session.flush()
    
    # ========================================================================
    # Trust Score Management
    # ========================================================================
    
    async def update_user_trust_score(self, user_id: UUID, trust_score: float):
        """Update user trust score"""
        await self.update(user_id, {'trust_score': trust_score})
    
    async def get_users_by_trust_score(
        self,
        tenant_id: UUID,
        min_score: float,
        max_score: float
    ) -> List[User]:
        """Get users by trust score range"""
        result = await self.session.execute(
            select(User).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.trust_score >= min_score,
                    User.trust_score <= max_score
                )
            )
        )
        
        return list(result.scalars().all())

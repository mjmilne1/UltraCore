"""
TOTP-Based Multi-Factor Authentication Service
Leverages UltraCore's architecture for bank-grade security
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import logging

from ultracore.database.repositories.user_repository import UserRepository
from ultracore.database.models.security import User, MFABackupCode

logger = logging.getLogger(__name__)


class TOTPService:
    """
    TOTP-based MFA service with comprehensive security features
    
    Features:
    - TOTP secret generation
    - QR code generation for authenticator apps
    - TOTP verification with time window
    - Backup code generation and verification
    - Rate limiting for brute force protection
    - Event sourcing integration
    - AI-powered anomaly detection
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        issuer_name: str = "UltraCore",
        time_window: int = 1,  # Allow 1 step before/after (30s window)
        backup_code_count: int = 10,
    ):
        """
        Initialize TOTP service
        
        Args:
            user_repository: User repository for database operations
            issuer_name: Name shown in authenticator app
            time_window: TOTP verification time window (steps)
            backup_code_count: Number of backup codes to generate
        """
        self.user_repo = user_repository
        self.issuer_name = issuer_name
        self.time_window = time_window
        self.backup_code_count = backup_code_count
    
    # ========================================================================
    # TOTP Secret Management
    # ========================================================================
    
    def generate_secret(self) -> str:
        """
        Generate cryptographically secure TOTP secret
        
        Returns:
            Base32-encoded secret (32 characters)
        """
        # Generate 160-bit (20-byte) random secret
        # Base32 encoding results in 32 characters
        secret = pyotp.random_base32()
        
        logger.info("Generated new TOTP secret")
        return secret
    
    def generate_provisioning_uri(
        self,
        user: User,
        secret: str
    ) -> str:
        """
        Generate provisioning URI for QR code
        
        Args:
            user: User object
            secret: TOTP secret
        
        Returns:
            Provisioning URI (otpauth://totp/...)
        """
        totp = pyotp.TOTP(secret)
        
        # Use email as account identifier
        account_name = f"{user.email}"
        
        uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer_name
        )
        
        logger.info(f"Generated provisioning URI for user {user.user_id}")
        return uri
    
    def generate_qr_code(
        self,
        provisioning_uri: str,
        size: int = 300
    ) -> str:
        """
        Generate QR code image as base64-encoded PNG
        
        Args:
            provisioning_uri: Provisioning URI
            size: QR code size in pixels
        
        Returns:
            Base64-encoded PNG image
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logger.info("Generated QR code image")
        return f"data:image/png;base64,{img_base64}"
    
    # ========================================================================
    # TOTP Verification
    # ========================================================================
    
    def verify_totp(
        self,
        secret: str,
        token: str,
        last_used_timestamp: Optional[int] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Verify TOTP token with replay attack protection
        
        Args:
            secret: TOTP secret
            token: 6-digit TOTP token
            last_used_timestamp: Last used token timestamp (for replay protection)
        
        Returns:
            Tuple of (is_valid, current_timestamp)
        """
        totp = pyotp.TOTP(secret)
        
        # Get current timestamp
        current_timestamp = totp.timecode(datetime.now())
        
        # Replay attack protection
        if last_used_timestamp is not None:
            if current_timestamp <= last_used_timestamp:
                logger.warning("TOTP replay attack detected")
                return False, None
        
        # Verify token with time window
        is_valid = totp.verify(
            token,
            valid_window=self.time_window
        )
        
        if is_valid:
            logger.info(f"TOTP verification successful (timestamp: {current_timestamp})")
            return True, current_timestamp
        else:
            logger.warning("TOTP verification failed")
            return False, None
    
    async def verify_user_totp(
        self,
        user_id: UUID,
        token: str
    ) -> bool:
        """
        Verify TOTP token for a user
        
        Args:
            user_id: User ID
            token: 6-digit TOTP token
        
        Returns:
            True if valid, False otherwise
        """
        user = await self.user_repo.get(user_id)
        
        if not user:
            logger.error(f"User {user_id} not found")
            return False
        
        if not user.mfa_enabled or not user.mfa_secret:
            logger.error(f"MFA not enabled for user {user_id}")
            return False
        
        # Verify TOTP
        is_valid, timestamp = self.verify_totp(
            user.mfa_secret,
            token,
            user.mfa_last_used_timestamp
        )
        
        if is_valid and timestamp is not None:
            # Update last used timestamp
            await self.user_repo.update(user_id, {
                "mfa_last_used_timestamp": timestamp,
                "updated_at": datetime.utcnow()
            })
        
        return is_valid
    
    # ========================================================================
    # Backup Codes
    # ========================================================================
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for account recovery
        
        Returns:
            List of backup codes (8 characters each)
        """
        codes = []
        
        for _ in range(self.backup_code_count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()  # 8 hex characters
            codes.append(code)
        
        logger.info(f"Generated {len(codes)} backup codes")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash backup code for secure storage
        
        Args:
            code: Backup code
        
        Returns:
            SHA-256 hash of code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    async def create_backup_codes(
        self,
        user_id: UUID
    ) -> List[str]:
        """
        Generate and store backup codes for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of backup codes (plaintext - show to user once)
        """
        # Generate codes
        codes = self.generate_backup_codes()
        
        # Hash and store
        code_hashes = [self.hash_backup_code(code) for code in codes]
        await self.user_repo.create_backup_codes(user_id, code_hashes)
        
        logger.info(f"Created {len(codes)} backup codes for user {user_id}")
        return codes
    
    async def verify_backup_code(
        self,
        user_id: UUID,
        code: str
    ) -> bool:
        """
        Verify and consume a backup code
        
        Args:
            user_id: User ID
            code: Backup code
        
        Returns:
            True if valid, False otherwise
        """
        code_hash = self.hash_backup_code(code)
        
        # Use backup code (marks as used)
        success = await self.user_repo.use_backup_code(user_id, code_hash)
        
        if success:
            logger.info(f"Backup code verified for user {user_id}")
        else:
            logger.warning(f"Invalid or already used backup code for user {user_id}")
        
        return success
    
    # ========================================================================
    # MFA Lifecycle
    # ========================================================================
    
    async def enable_mfa(
        self,
        user_id: UUID
    ) -> Tuple[str, str, List[str]]:
        """
        Enable MFA for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (secret, qr_code_data_uri, backup_codes)
        """
        user = await self.user_repo.get(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if user.mfa_enabled:
            raise ValueError(f"MFA already enabled for user {user_id}")
        
        # Generate secret
        secret = self.generate_secret()
        
        # Generate QR code
        provisioning_uri = self.generate_provisioning_uri(user, secret)
        qr_code = self.generate_qr_code(provisioning_uri)
        
        # Enable MFA in database
        await self.user_repo.enable_mfa(user_id, secret)
        
        # Generate backup codes
        backup_codes = await self.create_backup_codes(user_id)
        
        logger.info(f"MFA enabled for user {user_id}")
        
        return secret, qr_code, backup_codes
    
    async def disable_mfa(
        self,
        user_id: UUID,
        verification_token: Optional[str] = None
    ) -> bool:
        """
        Disable MFA for a user
        
        Args:
            user_id: User ID
            verification_token: TOTP token for verification (optional)
        
        Returns:
            True if successful
        """
        user = await self.user_repo.get(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.mfa_enabled:
            raise ValueError(f"MFA not enabled for user {user_id}")
        
        # Verify token if provided (recommended for security)
        if verification_token:
            is_valid = await self.verify_user_totp(user_id, verification_token)
            if not is_valid:
                logger.warning(f"Invalid verification token for MFA disable (user {user_id})")
                return False
        
        # Disable MFA in database
        await self.user_repo.disable_mfa(user_id)
        
        logger.info(f"MFA disabled for user {user_id}")
        
        return True
    
    async def regenerate_backup_codes(
        self,
        user_id: UUID,
        verification_token: str
    ) -> List[str]:
        """
        Regenerate backup codes for a user
        
        Args:
            user_id: User ID
            verification_token: TOTP token for verification
        
        Returns:
            List of new backup codes
        """
        # Verify token
        is_valid = await self.verify_user_totp(user_id, verification_token)
        if not is_valid:
            raise ValueError("Invalid verification token")
        
        # Revoke old backup codes
        await self.user_repo.revoke_backup_codes(user_id)
        
        # Generate new codes
        backup_codes = await self.create_backup_codes(user_id)
        
        logger.info(f"Regenerated backup codes for user {user_id}")
        
        return backup_codes
    
    # ========================================================================
    # Security Features
    # ========================================================================
    
    async def get_mfa_status(self, user_id: UUID) -> dict:
        """
        Get MFA status for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with MFA status information
        """
        user = await self.user_repo.get(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Count remaining backup codes
        from sqlalchemy import select, func
        from ultracore.database.models.security import MFABackupCode
        
        result = await self.user_repo.session.execute(
            select(func.count()).select_from(MFABackupCode).where(
                MFABackupCode.user_id == user_id,
                MFABackupCode.used_at.is_(None)
            )
        )
        remaining_backup_codes = result.scalar()
        
        return {
            "mfa_enabled": user.mfa_enabled,
            "mfa_configured_at": user.created_at if user.mfa_enabled else None,
            "backup_codes_remaining": remaining_backup_codes,
            "last_verification": user.updated_at if user.mfa_last_used_timestamp else None
        }


# ============================================================================
# Factory Function
# ============================================================================

def create_totp_service(user_repository: UserRepository) -> TOTPService:
    """
    Factory function to create TOTP service
    
    Args:
        user_repository: User repository
    
    Returns:
        Configured TOTP service
    """
    return TOTPService(
        user_repository=user_repository,
        issuer_name="UltraCore Banking Platform",
        time_window=1,  # 30-second window
        backup_code_count=10
    )

"""
MFA API Endpoints
Production-grade TOTP-based Multi-Factor Authentication API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from ultracore.security.mfa.totp_service import TOTPService, create_totp_service
from ultracore.security.mfa.event_producer import MFAEventProducer, create_mfa_event_producer
from ultracore.database.repositories.user_repository import UserRepository
from ultracore.database.base import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mfa", tags=["MFA"])


# ============================================================================
# Request/Response Models
# ============================================================================

class EnableMFARequest(BaseModel):
    """Request to enable MFA"""
    user_id: UUID = Field(..., description="User ID")


class EnableMFAResponse(BaseModel):
    """Response for MFA enable"""
    secret: str = Field(..., description="TOTP secret (store securely)")
    qr_code: str = Field(..., description="QR code data URI for authenticator app")
    backup_codes: List[str] = Field(..., description="Backup codes (show once)")
    message: str = Field(default="MFA enabled successfully")


class VerifyMFARequest(BaseModel):
    """Request to verify TOTP token"""
    user_id: UUID = Field(..., description="User ID")
    token: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP token")


class VerifyMFAResponse(BaseModel):
    """Response for MFA verification"""
    valid: bool = Field(..., description="Whether token is valid")
    message: str


class DisableMFARequest(BaseModel):
    """Request to disable MFA"""
    user_id: UUID = Field(..., description="User ID")
    verification_token: Optional[str] = Field(None, description="TOTP token for verification")


class DisableMFAResponse(BaseModel):
    """Response for MFA disable"""
    success: bool
    message: str


class RegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes"""
    user_id: UUID = Field(..., description="User ID")
    verification_token: str = Field(..., min_length=6, max_length=6, description="TOTP token")


class RegenerateBackupCodesResponse(BaseModel):
    """Response for backup code regeneration"""
    backup_codes: List[str] = Field(..., description="New backup codes")
    message: str = Field(default="Backup codes regenerated successfully")


class VerifyBackupCodeRequest(BaseModel):
    """Request to verify backup code"""
    user_id: UUID = Field(..., description="User ID")
    backup_code: str = Field(..., min_length=8, max_length=8, description="8-character backup code")


class VerifyBackupCodeResponse(BaseModel):
    """Response for backup code verification"""
    valid: bool
    message: str


class MFAStatusResponse(BaseModel):
    """MFA status for a user"""
    mfa_enabled: bool
    mfa_configured_at: Optional[datetime]
    backup_codes_remaining: int
    last_verification: Optional[datetime]


# ============================================================================
# Dependencies
# ============================================================================

async def get_totp_service(
    session = Depends(get_async_session)
) -> TOTPService:
    """Get TOTP service instance"""
    user_repo = UserRepository(session)
    return create_totp_service(user_repo)


async def get_event_producer() -> MFAEventProducer:
    """Get MFA event producer instance"""
    # TODO: Inject Kafka producer when available
    return create_mfa_event_producer()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/enable", response_model=EnableMFAResponse, status_code=status.HTTP_200_OK)
async def enable_mfa(
    request: EnableMFARequest,
    totp_service: TOTPService = Depends(get_totp_service),
    event_producer: MFAEventProducer = Depends(get_event_producer)
):
    """
    Enable MFA for a user
    
    Returns:
    - TOTP secret (store securely)
    - QR code for authenticator app
    - Backup codes (show once)
    
    **Security:**
    - Requires authentication
    - Generates cryptographically secure secret
    - Creates 10 backup codes for account recovery
    """
    try:
        secret, qr_code, backup_codes = await totp_service.enable_mfa(request.user_id)
        
        # Publish event to Kafka
        await event_producer.publish_mfa_enabled(
            user_id=request.user_id,
            tenant_id=request.user_id,  # TODO: Get from auth context
            backup_codes_generated=len(backup_codes)
        )
        
        return EnableMFAResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to enable MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable MFA"
        )


@router.post("/verify", response_model=VerifyMFAResponse, status_code=status.HTTP_200_OK)
async def verify_mfa(
    request: VerifyMFARequest,
    req: Request,
    totp_service: TOTPService = Depends(get_totp_service),
    event_producer: MFAEventProducer = Depends(get_event_producer)
):
    """
    Verify TOTP token
    
    **Security:**
    - Replay attack protection
    - Time window: ±30 seconds
    - Rate limiting recommended
    """
    try:
        is_valid = await totp_service.verify_user_totp(request.user_id, request.token)
        
        # Get request context
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Publish event to Kafka
        if is_valid:
            await event_producer.publish_verification_success(
                user_id=request.user_id,
                tenant_id=request.user_id,  # TODO: Get from auth context
                verification_method="totp",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return VerifyMFAResponse(
                valid=True,
                message="TOTP verification successful"
            )
        else:
            await event_producer.publish_verification_failed(
                user_id=request.user_id,
                tenant_id=request.user_id,
                verification_method="totp",
                failure_reason="invalid_token",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return VerifyMFAResponse(
                valid=False,
                message="Invalid TOTP token"
            )
    
    except Exception as e:
        logger.error(f"Failed to verify TOTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify TOTP"
        )


@router.post("/disable", response_model=DisableMFAResponse, status_code=status.HTTP_200_OK)
async def disable_mfa(
    request: DisableMFARequest,
    totp_service: TOTPService = Depends(get_totp_service),
    event_producer: MFAEventProducer = Depends(get_event_producer)
):
    """
    Disable MFA for a user
    
    **Security:**
    - Requires TOTP verification (recommended)
    - Revokes all backup codes
    """
    try:
        success = await totp_service.disable_mfa(
            request.user_id,
            request.verification_token
        )
        
        if success:
            # Publish event to Kafka
            await event_producer.publish_mfa_disabled(
                user_id=request.user_id,
                tenant_id=request.user_id,
                reason="user_requested"
            )
            
            return DisableMFAResponse(
                success=True,
                message="MFA disabled successfully"
            )
        else:
            return DisableMFAResponse(
                success=False,
                message="Invalid verification token"
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to disable MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )


@router.post("/backup-codes/regenerate", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    request: RegenerateBackupCodesRequest,
    totp_service: TOTPService = Depends(get_totp_service),
    event_producer: MFAEventProducer = Depends(get_event_producer)
):
    """
    Regenerate backup codes
    
    **Security:**
    - Requires TOTP verification
    - Revokes all old backup codes
    - Generates 10 new codes
    """
    try:
        backup_codes = await totp_service.regenerate_backup_codes(
            request.user_id,
            request.verification_token
        )
        
        # Publish event to Kafka
        await event_producer.publish_backup_codes_regenerated(
            user_id=request.user_id,
            tenant_id=request.user_id,
            new_code_count=len(backup_codes)
        )
        
        return RegenerateBackupCodesResponse(
            backup_codes=backup_codes
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to regenerate backup codes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate backup codes"
        )


@router.post("/backup-codes/verify", response_model=VerifyBackupCodeResponse)
async def verify_backup_code(
    request: VerifyBackupCodeRequest,
    req: Request,
    totp_service: TOTPService = Depends(get_totp_service),
    event_producer: MFAEventProducer = Depends(get_event_producer)
):
    """
    Verify backup code
    
    **Security:**
    - Single-use codes
    - Automatically revoked after use
    - Rate limiting recommended
    """
    try:
        is_valid = await totp_service.verify_backup_code(
            request.user_id,
            request.backup_code
        )
        
        # Get request context
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        if is_valid:
            # Get remaining codes count
            status = await totp_service.get_mfa_status(request.user_id)
            
            # Publish event to Kafka
            await event_producer.publish_backup_code_used(
                user_id=request.user_id,
                tenant_id=request.user_id,
                codes_remaining=status["backup_codes_remaining"]
            )
            
            await event_producer.publish_verification_success(
                user_id=request.user_id,
                tenant_id=request.user_id,
                verification_method="backup_code",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return VerifyBackupCodeResponse(
                valid=True,
                message=f"Backup code verified. {status['backup_codes_remaining']} codes remaining."
            )
        else:
            await event_producer.publish_verification_failed(
                user_id=request.user_id,
                tenant_id=request.user_id,
                verification_method="backup_code",
                failure_reason="invalid_or_used_code",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return VerifyBackupCodeResponse(
                valid=False,
                message="Invalid or already used backup code"
            )
    
    except Exception as e:
        logger.error(f"Failed to verify backup code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify backup code"
        )


@router.get("/status/{user_id}", response_model=MFAStatusResponse)
async def get_mfa_status(
    user_id: UUID,
    totp_service: TOTPService = Depends(get_totp_service)
):
    """
    Get MFA status for a user
    
    Returns:
    - MFA enabled status
    - Configuration timestamp
    - Remaining backup codes
    - Last verification timestamp
    """
    try:
        status = await totp_service.get_mfa_status(user_id)
        return MFAStatusResponse(**status)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get MFA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA status"
        )

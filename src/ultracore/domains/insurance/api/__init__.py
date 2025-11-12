"""Insurance REST API"""
from fastapi import APIRouter

from .policies import router as policies_router
from .claims import router as claims_router
from .quotes import router as quotes_router

# Create main router
router = APIRouter(prefix="/insurance", tags=["insurance"])

# Include sub-routers
router.include_router(policies_router)
router.include_router(claims_router)
router.include_router(quotes_router)

__all__ = ["router"]

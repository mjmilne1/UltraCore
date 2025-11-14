"""
RBAC Middleware and Decorators for FastAPI
Provides permission checking and access control for API endpoints
"""

from typing import Optional, List, Callable, Any
from uuid import UUID
from functools import wraps
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ultracore.security.rbac.rbac_service import RBACService
from ultracore.database.base import get_async_session

logger = logging.getLogger(__name__)

# HTTP Bearer token authentication
security = HTTPBearer()


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_rbac_service(
    session: AsyncSession = Depends(get_async_session)
) -> RBACService:
    """
    Dependency to get RBAC service instance
    
    Usage:
        @app.get("/api/v1/accounts")
        async def get_accounts(rbac: RBACService = Depends(get_rbac_service)):
            ...
    """
    return RBACService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Get current authenticated user from JWT token
    
    Returns:
        dict with user_id, tenant_id, username, etc.
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # TODO: Implement JWT token validation
        # For now, return a mock user
        # In production, decode JWT and get user from database
        
        token = credentials.credentials
        
        # Mock implementation - replace with actual JWT validation
        user = {
            "user_id": UUID("00000000-0000-0000-0000-000000000001"),
            "tenant_id": UUID("00000000-0000-0000-0000-000000000001"),
            "username": "admin",
            "email": "admin@ultracore.com"
        }
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_request_context(request: Request) -> dict:
    """
    Extract request context for access logging
    
    Returns:
        dict with ip_address, user_agent, request_id, etc.
    """
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": request.headers.get("x-request-id"),
        "method": request.method,
        "path": request.url.path
    }


# ============================================================================
# Permission Decorators
# ============================================================================

def require_permission(permission: str):
    """
    Decorator to require a specific permission for an endpoint
    
    Usage:
        @app.get("/api/v1/accounts")
        @require_permission("accounts:read")
        async def get_accounts():
            ...
    
    Args:
        permission: Permission name (e.g., "accounts:read")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies
            request: Request = kwargs.get('request')
            rbac: RBACService = kwargs.get('rbac')
            current_user: dict = kwargs.get('current_user')
            
            if not all([request, rbac, current_user]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies (request, rbac, current_user)"
                )
            
            # Get request context
            context = await get_request_context(request)
            
            # Check permission
            has_permission = await rbac.check_permission(
                user_id=current_user['user_id'],
                permission=permission,
                tenant_id=current_user.get('tenant_id'),
                context=context
            )
            
            if not has_permission:
                logger.warning(
                    f"Permission denied: user={current_user['user_id']}, "
                    f"permission={permission}, path={request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
            
            # Permission granted, execute endpoint
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    Decorator to require ANY of the specified permissions
    
    Usage:
        @app.get("/api/v1/data")
        @require_any_permission(["accounts:read", "transactions:read"])
        async def get_data():
            ...
    
    Args:
        permissions: List of permission names
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            rbac: RBACService = kwargs.get('rbac')
            current_user: dict = kwargs.get('current_user')
            
            if not all([request, rbac, current_user]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            # Check if user has ANY of the permissions
            has_permission = await rbac.check_multiple_permissions(
                user_id=current_user['user_id'],
                permissions=permissions,
                require_all=False,
                tenant_id=current_user.get('tenant_id')
            )
            
            if not has_permission:
                logger.warning(
                    f"Permission denied: user={current_user['user_id']}, "
                    f"required_any={permissions}, path={request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions (need any of): {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]):
    """
    Decorator to require ALL of the specified permissions
    
    Usage:
        @app.post("/api/v1/accounts")
        @require_all_permissions(["accounts:write", "accounts:approve"])
        async def create_account():
            ...
    
    Args:
        permissions: List of permission names
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            rbac: RBACService = kwargs.get('rbac')
            current_user: dict = kwargs.get('current_user')
            
            if not all([request, rbac, current_user]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            # Check if user has ALL of the permissions
            has_permission = await rbac.check_multiple_permissions(
                user_id=current_user['user_id'],
                permissions=permissions,
                require_all=True,
                tenant_id=current_user.get('tenant_id')
            )
            
            if not has_permission:
                logger.warning(
                    f"Permission denied: user={current_user['user_id']}, "
                    f"required_all={permissions}, path={request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions (need all of): {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator to require a specific role
    
    Usage:
        @app.get("/api/v1/admin/settings")
        @require_role("admin")
        async def get_admin_settings():
            ...
    
    Args:
        role_name: Role name (e.g., "admin", "manager")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            rbac: RBACService = kwargs.get('rbac')
            current_user: dict = kwargs.get('current_user')
            
            if not all([request, rbac, current_user]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            # Get user's roles
            user_roles = await rbac.get_user_roles(current_user['user_id'])
            role_names = [role.name for role in user_roles]
            
            if role_name not in role_names:
                logger.warning(
                    f"Role check failed: user={current_user['user_id']}, "
                    f"required_role={role_name}, user_roles={role_names}, "
                    f"path={request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role: {role_name}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_resource_access(resource_type: str, action: str, resource_id_param: str = "id"):
    """
    Decorator to check resource-specific access
    
    Usage:
        @app.get("/api/v1/accounts/{account_id}")
        @require_resource_access("accounts", "read", "account_id")
        async def get_account(account_id: UUID):
            ...
    
    Args:
        resource_type: Resource type (e.g., "accounts", "loans")
        action: Action (e.g., "read", "write", "delete")
        resource_id_param: Name of the path parameter containing resource ID
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            rbac: RBACService = kwargs.get('rbac')
            current_user: dict = kwargs.get('current_user')
            
            if not all([request, rbac, current_user]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            # Get resource ID from path parameters
            resource_id = kwargs.get(resource_id_param)
            
            # Get request context
            context = await get_request_context(request)
            
            # Check resource access
            access_granted, denial_reason = await rbac.check_resource_access(
                user_id=current_user['user_id'],
                resource_type=resource_type,
                action=action,
                resource_id=resource_id,
                tenant_id=current_user.get('tenant_id'),
                context=context
            )
            
            if not access_granted:
                logger.warning(
                    f"Resource access denied: user={current_user['user_id']}, "
                    f"resource={resource_type}:{resource_id}, action={action}, "
                    f"reason={denial_reason}, path={request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=denial_reason or f"Access denied to {resource_type}:{action}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# Middleware
# ============================================================================

class RBACMiddleware:
    """
    RBAC middleware for automatic permission checking
    
    Can be used to enforce permissions globally or for specific routes
    """
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        """
        Initialize RBAC middleware
        
        Args:
            app: FastAPI application
            excluded_paths: List of paths to exclude from RBAC (e.g., ["/health", "/docs"])
        """
        self.app = app
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
    
    async def __call__(self, request: Request, call_next):
        """
        Process request through RBAC middleware
        """
        # Skip excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Get current user from request
            # This assumes authentication middleware has already run
            user = getattr(request.state, 'user', None)
            
            if not user:
                # No user authenticated, let authentication middleware handle it
                return await call_next(request)
            
            # Add RBAC context to request state
            request.state.rbac_context = await get_request_context(request)
            
            # Continue processing
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            logger.error(f"RBAC middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during permission check"
            )


# ============================================================================
# Utility Functions
# ============================================================================

async def check_permission_or_403(
    rbac: RBACService,
    user_id: UUID,
    permission: str,
    tenant_id: Optional[UUID] = None,
    context: Optional[dict] = None
):
    """
    Check permission and raise 403 if denied
    
    Utility function for manual permission checking in endpoints
    
    Usage:
        await check_permission_or_403(rbac, user_id, "accounts:read")
    """
    has_permission = await rbac.check_permission(
        user_id=user_id,
        permission=permission,
        tenant_id=tenant_id,
        context=context
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}"
        )


async def check_resource_access_or_403(
    rbac: RBACService,
    user_id: UUID,
    resource_type: str,
    action: str,
    resource_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    context: Optional[dict] = None
):
    """
    Check resource access and raise 403 if denied
    
    Utility function for manual resource access checking in endpoints
    
    Usage:
        await check_resource_access_or_403(
            rbac, user_id, "accounts", "delete", account_id
        )
    """
    access_granted, denial_reason = await rbac.check_resource_access(
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        resource_id=resource_id,
        tenant_id=tenant_id,
        context=context
    )
    
    if not access_granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denial_reason or f"Access denied to {resource_type}:{action}"
        )

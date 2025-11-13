"""
RBAC API Routes
Endpoints for role and permission management
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ultracore.database.base import get_async_session
from ultracore.security.rbac import RBACService
from ultracore.security.rbac.middleware import (
    get_rbac_service,
    get_current_user,
    require_permission,
    require_role
)

router = APIRouter(prefix="/api/v1/rbac", tags=["RBAC"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RoleCreate(BaseModel):
    name: str
    display_name: str
    level: int
    description: Optional[str] = None
    parent_role_id: Optional[UUID] = None


class RoleResponse(BaseModel):
    role_id: UUID
    tenant_id: UUID
    name: str
    display_name: str
    description: Optional[str]
    level: str
    parent_role_id: Optional[UUID]
    is_active: bool
    is_system_role: bool
    
    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    resource: str
    action: str
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    permission_id: UUID
    tenant_id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class RoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID


class PermissionAssignment(BaseModel):
    role_id: UUID
    permission_id: UUID


class PermissionCheckRequest(BaseModel):
    user_id: UUID
    permission: str


class PermissionCheckResponse(BaseModel):
    has_permission: bool
    user_id: UUID
    permission: str


# ============================================================================
# Role Management Endpoints
# ============================================================================

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new role
    
    Requires: roles:write permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:write",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Create role
    role = await rbac.create_role(
        tenant_id=current_user['tenant_id'],
        name=role_data.name,
        display_name=role_data.display_name,
        level=role_data.level,
        description=role_data.description,
        parent_role_id=role_data.parent_role_id,
        created_by=current_user['user_id']
    )
    
    await session.commit()
    
    return role


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get role by ID
    
    Requires: roles:read permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:read",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Get role
    role = await rbac.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role not found: {role_id}"
        )
    
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a role
    
    Requires: roles:delete permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:delete",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Delete role
    deleted = await rbac.delete_role(role_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role not found or cannot be deleted: {role_id}"
        )
    
    await session.commit()


# ============================================================================
# Permission Management Endpoints
# ============================================================================

@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new permission
    
    Requires: permissions:write permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="permissions:write",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Create permission
    permission = await rbac.create_permission(
        tenant_id=current_user['tenant_id'],
        resource=permission_data.resource,
        action=permission_data.action,
        description=permission_data.description,
        created_by=current_user['user_id']
    )
    
    await session.commit()
    
    return permission


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get permission by ID
    
    Requires: permissions:read permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="permissions:read",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Get permission
    permission = await rbac.get_permission(permission_id)
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission not found: {permission_id}"
        )
    
    return permission


# ============================================================================
# Role-User Assignment Endpoints
# ============================================================================

@router.post("/role-assignments", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    assignment: RoleAssignment,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Assign role to user
    
    Requires: roles:assign permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:assign",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Assign role
    await rbac.assign_role_to_user(
        user_id=assignment.user_id,
        role_id=assignment.role_id,
        assigned_by=current_user['user_id']
    )
    
    await session.commit()
    
    return {"message": "Role assigned successfully"}


@router.delete("/role-assignments", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_from_user(
    assignment: RoleAssignment,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Revoke role from user
    
    Requires: roles:assign permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:assign",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Revoke role
    await rbac.revoke_role_from_user(
        user_id=assignment.user_id,
        role_id=assignment.role_id
    )
    
    await session.commit()


@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles(
    user_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all roles for a user
    
    Requires: users:read permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="users:read",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Get user roles
    roles = await rbac.get_user_roles(user_id)
    
    return roles


# ============================================================================
# Role-Permission Assignment Endpoints
# ============================================================================

@router.post("/permission-assignments", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    assignment: PermissionAssignment,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Assign permission to role
    
    Requires: permissions:assign permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="permissions:assign",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Assign permission
    await rbac.assign_permission_to_role(
        role_id=assignment.role_id,
        permission_id=assignment.permission_id,
        granted_by=current_user['user_id']
    )
    
    await session.commit()
    
    return {"message": "Permission assigned successfully"}


@router.delete("/permission-assignments", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission_from_role(
    assignment: PermissionAssignment,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Revoke permission from role
    
    Requires: permissions:assign permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="permissions:assign",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Revoke permission
    await rbac.revoke_permission_from_role(
        role_id=assignment.role_id,
        permission_id=assignment.permission_id
    )
    
    await session.commit()


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: UUID,
    request: Request,
    include_inherited: bool = False,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all permissions for a role
    
    Args:
        include_inherited: If True, includes permissions inherited from parent roles
    
    Requires: roles:read permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="roles:read",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Get role permissions
    if include_inherited:
        permissions = await rbac.get_role_all_permissions(role_id)
    else:
        permissions = await rbac.get_role_permissions(role_id)
    
    return permissions


# ============================================================================
# Permission Checking Endpoints
# ============================================================================

@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    check_request: PermissionCheckRequest,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Check if a user has a specific permission
    
    Requires: permissions:check permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="permissions:check",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Check target user's permission
    has_permission = await rbac.check_permission(
        user_id=check_request.user_id,
        permission=check_request.permission,
        tenant_id=current_user.get('tenant_id')
    )
    
    return PermissionCheckResponse(
        has_permission=has_permission,
        user_id=check_request.user_id,
        permission=check_request.permission
    )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all permissions for a user (including inherited)
    
    Requires: users:read permission
    """
    # Check permission
    await rbac.check_permission(
        user_id=current_user['user_id'],
        permission="users:read",
        tenant_id=current_user.get('tenant_id')
    )
    
    # Get user permissions
    permissions = await rbac.get_user_permissions(user_id)
    
    return {"user_id": user_id, "permissions": list(permissions)}


# ============================================================================
# Initialization Endpoints
# ============================================================================

@router.post("/initialize/roles", status_code=status.HTTP_201_CREATED)
async def initialize_default_roles(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Initialize default role hierarchy
    
    Requires: admin role
    """
    # Check if user is admin
    user_roles = await rbac.get_user_roles(current_user['user_id'])
    role_names = [role.name for role in user_roles]
    
    if "admin" not in role_names and "super_admin" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can initialize default roles"
        )
    
    # Initialize default roles
    roles = await rbac.initialize_default_roles(current_user['tenant_id'])
    
    await session.commit()
    
    return {
        "message": "Default roles initialized successfully",
        "roles": list(roles.keys())
    }


@router.post("/initialize/permissions", status_code=status.HTTP_201_CREATED)
async def initialize_default_permissions(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Initialize default permissions
    
    Requires: admin role
    """
    # Check if user is admin
    user_roles = await rbac.get_user_roles(current_user['user_id'])
    role_names = [role.name for role in user_roles]
    
    if "admin" not in role_names and "super_admin" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can initialize default permissions"
        )
    
    # Initialize default permissions
    permissions = await rbac.initialize_default_permissions(current_user['tenant_id'])
    
    await session.commit()
    
    return {
        "message": "Default permissions initialized successfully",
        "count": len(permissions)
    }

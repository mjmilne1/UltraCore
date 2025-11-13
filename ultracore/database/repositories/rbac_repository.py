"""
RBAC Repository
Data access for roles, permissions, and access control
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import logging

from ultracore.database.models.rbac import (
    Role, Permission, ResourcePolicy, AccessLog,
    role_permissions, user_roles
)
from ultracore.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RoleRepository(BaseRepository[Role]):
    """
    Role repository with hierarchical role management
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)
        self.session = session
    
    async def get_by_name(self, tenant_id: UUID, name: str) -> Optional[Role]:
        """Get role by name within tenant"""
        result = await self.session.execute(
            select(Role).where(
                and_(
                    Role.tenant_id == tenant_id,
                    Role.name == name
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_with_permissions(self, role_id: UUID) -> Optional[Role]:
        """Get role with all permissions loaded"""
        result = await self.session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.role_id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_hierarchy(self, role_id: UUID) -> List[Role]:
        """
        Get role hierarchy (role + all parent roles)
        Returns list from highest to lowest level
        """
        roles = []
        current_role = await self.get(role_id)
        
        while current_role:
            roles.append(current_role)
            if current_role.parent_role_id:
                current_role = await self.get(current_role.parent_role_id)
            else:
                break
        
        return roles
    
    async def get_by_level(self, tenant_id: UUID, level: int) -> List[Role]:
        """Get all roles at a specific hierarchy level"""
        result = await self.session.execute(
            select(Role).where(
                and_(
                    Role.tenant_id == tenant_id,
                    Role.level == level,
                    Role.is_active == True
                )
            )
        )
        return list(result.scalars().all())
    
    async def assign_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: Optional[UUID] = None
    ):
        """Assign permission to role"""
        await self.session.execute(
            role_permissions.insert().values(
                role_id=role_id,
                permission_id=permission_id,
                granted_at=datetime.utcnow(),
                granted_by=granted_by
            )
        )
        await self.session.flush()
    
    async def revoke_permission(self, role_id: UUID, permission_id: UUID):
        """Revoke permission from role"""
        await self.session.execute(
            role_permissions.delete().where(
                and_(
                    role_permissions.c.role_id == role_id,
                    role_permissions.c.permission_id == permission_id
                )
            )
        )
        await self.session.flush()
    
    async def get_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role"""
        role = await self.get_with_permissions(role_id)
        return role.permissions if role else []
    
    async def get_all_permissions(self, role_id: UUID) -> List[Permission]:
        """
        Get all permissions for a role including inherited permissions
        from parent roles
        """
        all_permissions = []
        hierarchy = await self.get_hierarchy(role_id)
        
        for role in hierarchy:
            permissions = await self.get_permissions(role.role_id)
            all_permissions.extend(permissions)
        
        # Remove duplicates
        unique_permissions = {p.permission_id: p for p in all_permissions}
        return list(unique_permissions.values())


class PermissionRepository(BaseRepository[Permission]):
    """
    Permission repository with resource-action management
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)
        self.session = session
    
    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name (e.g., 'accounts:read')"""
        result = await self.session.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_resource_action(
        self,
        resource: str,
        action: str
    ) -> Optional[Permission]:
        """Get permission by resource and action"""
        result = await self.session.execute(
            select(Permission).where(
                and_(
                    Permission.resource == resource,
                    Permission.action == action
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a resource"""
        result = await self.session.execute(
            select(Permission).where(
                and_(
                    Permission.resource == resource,
                    Permission.is_active == True
                )
            )
        )
        return list(result.scalars().all())
    
    async def create_if_not_exists(
        self,
        tenant_id: UUID,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create permission if it doesn't exist"""
        name = f"{resource}:{action}"
        
        # Check if exists
        existing = await self.get_by_name(name)
        if existing:
            return existing
        
        # Create new
        permission = Permission(
            tenant_id=tenant_id,
            name=name,
            resource=resource,
            action=action,
            description=description
        )
        
        self.session.add(permission)
        await self.session.flush()
        
        return permission


class ResourcePolicyRepository(BaseRepository[ResourcePolicy]):
    """
    Resource policy repository for fine-grained access control
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(ResourcePolicy, session)
        self.session = session
    
    async def get_for_resource(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID] = None
    ) -> List[ResourcePolicy]:
        """Get all policies for a resource"""
        conditions = [
            ResourcePolicy.tenant_id == tenant_id,
            ResourcePolicy.resource_type == resource_type,
            ResourcePolicy.is_active == True
        ]
        
        if resource_id:
            conditions.append(
                or_(
                    ResourcePolicy.resource_id == resource_id,
                    ResourcePolicy.resource_id.is_(None)  # Wildcard policies
                )
            )
        
        result = await self.session.execute(
            select(ResourcePolicy)
            .where(and_(*conditions))
            .order_by(ResourcePolicy.priority.desc())
        )
        return list(result.scalars().all())
    
    async def get_for_user(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID] = None
    ) -> List[ResourcePolicy]:
        """Get all policies applicable to a user"""
        # Get user's roles
        from ultracore.database.models.security import User
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        # Get policies for user's role and user-specific policies
        conditions = [
            ResourcePolicy.resource_type == resource_type,
            ResourcePolicy.is_active == True,
            or_(
                ResourcePolicy.user_id == user_id,
                ResourcePolicy.role_id.in_([user.role])  # Simplified - would need user_roles join
            )
        ]
        
        if resource_id:
            conditions.append(
                or_(
                    ResourcePolicy.resource_id == resource_id,
                    ResourcePolicy.resource_id.is_(None)
                )
            )
        
        result = await self.session.execute(
            select(ResourcePolicy)
            .where(and_(*conditions))
            .order_by(ResourcePolicy.priority.desc())
        )
        return list(result.scalars().all())
    
    async def check_access(
        self,
        user_id: UUID,
        resource_type: str,
        action: str,
        resource_id: Optional[UUID] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has access to perform action on resource
        
        Returns:
            (access_granted, denial_reason)
        """
        policies = await self.get_for_user(user_id, resource_type, resource_id)
        
        # No policies = deny by default
        if not policies:
            return (False, "No applicable policies found")
        
        # Check policies in priority order
        for policy in policies:
            # Explicit denials take precedence
            if policy.denied_actions and action in policy.denied_actions:
                return (False, f"Explicitly denied by policy: {policy.name}")
            
            # Check allowed actions
            if policy.allowed_actions and action in policy.allowed_actions:
                # TODO: Check conditions (IP range, time range, etc.)
                return (True, None)
        
        return (False, "Action not allowed by any policy")


class AccessLogRepository(BaseRepository[AccessLog]):
    """
    Access log repository for audit trail
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(AccessLog, session)
        self.session = session
    
    async def log_access(
        self,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        action: str,
        access_granted: bool,
        role_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        denial_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[UUID] = None,
        risk_score: Optional[float] = None,
        ai_decision: Optional[str] = None
    ) -> AccessLog:
        """Log an access attempt"""
        log = AccessLog(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            access_granted=access_granted,
            denial_reason=denial_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            risk_score=str(risk_score) if risk_score else None,
            ai_decision=ai_decision
        )
        
        self.session.add(log)
        await self.session.flush()
        
        return log
    
    async def get_user_access_history(
        self,
        user_id: UUID,
        limit: int = 100
    ) -> List[AccessLog]:
        """Get access history for a user"""
        result = await self.session.execute(
            select(AccessLog)
            .where(AccessLog.user_id == user_id)
            .order_by(AccessLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_denied_access_attempts(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> List[AccessLog]:
        """Get all denied access attempts in the last N hours"""
        cutoff_time = datetime.utcnow() - datetime.timedelta(hours=hours)
        
        result = await self.session.execute(
            select(AccessLog).where(
                and_(
                    AccessLog.tenant_id == tenant_id,
                    AccessLog.access_granted == False,
                    AccessLog.timestamp >= cutoff_time
                )
            ).order_by(AccessLog.timestamp.desc())
        )
        return list(result.scalars().all())
    
    async def get_access_stats(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get access statistics for the last N hours"""
        cutoff_time = datetime.utcnow() - datetime.timedelta(hours=hours)
        
        # Total access attempts
        total_result = await self.session.execute(
            select(func.count()).select_from(AccessLog).where(
                and_(
                    AccessLog.tenant_id == tenant_id,
                    AccessLog.timestamp >= cutoff_time
                )
            )
        )
        total = total_result.scalar()
        
        # Granted access
        granted_result = await self.session.execute(
            select(func.count()).select_from(AccessLog).where(
                and_(
                    AccessLog.tenant_id == tenant_id,
                    AccessLog.timestamp >= cutoff_time,
                    AccessLog.access_granted == True
                )
            )
        )
        granted = granted_result.scalar()
        
        # Denied access
        denied = total - granted
        
        return {
            "total_attempts": total,
            "granted": granted,
            "denied": denied,
            "success_rate": (granted / total * 100) if total > 0 else 0
        }


class UserRoleRepository:
    """
    User-Role association repository
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None
    ):
        """Assign role to user"""
        await self.session.execute(
            user_roles.insert().values(
                user_id=user_id,
                role_id=role_id,
                assigned_at=datetime.utcnow(),
                assigned_by=assigned_by,
                expires_at=expires_at
            )
        )
        await self.session.flush()
    
    async def revoke_role(self, user_id: UUID, role_id: UUID):
        """Revoke role from user"""
        await self.session.execute(
            user_roles.delete().where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            )
        )
        await self.session.flush()
    
    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user"""
        result = await self.session.execute(
            select(Role)
            .join(user_roles, Role.role_id == user_roles.c.role_id)
            .where(user_roles.c.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def get_role_users(self, role_id: UUID) -> List[UUID]:
        """Get all users with a specific role"""
        result = await self.session.execute(
            select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)
        )
        return [row[0] for row in result.all()]

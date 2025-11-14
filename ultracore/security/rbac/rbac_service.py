"""
RBAC Service Layer
Business logic for role-based access control
"""

from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ultracore.database.models.rbac import Role, Permission, ResourcePolicy, AccessLog
from ultracore.database.repositories.rbac_repository import (
    RoleRepository,
    PermissionRepository,
    ResourcePolicyRepository,
    AccessLogRepository,
    UserRoleRepository
)

logger = logging.getLogger(__name__)


class RBACService:
    """
    Comprehensive RBAC service with permission checking and role management
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.role_repo = RoleRepository(session)
        self.permission_repo = PermissionRepository(session)
        self.policy_repo = ResourcePolicyRepository(session)
        self.access_log_repo = AccessLogRepository(session)
        self.user_role_repo = UserRoleRepository(session)
    
    # ========================================================================
    # Permission Checking (Core RBAC Functionality)
    # ========================================================================
    
    async def check_permission(
        self,
        user_id: UUID,
        permission: str,
        tenant_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user_id: User ID
            permission: Permission name (e.g., "accounts:read")
            tenant_id: Tenant ID for multi-tenancy
            context: Additional context (IP, user agent, etc.)
        
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get user's roles
            user_roles = await self.user_role_repo.get_user_roles(user_id)
            
            if not user_roles:
                logger.warning(f"User {user_id} has no roles assigned")
                return False
            
            # Get all permissions for user's roles (including inherited)
            all_permissions = set()
            for role in user_roles:
                role_permissions = await self.role_repo.get_all_permissions(role.role_id)
                all_permissions.update(p.name for p in role_permissions)
            
            # Check if permission exists in user's permission set
            has_permission = permission in all_permissions
            
            # Log access attempt
            await self._log_access(
                tenant_id=tenant_id or user_roles[0].tenant_id,
                user_id=user_id,
                role_id=user_roles[0].role_id if user_roles else None,
                resource_type=permission.split(':')[0] if ':' in permission else 'unknown',
                action=permission.split(':')[1] if ':' in permission else permission,
                access_granted=has_permission,
                denial_reason=None if has_permission else f"Missing permission: {permission}",
                context=context
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission for user {user_id}: {e}")
            return False
    
    async def check_resource_access(
        self,
        user_id: UUID,
        resource_type: str,
        action: str,
        resource_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can perform action on a specific resource
        
        Uses resource policies for fine-grained access control
        
        Returns:
            (access_granted, denial_reason)
        """
        try:
            # First check basic permission
            permission = f"{resource_type}:{action}"
            has_basic_permission = await self.check_permission(
                user_id, permission, tenant_id, context
            )
            
            if not has_basic_permission:
                return (False, f"Missing permission: {permission}")
            
            # Check resource-specific policies
            access_granted, denial_reason = await self.policy_repo.check_access(
                user_id=user_id,
                resource_type=resource_type,
                action=action,
                resource_id=resource_id
            )
            
            # Log access attempt
            await self._log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                access_granted=access_granted,
                denial_reason=denial_reason,
                context=context
            )
            
            return (access_granted, denial_reason)
            
        except Exception as e:
            logger.error(f"Error checking resource access for user {user_id}: {e}")
            return (False, f"Internal error: {str(e)}")
    
    async def check_multiple_permissions(
        self,
        user_id: UUID,
        permissions: List[str],
        require_all: bool = True,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """
        Check multiple permissions at once
        
        Args:
            user_id: User ID
            permissions: List of permission names
            require_all: If True, user must have ALL permissions. If False, user needs ANY permission.
            tenant_id: Tenant ID
        
        Returns:
            True if permission check passes, False otherwise
        """
        results = []
        for permission in permissions:
            has_permission = await self.check_permission(user_id, permission, tenant_id)
            results.append(has_permission)
        
        if require_all:
            return all(results)
        else:
            return any(results)
    
    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """
        Get all permissions for a user (including inherited from roles)
        
        Returns:
            Set of permission names
        """
        user_roles = await self.user_role_repo.get_user_roles(user_id)
        
        all_permissions = set()
        for role in user_roles:
            role_permissions = await self.role_repo.get_all_permissions(role.role_id)
            all_permissions.update(p.name for p in role_permissions)
        
        return all_permissions
    
    # ========================================================================
    # Role Management
    # ========================================================================
    
    async def create_role(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        level: int,
        description: Optional[str] = None,
        parent_role_id: Optional[UUID] = None,
        is_system_role: bool = False,
        created_by: Optional[UUID] = None
    ) -> Role:
        """Create a new role"""
        role = Role(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            level=str(level),
            parent_role_id=parent_role_id,
            is_system_role=is_system_role,
            created_by=created_by
        )
        
        self.session.add(role)
        await self.session.flush()
        
        logger.info(f"Created role: {name} (ID: {role.role_id})")
        
        return role
    
    async def get_role(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID"""
        return await self.role_repo.get(role_id)
    
    async def get_role_by_name(self, tenant_id: UUID, name: str) -> Optional[Role]:
        """Get role by name"""
        return await self.role_repo.get_by_name(tenant_id, name)
    
    async def update_role(
        self,
        role_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[Role]:
        """Update role"""
        if updated_by:
            updates['updated_by'] = updated_by
        
        return await self.role_repo.update(role_id, updates)
    
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role (only if not a system role)"""
        role = await self.role_repo.get(role_id)
        
        if not role:
            return False
        
        if role.is_system_role:
            logger.warning(f"Attempted to delete system role: {role.name}")
            return False
        
        return await self.role_repo.delete(role_id)
    
    async def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None
    ):
        """Assign role to user"""
        await self.user_role_repo.assign_role(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        
        logger.info(f"Assigned role {role_id} to user {user_id}")
    
    async def revoke_role_from_user(self, user_id: UUID, role_id: UUID):
        """Revoke role from user"""
        await self.user_role_repo.revoke_role(user_id, role_id)
        
        logger.info(f"Revoked role {role_id} from user {user_id}")
    
    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user"""
        return await self.user_role_repo.get_user_roles(user_id)
    
    # ========================================================================
    # Permission Management
    # ========================================================================
    
    async def create_permission(
        self,
        tenant_id: UUID,
        resource: str,
        action: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> Permission:
        """Create a new permission"""
        return await self.permission_repo.create_if_not_exists(
            tenant_id=tenant_id,
            resource=resource,
            action=action,
            description=description
        )
    
    async def get_permission(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID"""
        return await self.permission_repo.get(permission_id)
    
    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name (e.g., 'accounts:read')"""
        return await self.permission_repo.get_by_name(name)
    
    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: Optional[UUID] = None
    ):
        """Assign permission to role"""
        await self.role_repo.assign_permission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by
        )
        
        logger.info(f"Assigned permission {permission_id} to role {role_id}")
    
    async def revoke_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID
    ):
        """Revoke permission from role"""
        await self.role_repo.revoke_permission(role_id, permission_id)
        
        logger.info(f"Revoked permission {permission_id} from role {role_id}")
    
    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role (direct, not inherited)"""
        return await self.role_repo.get_permissions(role_id)
    
    async def get_role_all_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role (including inherited)"""
        return await self.role_repo.get_all_permissions(role_id)
    
    # ========================================================================
    # Resource Policy Management
    # ========================================================================
    
    async def create_resource_policy(
        self,
        tenant_id: UUID,
        name: str,
        resource_type: str,
        allowed_actions: List[str],
        role_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        denied_actions: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> ResourcePolicy:
        """Create a resource policy"""
        policy = ResourcePolicy(
            tenant_id=tenant_id,
            name=name,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            role_id=role_id,
            user_id=user_id,
            allowed_actions=allowed_actions,
            denied_actions=denied_actions,
            conditions=conditions,
            priority=str(priority),
            created_by=created_by
        )
        
        self.session.add(policy)
        await self.session.flush()
        
        logger.info(f"Created resource policy: {name} (ID: {policy.policy_id})")
        
        return policy
    
    async def get_resource_policies(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID] = None
    ) -> List[ResourcePolicy]:
        """Get all policies for a resource"""
        return await self.policy_repo.get_for_resource(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
    
    # ========================================================================
    # Audit and Reporting
    # ========================================================================
    
    async def get_access_logs(
        self,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[AccessLog]:
        """Get access logs"""
        if user_id:
            return await self.access_log_repo.get_user_access_history(user_id, limit)
        else:
            # Get all logs for tenant (would need to implement this in repository)
            return []
    
    async def get_denied_access_attempts(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> List[AccessLog]:
        """Get all denied access attempts"""
        return await self.access_log_repo.get_denied_access_attempts(tenant_id, hours)
    
    async def get_access_statistics(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get access statistics"""
        return await self.access_log_repo.get_access_stats(tenant_id, hours)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def initialize_default_roles(self, tenant_id: UUID):
        """
        Initialize default role hierarchy for a tenant
        
        Creates:
        - super_admin (level 0)
        - admin (level 1)
        - manager (level 2)
        - officer (level 3)
        - customer (level 4)
        """
        # Create super_admin role
        super_admin = await self.create_role(
            tenant_id=tenant_id,
            name="super_admin",
            display_name="System Administrator",
            level=0,
            description="Full system access",
            is_system_role=True
        )
        
        # Create admin role
        admin = await self.create_role(
            tenant_id=tenant_id,
            name="admin",
            display_name="Administrator",
            level=1,
            description="Organization administrator",
            parent_role_id=super_admin.role_id,
            is_system_role=True
        )
        
        # Create manager role
        manager = await self.create_role(
            tenant_id=tenant_id,
            name="manager",
            display_name="Manager",
            level=2,
            description="Department manager",
            parent_role_id=admin.role_id,
            is_system_role=True
        )
        
        # Create officer role
        officer = await self.create_role(
            tenant_id=tenant_id,
            name="officer",
            display_name="Officer",
            level=3,
            description="Bank officer/staff",
            parent_role_id=manager.role_id,
            is_system_role=True
        )
        
        # Create customer role
        customer = await self.create_role(
            tenant_id=tenant_id,
            name="customer",
            display_name="Customer",
            level=4,
            description="End customer",
            parent_role_id=officer.role_id,
            is_system_role=True
        )
        
        await self.session.commit()
        
        logger.info(f"Initialized default roles for tenant {tenant_id}")
        
        return {
            "super_admin": super_admin,
            "admin": admin,
            "manager": manager,
            "officer": officer,
            "customer": customer
        }
    
    async def initialize_default_permissions(self, tenant_id: UUID):
        """
        Initialize default permissions for common resources
        """
        resources = [
            "accounts", "transactions", "loans", "deposits",
            "clients", "users", "reports", "settings"
        ]
        
        actions = ["read", "write", "delete", "approve"]
        
        permissions = []
        for resource in resources:
            for action in actions:
                permission = await self.create_permission(
                    tenant_id=tenant_id,
                    resource=resource,
                    action=action,
                    description=f"{action.capitalize()} {resource}"
                )
                permissions.append(permission)
        
        await self.session.commit()
        
        logger.info(f"Initialized {len(permissions)} default permissions for tenant {tenant_id}")
        
        return permissions
    
    async def _log_access(
        self,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        action: str,
        access_granted: bool,
        role_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        denial_reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Internal method to log access attempts"""
        try:
            await self.access_log_repo.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                role_id=role_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                access_granted=access_granted,
                denial_reason=denial_reason,
                ip_address=context.get('ip_address') if context else None,
                user_agent=context.get('user_agent') if context else None,
                request_id=context.get('request_id') if context else None,
                risk_score=context.get('risk_score') if context else None,
                ai_decision=context.get('ai_decision') if context else None
            )
        except Exception as e:
            logger.error(f"Error logging access attempt: {e}")

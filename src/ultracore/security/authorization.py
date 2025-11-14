"""
Authorization Service - Event-Sourced
Provides role-based access control (RBAC) following UltraCore's event-sourcing architecture
"""
from typing import List, Set, Dict, Optional
from enum import Enum
from uuid import UUID, uuid4

from ultracore.security.events import (
    create_role_assigned_event,
    create_permission_granted_event,
    create_access_denied_event
)


class Permission(str, Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_ACCOUNTS = "manage_accounts"
    APPROVE_TRANSACTIONS = "approve_transactions"
    VIEW_REPORTS = "view_reports"
    CONFIGURE_SYSTEM = "configure_system"


class Role(str, Enum):
    """System roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    CUSTOMER = "customer"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.ADMIN,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ACCOUNTS,
        Permission.APPROVE_TRANSACTIONS,
        Permission.VIEW_REPORTS,
        Permission.CONFIGURE_SYSTEM,
    },
    Role.MANAGER: {
        Permission.READ,
        Permission.WRITE,
        Permission.MANAGE_ACCOUNTS,
        Permission.APPROVE_TRANSACTIONS,
        Permission.VIEW_REPORTS,
    },
    Role.OPERATOR: {
        Permission.READ,
        Permission.WRITE,
        Permission.MANAGE_ACCOUNTS,
    },
    Role.VIEWER: {
        Permission.READ,
        Permission.VIEW_REPORTS,
    },
    Role.CUSTOMER: {
        Permission.READ,
    },
}


class AuthorizationService:
    """
    Event-sourced authorization service for role-based access control
    
    All authorization operations publish events to Kafka for audit and replay
    """
    
    def __init__(self, event_store=None, tenant_id: str = "default"):
        """
        Initialize authorization service
        
        Args:
            event_store: Kafka event store for publishing events
            tenant_id: Tenant identifier for multi-tenancy
        """
        self.role_permissions = ROLE_PERMISSIONS
        self.event_store = event_store
        self.tenant_id = tenant_id
        
        # In-memory cache for read model (in production, use Redis or read database)
        self.user_roles: Dict[str, Set[Role]] = {}
        self.user_permissions: Dict[str, Set[Permission]] = {}
    
    async def assign_role(
        self, 
        user_id: str, 
        role: Role,
        assigned_by: str,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """
        Assign a role to a user and publish RoleAssigned event
        
        Args:
            user_id: User identifier
            role: Role to assign
            assigned_by: User who assigned the role
            correlation_id: Correlation ID for event tracking
        """
        # Update read model
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role)
        
        # Publish RoleAssigned event
        if self.event_store:
            event = create_role_assigned_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                role=role.value,
                assigned_by=assigned_by,
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="User",
                event_type="role.assigned",
                event_data=event.data,
                aggregate_id=user_id,
                user_id=assigned_by,
                idempotency_key=str(event.metadata.event_id)
            )
    
    async def revoke_role(
        self, 
        user_id: str, 
        role: Role,
        revoked_by: str,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """
        Revoke a role from a user and publish RoleRevoked event
        
        Args:
            user_id: User identifier
            role: Role to revoke
            revoked_by: User who revoked the role
            correlation_id: Correlation ID for event tracking
        """
        # Update read model
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role)
        
        # Publish RoleRevoked event
        if self.event_store:
            event_data = {
                "user_id": user_id,
                "tenant_id": self.tenant_id,
                "role": role.value,
                "revoked_by": revoked_by
            }
            
            await self.event_store.append_event(
                entity="User",
                event_type="role.revoked",
                event_data=event_data,
                aggregate_id=user_id,
                user_id=revoked_by,
                idempotency_key=f"{user_id}-role-revoked-{uuid4()}"
            )
    
    def get_user_roles(self, user_id: str) -> Set[Role]:
        """
        Get all roles assigned to a user (from read model)
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of roles assigned to the user
        """
        return self.user_roles.get(user_id, set())
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles (from read model)
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of permissions the user has
        """
        # Check for custom permissions first
        if user_id in self.user_permissions:
            return self.user_permissions[user_id]
        
        # Otherwise, derive from roles
        permissions = set()
        user_roles = self.get_user_roles(user_id)
        
        for role in user_roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        
        return permissions
    
    async def grant_permission(
        self, 
        user_id: str, 
        permission: Permission,
        granted_by: str,
        resource_id: Optional[str] = None,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """
        Grant a specific permission to a user and publish PermissionGranted event
        
        Args:
            user_id: User identifier
            permission: Permission to grant
            granted_by: User who granted the permission
            resource_id: Optional resource identifier for resource-specific permissions
            correlation_id: Correlation ID for event tracking
        """
        # Update read model
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = set()
        self.user_permissions[user_id].add(permission)
        
        # Publish PermissionGranted event
        if self.event_store:
            event = create_permission_granted_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                permission=permission.value,
                granted_by=granted_by,
                resource_id=resource_id,
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="User",
                event_type="permission.granted",
                event_data=event.data,
                aggregate_id=user_id,
                user_id=granted_by,
                idempotency_key=str(event.metadata.event_id)
            )
    
    async def revoke_permission(
        self, 
        user_id: str, 
        permission: Permission,
        revoked_by: str,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """
        Revoke a specific permission from a user and publish PermissionRevoked event
        
        Args:
            user_id: User identifier
            permission: Permission to revoke
            revoked_by: User who revoked the permission
            correlation_id: Correlation ID for event tracking
        """
        # Update read model
        if user_id in self.user_permissions:
            self.user_permissions[user_id].discard(permission)
        
        # Publish PermissionRevoked event
        if self.event_store:
            event_data = {
                "user_id": user_id,
                "tenant_id": self.tenant_id,
                "permission": permission.value,
                "revoked_by": revoked_by
            }
            
            await self.event_store.append_event(
                entity="User",
                event_type="permission.revoked",
                event_data=event_data,
                aggregate_id=user_id,
                user_id=revoked_by,
                idempotency_key=f"{user_id}-permission-revoked-{uuid4()}"
            )
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if a user has a specific permission (query read model)
        
        Args:
            user_id: User identifier
            permission: Permission to check
            
        Returns:
            True if user has the permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions or Permission.ADMIN in user_permissions
    
    def has_role(self, user_id: str, role: Role) -> bool:
        """
        Check if a user has a specific role (query read model)
        
        Args:
            user_id: User identifier
            role: Role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        user_roles = self.get_user_roles(user_id)
        return role in user_roles
    
    async def check_permission(
        self, 
        user_id: str, 
        permission: Permission,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """
        Check if user has permission, raise exception and publish AccessDenied event if not
        
        Args:
            user_id: User identifier
            permission: Permission to check
            correlation_id: Correlation ID for event tracking
            
        Raises:
            PermissionError: If user doesn't have the permission
        """
        if not self.has_permission(user_id, permission):
            # Publish AccessDenied event
            if self.event_store:
                event = create_access_denied_event(
                    user_id=user_id,
                    tenant_id=self.tenant_id,
                    resource_id="system",
                    required_permission=permission.value,
                    reason=f"User does not have permission: {permission.value}",
                    correlation_id=correlation_id
                )
                
                await self.event_store.append_event(
                    entity="AccessControl",
                    event_type="access.denied",
                    event_data=event.data,
                    aggregate_id=user_id,
                    user_id=user_id,
                    idempotency_key=str(event.metadata.event_id)
                )
            
            raise PermissionError(
                f"User {user_id} does not have permission: {permission}"
            )
    
    def is_admin(self, user_id: str) -> bool:
        """
        Check if a user is an administrator (query read model)
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user is admin, False otherwise
        """
        return self.has_role(user_id, Role.ADMIN) or \
               self.has_permission(user_id, Permission.ADMIN)
    
    async def can_access_resource(
        self, 
        user_id: str, 
        resource_id: str, 
        required_permission: Permission,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if user can access a specific resource and publish event
        
        Args:
            user_id: User identifier
            resource_id: Resource identifier
            required_permission: Permission required for access
            correlation_id: Correlation ID for event tracking
            
        Returns:
            True if user can access the resource, False otherwise
        """
        # Admins can access everything
        if self.is_admin(user_id):
            return True
        
        # Check if user has the required permission
        has_access = self.has_permission(user_id, required_permission)
        
        if not has_access and self.event_store:
            # Publish AccessDenied event
            event = create_access_denied_event(
                user_id=user_id,
                tenant_id=self.tenant_id,
                resource_id=resource_id,
                required_permission=required_permission.value,
                reason=f"User lacks required permission: {required_permission.value}",
                correlation_id=correlation_id
            )
            
            await self.event_store.append_event(
                entity="AccessControl",
                event_type="access.denied",
                event_data=event.data,
                aggregate_id=user_id,
                user_id=user_id,
                idempotency_key=str(event.metadata.event_id)
            )
        
        return has_access

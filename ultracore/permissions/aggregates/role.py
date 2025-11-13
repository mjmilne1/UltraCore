"""Role Aggregate - Event-sourced RBAC"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any, Dict

from ultracore.permissions.events import *
from ultracore.permissions.event_publisher import get_permissions_event_publisher


@dataclass
class RoleAggregate:
    """Event-sourced role aggregate"""
    tenant_id: str
    role_id: str
    name: str = ""
    role_type: RoleType = RoleType.CUSTOM
    permissions: List[str] = field(default_factory=list)
    is_system_role: bool = False
    _events: List[Any] = field(default_factory=list)
    
    def create(self, name: str, role_type: RoleType, description: Optional[str],
               permissions: List[str], is_system_role: bool, created_by: str):
        event = RoleCreated(
            tenant_id=self.tenant_id, role_id=self.role_id, name=name,
            role_type=role_type, description=description, permissions=permissions,
            is_system_role=is_system_role, created_by=created_by, created_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_permissions_event_publisher().publish_role_event(event)
    
    def update_permissions(self, permissions: List[str], updated_by: str):
        if self.is_system_role:
            raise ValueError("Cannot modify system role")
        event = RoleUpdated(
            tenant_id=self.tenant_id, role_id=self.role_id, permissions=permissions,
            updated_by=updated_by, updated_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_permissions_event_publisher().publish_role_event(event)
    
    def _apply_event(self, event: Any):
        if isinstance(event, RoleCreated):
            self.name, self.role_type = event.name, event.role_type
            self.permissions, self.is_system_role = event.permissions, event.is_system_role
        elif isinstance(event, RoleUpdated):
            self.permissions = event.permissions
        self._events.append(event)


@dataclass
class UserRoleAggregate:
    """Event-sourced user-role assignment"""
    tenant_id: str
    user_id: str
    roles: List[str] = field(default_factory=list)
    _events: List[Any] = field(default_factory=list)
    
    def assign_role(self, role_id: str, granted_by: str, expires_at: Optional[datetime] = None):
        event = RoleAssigned(
            tenant_id=self.tenant_id, user_id=self.user_id, role_id=role_id,
            granted_by=granted_by, expires_at=expires_at, granted_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_permissions_event_publisher().publish_role_event(event)
    
    def revoke_role(self, role_id: str, revoked_by: str, reason: Optional[str] = None):
        if role_id not in self.roles:
            raise ValueError("Role not assigned to user")
        event = RoleRevoked(
            tenant_id=self.tenant_id, user_id=self.user_id, role_id=role_id,
            revoked_by=revoked_by, reason=reason, revoked_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_permissions_event_publisher().publish_role_event(event)
    
    def _apply_event(self, event: Any):
        if isinstance(event, RoleAssigned):
            if event.role_id not in self.roles:
                self.roles.append(event.role_id)
        elif isinstance(event, RoleRevoked):
            if event.role_id in self.roles:
                self.roles.remove(event.role_id)
        self._events.append(event)

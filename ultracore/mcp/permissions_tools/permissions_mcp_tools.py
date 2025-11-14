"""Permissions & Roles MCP Tools"""
from typing import Dict, List, Any
from datetime import datetime
import uuid

async def create_role(
    name: str,
    description: str = "",
    permissions: List[str] = None,
    inherits_from: List[str] = None
) -> Dict:
    """
    Create a new role
    
    Args:
        name: Role name
        description: Role description
        permissions: List of permission identifiers
        inherits_from: List of parent role IDs to inherit permissions from
        
    Returns:
        Created role details
        
    Example:
        >>> role = await create_role(
        ...     name="Portfolio Manager",
        ...     description="Can manage client portfolios",
        ...     permissions=["portfolio.read", "portfolio.update", "trade.execute"],
        ...     inherits_from=["user"]
        ... )
    """
    role_id = f"role_{uuid.uuid4().hex[:12]}"
    
    if permissions is None:
        permissions = []
    
    if inherits_from is None:
        inherits_from = []
    
    # Validate role name
    if not name or len(name) < 2:
        raise ValueError("Role name must be at least 2 characters")
    
    # Validate permissions format
    for perm in permissions:
        if "." not in perm:
            raise ValueError(f"Invalid permission format: {perm}. Must be 'resource.action'")
    
    role = {
        "role_id": role_id,
        "name": name,
        "description": description,
        "permissions": permissions,
        "inherits_from": inherits_from,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_system_role": False,
        "user_count": 0
    }
    
    return {
        "status": "created",
        "role": role,
        "message": f"Role '{name}' created successfully"
    }

async def assign_permission(
    role_id: str,
    permission: str,
    resource_id: str = None,
    conditions: Dict[str, Any] = None
) -> Dict:
    """
    Assign a permission to a role
    
    Args:
        role_id: Role identifier
        permission: Permission identifier (resource.action)
        resource_id: Optional specific resource ID
        conditions: Optional conditions for permission
        
    Returns:
        Assignment result
        
    Example:
        >>> result = await assign_permission(
        ...     role_id="role_abc123",
        ...     permission="portfolio.update",
        ...     conditions={"portfolio_value_limit": 1000000}
        ... )
    """
    # Validate permission format
    if "." not in permission:
        raise ValueError(f"Invalid permission format: {permission}. Must be 'resource.action'")
    
    resource, action = permission.split(".", 1)
    
    # Validate action
    valid_actions = ["create", "read", "update", "delete", "execute", "approve", "reject"]
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}. Must be one of: {valid_actions}")
    
    assignment = {
        "assignment_id": f"assign_{uuid.uuid4().hex[:12]}",
        "role_id": role_id,
        "permission": permission,
        "resource": resource,
        "action": action,
        "resource_id": resource_id,
        "conditions": conditions or {},
        "assigned_at": datetime.utcnow().isoformat(),
        "assigned_by": "system"
    }
    
    return {
        "status": "assigned",
        "assignment": assignment,
        "message": f"Permission '{permission}' assigned to role {role_id}"
    }

async def check_access(
    user_id: str,
    resource: str,
    action: str,
    resource_id: str = None,
    context: Dict[str, Any] = None
) -> Dict:
    """
    Check if user has access to perform action on resource
    
    Args:
        user_id: User identifier
        resource: Resource type (portfolio, client, trade, etc.)
        action: Action to perform (create, read, update, delete, execute)
        resource_id: Optional specific resource ID
        context: Optional context data for conditional permissions
        
    Returns:
        Access check result with allowed status and reason
        
    Example:
        >>> result = await check_access(
        ...     user_id="user_123",
        ...     resource="portfolio",
        ...     action="update",
        ...     resource_id="portfolio_456",
        ...     context={"portfolio_value": 500000}
        ... )
    """
    check_id = f"check_{uuid.uuid4().hex[:12]}"
    
    # In production, fetch user roles and permissions from database
    # For now, simulate access check
    
    # Simulate user roles
    user_roles = ["portfolio_manager", "trader"]
    
    # Simulate role permissions
    role_permissions = {
        "portfolio_manager": [
            "portfolio.read",
            "portfolio.update",
            "client.read",
            "trade.execute"
        ],
        "trader": [
            "trade.create",
            "trade.execute",
            "portfolio.read"
        ]
    }
    
    # Check if user has permission
    permission = f"{resource}.{action}"
    allowed = False
    matched_role = None
    
    for role in user_roles:
        if permission in role_permissions.get(role, []):
            allowed = True
            matched_role = role
            break
    
    # Check conditions if provided
    conditions_met = True
    if context and "portfolio_value" in context:
        # Example: Portfolio managers can only update portfolios < $1M
        if matched_role == "portfolio_manager" and context["portfolio_value"] > 1000000:
            allowed = False
            conditions_met = False
    
    result = {
        "check_id": check_id,
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "resource_id": resource_id,
        "allowed": allowed,
        "matched_role": matched_role,
        "conditions_met": conditions_met,
        "reason": self._get_access_reason(allowed, matched_role, conditions_met),
        "checked_at": datetime.utcnow().isoformat()
    }
    
    return result

def _get_access_reason(allowed: bool, matched_role: str, conditions_met: bool) -> str:
    """Get human-readable reason for access decision"""
    if allowed:
        return f"Access granted via role: {matched_role}"
    elif not conditions_met:
        return "Access denied: Conditions not met"
    else:
        return "Access denied: Insufficient permissions"

async def get_user_permissions(
    user_id: str,
    include_inherited: bool = True
) -> Dict:
    """
    Get all permissions for a user
    
    Args:
        user_id: User identifier
        include_inherited: Include permissions from parent roles
        
    Returns:
        User permissions grouped by resource
        
    Example:
        >>> permissions = await get_user_permissions(
        ...     user_id="user_123",
        ...     include_inherited=True
        ... )
    """
    # In production, fetch from database
    # For now, return simulated permissions
    
    permissions_by_resource = {
        "portfolio": ["read", "update"],
        "client": ["read"],
        "trade": ["create", "execute"],
        "report": ["read", "create"]
    }
    
    # Flatten to permission list
    all_permissions = []
    for resource, actions in permissions_by_resource.items():
        for action in actions:
            all_permissions.append(f"{resource}.{action}")
    
    return {
        "user_id": user_id,
        "total_permissions": len(all_permissions),
        "permissions": all_permissions,
        "permissions_by_resource": permissions_by_resource,
        "roles": ["portfolio_manager", "trader"],
        "include_inherited": include_inherited,
        "retrieved_at": datetime.utcnow().isoformat()
    }

async def revoke_permission(
    role_id: str,
    permission: str
) -> Dict:
    """
    Revoke a permission from a role
    
    Args:
        role_id: Role identifier
        permission: Permission to revoke (resource.action)
        
    Returns:
        Revocation result
        
    Example:
        >>> result = await revoke_permission(
        ...     role_id="role_abc123",
        ...     permission="portfolio.delete"
        ... )
    """
    # Validate permission format
    if "." not in permission:
        raise ValueError(f"Invalid permission format: {permission}. Must be 'resource.action'")
    
    revocation = {
        "revocation_id": f"revoke_{uuid.uuid4().hex[:12]}",
        "role_id": role_id,
        "permission": permission,
        "revoked_at": datetime.utcnow().isoformat(),
        "revoked_by": "system"
    }
    
    return {
        "status": "revoked",
        "revocation": revocation,
        "message": f"Permission '{permission}' revoked from role {role_id}"
    }

async def audit_access(
    user_id: str = None,
    resource: str = None,
    date_range_start: str = None,
    date_range_end: str = None,
    action_type: str = None
) -> List[Dict]:
    """
    Audit access logs
    
    Args:
        user_id: Optional user filter
        resource: Optional resource filter
        date_range_start: Start date (ISO format)
        date_range_end: End date (ISO format)
        action_type: Optional action filter (granted, denied)
        
    Returns:
        List of access log entries
        
    Example:
        >>> logs = await audit_access(
        ...     user_id="user_123",
        ...     resource="portfolio",
        ...     date_range_start="2024-11-01T00:00:00Z",
        ...     action_type="denied"
        ... )
    """
    # In production, query access logs from database
    # For now, return simulated audit logs
    
    audit_logs = [
        {
            "log_id": f"log_{uuid.uuid4().hex[:12]}",
            "user_id": user_id or "user_123",
            "resource": resource or "portfolio",
            "action": "update",
            "resource_id": "portfolio_456",
            "result": "granted",
            "role": "portfolio_manager",
            "timestamp": "2024-11-14T10:30:00Z",
            "ip_address": "203.0.113.42",
            "user_agent": "Mozilla/5.0"
        },
        {
            "log_id": f"log_{uuid.uuid4().hex[:12]}",
            "user_id": user_id or "user_123",
            "resource": resource or "portfolio",
            "action": "delete",
            "resource_id": "portfolio_789",
            "result": "denied",
            "reason": "Insufficient permissions",
            "timestamp": "2024-11-14T11:15:00Z",
            "ip_address": "203.0.113.42",
            "user_agent": "Mozilla/5.0"
        },
        {
            "log_id": f"log_{uuid.uuid4().hex[:12]}",
            "user_id": user_id or "user_456",
            "resource": resource or "client",
            "action": "read",
            "resource_id": "client_101",
            "result": "granted",
            "role": "advisor",
            "timestamp": "2024-11-14T12:00:00Z",
            "ip_address": "203.0.113.99",
            "user_agent": "Mobile App v2.1"
        }
    ]
    
    # Filter by action_type if provided
    if action_type:
        audit_logs = [log for log in audit_logs if log["result"] == action_type]
    
    return audit_logs

# MCP Tool Registry
MCP_TOOLS = {
    "create_role": create_role,
    "assign_permission": assign_permission,
    "check_access": check_access,
    "get_user_permissions": get_user_permissions,
    "revoke_permission": revoke_permission,
    "audit_access": audit_access
}

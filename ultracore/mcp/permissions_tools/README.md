# Permissions & Roles MCP Tools

## Overview
MCP tools for managing roles, permissions, and access control.

## Functions

### `create_role()`
Create a new role with permissions.

**Parameters:**
- `name` - Role name
- `description` - Role description
- `permissions` - List of permission identifiers
- `inherits_from` - List of parent role IDs

**Returns:** Created role details

**Example:**
```python
role = await create_role(
    name="Portfolio Manager",
    description="Can manage client portfolios",
    permissions=["portfolio.read", "portfolio.update", "trade.execute"],
    inherits_from=["user"]
)
```

### `assign_permission()`
Assign a permission to a role.

**Parameters:**
- `role_id` - Role identifier
- `permission` - Permission identifier (resource.action)
- `resource_id` - Optional specific resource ID
- `conditions` - Optional conditions for permission

**Returns:** Assignment result

### `check_access()`
Check if user has access to perform action on resource.

**Parameters:**
- `user_id` - User identifier
- `resource` - Resource type (portfolio, client, trade, etc.)
- `action` - Action to perform (create, read, update, delete, execute)
- `resource_id` - Optional specific resource ID
- `context` - Optional context data for conditional permissions

**Returns:** Access check result with allowed status and reason

**Example:**
```python
result = await check_access(
    user_id="user_123",
    resource="portfolio",
    action="update",
    resource_id="portfolio_456"
)

if result["allowed"]:
    # Proceed with operation
    pass
else:
    print(f"Access denied: {result['reason']}")
```

### `get_user_permissions()`
Get all permissions for a user.

**Parameters:**
- `user_id` - User identifier
- `include_inherited` - Include permissions from parent roles

**Returns:** User permissions grouped by resource

### `revoke_permission()`
Revoke a permission from a role.

**Parameters:**
- `role_id` - Role identifier
- `permission` - Permission to revoke (resource.action)

**Returns:** Revocation result

### `audit_access()`
Audit access logs.

**Parameters:**
- `user_id` - Optional user filter
- `resource` - Optional resource filter
- `date_range_start` - Start date (ISO format)
- `date_range_end` - End date (ISO format)
- `action_type` - Optional action filter (granted, denied)

**Returns:** List of access log entries

## Permission Format

Permissions follow the format: `resource.action`

**Resources:**
- `portfolio` - Portfolio management
- `client` - Client management
- `trade` - Trading operations
- `report` - Reporting
- `compliance` - Compliance operations
- `admin` - Administrative functions

**Actions:**
- `create` - Create new resource
- `read` - View resource
- `update` - Modify resource
- `delete` - Delete resource
- `execute` - Execute operation
- `approve` - Approve operation
- `reject` - Reject operation

## Usage Example

```python
from ultracore.mcp.permissions_tools.permissions_mcp_tools import (
    create_role,
    assign_permission,
    check_access
)

# Create a role
role = await create_role(
    name="Senior Advisor",
    description="Senior financial advisor with elevated permissions",
    permissions=["client.read", "client.update", "portfolio.read"]
)

# Assign additional permission
await assign_permission(
    role_id=role["role"]["role_id"],
    permission="portfolio.update",
    conditions={"portfolio_value_limit": 5000000}
)

# Check access before operation
access = await check_access(
    user_id="user_123",
    resource="portfolio",
    action="update",
    resource_id="portfolio_456",
    context={"portfolio_value": 2500000}
)

if access["allowed"]:
    # Proceed with portfolio update
    print("Access granted")
else:
    print(f"Access denied: {access['reason']}")
```

## ASIC Compliance

All access checks and permission changes are logged for ASIC audit trail requirements:
- User identification
- Resource accessed
- Action performed
- Timestamp
- IP address
- Result (granted/denied)
- Reason for denial

# RBAC Usage Examples

## Quick Start Guide

This document provides practical examples of using UltraCore's RBAC system in your API endpoints.

---

## 1. Basic Permission Checking

### Using the `@require_permission` Decorator

```python
from fastapi import APIRouter, Depends, Request
from ultracore.security.rbac.middleware import (
    require_permission,
    get_rbac_service,
    get_current_user
)

router = APIRouter()

@router.get("/api/v1/accounts")
@require_permission("accounts:read")
async def get_accounts(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all accounts
    
    Automatically checks if current user has 'accounts:read' permission
    Returns 403 if permission denied
    """
    # Your endpoint logic here
    accounts = await get_all_accounts()
    return accounts
```

---

## 2. Multiple Permission Checking

### Require ANY Permission

```python
from ultracore.security.rbac.middleware import require_any_permission

@router.get("/api/v1/dashboard")
@require_any_permission(["accounts:read", "transactions:read", "loans:read"])
async def get_dashboard(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard data
    
    User needs ANY of: accounts:read, transactions:read, or loans:read
    """
    return {"message": "Dashboard data"}
```

### Require ALL Permissions

```python
from ultracore.security.rbac.middleware import require_all_permissions

@router.post("/api/v1/accounts")
@require_all_permissions(["accounts:write", "accounts:approve"])
async def create_account(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Create new account
    
    User needs BOTH: accounts:write AND accounts:approve
    """
    return {"message": "Account created"}
```

---

## 3. Role-Based Access

### Using the `@require_role` Decorator

```python
from ultracore.security.rbac.middleware import require_role

@router.get("/api/v1/admin/settings")
@require_role("admin")
async def get_admin_settings(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get admin settings
    
    Only users with 'admin' role can access
    """
    return {"message": "Admin settings"}
```

---

## 4. Resource-Specific Access Control

### Using the `@require_resource_access` Decorator

```python
from ultracore.security.rbac.middleware import require_resource_access
from uuid import UUID

@router.get("/api/v1/accounts/{account_id}")
@require_resource_access("accounts", "read", "account_id")
async def get_account(
    account_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific account
    
    Checks:
    1. User has 'accounts:read' permission
    2. User has access to THIS specific account (via resource policies)
    """
    account = await get_account_by_id(account_id)
    return account


@router.delete("/api/v1/loans/{loan_id}")
@require_resource_access("loans", "delete", "loan_id")
async def delete_loan(
    loan_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete specific loan
    
    Checks:
    1. User has 'loans:delete' permission
    2. User has delete access to THIS specific loan
    """
    await delete_loan_by_id(loan_id)
    return {"message": "Loan deleted"}
```

---

## 5. Manual Permission Checking

### Using Utility Functions

```python
from ultracore.security.rbac.middleware import check_permission_or_403

@router.post("/api/v1/transactions")
async def create_transaction(
    transaction_data: TransactionCreate,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Create transaction with conditional permission checking
    """
    # Check basic permission
    await check_permission_or_403(
        rbac, 
        current_user['user_id'], 
        "transactions:write"
    )
    
    # Additional logic based on transaction amount
    if transaction_data.amount > 10000:
        # Large transactions require approval permission
        await check_permission_or_403(
            rbac,
            current_user['user_id'],
            "transactions:approve"
        )
    
    # Create transaction
    transaction = await create_new_transaction(transaction_data)
    return transaction
```

### Using RBAC Service Directly

```python
@router.get("/api/v1/reports/custom")
async def get_custom_report(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get custom report with complex permission logic
    """
    # Get all user permissions
    user_permissions = await rbac.get_user_permissions(current_user['user_id'])
    
    # Build report based on permissions
    report = {}
    
    if "accounts:read" in user_permissions:
        report['accounts'] = await get_accounts_summary()
    
    if "transactions:read" in user_permissions:
        report['transactions'] = await get_transactions_summary()
    
    if "loans:read" in user_permissions:
        report['loans'] = await get_loans_summary()
    
    return report
```

---

## 6. Combining Multiple Decorators

```python
@router.post("/api/v1/accounts/{account_id}/approve")
@require_role("manager")  # Must be a manager
@require_permission("accounts:approve")  # Must have approve permission
@require_resource_access("accounts", "approve", "account_id")  # Must have access to this account
async def approve_account(
    account_id: UUID,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Approve account
    
    Requires:
    1. Manager role
    2. accounts:approve permission
    3. Access to this specific account
    """
    await approve_account_by_id(account_id)
    return {"message": "Account approved"}
```

---

## 7. Initialization

### Initialize Default Roles and Permissions

```python
from ultracore.security.rbac import RBACService
from ultracore.database.base import get_async_session

async def initialize_tenant_rbac(tenant_id: UUID):
    """
    Initialize RBAC for a new tenant
    """
    async with get_async_session() as session:
        rbac = RBACService(session)
        
        # Initialize default roles
        roles = await rbac.initialize_default_roles(tenant_id)
        print(f"Created roles: {list(roles.keys())}")
        
        # Initialize default permissions
        permissions = await rbac.initialize_default_permissions(tenant_id)
        print(f"Created {len(permissions)} permissions")
        
        # Assign all permissions to super_admin role
        super_admin = roles['super_admin']
        for permission in permissions:
            await rbac.assign_permission_to_role(
                role_id=super_admin.role_id,
                permission_id=permission.permission_id
            )
        
        await session.commit()
        print("RBAC initialization complete")
```

---

## 8. Custom Role and Permission Setup

### Create Custom Roles

```python
async def setup_custom_roles(tenant_id: UUID):
    """
    Create custom roles for specific use cases
    """
    async with get_async_session() as session:
        rbac = RBACService(session)
        
        # Get base role
        officer_role = await rbac.get_role_by_name(tenant_id, "officer")
        
        # Create loan officer role
        loan_officer = await rbac.create_role(
            tenant_id=tenant_id,
            name="loan_officer",
            display_name="Loan Officer",
            level=3,
            description="Specialized in loan management",
            parent_role_id=officer_role.role_id
        )
        
        # Create permissions
        review_loans = await rbac.create_permission(
            tenant_id=tenant_id,
            resource="loans",
            action="review",
            description="Review loan applications"
        )
        
        approve_loans = await rbac.create_permission(
            tenant_id=tenant_id,
            resource="loans",
            action="approve",
            description="Approve loan applications"
        )
        
        # Assign permissions to role
        await rbac.assign_permission_to_role(
            role_id=loan_officer.role_id,
            permission_id=review_loans.permission_id
        )
        
        await rbac.assign_permission_to_role(
            role_id=loan_officer.role_id,
            permission_id=approve_loans.permission_id
        )
        
        await session.commit()
        print("Custom roles created")
```

---

## 9. Resource Policies

### Create Fine-Grained Access Policies

```python
async def setup_resource_policies(tenant_id: UUID):
    """
    Create resource-specific access policies
    """
    async with get_async_session() as session:
        rbac = RBACService(session)
        
        # Get role
        manager_role = await rbac.get_role_by_name(tenant_id, "manager")
        
        # Create policy: Managers can only approve accounts under $100k
        policy = await rbac.create_resource_policy(
            tenant_id=tenant_id,
            name="manager_account_approval_limit",
            resource_type="accounts",
            allowed_actions=["approve"],
            role_id=manager_role.role_id,
            conditions={
                "max_balance": 100000,
                "business_hours_only": True
            },
            priority=10,
            description="Managers can approve accounts under $100k during business hours"
        )
        
        # Create policy: Deny delete access to system accounts
        deny_policy = await rbac.create_resource_policy(
            tenant_id=tenant_id,
            name="protect_system_accounts",
            resource_type="accounts",
            denied_actions=["delete"],
            conditions={
                "is_system_account": True
            },
            priority=100,  # High priority (denials take precedence)
            description="Prevent deletion of system accounts"
        )
        
        await session.commit()
        print("Resource policies created")
```

---

## 10. Access Audit and Reporting

### Get Access Logs

```python
@router.get("/api/v1/admin/access-logs")
@require_role("admin")
async def get_access_logs(
    user_id: Optional[UUID] = None,
    hours: int = 24,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get access logs
    """
    if user_id:
        logs = await rbac.get_access_logs(user_id=user_id, limit=100)
    else:
        # Get denied access attempts
        logs = await rbac.get_denied_access_attempts(
            tenant_id=current_user['tenant_id'],
            hours=hours
        )
    
    return {"logs": logs}


@router.get("/api/v1/admin/access-stats")
@require_role("admin")
async def get_access_statistics(
    hours: int = 24,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get access statistics
    """
    stats = await rbac.get_access_statistics(
        tenant_id=current_user['tenant_id'],
        hours=hours
    )
    
    return stats
```

---

## Best Practices

1. **Use Decorators for Simple Cases**
   - `@require_permission()` for single permission checks
   - `@require_role()` for role-based access
   - `@require_resource_access()` for resource-specific access

2. **Use Manual Checking for Complex Logic**
   - When permissions depend on request data
   - When building dynamic responses based on permissions
   - When implementing conditional access control

3. **Always Log Access Attempts**
   - RBAC service automatically logs all permission checks
   - Use access logs for compliance and security audits
   - Monitor denied access attempts for security threats

4. **Use Resource Policies for Fine-Grained Control**
   - Implement business rules as resource policies
   - Use conditions for context-aware access control
   - Set appropriate priorities (denials should have high priority)

5. **Initialize RBAC for Each Tenant**
   - Create default roles and permissions
   - Assign appropriate permissions to each role
   - Create custom roles as needed

6. **Test Permission Checks**
   - Write integration tests for RBAC
   - Test both granted and denied access
   - Verify audit logs are created

---

## Common Patterns

### Pattern 1: Hierarchical Access

```python
# Users with higher-level roles automatically have permissions of lower roles
# super_admin → admin → manager → officer → customer
# super_admin has ALL permissions
# customer has minimal permissions
```

### Pattern 2: Resource Ownership

```python
# Users can only access their own resources
@router.get("/api/v1/my-accounts")
async def get_my_accounts(
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    # No permission check needed - users can always view their own data
    accounts = await get_accounts_by_user(current_user['user_id'])
    return accounts
```

### Pattern 3: Conditional Permissions

```python
# Different permissions based on request data
@router.post("/api/v1/transfers")
async def create_transfer(
    transfer: TransferCreate,
    request: Request,
    rbac: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(get_current_user)
):
    # Small transfers: basic permission
    if transfer.amount <= 1000:
        await check_permission_or_403(rbac, current_user['user_id'], "transfers:write")
    # Large transfers: approval permission
    else:
        await check_permission_or_403(rbac, current_user['user_id'], "transfers:approve")
    
    return await create_new_transfer(transfer)
```

---

## Troubleshooting

### Permission Denied (403)

```python
# Check user's permissions
permissions = await rbac.get_user_permissions(user_id)
print(f"User permissions: {permissions}")

# Check user's roles
roles = await rbac.get_user_roles(user_id)
print(f"User roles: {[r.name for r in roles]}")

# Check access logs
logs = await rbac.get_access_logs(user_id=user_id, limit=10)
for log in logs:
    if not log.access_granted:
        print(f"Denied: {log.action} on {log.resource_type}, reason: {log.denial_reason}")
```

### Missing Dependencies

```python
# Ensure all required dependencies are injected
@router.get("/api/v1/protected")
@require_permission("resource:read")
async def protected_endpoint(
    request: Request,  # Required
    rbac: RBACService = Depends(get_rbac_service),  # Required
    current_user: dict = Depends(get_current_user)  # Required
):
    return {"message": "Success"}
```

---

## Next Steps

- Integrate Kafka event sourcing for RBAC events
- Add AI-powered access control with risk scoring
- Implement rate limiting based on user roles
- Create RBAC admin UI for role and permission management

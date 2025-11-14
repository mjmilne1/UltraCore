"""
Comprehensive Integration Tests for RBAC Middleware
Tests all 5 permission decorators and resource access with PostgreSQL
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import FastAPI, Depends, Request, APIRouter
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient  # Keep for reference
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from ultracore.database.base import Base, get_async_session
from ultracore.database.models.security import User
from ultracore.database.models.rbac import Role, Permission, ResourcePolicy
from ultracore.database.repositories.user_repository import UserRepository
from ultracore.database.repositories.rbac_repository import (
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
    ResourcePolicyRepository
)
from ultracore.security.rbac import RBACService
from ultracore.security.rbac.middleware import (
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_role,
    require_resource_access,
    get_rbac_service,
    get_current_user,
    RBACMiddleware
)


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://ultracore:ultracore@localhost:5432/ultracore_test"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def engine():
    """Create async engine for tests"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(engine):
    """Create async session for tests"""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def tenant_id():
    """Test tenant ID"""
    return uuid4()


@pytest.fixture
async def test_user(session: AsyncSession, tenant_id: UUID):
    """Create test user"""
    user_repo = UserRepository(session)
    
    user = User(
        user_id=uuid4(),
        tenant_id=tenant_id,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(user)
    await session.flush()
    
    return user


@pytest.fixture
async def admin_user(session: AsyncSession, tenant_id: UUID):
    """Create admin user"""
    user_repo = UserRepository(session)
    
    user = User(
        user_id=uuid4(),
        tenant_id=tenant_id,
        username="adminuser",
        email="admin@example.com",
        password_hash="hashed_password",
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(user)
    await session.flush()
    
    return user


@pytest.fixture
async def test_role(session: AsyncSession, tenant_id: UUID):
    """Create test role"""
    role = Role(
        role_id=uuid4(),
        tenant_id=tenant_id,
        name="test_role",
        display_name="Test Role",
        level=3,
        is_active=True,
        is_system_role=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(role)
    await session.flush()
    
    return role


@pytest.fixture
async def admin_role(session: AsyncSession, tenant_id: UUID):
    """Create admin role"""
    role = Role(
        role_id=uuid4(),
        tenant_id=tenant_id,
        name="admin",
        display_name="Administrator",
        level=1,
        is_active=True,
        is_system_role=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(role)
    await session.flush()
    
    return role


@pytest.fixture
async def test_permission(session: AsyncSession, tenant_id: UUID):
    """Create test permission"""
    permission = Permission(
        permission_id=uuid4(),
        tenant_id=tenant_id,
        name="accounts:read",
        resource="accounts",
        action="read",
        description="Read accounts",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(permission)
    await session.flush()
    
    return permission


@pytest.fixture
async def write_permission(session: AsyncSession, tenant_id: UUID):
    """Create write permission"""
    permission = Permission(
        permission_id=uuid4(),
        tenant_id=tenant_id,
        name="accounts:write",
        resource="accounts",
        action="write",
        description="Write accounts",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(permission)
    await session.flush()
    
    return permission


@pytest.fixture
async def delete_permission(session: AsyncSession, tenant_id: UUID):
    """Create delete permission"""
    permission = Permission(
        permission_id=uuid4(),
        tenant_id=tenant_id,
        name="accounts:delete",
        resource="accounts",
        action="delete",
        description="Delete accounts",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(permission)
    await session.flush()
    
    return permission


@pytest.fixture
async def rbac_service(session: AsyncSession):
    """Create RBAC service"""
    return RBACService(session)


# ============================================================================
# Test FastAPI App Setup
# ============================================================================

def create_test_app(session: AsyncSession, current_user: dict = None):
    """Create test FastAPI app with RBAC middleware"""
    app = FastAPI()
    router = APIRouter()
    
    # Override dependencies
    async def override_get_session():
        yield session
    
    async def override_get_current_user():
        if current_user is None:
            return {
                "user_id": uuid4(),
                "tenant_id": uuid4(),
                "username": "anonymous"
            }
        return current_user
    
    async def override_get_rbac_service():
        yield RBACService(session)
    
    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_rbac_service] = override_get_rbac_service
    
    # Test endpoints
    @router.get("/test/require-permission")
    @require_permission("accounts:read")
    async def test_require_permission(
        request: Request,
        rbac: RBACService = Depends(get_rbac_service),
        user: dict = Depends(get_current_user)
    ):
        return {"message": "Permission granted"}
    
    @router.get("/test/require-any-permission")
    @require_any_permission(["accounts:read", "accounts:write"])
    async def test_require_any_permission(
        request: Request,
        rbac: RBACService = Depends(get_rbac_service),
        user: dict = Depends(get_current_user)
    ):
        return {"message": "Permission granted"}
    
    @router.get("/test/require-all-permissions")
    @require_all_permissions(["accounts:read", "accounts:write"])
    async def test_require_all_permissions(
        request: Request,
        rbac: RBACService = Depends(get_rbac_service),
        user: dict = Depends(get_current_user)
    ):
        return {"message": "Permission granted"}
    
    @router.get("/test/require-role")
    @require_role("admin")
    async def test_require_role(
        request: Request,
        rbac: RBACService = Depends(get_rbac_service),
        user: dict = Depends(get_current_user)
    ):
        return {"message": "Role granted"}
    
    @router.delete("/test/accounts/{account_id}")
    @require_resource_access("accounts", "delete", "account_id")
    async def test_require_resource_access(
        account_id: UUID,
        request: Request,
        rbac: RBACService = Depends(get_rbac_service),
        user: dict = Depends(get_current_user)
    ):
        return {"message": "Resource access granted"}
    
    app.include_router(router)
    
    return app


# ============================================================================
# Test: @require_permission Decorator
# ============================================================================

@pytest.mark.asyncio
async def test_require_permission_granted(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    test_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_permission decorator with granted permission"""
    # Assign permission to role
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=test_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    # Assign role to user
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    # Create app with current user
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    # Test endpoint
    response = client.get("/test/require-permission")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Permission granted"}


@pytest.mark.asyncio
async def test_require_permission_denied(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User
):
    """Test @require_permission decorator with denied permission"""
    # User has no permissions
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    
    # Test endpoint using async client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test/require-permission")
    
    assert response.status_code == 403
    assert "Missing required permission" in response.json()["detail"]


# ============================================================================
# Test: @require_any_permission Decorator
# ============================================================================

@pytest.mark.asyncio
async def test_require_any_permission_granted_first(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    test_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_any_permission with first permission granted"""
    # Assign only read permission
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=test_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-any-permission")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Permission granted"}


@pytest.mark.asyncio
async def test_require_any_permission_granted_second(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    write_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_any_permission with second permission granted"""
    # Assign only write permission
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=write_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-any-permission")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Permission granted"}


@pytest.mark.asyncio
async def test_require_any_permission_denied(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User
):
    """Test @require_any_permission with no permissions"""
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-any-permission")
    
    assert response.status_code == 403
    assert "Missing required permissions" in response.json()["detail"]


# ============================================================================
# Test: @require_all_permissions Decorator
# ============================================================================

@pytest.mark.asyncio
async def test_require_all_permissions_granted(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    test_permission: Permission,
    write_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_all_permissions with all permissions granted"""
    # Assign both permissions
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=test_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=write_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-all-permissions")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Permission granted"}


@pytest.mark.asyncio
async def test_require_all_permissions_denied_missing_one(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    test_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_all_permissions with only one permission"""
    # Assign only read permission (missing write)
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=test_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-all-permissions")
    
    assert response.status_code == 403
    assert "Missing required permissions" in response.json()["detail"]


# ============================================================================
# Test: @require_role Decorator
# ============================================================================

@pytest.mark.asyncio
async def test_require_role_granted(
    session: AsyncSession,
    tenant_id: UUID,
    admin_user: User,
    admin_role: Role,
    rbac_service: RBACService
):
    """Test @require_role decorator with granted role"""
    # Assign admin role to user
    await rbac_service.assign_role_to_user(
        user_id=admin_user.user_id,
        role_id=admin_role.role_id,
        assigned_by=admin_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": admin_user.user_id,
        "tenant_id": tenant_id,
        "username": admin_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-role")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Role granted"}


@pytest.mark.asyncio
async def test_require_role_denied(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    rbac_service: RBACService
):
    """Test @require_role decorator with wrong role"""
    # Assign non-admin role
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.get("/test/require-role")
    
    assert response.status_code == 403
    assert "Missing required role" in response.json()["detail"]


# ============================================================================
# Test: @require_resource_access Decorator
# ============================================================================

@pytest.mark.asyncio
async def test_require_resource_access_granted(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    delete_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_resource_access with granted access"""
    # Assign delete permission
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=delete_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    # Create resource policy allowing delete
    account_id = uuid4()
    await rbac_service.create_resource_policy(
        tenant_id=tenant_id,
        name="allow_delete_account",
        resource_type="accounts",
        resource_id=account_id,
        allowed_actions=["delete"],
        role_id=test_role.role_id,
        priority=10,
        created_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.delete(f"/test/accounts/{account_id}")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Resource access granted"}


@pytest.mark.asyncio
async def test_require_resource_access_denied_no_permission(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User
):
    """Test @require_resource_access without permission"""
    account_id = uuid4()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.delete(f"/test/accounts/{account_id}")
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_require_resource_access_denied_by_policy(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    delete_permission: Permission,
    rbac_service: RBACService
):
    """Test @require_resource_access denied by resource policy"""
    # Assign delete permission
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=delete_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    # Create resource policy DENYING delete
    account_id = uuid4()
    await rbac_service.create_resource_policy(
        tenant_id=tenant_id,
        name="deny_delete_account",
        resource_type="accounts",
        resource_id=account_id,
        denied_actions=["delete"],
        role_id=test_role.role_id,
        priority=100,  # High priority
        created_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    response = client.delete(f"/test/accounts/{account_id}")
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


# ============================================================================
# Test: Access Logging
# ============================================================================

@pytest.mark.asyncio
async def test_access_logging_granted(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    test_role: Role,
    test_permission: Permission,
    rbac_service: RBACService
):
    """Test that granted access is logged"""
    # Setup permissions
    await rbac_service.assign_permission_to_role(
        role_id=test_role.role_id,
        permission_id=test_permission.permission_id,
        granted_by=test_user.user_id
    )
    
    await rbac_service.assign_role_to_user(
        user_id=test_user.user_id,
        role_id=test_role.role_id,
        assigned_by=test_user.user_id
    )
    
    await session.commit()
    
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    # Make request
    response = client.get("/test/require-permission")
    assert response.status_code == 200
    
    # Check access log
    logs = await rbac_service.get_access_logs(user_id=test_user.user_id, limit=1)
    
    assert len(logs) > 0
    assert logs[0].user_id == test_user.user_id
    assert logs[0].access_granted == True
    assert logs[0].action == "read"
    assert logs[0].resource_type == "accounts"


@pytest.mark.asyncio
async def test_access_logging_denied(
    session: AsyncSession,
    tenant_id: UUID,
    test_user: User,
    rbac_service: RBACService
):
    """Test that denied access is logged"""
    current_user = {
        "user_id": test_user.user_id,
        "tenant_id": tenant_id,
        "username": test_user.username
    }
    app = create_test_app(session, current_user)
    client = TestClient(app)
    
    # Make request
    response = client.get("/test/require-permission")
    assert response.status_code == 403
    
    # Check access log
    logs = await rbac_service.get_access_logs(user_id=test_user.user_id, limit=1)
    
    assert len(logs) > 0
    assert logs[0].user_id == test_user.user_id
    assert logs[0].access_granted == False
    assert logs[0].denial_reason is not None
    assert "permission" in logs[0].denial_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

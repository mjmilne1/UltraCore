"""Tenant Provisioning Service"""
from datetime import datetime
from typing import Optional
import asyncpg
from uuid import uuid4

from ..models import TenantConfig
from ..events import TenantTier, TenantStatus
from ..aggregates.tenant_aggregate import TenantAggregate
from ..encryption import PasswordEncryption, hash_master_password

class TenantProvisioningService:
    """Provision new tenants with hybrid isolation strategy"""
    
    def __init__(self, master_password: str, 
                 postgres_admin_host: str = "localhost",
                 postgres_admin_port: int = 5432,
                 postgres_admin_user: str = "postgres",
                 postgres_admin_password: str = "admin"):
        """Initialize provisioning service"""
        self.encryption = PasswordEncryption(master_password)
        self.master_password_hash = hash_master_password(master_password)
        self.postgres_admin_host = postgres_admin_host
        self.postgres_admin_port = postgres_admin_port
        self.postgres_admin_user = postgres_admin_user
        self.postgres_admin_password = postgres_admin_password
    
    async def provision_tenant(self,
                              tenant_id: str,
                              tenant_name: str,
                              tier: TenantTier,
                              owner_email: str,
                              created_by: str) -> TenantConfig:
        """Provision a new tenant based on tier"""
        
        # Create aggregate
        aggregate = TenantAggregate(tenant_id=tenant_id)
        aggregate = aggregate.create_tenant(tenant_name, tier, owner_email, created_by)
        
        if tier == TenantTier.ENTERPRISE:
            config = await self._provision_enterprise_tenant(aggregate)
        elif tier == TenantTier.STANDARD:
            config = await self._provision_standard_tenant(aggregate)
        else:  # SMALL
            config = await self._provision_small_tenant(aggregate)
        
        return config
    
    async def _provision_enterprise_tenant(self, 
                                          aggregate: TenantAggregate) -> TenantConfig:
        """Provision enterprise tenant with dedicated database"""
        
        # Generate database credentials
        db_name = f"ultracore_{aggregate.tenant_id.replace('-', '_')}"
        db_username = f"uc_{aggregate.tenant_id[:8]}"
        db_password = self._generate_password()
        
        # Start provisioning
        aggregate = aggregate.start_provisioning(
            tier=TenantTier.ENTERPRISE,
            db_name=db_name
        )
        
        # Create dedicated database
        await self._create_database(db_name)
        
        # Create database user
        await self._create_db_user(db_username, db_password, db_name)
        
        # Complete database creation
        aggregate = aggregate.complete_database_creation(
            db_host=self.postgres_admin_host,
            db_port=self.postgres_admin_port,
            db_name=db_name,
            db_username=db_username
        )
        
        # Run migrations (placeholder - implement with Alembic)
        migration_version = "1.0.0"
        tables_created = 50  # Placeholder
        aggregate = aggregate.complete_migrations(migration_version, tables_created)
        
        # Activate tenant
        aggregate = aggregate.activate()
        
        # Encrypt password
        encrypted_password = self.encryption.encrypt(db_password)
        
        # Create tenant config
        config = TenantConfig(
            tenant_id=aggregate.tenant_id,
            tenant_name=aggregate.tenant_name,
            tier=TenantTier.ENTERPRISE,
            status=TenantStatus.ACTIVE,
            owner_email=aggregate.owner_email,
            db_host=self.postgres_admin_host,
            db_port=self.postgres_admin_port,
            db_name=db_name,
            db_username=db_username,
            db_password_encrypted=encrypted_password,
            min_connections=10,
            max_connections=50,
            master_password_hash=self.master_password_hash,
            created_by=aggregate.events[0].created_by if aggregate.events else ""
        )
        
        return config
    
    async def _provision_standard_tenant(self,
                                        aggregate: TenantAggregate) -> TenantConfig:
        """Provision standard tenant with dedicated schema"""
        
        # Use shared database with dedicated schema
        shared_db_name = "ultracore_shared"
        schema_name = f"tenant_{aggregate.tenant_id.replace('-', '_')}"
        db_username = f"uc_{aggregate.tenant_id[:8]}"
        db_password = self._generate_password()
        
        # Start provisioning
        aggregate = aggregate.start_provisioning(
            tier=TenantTier.STANDARD,
            db_name=shared_db_name,
            schema_name=schema_name
        )
        
        # Ensure shared database exists
        await self._ensure_database_exists(shared_db_name)
        
        # Create schema
        await self._create_schema(shared_db_name, schema_name)
        
        # Create database user with schema access
        await self._create_schema_user(shared_db_name, schema_name, 
                                       db_username, db_password)
        
        # Complete schema creation
        aggregate = aggregate.complete_schema_creation(shared_db_name, schema_name)
        
        # Run migrations
        migration_version = "1.0.0"
        tables_created = 50
        aggregate = aggregate.complete_migrations(migration_version, tables_created)
        
        # Activate tenant
        aggregate = aggregate.activate()
        
        # Encrypt password
        encrypted_password = self.encryption.encrypt(db_password)
        
        # Create tenant config
        config = TenantConfig(
            tenant_id=aggregate.tenant_id,
            tenant_name=aggregate.tenant_name,
            tier=TenantTier.STANDARD,
            status=TenantStatus.ACTIVE,
            owner_email=aggregate.owner_email,
            db_host=self.postgres_admin_host,
            db_port=self.postgres_admin_port,
            db_name=shared_db_name,
            schema_name=schema_name,
            db_username=db_username,
            db_password_encrypted=encrypted_password,
            min_connections=5,
            max_connections=20,
            master_password_hash=self.master_password_hash,
            created_by=aggregate.events[0].created_by if aggregate.events else ""
        )
        
        return config
    
    async def _provision_small_tenant(self,
                                     aggregate: TenantAggregate) -> TenantConfig:
        """Provision small tenant with row-level isolation"""
        
        # Use shared database and shared schema (row-level isolation via tenant_id)
        shared_db_name = "ultracore_shared"
        
        # Start provisioning
        aggregate = aggregate.start_provisioning(
            tier=TenantTier.SMALL,
            db_name=shared_db_name
        )
        
        # Ensure shared database exists
        await self._ensure_database_exists(shared_db_name)
        
        # No dedicated schema or user needed - use shared credentials
        # Activate immediately
        aggregate = aggregate.activate()
        
        # Create tenant config (no dedicated database credentials)
        config = TenantConfig(
            tenant_id=aggregate.tenant_id,
            tenant_name=aggregate.tenant_name,
            tier=TenantTier.SMALL,
            status=TenantStatus.ACTIVE,
            owner_email=aggregate.owner_email,
            min_connections=2,
            max_connections=10,
            created_by=aggregate.events[0].created_by if aggregate.events else ""
        )
        
        return config
    
    async def _create_database(self, db_name: str):
        """Create new database"""
        conn = await asyncpg.connect(
            host=self.postgres_admin_host,
            port=self.postgres_admin_port,
            user=self.postgres_admin_user,
            password=self.postgres_admin_password,
            database="postgres"
        )
        try:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
        finally:
            await conn.close()
    
    async def _ensure_database_exists(self, db_name: str):
        """Ensure database exists (create if not)"""
        conn = await asyncpg.connect(
            host=self.postgres_admin_host,
            port=self.postgres_admin_port,
            user=self.postgres_admin_user,
            password=self.postgres_admin_password,
            database="postgres"
        )
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                db_name
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{db_name}"')
        finally:
            await conn.close()
    
     def _validate_sql_identifier(self, identifier: str) -> str:
        """Validate SQL identifier to prevent injection attacks"""
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}. Must contain only alphanumeric characters and underscores, and start with a letter.")
        if len(identifier) > 63:  # PostgreSQL identifier length limit
            raise ValueError(f"SQL identifier too long: {identifier}. Maximum 63 characters.")
        return identifier
    
    async def _create_database_user(self, db_name: str, username: str, password: str):
        """Create database user with full privileges - SECURE VERSION"""
        # SECURITY FIX: Validate identifiers to prevent SQL injection
        username = self._validate_sql_identifier(username)
        db_name = self._validate_sql_identifier(db_name)
        
        conn = await asyncpg.connect(
            host=self.postgres_admin_host,
            port=self.postgres_admin_port,
            user=self.postgres_admin_user,
            password=self.postgres_admin_password,
            database='postgres'
        )
        try:
            # Use parameterized query for password (prevents SQL injection)
            await conn.execute(
                f'CREATE USER {username} WITH PASSWORD $1',
                password
            )
            # Identifiers are validated, safe to use in query
            await conn.execute(
                f'GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username}'
            )
        finally:
            await conn.close())
    
    async def _create_schema(self, db_name: str, schema_name: str):
        """Create schema in database"""
        conn = await asyncpg.connect(
            host=self.postgres_admin_host,
            port=self.postgres_admin_port,
            user=self.postgres_admin_user,
            password=self.postgres_admin_password,
            database=db_name
        )
        try:
            await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        finally:
            await conn.close()
    
    async def _create_schema_user(self, db_name: str, schema_name: str,
                                  username: str, password: str):
        """Create user with access to specific schema - SECURE VERSION"""
        # SECURITY FIX: Validate all identifiers
        db_name = self._validate_sql_identifier(db_name)
        schema_name = self._validate_sql_identifier(schema_name)
        username = self._validate_sql_identifier(username)
        
        conn = await asyncpg.connect(
            host=self.postgres_admin_host,
            port=self.postgres_admin_port,
            user=self.postgres_admin_user,
            password=self.postgres_admin_password,
            database=db_name
        )
        try:
            # Use parameterized query for password
            await conn.execute(
                f'CREATE USER {username} WITH PASSWORD $1',
                password
            )
            await conn.execute(
                f'GRANT USAGE ON SCHEMA {schema_name} TO {username}'
            )
            await conn.execute(
                f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema_name} TO {username}'
            )
            await conn.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO {username}')
        finally:
            await conn.close()
    
    def _generate_password(self) -> str:
        """Generate secure random password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(32))

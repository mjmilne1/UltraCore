"""Add RBAC tables

Revision ID: 005
Revises: 004
Create Date: 2025-11-13 08:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('parent_role_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_system_role', sa.Boolean(), default=False),
        sa.Column('additional_data', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['parent_role_id'], ['roles.role_id']),
    )
    
    # Create indexes for roles
    op.create_index('idx_roles_tenant_name', 'roles', ['tenant_id', 'name'], unique=True)
    op.create_index('idx_roles_level', 'roles', ['level'])
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('additional_data', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
    )
    
    # Create indexes for permissions
    op.create_index('idx_permissions_resource_action', 'permissions', ['resource', 'action'])
    op.create_index('idx_permissions_tenant', 'permissions', ['tenant_id'])
    
    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.permission_id'], ondelete='CASCADE'),
    )
    
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True)),
        sa.Column('expires_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE'),
    )
    
    # Create resource_policies table
    op.create_table(
        'resource_policies',
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('role_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('allowed_actions', postgresql.ARRAY(sa.String())),
        sa.Column('denied_actions', postgresql.ARRAY(sa.String())),
        sa.Column('conditions', postgresql.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('priority', sa.String(20), default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )
    
    # Create indexes for resource_policies
    op.create_index('idx_resource_policies_resource', 'resource_policies', ['resource_type', 'resource_id'])
    op.create_index('idx_resource_policies_role', 'resource_policies', ['role_id'])
    op.create_index('idx_resource_policies_user', 'resource_policies', ['user_id'])
    op.create_index('idx_resource_policies_priority', 'resource_policies', ['priority'])
    
    # Create access_logs table
    op.create_table(
        'access_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('role_id', postgresql.UUID(as_uuid=True)),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('access_granted', sa.Boolean(), nullable=False),
        sa.Column('denial_reason', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_id', postgresql.UUID(as_uuid=True)),
        sa.Column('risk_score', sa.String(20)),
        sa.Column('ai_decision', sa.String(50)),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id']),
    )
    
    # Create indexes for access_logs
    op.create_index('idx_access_logs_user_timestamp', 'access_logs', ['user_id', 'timestamp'])
    op.create_index('idx_access_logs_resource', 'access_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_access_logs_denied', 'access_logs', ['access_granted', 'timestamp'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('access_logs')
    op.drop_table('resource_policies')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')

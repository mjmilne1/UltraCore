"""Add mfa_last_used_timestamp to users

Revision ID: 004
Revises: 003
Create Date: 2025-11-13 07:40:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add mfa_last_used_timestamp column to users table
    op.add_column('users', sa.Column('mfa_last_used_timestamp', sa.Integer(), nullable=True))


def downgrade():
    # Remove mfa_last_used_timestamp column
    op.drop_column('users', 'mfa_last_used_timestamp')

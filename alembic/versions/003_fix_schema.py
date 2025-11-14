"""Fix schema to match models

Revision ID: 003
Revises: 002
Create Date: 2025-11-13 07:35:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Rename metadata to additional_data in security_events
    op.alter_column('security_events', 'metadata', new_column_name='additional_data')


def downgrade():
    # Rename back
    op.alter_column('security_events', 'additional_data', new_column_name='metadata')

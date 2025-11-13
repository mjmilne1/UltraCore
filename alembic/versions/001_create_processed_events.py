"""
Create processed_events table for idempotency

This table tracks which events have been processed to ensure
exactly-once semantics in event materialization.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create processed_events table"""
    
    op.create_table(
        'processed_events',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('aggregate_id', sa.String(100), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumer_group', sa.String(100), nullable=True),
        
        # Indexes for performance
        sa.Index('idx_processed_events_tenant_aggregate', 'tenant_id', 'aggregate_id'),
        sa.Index('idx_processed_events_processed_at', 'processed_at'),
        
        # Unique constraint on event_id
        sa.UniqueConstraint('event_id', name='uq_processed_events_event_id'),
        
        comment='Tracks processed events for idempotency'
    )


def downgrade() -> None:
    """Drop processed_events table"""
    op.drop_table('processed_events')

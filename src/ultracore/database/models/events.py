"""
UltraCore Database Models - Event Store

Event Sourcing implementation:
- All state changes captured as events
- Immutable event log
- Event replay capability
- Audit trail
- Time travel debugging

Architecture:
- Partition by tenant_id and event_date
- Index on aggregate_id for fast lookups
- Never update/delete events (append-only)
"""

from sqlalchemy import Column, String, DateTime, Integer, Index, text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

from ultracore.database.models.base import Base


class EventStore(Base):
    """
    Event Store - Immutable event log
    
    Features:
    - Append-only (never update/delete)
    - Partition by tenant_id and date
    - All domain events stored here
    - Full audit trail
    - Event replay for debugging
    """
    
    __tablename__ = "event_store"
    __table_args__ = (
        # Composite index for event queries
        Index('idx_event_store_aggregate', 'tenant_id', 'aggregate_type', 'aggregate_id', 'event_date'),
        Index('idx_event_store_type', 'tenant_id', 'event_type', 'event_date'),
        Index('idx_event_store_date', 'event_date'),
        
        # Partition hint (requires PostgreSQL 10+)
        {'postgresql_partition_by': 'RANGE (event_date)'},
        
        {'comment': 'Event Store - Immutable event log for event sourcing'}
    )
    
    # Primary Key (sequence for fast inserts)
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Event sequence number"
    )
    
    # Multi-tenancy
    tenant_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tenant identifier"
    )
    
    # Event metadata
    event_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=text("gen_random_uuid()"),
        comment="Unique event identifier"
    )
    
    event_type = Column(
        String(100),
        nullable=False,
        comment="Event type (e.g., CustomerCreated, AccountOpened)"
    )
    
    event_version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Event schema version"
    )
    
    # Aggregate (the entity being changed)
    aggregate_type = Column(
        String(100),
        nullable=False,
        comment="Aggregate type (Customer, Account, Loan, etc.)"
    )
    
    aggregate_id = Column(
        String(100),
        nullable=False,
        comment="Aggregate identifier"
    )
    
    aggregate_version = Column(
        Integer,
        nullable=False,
        comment="Aggregate version after this event"
    )
    
    # Event data
    event_data = Column(
        JSONB,
        nullable=False,
        comment="Event payload (all state changes)"
    )
    
    # Causation (for tracking event chains)
    correlation_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Correlation ID for related events"
    )
    
    causation_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of event that caused this event"
    )
    
    # Timestamps
    event_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="When event occurred"
    )
    
    # User context
    user_id = Column(
        String(100),
        nullable=False,
        comment="User who triggered the event"
    )
    
    # Metadata
    metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional metadata (IP, user agent, etc.)"
    )
    
    def __repr__(self):
        return f"<EventStore(id={self.id}, type={self.event_type}, aggregate={self.aggregate_type}:{self.aggregate_id})>"

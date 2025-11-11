"""
UltraCore Database Models - Base

Base model with common fields for all entities:
- tenant_id (multi-tenancy)
- Timestamps (created_at, updated_at)
- Soft delete support
- Audit fields
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from ultracore.database.config import Base


class BaseModel(Base):
    """
    Abstract base model with common fields
    
    Features:
    - Multi-tenancy (tenant_id)
    - Timestamps (created_at, updated_at)
    - Soft delete (deleted_at)
    - Audit trail (created_by, updated_by)
    - Optimistic locking (version)
    """
    
    __abstract__ = True
    
    # Primary Key (UUID for distributed systems)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        comment="Primary key UUID"
    )
    
    # Multi-tenancy
    tenant_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tenant identifier for multi-tenancy"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
        comment="Last update timestamp"
    )
    
    # Soft delete
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    # Audit fields
    created_by = Column(
        String(100),
        nullable=False,
        comment="User who created the record"
    )
    
    updated_by = Column(
        String(100),
        nullable=True,
        comment="User who last updated the record"
    )
    
    # Optimistic locking
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Version number for optimistic locking"
    )
    
    # Extended attributes (JSON)
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="Extended attributes in JSON format"
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted"""
        return self.deleted_at is not None


# Common indexes for all tables (applied via naming convention)
# Index naming: idx_{tablename}_{column_name}
# Unique index: uq_{tablename}_{column_name}
# Foreign key: fk_{tablename}_{column_name}

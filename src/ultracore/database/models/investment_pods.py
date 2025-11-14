"""
Database models for Investment Pods.

SQLAlchemy ORM models for pod persistence.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship

from ..config import Base


class InvestmentPodDB(Base):
    """Investment Pod database model."""
    
    __tablename__ = "investment_pods"
    
    # Primary key
    pod_id = Column(String(36), primary_key=True)
    
    # Tenant and user
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Goal information
    goal_type = Column(String(50), nullable=False)
    goal_name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)
    target_date = Column(DateTime, nullable=True)
    
    # Financial details
    initial_deposit = Column(Numeric(15, 2), nullable=False)
    monthly_contribution = Column(Numeric(15, 2), nullable=False, default=0)
    current_value = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Risk and strategy
    risk_tolerance = Column(String(50), nullable=False)
    target_allocation = Column(JSON, nullable=False)
    current_allocation = Column(JSON, nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default="draft")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    funded_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    transactions = relationship("PodTransactionDB", back_populates="pod", cascade="all, delete-orphan")
    performance_history = relationship("PodPerformanceDB", back_populates="pod", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_pod_tenant_user", "tenant_id", "user_id"),
        Index("idx_pod_status", "status"),
        Index("idx_pod_goal_type", "goal_type"),
    )


class PodTransactionDB(Base):
    """Pod transaction database model."""
    
    __tablename__ = "pod_transactions"
    
    # Primary key
    transaction_id = Column(String(36), primary_key=True)
    
    # Foreign key
    pod_id = Column(String(36), ForeignKey("investment_pods.pod_id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # contribution, withdrawal, rebalance, etc.
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    pod = relationship("InvestmentPodDB", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_pod", "pod_id"),
        Index("idx_transaction_type", "transaction_type"),
        Index("idx_transaction_created", "created_at"),
    )


class PodAllocationDB(Base):
    """Pod allocation snapshot database model."""
    
    __tablename__ = "pod_allocations"
    
    # Primary key
    allocation_id = Column(String(36), primary_key=True)
    
    # Foreign key
    pod_id = Column(String(36), ForeignKey("investment_pods.pod_id"), nullable=False)
    
    # Allocation details
    allocation_type = Column(String(50), nullable=False)  # target, current
    allocation = Column(JSON, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_allocation_pod", "pod_id"),
        Index("idx_allocation_type", "allocation_type"),
    )


class PodPerformanceDB(Base):
    """Pod performance history database model."""
    
    __tablename__ = "pod_performance_history"
    
    # Primary key
    performance_id = Column(String(36), primary_key=True)
    
    # Foreign key
    pod_id = Column(String(36), ForeignKey("investment_pods.pod_id"), nullable=False)
    
    # Performance metrics
    current_value = Column(Numeric(15, 2), nullable=False)
    total_contributions = Column(Numeric(15, 2), nullable=False)
    total_withdrawals = Column(Numeric(15, 2), nullable=False)
    total_return = Column(Numeric(15, 2), nullable=False)
    total_return_pct = Column(Numeric(10, 4), nullable=False)
    
    # Risk metrics
    volatility = Column(Numeric(10, 4), nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)
    
    # Timestamp
    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    pod = relationship("InvestmentPodDB", back_populates="performance_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_performance_pod", "pod_id"),
        Index("idx_performance_date", "snapshot_date"),
    )

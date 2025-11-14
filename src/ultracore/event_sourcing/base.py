"""
Event Sourcing Base Classes.

Core abstractions for event sourcing implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type
from uuid import UUID, uuid4
import json


class EventType(str, Enum):
    """Event type categories."""
    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    CUSTOMER_KYC_COMPLETED = "customer.kyc.completed"
    CUSTOMER_RISK_ASSESSED = "customer.risk.assessed"
    
    # Account events
    ACCOUNT_OPENED = "account.opened"
    ACCOUNT_CLOSED = "account.closed"
    ACCOUNT_FROZEN = "account.frozen"
    ACCOUNT_UNFROZEN = "account.unfrozen"
    ACCOUNT_BALANCE_UPDATED = "account.balance.updated"
    
    # Transaction events
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_POSTED = "transaction.posted"
    TRANSACTION_REVERSED = "transaction.reversed"
    TRANSACTION_SETTLED = "transaction.settled"
    
    # Payment events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Loan events
    LOAN_APPLICATION_SUBMITTED = "loan.application.submitted"
    LOAN_APPROVED = "loan.approved"
    LOAN_REJECTED = "loan.rejected"
    LOAN_DISBURSED = "loan.disbursed"
    LOAN_REPAYMENT_MADE = "loan.repayment.made"
    LOAN_DEFAULTED = "loan.defaulted"
    
    # Investment events
    INVESTMENT_POD_CREATED = "investment.pod.created"
    INVESTMENT_CONTRIBUTED = "investment.contributed"
    INVESTMENT_WITHDRAWN = "investment.withdrawn"
    INVESTMENT_REBALANCED = "investment.rebalanced"
    
    # Compliance events
    COMPLIANCE_CHECK_INITIATED = "compliance.check.initiated"
    COMPLIANCE_CHECK_PASSED = "compliance.check.passed"
    COMPLIANCE_CHECK_FAILED = "compliance.check.failed"
    SUSPICIOUS_ACTIVITY_DETECTED = "compliance.suspicious.activity"
    REGULATORY_REPORT_FILED = "compliance.report.filed"
    
    # Risk events
    RISK_ASSESSMENT_COMPLETED = "risk.assessment.completed"
    RISK_LIMIT_BREACHED = "risk.limit.breached"
    FRAUD_DETECTED = "risk.fraud.detected"
    
    # Collateral events
    COLLATERAL_PLEDGED = "collateral.pledged"
    COLLATERAL_RELEASED = "collateral.released"
    COLLATERAL_VALUED = "collateral.valued"
    
    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_FAILED = "notification.failed"
    
    # Audit events
    AUDIT_LOG_CREATED = "audit.log.created"
    
    # System events
    SYSTEM_SNAPSHOT_CREATED = "system.snapshot.created"
    SYSTEM_MIGRATION_COMPLETED = "system.migration.completed"


@dataclass
class EventMetadata:
    """Event metadata."""
    event_id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.SYSTEM_SNAPSHOT_CREATED
    aggregate_id: str = ""
    aggregate_type: str = ""
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    causation_id: Optional[UUID] = None  # ID of event that caused this event
    correlation_id: Optional[UUID] = None  # ID for tracking related events
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class Event:
    """
    Base event class.
    
    All domain events inherit from this class.
    """
    metadata: EventMetadata
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "metadata": {
                "event_id": str(self.metadata.event_id),
                "event_type": self.metadata.event_type.value,
                "aggregate_id": self.metadata.aggregate_id,
                "aggregate_type": self.metadata.aggregate_type,
                "version": self.metadata.version,
                "timestamp": self.metadata.timestamp.isoformat(),
                "causation_id": str(self.metadata.causation_id) if self.metadata.causation_id else None,
                "correlation_id": str(self.metadata.correlation_id) if self.metadata.correlation_id else None,
                "user_id": self.metadata.user_id,
                "tenant_id": self.metadata.tenant_id,
            },
            "data": self.data
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        metadata = EventMetadata(
            event_id=UUID(data["metadata"]["event_id"]),
            event_type=EventType(data["metadata"]["event_type"]),
            aggregate_id=data["metadata"]["aggregate_id"],
            aggregate_type=data["metadata"]["aggregate_type"],
            version=data["metadata"]["version"],
            timestamp=datetime.fromisoformat(data["metadata"]["timestamp"]),
            causation_id=UUID(data["metadata"]["causation_id"]) if data["metadata"].get("causation_id") else None,
            correlation_id=UUID(data["metadata"]["correlation_id"]) if data["metadata"].get("correlation_id") else None,
            user_id=data["metadata"].get("user_id"),
            tenant_id=data["metadata"].get("tenant_id"),
        )
        return cls(metadata=metadata, data=data["data"])
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))


class AggregateRoot(ABC):
    """
    Base class for aggregate roots.
    
    Aggregates are the consistency boundaries in event sourcing.
    """
    
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.uncommitted_events: List[Event] = []
    
    @abstractmethod
    def get_aggregate_type(self) -> str:
        """Get the aggregate type name."""
        pass
    
    def apply_event(self, event: Event) -> None:
        """
        Apply an event to the aggregate.
        
        This method should be implemented to update aggregate state.
        """
        self.version = event.metadata.version
    
    def raise_event(self, event_type: EventType, data: Dict[str, Any], **metadata_kwargs) -> Event:
        """
        Raise a new domain event.
        
        Args:
            event_type: Type of event
            data: Event data
            **metadata_kwargs: Additional metadata fields
            
        Returns:
            Created event
        """
        metadata = EventMetadata(
            event_type=event_type,
            aggregate_id=self.aggregate_id,
            aggregate_type=self.get_aggregate_type(),
            version=self.version + 1,
            **metadata_kwargs
        )
        
        event = Event(metadata=metadata, data=data)
        self.uncommitted_events.append(event)
        self.apply_event(event)
        
        return event
    
    def get_uncommitted_events(self) -> List[Event]:
        """Get uncommitted events."""
        return self.uncommitted_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Mark all uncommitted events as committed."""
        self.uncommitted_events.clear()
    
    def load_from_history(self, events: List[Event]) -> None:
        """
        Load aggregate from event history.
        
        Args:
            events: List of historical events
        """
        for event in events:
            self.apply_event(event)


class EventHandler(ABC):
    """
    Base class for event handlers.
    
    Event handlers process events and update read models.
    """
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """
        Handle an event.
        
        Args:
            event: Event to handle
        """
        pass
    
    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """
        Check if handler can handle event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            True if handler can handle event type
        """
        pass


class EventStore(ABC):
    """
    Abstract event store.
    
    Provides interface for storing and retrieving events.
    """
    
    @abstractmethod
    async def save_events(
        self,
        aggregate_id: str,
        events: List[Event],
        expected_version: Optional[int] = None
    ) -> None:
        """
        Save events to the store.
        
        Args:
            aggregate_id: Aggregate ID
            events: Events to save
            expected_version: Expected current version (for optimistic concurrency)
            
        Raises:
            ConcurrencyError: If expected version doesn't match
        """
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """
        Get events for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            from_version: Start version (inclusive)
            to_version: End version (inclusive)
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: EventType,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events by type.
        
        Args:
            event_type: Event type to filter
            from_timestamp: Start timestamp
            to_timestamp: End timestamp
            limit: Maximum number of events
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """
        Get current version of aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            
        Returns:
            Current version
        """
        pass


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails."""
    pass


class Snapshot:
    """
    Aggregate snapshot for optimization.
    
    Snapshots allow rebuilding aggregate state without replaying all events.
    """
    
    def __init__(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        state: Dict[str, Any],
        timestamp: datetime
    ):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = version
        self.state = state
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "state": self.state,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Create snapshot from dictionary."""
        return cls(
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            version=data["version"],
            state=data["state"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

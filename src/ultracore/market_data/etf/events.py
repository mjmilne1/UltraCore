"""
ETF Domain Events - Event Sourcing
All changes to ETF data are captured as immutable events
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

from ultracore.event_sourcing.base import Event, EventMetadata, EventType


# ETF-specific event types (extending the base EventType enum)
class ETFEventType:
    """ETF event type constants"""
    ETF_CREATED = "etf.created"
    ETF_METADATA_UPDATED = "etf.metadata.updated"
    ETF_DATA_UPDATED = "etf.data.updated"
    ETF_PRICE_UPDATED = "etf.price.updated"
    ETF_DELISTED = "etf.delisted"
    ETF_COLLECTION_STARTED = "etf.collection.started"
    ETF_COLLECTION_COMPLETED = "etf.collection.completed"
    ETF_COLLECTION_FAILED = "etf.collection.failed"


@dataclass
class ETFCreatedEvent:
    """Event fired when a new ETF is added to the system"""
    aggregate_id: UUID
    ticker: str
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,  # Use a base type
                aggregate_id=str(self.aggregate_id),
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_CREATED,
                "ticker": self.ticker,
                "metadata": self.metadata
            }
        )


@dataclass
class ETFMetadataUpdatedEvent:
    """Event fired when ETF metadata is updated"""
    aggregate_id: UUID
    ticker: str
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.aggregate_id),
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_METADATA_UPDATED,
                "ticker": self.ticker,
                "metadata": self.metadata
            }
        )


@dataclass
class ETFDataUpdatedEvent:
    """Event fired when historical price data is added/updated"""
    aggregate_id: UUID
    ticker: str
    price_data: List[Dict[str, Any]]
    data_points: int
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.aggregate_id),
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_DATA_UPDATED,
                "ticker": self.ticker,
                "price_data": self.price_data,
                "data_points": self.data_points
            }
        )


@dataclass
class ETFPriceUpdatedEvent:
    """Event fired when latest daily price is updated"""
    aggregate_id: UUID
    ticker: str
    price_data: Dict[str, Any]
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.aggregate_id),
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_PRICE_UPDATED,
                "ticker": self.ticker,
                "price_data": self.price_data
            }
        )


@dataclass
class ETFDelistedEvent:
    """Event fired when an ETF is delisted"""
    aggregate_id: UUID
    ticker: str
    reason: str
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.aggregate_id),
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_DELISTED,
                "ticker": self.ticker,
                "reason": self.reason
            }
        )


@dataclass
class ETFDataCollectionStartedEvent:
    """Event fired when data collection job starts"""
    job_id: UUID
    etf_count: int
    collection_type: str  # "initial" or "update"
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.job_id),
                aggregate_type="ETFCollection",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_COLLECTION_STARTED,
                "job_id": str(self.job_id),
                "etf_count": self.etf_count,
                "collection_type": self.collection_type
            }
        )


@dataclass
class ETFDataCollectionCompletedEvent:
    """Event fired when data collection job completes"""
    job_id: UUID
    successful: int
    failed: int
    duration_seconds: float
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=str(self.job_id),
                aggregate_type="ETFCollection",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_COLLECTION_COMPLETED,
                "job_id": str(self.job_id),
                "successful": self.successful,
                "failed": self.failed,
                "duration_seconds": duration_seconds
            }
        )


@dataclass
class ETFDataCollectionFailedEvent:
    """Event fired when data collection fails for an ETF"""
    ticker: str
    error: str
    retry_count: int
    timestamp: datetime
    
    def to_event(self) -> Event:
        """Convert to base Event"""
        return Event(
            metadata=EventMetadata(
                event_type=EventType.SYSTEM_SNAPSHOT_CREATED,
                aggregate_id=ticker,
                aggregate_type="ETF",
                timestamp=self.timestamp
            ),
            data={
                "event_subtype": ETFEventType.ETF_COLLECTION_FAILED,
                "ticker": self.ticker,
                "error": self.error,
                "retry_count": self.retry_count
            }
        )

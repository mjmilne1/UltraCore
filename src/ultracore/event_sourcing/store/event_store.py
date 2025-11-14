"""
Kafka Event Store.

Event store implementation using Kafka as the backend.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from ..base import Event, EventStore, EventType, ConcurrencyError
from ..kafka.config import KafkaConfig, default_config
from ..kafka.producer import EventProducer
from .snapshot_store import SnapshotStore


logger = logging.getLogger(__name__)


class KafkaEventStore(EventStore):
    """
    Kafka-backed event store.
    
    Stores events in Kafka topics with support for:
    - Optimistic concurrency control
    - Event versioning
    - Snapshots for performance
    - Event replay
    """
    
    def __init__(
        self,
        config: Optional[KafkaConfig] = None,
        snapshot_store: Optional[SnapshotStore] = None
    ):
        """
        Initialize Kafka event store.
        
        Args:
            config: Kafka configuration
            snapshot_store: Snapshot store for optimization
        """
        self.config = config or default_config
        self.producer = EventProducer(self.config)
        self.snapshot_store = snapshot_store or SnapshotStore()
        
        # In-memory cache for aggregate versions (for concurrency control)
        self._aggregate_versions: Dict[str, int] = {}
        
        # In-memory event cache (for development/testing)
        # In production, this would query Kafka directly
        self._event_cache: Dict[str, List[Event]] = defaultdict(list)
    
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
        # Check optimistic concurrency
        current_version = await self.get_aggregate_version(aggregate_id)
        
        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyError(
                f"Concurrency conflict for aggregate {aggregate_id}: "
                f"expected version {expected_version}, "
                f"current version {current_version}"
            )
        
        # Publish events to Kafka
        for event in events:
            success = await self.producer.publish_event(event)
            if not success:
                logger.error(f"Failed to save event {event.metadata.event_id}")
                raise Exception("Failed to save event")
            
            # Update cache
            self._event_cache[aggregate_id].append(event)
            self._aggregate_versions[aggregate_id] = event.metadata.version
        
        logger.info(
            f"Saved {len(events)} events for aggregate {aggregate_id}, "
            f"new version: {self._aggregate_versions[aggregate_id]}"
        )
        
        # Check if we should create a snapshot
        if current_version > 0 and current_version % 100 == 0:
            # Every 100 events, create a snapshot
            logger.info(
                f"Snapshot threshold reached for aggregate {aggregate_id}, "
                f"consider creating snapshot"
            )
    
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
        # Check if we have a snapshot
        snapshot = await self.snapshot_store.get_snapshot(aggregate_id)
        
        if snapshot and snapshot.version >= from_version:
            # Start from snapshot version
            from_version = snapshot.version + 1
            logger.debug(
                f"Using snapshot at version {snapshot.version} "
                f"for aggregate {aggregate_id}"
            )
        
        # Get events from cache (in production, query Kafka)
        events = self._event_cache.get(aggregate_id, [])
        
        # Filter by version range
        filtered_events = [
            e for e in events
            if e.metadata.version >= from_version and
            (to_version is None or e.metadata.version <= to_version)
        ]
        
        logger.debug(
            f"Retrieved {len(filtered_events)} events for aggregate {aggregate_id} "
            f"(versions {from_version}-{to_version or 'latest'})"
        )
        
        return filtered_events
    
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
        # Collect all events from cache
        all_events = []
        for events in self._event_cache.values():
            all_events.extend(events)
        
        # Filter by type
        filtered_events = [
            e for e in all_events
            if e.metadata.event_type == event_type
        ]
        
        # Filter by timestamp
        if from_timestamp:
            filtered_events = [
                e for e in filtered_events
                if e.metadata.timestamp >= from_timestamp
            ]
        
        if to_timestamp:
            filtered_events = [
                e for e in filtered_events
                if e.metadata.timestamp <= to_timestamp
            ]
        
        # Sort by timestamp
        filtered_events.sort(key=lambda e: e.metadata.timestamp)
        
        # Apply limit
        filtered_events = filtered_events[:limit]
        
        logger.debug(
            f"Retrieved {len(filtered_events)} events of type {event_type}"
        )
        
        return filtered_events
    
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """
        Get current version of aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            
        Returns:
            Current version
        """
        return self._aggregate_versions.get(aggregate_id, 0)
    
    async def replay_events(
        self,
        aggregate_id: str,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """
        Replay events for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            to_version: Version to replay to (None for all)
            
        Returns:
            List of replayed events
        """
        events = await self.get_events(aggregate_id, to_version=to_version)
        
        logger.info(
            f"Replaying {len(events)} events for aggregate {aggregate_id}"
        )
        
        return events
    
    async def get_all_aggregate_ids(self) -> List[str]:
        """
        Get all aggregate IDs in the store.
        
        Returns:
            List of aggregate IDs
        """
        return list(self._event_cache.keys())
    
    async def get_event_count(self, aggregate_id: str) -> int:
        """
        Get event count for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            
        Returns:
            Number of events
        """
        return len(self._event_cache.get(aggregate_id, []))
    
    async def get_total_event_count(self) -> int:
        """
        Get total event count across all aggregates.
        
        Returns:
            Total number of events
        """
        return sum(len(events) for events in self._event_cache.values())
    
    def close(self) -> None:
        """Close the event store."""
        self.producer.close()
        logger.info("Event store closed")

"""
Event Store
Kafka-backed event store for event sourcing
"""

from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from uuid import UUID
import json
import logging

try:
    from kafka import KafkaConsumer
    from kafka.structs import TopicPartition
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None

logger = logging.getLogger(__name__)


class Event:
    """Event model"""
    
    def __init__(
        self,
        event_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        event_data: Dict[str, Any],
        tenant_id: str,
        user_id: str,
        event_timestamp: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_version: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.event_data = event_data
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.event_timestamp = datetime.fromisoformat(event_timestamp)
        self.correlation_id = correlation_id or event_id
        self.causation_id = causation_id
        self.event_version = event_version
        self.metadata = metadata or {}
    
    @classmethod
    def from_kafka_message(cls, message) -> 'Event':
        """Create Event from Kafka message"""
        value = json.loads(message.value.decode('utf-8'))
        return cls(**value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_data": self.event_data,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "event_timestamp": self.event_timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "event_version": self.event_version,
            "metadata": self.metadata,
        }


class EventStore:
    """
    Kafka-backed Event Store
    
    Provides event sourcing capabilities:
    - Read events by aggregate ID
    - Read events by event type
    - Read all events from a topic
    - Stream events in real-time
    - Replay events from a specific point
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "ultracore-event-store"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
    
    def get_events_by_aggregate(
        self,
        topic: str,
        aggregate_id: str,
        from_offset: int = 0
    ) -> List[Event]:
        """
        Get all events for a specific aggregate
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID to filter by
            from_offset: Starting offset (for replay)
        
        Returns:
            List of events for the aggregate
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        events = []
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000,  # Stop after 5s of no messages
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            
            # Read all messages
            for message in consumer:
                # Filter by aggregate_id (key)
                if message.key == aggregate_id:
                    if message.offset >= from_offset:
                        event = Event.from_kafka_message(message)
                        events.append(event)
            
            consumer.close()
            
            logger.info(f"Retrieved {len(events)} events for aggregate {aggregate_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []
    
    def get_events_by_type(
        self,
        topic: str,
        event_type: str,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events by event type
        
        Args:
            topic: Kafka topic
            event_type: Event type to filter by
            limit: Maximum number of events to return
        
        Returns:
            List of events matching the type
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        events = []
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            
            for message in consumer:
                event = Event.from_kafka_message(message)
                if event.event_type == event_type:
                    events.append(event)
                    if len(events) >= limit:
                        break
            
            consumer.close()
            
            logger.info(f"Retrieved {len(events)} events of type {event_type}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []
    
    def get_all_events(
        self,
        topic: str,
        from_offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get all events from a topic
        
        Args:
            topic: Kafka topic
            from_offset: Starting offset
            limit: Maximum number of events (None = all)
        
        Returns:
            List of all events
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        events = []
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            
            for message in consumer:
                if message.offset >= from_offset:
                    event = Event.from_kafka_message(message)
                    events.append(event)
                    
                    if limit and len(events) >= limit:
                        break
            
            consumer.close()
            
            logger.info(f"Retrieved {len(events)} events from {topic}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []
    
    def stream_events(
        self,
        topic: str,
        from_offset: int = 0
    ) -> AsyncIterator[Event]:
        """
        Stream events in real-time
        
        Args:
            topic: Kafka topic
            from_offset: Starting offset
        
        Yields:
            Events as they arrive
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            
            # Seek to offset if specified
            if from_offset > 0:
                partitions = consumer.partitions_for_topic(topic)
                for partition in partitions:
                    tp = TopicPartition(topic, partition)
                    consumer.seek(tp, from_offset)
            
            for message in consumer:
                event = Event.from_kafka_message(message)
                yield event
                
        except Exception as e:
            logger.error(f"Failed to stream events: {e}")
    
    def get_latest_offset(self, topic: str, partition: int = 0) -> int:
        """
        Get the latest offset for a topic partition
        
        Args:
            topic: Kafka topic
            partition: Partition number
        
        Returns:
            Latest offset
        """
        if not KAFKA_AVAILABLE:
            return 0
        
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                enable_auto_commit=False
            )
            
            tp = TopicPartition(topic, partition)
            consumer.assign([tp])
            consumer.seek_to_end(tp)
            offset = consumer.position(tp)
            
            consumer.close()
            return offset
            
        except Exception as e:
            logger.error(f"Failed to get latest offset: {e}")
            return 0
    
    def rebuild_aggregate(
        self,
        topic: str,
        aggregate_id: str,
        aggregate_class: type
    ) -> Any:
        """
        Rebuild aggregate state from events
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID
            aggregate_class: Class with apply_event method
        
        Returns:
            Rebuilt aggregate instance
        """
        events = self.get_events_by_aggregate(topic, aggregate_id)
        
        # Create new aggregate instance
        aggregate = aggregate_class()
        
        # Apply each event in order
        for event in events:
            if hasattr(aggregate, 'apply_event'):
                aggregate.apply_event(event)
        
        return aggregate


# ============================================================================
# Singleton
# ============================================================================

_event_store: Optional[EventStore] = None


def get_event_store(bootstrap_servers: str = "localhost:9092") -> EventStore:
    """Get singleton event store"""
    global _event_store
    if _event_store is None:
        _event_store = EventStore(bootstrap_servers)
    return _event_store

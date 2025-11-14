"""
Event Store helper for testing.

Provides methods to query events from Kafka for test verification.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta, timezone

try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None

logger = logging.getLogger(__name__)


class EventStore:
    """
    Event store for querying events from Kafka.
    
    Used in tests to verify events were published correctly.
    For testing, can accept a MockKafkaProducer to query from in-memory events.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", kafka_producer=None):
        self.bootstrap_servers = bootstrap_servers
        self.consumer: Optional[KafkaConsumer] = None
        self.kafka_producer = kafka_producer  # For testing with MockKafkaProducer
    
    async def get_events_by_aggregate(
        self,
        topic: str,
        aggregate_id: str,
        since: Optional[datetime] = None,
        until_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific aggregate.
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID to filter by
            since: Only return events after this timestamp
            until_timestamp: Only return events before this timestamp
        
        Returns:
            List of events
        """
        # If we have a mock Kafka producer, query from it
        if self.kafka_producer and hasattr(self.kafka_producer, 'messages'):
            events = []
            for msg in self.kafka_producer.messages:
                event = msg['value']
                
                # Filter by aggregate_id
                if event.get('aggregate_id') == aggregate_id:
                    # Filter by timestamp if specified
                    event_timestamp_str = event.get('timestamp', event.get('event_timestamp', ''))
                    if event_timestamp_str:
                        # Parse timestamp and ensure timezone-aware
                        event_timestamp = datetime.fromisoformat(event_timestamp_str.replace('Z', '+00:00'))
                        if not event_timestamp.tzinfo:
                            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
                        
                        # Ensure timezone-aware comparison
                        if since:
                            since_aware = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
                            if event_timestamp < since_aware:
                                continue
                        if until_timestamp:
                            until_aware = until_timestamp if until_timestamp.tzinfo else until_timestamp.replace(tzinfo=timezone.utc)
                            if event_timestamp > until_aware:
                                continue
                    
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda e: e['timestamp'])
            return events
        
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        try:
            # Create consumer for this query
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"test_query_{aggregate_id}",
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000  # 5 second timeout
            )
            
            events = []
            
            # Read all messages
            for message in consumer:
                event = message.value
                
                # Filter by aggregate_id
                if event.get('aggregate_id') == aggregate_id:
                    # Filter by timestamp if specified
                    event_time = datetime.fromisoformat(
                        event.get('event_timestamp', event.get('timestamp', '')).replace('Z', '+00:00')
                    )
                    
                    if since and event_time < since:
                        continue
                    if until_timestamp and event_time > until_timestamp:
                        continue
                    
                    events.append(event)
            
            consumer.close()
            return events
            
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def get_events_by_type(
        self,
        topic: str,
        event_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get events by event type.
        
        Args:
            topic: Kafka topic
            event_type: Event type to filter by
            limit: Maximum number of events to return
        
        Returns:
            List of events
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"test_query_{event_type}",
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000
            )
            
            events = []
            
            for message in consumer:
                event = message.value
                
                if event.get('event_type') == event_type:
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
            
            consumer.close()
            return events
            
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def get_events_by_tenant(
        self,
        topic: str,
        tenant_id: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific tenant.
        
        Args:
            topic: Kafka topic
            tenant_id: Tenant ID to filter by
            since: Only return events after this timestamp
        
        Returns:
            List of events
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available")
            return []
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"test_query_tenant_{tenant_id}",
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000
            )
            
            events = []
            
            for message in consumer:
                event = message.value
                
                if event.get('tenant_id') == tenant_id:
                    if since:
                        event_time = datetime.fromisoformat(
                            event['event_timestamp'].replace('Z', '+00:00')
                        )
                        if event_time < since:
                            continue
                    
                    events.append(event)
            
            consumer.close()
            return events
            
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def replay_events(
        self,
        topic: str,
        aggregate_id: str,
        up_to_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Replay events for an aggregate up to a specific timestamp.
        
        Used for time travel queries and event replay testing.
        
        Args:
            topic: Kafka topic
            aggregate_id: Aggregate ID
            up_to_timestamp: Replay events up to this timestamp
        
        Returns:
            List of events in order
        """
        events = await self.get_events_by_aggregate(topic, aggregate_id)
        
        if up_to_timestamp:
            events = [
                e for e in events
                if datetime.fromisoformat(
                    e['event_timestamp'].replace('Z', '+00:00')
                ) <= up_to_timestamp
            ]
        
        # Sort by timestamp
        events.sort(key=lambda e: e['event_timestamp'])
        
        return events
    
    def close(self):
        """Close event store."""
        if self.consumer:
            self.consumer.close()

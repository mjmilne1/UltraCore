"""
Mock Kafka Producer and Consumer for testing.

These are synchronous mocks that replace the async Kafka clients.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4


class MockKafkaProducer:
    """Mock Kafka producer for testing (synchronous)."""
    
    def __init__(self, bootstrap_servers: str, client_id: str, acks: str = "all"):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.acks = acks  # Acknowledgment level: 'all', '1', or '0'
        self.messages: List[Dict[str, Any]] = []
        self.send_count = 0
        self.error_count = 0
        self.closed = False
        self.idempotence_enabled = True  # Kafka idempotence for exactly-once semantics
        self.max_in_flight_requests = 1  # For ordering guarantees
        self.producer = self  # Self-reference for compatibility with tests that access .producer
    
    def send(self, topic: str, key: str, value: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send message to Kafka topic (mock)."""
        if self.closed:
            raise RuntimeError("Producer is closed")
        
        message = {
            "topic": topic,
            "key": key,
            "value": value,
            "headers": headers or {},
            "timestamp": datetime.utcnow().isoformat(),
            "offset": self.send_count,
            "partition": hash(key) % 3  # Mock partitioning
        }
        
        self.messages.append(message)
        self.send_count += 1
        
        return {
            "topic": topic,
            "partition": message["partition"],
            "offset": message["offset"],
            "timestamp": message["timestamp"]
        }
    
    async def publish_event(self, topic: Optional[str] = None, event_type: Optional[str] = None, 
                           aggregate_type: Optional[str] = None, aggregate_id: Optional[str] = None,
                           event_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Publish event to Kafka (async version for compatibility)."""
        # Generate event ID
        event_id = str(uuid4())
        
        # Build event envelope
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id or str(uuid4()),
            "event_data": event_data or {},
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs  # Include any additional fields (causation_id, correlation_id, etc.)
        }
        
        topic = topic or "ultracore.events"
        key = aggregate_id or str(uuid4())
        headers = kwargs.get("headers", {})
        
        # Add event_type to headers
        if event_type:
            headers["event_type"] = event_type
        
        self.send(topic, key, event, headers=headers)
        return event_id  # Return event ID for causation tracking
    
    def flush(self):
        """Flush pending messages (mock)."""
        pass
    
    def close(self):
        """Close producer."""
        self.closed = True
    
    def get_messages_by_key(self, key: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific key."""
        return [msg for msg in self.messages if msg["key"] == key]
    
    def get_messages_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific topic."""
        return [msg for msg in self.messages if msg["topic"] == topic]
    
    def clear(self):
        """Clear all messages."""
        self.messages = []
        self.send_count = 0


class MockKafkaConsumer:
    """Mock Kafka consumer for testing (synchronous)."""
    
    def __init__(self, bootstrap_servers: str, group_id: str, topics: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.messages: List[Dict[str, Any]] = []
        self.position = 0
        self.closed = False
        self.committed_offsets: Dict[str, int] = {}
    
    def subscribe(self, topics: List[str]):
        """Subscribe to topics."""
        self.topics = topics
    
    def poll(self, timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        """Poll for messages (mock)."""
        if self.closed:
            raise RuntimeError("Consumer is closed")
        
        # Return messages from current position
        batch = self.messages[self.position:self.position + 10]
        self.position += len(batch)
        return batch
    
    def commit(self):
        """Commit current offset."""
        for topic in self.topics:
            self.committed_offsets[topic] = self.position
    
    def seek_to_beginning(self):
        """Seek to beginning of topics."""
        self.position = 0
    
    def seek_to_end(self):
        """Seek to end of topics."""
        self.position = len(self.messages)
    
    def close(self):
        """Close consumer."""
        self.closed = True
    
    def add_message(self, topic: str, key: str, value: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        """Add a message to the mock consumer (for testing)."""
        message = {
            "topic": topic,
            "key": key,
            "value": value,
            "headers": headers or {},
            "timestamp": datetime.utcnow().isoformat(),
            "offset": len(self.messages),
            "partition": hash(key) % 3
        }
        self.messages.append(message)
    
    def clear(self):
        """Clear all messages."""
        self.messages = []
        self.position = 0
        self.committed_offsets = {}

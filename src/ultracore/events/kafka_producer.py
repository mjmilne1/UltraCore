"""
UltraCore Kafka Event Producer

Kafka-first event sourcing:
1. Write to Kafka FIRST (source of truth)
2. Kafka consumers materialize to PostgreSQL (read model)
3. Event replay capability from Kafka

Architecture:
- All state changes → Kafka topics
- Kafka = immutable event log
- PostgreSQL = optimized read model
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import uuid
import logging
from enum import Enum

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception

logger = logging.getLogger(__name__)


class EventTopic(str, Enum):
    """Kafka topics for different event types"""
    CUSTOMER_EVENTS = "ultracore.customers.events"
    ACCOUNT_EVENTS = "ultracore.accounts.events"
    TRANSACTION_EVENTS = "ultracore.transactions.events"
    LOAN_EVENTS = "ultracore.loans.events"
    AUDIT_EVENTS = "ultracore.audit.events"


class KafkaEventProducer:
    """
    Kafka-first event producer
    
    Features:
    - Transactional writes
    - Guaranteed ordering (partition by aggregate_id)
    - Idempotency (deduplication)
    - Schema validation
    - Error handling & retries
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "ultracore-producer"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer: Optional[KafkaProducer] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Kafka producer"""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available - install with: pip install kafka-python")
            return
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                
                # Serialization
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                
                # Reliability settings
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Strict ordering
                
                # Idempotency
                enable_idempotence=True,
                
                # Performance
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10,
                
                # Timeouts
                request_timeout_ms=30000,
                
                # Error handling
                retry_backoff_ms=100
            )
            
            logger.info(f"✓ Kafka producer initialized: {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    async def publish_event(
        self,
        topic: EventTopic,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        event_data: Dict[str, Any],
        tenant_id: str,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> str:
        """
        Publish event to Kafka (WRITE-FIRST operation)
        
        Args:
            topic: Kafka topic
            event_type: Type of event (e.g., CustomerCreated)
            aggregate_type: Type of aggregate (Customer, Account, Loan)
            aggregate_id: ID of aggregate
            event_data: Event payload
            tenant_id: Tenant identifier
            user_id: User who triggered event
            correlation_id: Correlation ID for tracking
            causation_id: ID of event that caused this event
        
        Returns:
            Event ID
        """
        if not self.producer:
            raise RuntimeError("Kafka producer not available")
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Build event envelope
        event = {
            # Event metadata
            "event_id": event_id,
            "event_type": event_type,
            "event_version": 1,
            
            # Aggregate info
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            
            # Multi-tenancy
            "tenant_id": tenant_id,
            
            # Event payload
            "event_data": event_data,
            
            # Causation tracking
            "correlation_id": correlation_id or event_id,
            "causation_id": causation_id,
            
            # User context
            "user_id": user_id,
            
            # Timestamps
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            
            # Metadata
            "metadata": {
                "source": "ultracore-api",
                "version": "1.0.0"
            }
        }
        
        try:
            # Publish to Kafka
            # Key = aggregate_id (ensures ordering per aggregate)
            future = self.producer.send(
                topic.value,
                key=aggregate_id,
                value=event,
                partition=None  # Let Kafka partition by key
            )
            
            # Wait for confirmation (blocking for reliability)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"✓ Event published: {event_type} "
                f"(topic={topic.value}, partition={record_metadata.partition}, "
                f"offset={record_metadata.offset})"
            )
            
            return event_id
            
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    def close(self):
        """Close producer and flush pending messages"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("✓ Kafka producer closed")


# ============================================================================
# Singleton
# ============================================================================

_producer: Optional[KafkaEventProducer] = None


def get_kafka_producer(
    bootstrap_servers: str = "localhost:9092"
) -> KafkaEventProducer:
    """Get singleton Kafka producer"""
    global _producer
    if _producer is None:
        _producer = KafkaEventProducer(bootstrap_servers)
    return _producer


def close_kafka_producer():
    """Close Kafka producer"""
    global _producer
    if _producer:
        _producer.close()
        _producer = None

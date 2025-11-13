"""
Production-Grade Kafka Event Store
Simplified for aiokafka 0.12.0 compatibility
"""
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal
import json

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from ultracore.infrastructure.kafka_event_store.schemas import (
    TopicConvention, 
    get_schema_registry
)


class ProductionKafkaEventStore:
    """Production Kafka event store - simplified config"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        environment: str = 'dev'
    ):
        self.bootstrap_servers = bootstrap_servers
        self.environment = environment
        self.producer: Optional[AIOKafkaProducer] = None
        self.transactional_producer: Optional[AIOKafkaProducer] = None
        self.schema_registry = get_schema_registry()
        self.topic_convention = TopicConvention()
    
    async def initialize(self):
        """Initialize Kafka with production settings"""
        if not KAFKA_AVAILABLE:
            print("⚠️  Kafka not available")
            return False
        
        try:
            # Standard idempotent producer (simplified)
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=self._serialize_value,
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                
                # Core reliability settings
                enable_idempotence=True,
                acks='all',
                compression_type='snappy',
                
                # Timeouts
                request_timeout_ms=30000,
                
                # Client ID
                client_id='ultracore-producer'
            )
            
            await self.producer.start()
            print("✅ Idempotent Kafka producer started")
            
            # Transactional producer for exactly-once semantics
            self.transactional_producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=self._serialize_value,
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                
                # Exactly-once settings
                enable_idempotence=True,
                transactional_id='ultracore-ledger-tx',
                acks='all',
                compression_type='snappy',
                
                client_id='ultracore-tx-producer'
            )
            
            await self.transactional_producer.start()
            print("✅ Transactional Kafka producer started (exactly-once)")
            
            return True
            
        except Exception as e:
            print(f"❌ Kafka initialization failed: {e}")
            return False
    
    def _serialize_value(self, value):
        """Serialize value with Decimal support"""
        if isinstance(value, bytes):
            return value
        
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(value, default=decimal_default).encode('utf-8')
    
    async def append_event(
        self,
        entity: str,
        event_type: str,
        event_data: Dict,
        aggregate_id: str,
        user_id: str = 'system',
        idempotency_key: Optional[str] = None,
        exactly_once: bool = False
    ) -> str:
        """Append event with idempotency"""
        
        # Build topic name
        topic = self.topic_convention.build_topic_name(
            entity=entity,
            event_type=event_type,
            environment=self.environment
        )
        
        # Validate schema
        try:
            self.schema_registry.validate_event(event_type, event_data)
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            raise
        
        # Build event envelope
        event_id = idempotency_key or f"{entity}-{aggregate_id}-{datetime.now(timezone.utc).timestamp()}"
        
        event = {
            'event_id': event_id,
            'aggregate_id': aggregate_id,
            'aggregate_type': entity,
            'event_type': event_type,
            'event_data': event_data,
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': 1
        }
        
        # Choose producer
        producer = self.transactional_producer if exactly_once else self.producer
        
        if not producer:
            raise RuntimeError("Kafka producer not initialized")
        
        try:
            if exactly_once:
                # Exactly-once for critical operations
                async with producer.transaction():
                    metadata = await producer.send_and_wait(
                        topic,
                        key=aggregate_id,
                        value=event,
                        headers=[
                            ('event_type', event_type.encode('utf-8')),
                            ('idempotency_key', event_id.encode('utf-8'))
                        ]
                    )
                    print(f"📝 Kafka TX: {topic} - {event_type} - offset {metadata.offset}")
            else:
                # Idempotent (at-least-once)
                metadata = await producer.send_and_wait(
                    topic,
                    key=aggregate_id,
                    value=event,
                    headers=[
                        ('event_type', event_type.encode('utf-8')),
                        ('idempotency_key', event_id.encode('utf-8'))
                    ]
                )
                print(f"📝 Kafka: {topic} - {event_type} - offset {metadata.offset}")
            
            return event_id
            
        except KafkaError as e:
            print(f"❌ Kafka error: {e}")
            await self._write_to_dlq(topic, event, str(e))
            raise
    
    async def _write_to_dlq(self, original_topic: str, event: Dict, error: str):
        """Write failed event to Dead Letter Queue"""
        if not self.producer:
            return
        
        dlq_topic = self.topic_convention.get_dlq_topic(original_topic)
        
        dlq_event = {
            **event,
            'dlq_metadata': {
                'original_topic': original_topic,
                'error': error,
                'dlq_timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            await self.producer.send(
                dlq_topic,
                value=dlq_event,
                headers=[('error', error.encode('utf-8'))]
            )
            print(f"💀 Written to DLQ: {dlq_topic}")
        except Exception as e:
            print(f"❌ DLQ write failed: {e}")
    
    async def stop(self):
        """Gracefully shutdown"""
        if self.producer:
            await self.producer.stop()
        if self.transactional_producer:
            await self.transactional_producer.stop()
        
        print("✅ Kafka producers stopped")


# Global instance
_production_kafka_store: Optional[ProductionKafkaEventStore] = None


def get_production_kafka_store() -> ProductionKafkaEventStore:
    global _production_kafka_store
    
    if _production_kafka_store is None:
        _production_kafka_store = ProductionKafkaEventStore()
    
    return _production_kafka_store

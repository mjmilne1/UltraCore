"""
Event Bus - Real-time Event Streaming
Supports: Kafka, Pulsar, Redpanda, In-Memory
"""
from typing import Dict, List, Callable, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import json
import asyncio
from collections import defaultdict


class EventBusType(str, Enum):
    IN_MEMORY = 'IN_MEMORY'
    KAFKA = 'KAFKA'
    PULSAR = 'PULSAR'
    REDPANDA = 'REDPANDA'


class EventTopic(str, Enum):
    # Domain Events
    LOAN_EVENTS = 'ultracore.loans'
    CLIENT_EVENTS = 'ultracore.clients'
    ACCOUNT_EVENTS = 'ultracore.accounts'
    PAYMENT_EVENTS = 'ultracore.payments'
    CARD_EVENTS = 'ultracore.cards'
    INVESTMENT_EVENTS = 'ultracore.investments'
    INSURANCE_EVENTS = 'ultracore.insurance'
    MERCHANT_EVENTS = 'ultracore.merchants'
    RISK_EVENTS = 'ultracore.risk'
    
    # System Events
    COMPLIANCE_EVENTS = 'ultracore.compliance'
    FRAUD_EVENTS = 'ultracore.fraud'
    AUDIT_EVENTS = 'ultracore.audit'
    
    # Financial Events
    ORDERS = 'ultracore.orders'
    FILLS = 'ultracore.fills'
    FUNDING = 'ultracore.funding'
    SETTLEMENT = 'ultracore.settlement'


class Event:
    def __init__(
        self,
        topic: EventTopic,
        event_type: str,
        event_data: Dict,
        aggregate_id: str,
        user_id: str = 'system'
    ):
        self.topic = topic
        self.event_type = event_type
        self.event_data = event_data
        self.aggregate_id = aggregate_id
        self.user_id = user_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'topic': self.topic.value,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'aggregate_id': self.aggregate_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBus(ABC):
    """Abstract Event Bus interface"""
    
    @abstractmethod
    async def publish(self, event: Event):
        """Publish event to topic"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: EventTopic, handler: Callable):
        """Subscribe to topic with handler"""
        pass
    
    @abstractmethod
    async def start(self):
        """Start event bus"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop event bus"""
        pass


class InMemoryEventBus(EventBus):
    """
    In-Memory Event Bus
    Fast, simple, for development and testing
    """
    
    def __init__(self):
        self.subscribers: Dict[EventTopic, List[Callable]] = defaultdict(list)
        self.event_log: List[Event] = []
        self.running = False
    
    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        # Store in log
        self.event_log.append(event)
        
        # Notify subscribers
        handlers = self.subscribers.get(event.topic, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
    
    async def subscribe(self, topic: EventTopic, handler: Callable):
        """Subscribe to topic"""
        self.subscribers[topic].append(handler)
        print(f"✓ Subscribed to {topic.value}")
    
    async def start(self):
        """Start event bus"""
        self.running = True
        print("✓ In-Memory Event Bus started")
    
    async def stop(self):
        """Stop event bus"""
        self.running = False
        print("✓ In-Memory Event Bus stopped")
    
    def get_events(self, topic: Optional[EventTopic] = None) -> List[Event]:
        """Get events from log"""
        if topic:
            return [e for e in self.event_log if e.topic == topic]
        return self.event_log


class KafkaEventBus(EventBus):
    """
    Kafka Event Bus
    Production-ready, high-throughput event streaming
    """
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = {}
        self.running = False
    
    async def publish(self, event: Event):
        """Publish event to Kafka"""
        try:
            # Try to import kafka
            from aiokafka import AIOKafkaProducer
            
            if not self.producer:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.producer.start()
            
            await self.producer.send(
                event.topic.value,
                value=event.to_dict()
            )
            
        except ImportError:
            print("⚠️  aiokafka not installed. Install with: pip install aiokafka")
            print("   Falling back to logging...")
            print(f"   Would publish to Kafka: {event.topic.value} - {event.event_type}")
    
    async def subscribe(self, topic: EventTopic, handler: Callable):
        """Subscribe to Kafka topic"""
        try:
            from aiokafka import AIOKafkaConsumer
            
            consumer = AIOKafkaConsumer(
                topic.value,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=f'ultracore-{topic.value}'
            )
            
            await consumer.start()
            self.consumers[topic] = (consumer, handler)
            
            # Start consuming in background
            asyncio.create_task(self._consume(consumer, handler))
            
            print(f"✓ Subscribed to Kafka topic: {topic.value}")
            
        except ImportError:
            print("⚠️  aiokafka not installed")
    
    async def _consume(self, consumer, handler):
        """Consume messages"""
        try:
            async for msg in consumer:
                event_data = msg.value
                event = Event(
                    topic=EventTopic(event_data['topic']),
                    event_type=event_data['event_type'],
                    event_data=event_data['event_data'],
                    aggregate_id=event_data['aggregate_id'],
                    user_id=event_data['user_id']
                )
                await handler(event)
        except Exception as e:
            print(f"Error consuming: {e}")
    
    async def start(self):
        """Start Kafka connection"""
        self.running = True
        print("✓ Kafka Event Bus started")
    
    async def stop(self):
        """Stop Kafka connection"""
        if self.producer:
            await self.producer.stop()
        
        for consumer, _ in self.consumers.values():
            await consumer.stop()
        
        self.running = False
        print("✓ Kafka Event Bus stopped")


class RedpandaEventBus(KafkaEventBus):
    """
    Redpanda Event Bus
    Kafka-compatible, but simpler and faster
    """
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        super().__init__(bootstrap_servers)
        print("Using Redpanda (Kafka-compatible)")


# Global event bus instance
_event_bus: Optional[EventBus] = None


def initialize_event_bus(
    bus_type: EventBusType = EventBusType.IN_MEMORY,
    config: Optional[Dict] = None
) -> EventBus:
    """Initialize event bus"""
    global _event_bus
    
    if bus_type == EventBusType.IN_MEMORY:
        _event_bus = InMemoryEventBus()
    elif bus_type == EventBusType.KAFKA:
        bootstrap_servers = config.get('bootstrap_servers', 'localhost:9092') if config else 'localhost:9092'
        _event_bus = KafkaEventBus(bootstrap_servers)
    elif bus_type == EventBusType.REDPANDA:
        bootstrap_servers = config.get('bootstrap_servers', 'localhost:9092') if config else 'localhost:9092'
        _event_bus = RedpandaEventBus(bootstrap_servers)
    else:
        _event_bus = InMemoryEventBus()
    
    return _event_bus


def get_event_bus() -> EventBus:
    """Get event bus instance"""
    global _event_bus
    
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    
    return _event_bus

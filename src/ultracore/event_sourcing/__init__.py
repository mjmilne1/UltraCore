"""
Event Sourcing Framework.

Production-grade event sourcing implementation with Kafka integration.
"""

from .base import (
    Event,
    EventMetadata,
    EventType,
    AggregateRoot,
    EventHandler,
    EventStore,
)
from .store.event_store import KafkaEventStore
from .kafka.config import KafkaConfig
from .kafka.producer import EventProducer
from .kafka.consumer import EventConsumer

__all__ = [
    "Event",
    "EventMetadata",
    "EventType",
    "AggregateRoot",
    "EventHandler",
    "EventStore",
    "KafkaEventStore",
    "KafkaConfig",
    "EventProducer",
    "EventConsumer",
]

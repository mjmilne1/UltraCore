"""Kafka integration for event sourcing."""

from .config import KafkaConfig, default_config
from .producer import EventProducer
from .consumer import EventConsumer

__all__ = ["KafkaConfig", "default_config", "EventProducer", "EventConsumer"]

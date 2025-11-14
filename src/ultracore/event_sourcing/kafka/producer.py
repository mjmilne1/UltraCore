"""
Kafka Event Producer.

Produces events to Kafka topics.
"""

import logging
from typing import Optional
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic

from ..base import Event
from .config import KafkaConfig, default_config


logger = logging.getLogger(__name__)


class EventProducer:
    """
    Kafka event producer.
    
    Publishes events to Kafka topics with guaranteed delivery.
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """
        Initialize event producer.
        
        Args:
            config: Kafka configuration
        """
        self.config = config or default_config
        self.producer = Producer(self.config.get_producer_config())
        self._ensure_topics_exist()
    
    def _ensure_topics_exist(self) -> None:
        """Ensure required topics exist."""
        admin_client = AdminClient({
            "bootstrap.servers": self.config.bootstrap_servers
        })
        
        topics = [
            NewTopic(
                self.config.event_store_topic,
                num_partitions=self.config.default_partitions,
                replication_factor=self.config.default_replication_factor
            ),
            NewTopic(
                self.config.dead_letter_topic,
                num_partitions=self.config.default_partitions,
                replication_factor=self.config.default_replication_factor
            ),
            NewTopic(
                self.config.snapshot_topic,
                num_partitions=self.config.default_partitions,
                replication_factor=self.config.default_replication_factor
            ),
        ]
        
        # Create topics (will skip if they already exist)
        fs = admin_client.create_topics(topics)
        
        for topic, f in fs.items():
            try:
                f.result()  # Wait for operation to complete
                logger.info(f"Topic {topic} created")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.error(f"Failed to create topic {topic}: {e}")
    
    async def publish_event(
        self,
        event: Event,
        topic: Optional[str] = None
    ) -> bool:
        """
        Publish an event to Kafka.
        
        Args:
            event: Event to publish
            topic: Topic to publish to (defaults to event store topic)
            
        Returns:
            True if successful
        """
        topic = topic or self.config.event_store_topic
        
        try:
            # Serialize event
            key = event.metadata.aggregate_id.encode('utf-8')
            value = event.to_json().encode('utf-8')
            
            # Produce to Kafka
            self.producer.produce(
                topic=topic,
                key=key,
                value=value,
                on_delivery=self._delivery_callback
            )
            
            # Wait for delivery
            self.producer.flush()
            
            logger.debug(
                f"Published event {event.metadata.event_id} "
                f"to topic {topic}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[partition {msg.partition()}] at offset {msg.offset()}"
            )
    
    async def publish_events(self, events: list[Event]) -> bool:
        """
        Publish multiple events.
        
        Args:
            events: Events to publish
            
        Returns:
            True if all successful
        """
        success = True
        for event in events:
            if not await self.publish_event(event):
                success = False
        return success
    
    def close(self) -> None:
        """Close the producer."""
        self.producer.flush()
        logger.info("Event producer closed")

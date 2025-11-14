"""
Kafka Event Consumer.

Consumes events from Kafka topics.
"""

import logging
from typing import Callable, List, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition

from ..base import Event, EventHandler
from .config import KafkaConfig, default_config


logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Kafka event consumer.
    
    Consumes events from Kafka topics and dispatches to handlers.
    """
    
    def __init__(
        self,
        handlers: List[EventHandler],
        config: Optional[KafkaConfig] = None,
        group_id: Optional[str] = None
    ):
        """
        Initialize event consumer.
        
        Args:
            handlers: List of event handlers
            config: Kafka configuration
            group_id: Consumer group ID (overrides config)
        """
        self.config = config or default_config
        self.handlers = handlers
        self.consumer = Consumer(self.config.get_consumer_config(group_id))
        self.running = False
    
    async def start(self, topics: Optional[List[str]] = None) -> None:
        """
        Start consuming events.
        
        Args:
            topics: Topics to subscribe to (defaults to event store topic)
        """
        topics = topics or [self.config.event_store_topic]
        
        self.consumer.subscribe(topics)
        self.running = True
        
        logger.info(f"Event consumer started, subscribed to {topics}")
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition, not an error
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                # Process message
                await self._process_message(msg)
                
                # Commit offset
                self.consumer.commit(asynchronous=False)
                
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.consumer.close()
            logger.info("Event consumer stopped")
    
    async def _process_message(self, msg) -> None:
        """
        Process a Kafka message.
        
        Args:
            msg: Kafka message
        """
        try:
            # Deserialize event
            event_json = msg.value().decode('utf-8')
            event = Event.from_json(event_json)
            
            logger.debug(
                f"Processing event {event.metadata.event_id} "
                f"of type {event.metadata.event_type}"
            )
            
            # Dispatch to handlers
            handled = False
            for handler in self.handlers:
                if handler.can_handle(event.metadata.event_type):
                    await handler.handle(event)
                    handled = True
            
            if not handled:
                logger.warning(
                    f"No handler found for event type "
                    f"{event.metadata.event_type}"
                )
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Send to dead letter queue
            await self._send_to_dlq(msg)
    
    async def _send_to_dlq(self, msg) -> None:
        """
        Send failed message to dead letter queue.
        
        Args:
            msg: Failed message
        """
        try:
            from .producer import EventProducer
            
            producer = EventProducer(self.config)
            
            # Create DLQ event with original message
            event_json = msg.value().decode('utf-8')
            event = Event.from_json(event_json)
            
            # Add error metadata
            event.data["_dlq_reason"] = "Processing failed"
            event.data["_original_topic"] = msg.topic()
            event.data["_original_partition"] = msg.partition()
            event.data["_original_offset"] = msg.offset()
            
            await producer.publish_event(event, self.config.dead_letter_topic)
            
            logger.info(
                f"Sent event {event.metadata.event_id} to DLQ"
            )
            
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def stop(self) -> None:
        """Stop consuming events."""
        self.running = False
    
    def seek_to_beginning(self, topic: str) -> None:
        """
        Seek to beginning of topic.
        
        Args:
            topic: Topic to seek
        """
        partitions = self.consumer.assignment()
        for partition in partitions:
            if partition.topic == topic:
                self.consumer.seek(TopicPartition(topic, partition.partition, 0))
        
        logger.info(f"Seeked to beginning of topic {topic}")
    
    def seek_to_end(self, topic: str) -> None:
        """
        Seek to end of topic.
        
        Args:
            topic: Topic to seek
        """
        partitions = self.consumer.assignment()
        for partition in partitions:
            if partition.topic == topic:
                # Get high watermark
                low, high = self.consumer.get_watermark_offsets(partition)
                self.consumer.seek(TopicPartition(topic, partition.partition, high))
        
        logger.info(f"Seeked to end of topic {topic}")
    
    def get_lag(self) -> dict:
        """
        Get consumer lag for all assigned partitions.
        
        Returns:
            Dictionary of partition lags
        """
        lag = {}
        partitions = self.consumer.assignment()
        
        for partition in partitions:
            # Get current position
            position = self.consumer.position([partition])[0].offset
            
            # Get high watermark
            low, high = self.consumer.get_watermark_offsets(partition)
            
            # Calculate lag
            partition_lag = high - position
            
            lag[f"{partition.topic}-{partition.partition}"] = {
                "position": position,
                "high_watermark": high,
                "lag": partition_lag
            }
        
        return lag

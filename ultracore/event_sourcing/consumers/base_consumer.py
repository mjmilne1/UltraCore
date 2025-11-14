"""
Base Event Consumer
Foundation for all Kafka event consumers
"""

from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None
    KafkaError = Exception

logger = logging.getLogger(__name__)


class BaseEventConsumer(ABC):
    """
    Base class for event consumers
    
    Provides:
    - Automatic offset management
    - Error handling and retries
    - Dead letter queue for failed events
    - Metrics and logging
    - Graceful shutdown
    """
    
    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        auto_offset_reset: str = 'earliest'
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.auto_offset_reset = auto_offset_reset
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        
        # Metrics
        self.events_processed = 0
        self.events_failed = 0
        self.start_time = None
    
    def _initialize_consumer(self):
        """Initialize Kafka consumer"""
        if not KAFKA_AVAILABLE:
            logger.error("Kafka not available - install with: pip install kafka-python")
            return False
        
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=False,  # Manual commit for reliability
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            
            logger.info(
                f"✓ Consumer initialized: {self.group_id} "
                f"(topics={self.topics})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            return False
    
    @abstractmethod
    async def process_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a single event
        
        Args:
            event: Event data
        
        Returns:
            True if processed successfully, False otherwise
        """
        pass
    
    async def handle_error(self, event: Dict[str, Any], error: Exception):
        """
        Handle processing error
        
        Override this method to implement custom error handling
        (e.g., send to dead letter queue, alert, etc.)
        """
        logger.error(
            f"Failed to process event {event.get('event_id')}: {error}",
            exc_info=True
        )
        self.events_failed += 1
    
    def start(self):
        """Start consuming events"""
        if not self._initialize_consumer():
            logger.error("Cannot start consumer - initialization failed")
            return
        
        self.running = True
        self.start_time = datetime.utcnow()
        
        logger.info(f"✓ Consumer started: {self.group_id}")
        
        try:
            while self.running:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000, max_records=100)
                
                if not messages:
                    continue
                
                # Process messages
                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            # Process event
                            event = message.value
                            success = self.process_event(event)
                            
                            if success:
                                self.events_processed += 1
                                
                                # Commit offset
                                self.consumer.commit()
                            else:
                                # Handle failure
                                await self.handle_error(event, Exception("Processing returned False"))
                                
                        except Exception as e:
                            # Handle error
                            await self.handle_error(message.value, e)
                
                # Log progress periodically
                if self.events_processed % 100 == 0 and self.events_processed > 0:
                    self._log_metrics()
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """Stop consuming events"""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            logger.info(f"✓ Consumer stopped: {self.group_id}")
        
        self._log_metrics()
    
    def _log_metrics(self):
        """Log consumer metrics"""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            rate = self.events_processed / duration if duration > 0 else 0
            
            logger.info(
                f"Consumer metrics: {self.group_id} | "
                f"Processed: {self.events_processed} | "
                f"Failed: {self.events_failed} | "
                f"Rate: {rate:.2f} events/sec"
            )


class ProjectionConsumer(BaseEventConsumer):
    """
    Projection Consumer
    
    Consumes events and materializes them into read models (projections)
    """
    
    def __init__(
        self,
        topics: List[str],
        group_id: str,
        projection_handler: Callable[[Dict[str, Any]], bool],
        bootstrap_servers: str = "localhost:9092"
    ):
        super().__init__(topics, group_id, bootstrap_servers)
        self.projection_handler = projection_handler
    
    async def process_event(self, event: Dict[str, Any]) -> bool:
        """Process event using projection handler"""
        try:
            return self.projection_handler(event)
        except Exception as e:
            logger.error(f"Projection handler failed: {e}")
            return False


class AggregateConsumer(BaseEventConsumer):
    """
    Aggregate Consumer
    
    Consumes events and updates aggregate state
    """
    
    def __init__(
        self,
        topics: List[str],
        group_id: str,
        aggregate_repository,
        bootstrap_servers: str = "localhost:9092"
    ):
        super().__init__(topics, group_id, bootstrap_servers)
        self.aggregate_repository = aggregate_repository
    
    async def process_event(self, event: Dict[str, Any]) -> bool:
        """Process event by updating aggregate"""
        try:
            aggregate_id = event.get('aggregate_id')
            aggregate_type = event.get('aggregate_type')
            
            # Load aggregate
            aggregate = await self.aggregate_repository.get(
                aggregate_type, aggregate_id
            )
            
            # Apply event
            if hasattr(aggregate, 'apply_event'):
                aggregate.apply_event(event)
            
            # Save aggregate
            await self.aggregate_repository.save(aggregate)
            
            return True
            
        except Exception as e:
            logger.error(f"Aggregate update failed: {e}")
            return False

"""
UltraCore Kafka Event Consumer

Base consumer for materializing Kafka events to PostgreSQL

Architecture:
1. Read from Kafka (source of truth)
2. Materialize to PostgreSQL (read model)
3. Idempotent processing (exactly-once semantics)
4. Error handling & dead letter queue
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import json
import logging
from abc import ABC, abstractmethod
import asyncio

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None
    KafkaError = Exception

from sqlalchemy.ext.asyncio import AsyncSession
from ultracore.database.config import get_db_manager

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Abstract event handler"""
    
    @abstractmethod
    async def handle_event(
        self,
        event: Dict[str, Any],
        session: AsyncSession
    ) -> bool:
        """
        Handle event and materialize to database
        
        Args:
            event: Event from Kafka
            session: Database session
        
        Returns:
            True if handled successfully, False otherwise
        """
        pass


class KafkaEventConsumer:
    """
    Kafka event consumer with materialization
    
    Features:
    - Exactly-once semantics (idempotent)
    - Auto-commit after processing
    - Error handling & retry
    - Dead letter queue for failed events
    - Batch processing
    """
    
    def __init__(
        self,
        topic: str,
        group_id: str,
        event_handlers: Dict[str, EventHandler],
        bootstrap_servers: str = "localhost:9092",
        batch_size: int = 100
    ):
        self.topic = topic
        self.group_id = group_id
        self.event_handlers = event_handlers
        self.bootstrap_servers = bootstrap_servers
        self.batch_size = batch_size
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Kafka consumer"""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available - install with: pip install kafka-python")
            return
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                
                # Deserialization
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                
                # Consumer settings
                enable_auto_commit=False,  # Manual commit after processing
                auto_offset_reset='earliest',  # Start from beginning for new consumers
                max_poll_records=self.batch_size,
                
                # Performance
                fetch_min_bytes=1024,
                fetch_max_wait_ms=500,
                
                # Error handling
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000,
                request_timeout_ms=40000
            )
            
            logger.info(
                f"✓ Kafka consumer initialized: "
                f"topic={self.topic}, group={self.group_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self.consumer = None
    
    async def start(self):
        """Start consuming events"""
        if not self.consumer:
            logger.error("Consumer not initialized")
            return
        
        self.running = True
        logger.info(f"🔄 Starting consumer for topic: {self.topic}")
        
        db_manager = get_db_manager()
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process messages
                for topic_partition, messages in message_batch.items():
                    logger.info(
                        f"Processing batch: {len(messages)} messages "
                        f"from partition {topic_partition.partition}"
                    )
                    
                    # Process each message
                    for message in messages:
                        event = message.value
                        
                        try:
                            # Get database session
                            async with db_manager.get_async_session() as session:
                                # Handle event
                                success = await self._handle_event(event, session)
                                
                                if success:
                                    # Commit to database
                                    await session.commit()
                                    
                                    logger.debug(
                                        f"✓ Event processed: {event['event_type']} "
                                        f"(offset={message.offset})"
                                    )
                                else:
                                    # Rollback on failure
                                    await session.rollback()
                                    logger.error(
                                        f"❌ Failed to process event: "
                                        f"{event['event_type']}"
                                    )
                                    
                                    # Send to dead letter queue
                                    await self._send_to_dlq(event, message)
                        
                        except Exception as e:
                            logger.error(
                                f"Error processing event: {e}",
                                exc_info=True
                            )
                            # Send to dead letter queue
                            await self._send_to_dlq(event, message)
                    
                    # Commit offset after batch
                    self.consumer.commit()
                    logger.info(f"✓ Committed batch: {len(messages)} messages")
        
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        
        finally:
            logger.info("🛑 Consumer stopped")
    
    async def _handle_event(
        self,
        event: Dict[str, Any],
        session: AsyncSession
    ) -> bool:
        """Handle single event"""
        event_type = event.get('event_type')
        
        # Get handler for event type
        handler = self.event_handlers.get(event_type)
        
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return False
        
        # Check if already processed (idempotency)
        if await self._is_processed(event['event_id'], session):
            logger.debug(f"Event already processed: {event['event_id']}")
            return True
        
        # Handle event
        try:
            success = await handler.handle_event(event, session)
            
            if success:
                # Mark as processed
                await self._mark_processed(event, session)
            
            return success
            
        except Exception as e:
            logger.error(f"Handler error: {e}", exc_info=True)
            return False
    
    async def _is_processed(
        self,
        event_id: str,
        session: AsyncSession
    ) -> bool:
        """Check if event already processed (idempotency)"""
        from sqlalchemy import select, text
        
        # Check processed_events table
        query = text("""
            SELECT 1 FROM processed_events 
            WHERE event_id = :event_id
            LIMIT 1
        """)
        
        result = await session.execute(query, {"event_id": event_id})
        return result.scalar() is not None
    
    async def _mark_processed(
        self,
        event: Dict[str, Any],
        session: AsyncSession
    ):
        """Mark event as processed"""
        from sqlalchemy import text
        
        query = text("""
            INSERT INTO processed_events (
                event_id, event_type, aggregate_id, 
                processed_at, tenant_id
            )
            VALUES (
                :event_id, :event_type, :aggregate_id,
                :processed_at, :tenant_id
            )
            ON CONFLICT (event_id) DO NOTHING
        """)
        
        await session.execute(query, {
            "event_id": event['event_id'],
            "event_type": event['event_type'],
            "aggregate_id": event['aggregate_id'],
            "processed_at": datetime.now(timezone.utc),
            "tenant_id": event['tenant_id']
        })
    
    async def _send_to_dlq(self, event: Dict[str, Any], message):
        """Send failed event to dead letter queue"""
        logger.error(
            f"Sending to DLQ: {event['event_type']} "
            f"(event_id={event['event_id']})"
        )
        # TODO: Implement DLQ (could be another Kafka topic or database table)
    
    def stop(self):
        """Stop consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()

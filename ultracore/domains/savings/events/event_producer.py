"""
Savings Event Producer
Publishes savings events to Kafka topics
"""

import json
from typing import Any, Dict
from uuid import UUID

from ultracore.domains.savings.events.account_events import BaseEvent


class SavingsEventProducer:
    """
    Kafka Event Producer for Savings Domain
    
    Publishes all savings events to appropriate Kafka topics for:
    - Event sourcing
    - Data mesh integration
    - Real-time analytics
    - Audit trail
    - Downstream system integration
    """
    
    # Kafka topics
    TOPIC_ACCOUNT_LIFECYCLE = "ultracore.savings.accounts.lifecycle"
    TOPIC_TRANSACTIONS = "ultracore.savings.accounts.transactions"
    TOPIC_INTEREST = "ultracore.savings.interest"
    TOPIC_FEES = "ultracore.savings.fees"
    TOPIC_COMPLIANCE = "ultracore.savings.compliance"
    
    def __init__(self, kafka_producer=None):
        """
        Initialize event producer
        
        Args:
            kafka_producer: Kafka producer instance (optional, for testing can be None)
        """
        self.kafka_producer = kafka_producer
    
    async def publish_event(self, event: BaseEvent, topic: str) -> None:
        """
        Publish event to Kafka topic
        
        Args:
            event: Event to publish
            topic: Kafka topic name
        """
        if not self.kafka_producer:
            # For testing or when Kafka is not available
            print(f"[EVENT] {topic}: {event.event_type}")
            return
        
        # Convert event to dict
        event_dict = event.model_dump()
        
        # Convert UUIDs to strings for JSON serialization
        event_dict = self._serialize_uuids(event_dict)
        
        # Publish to Kafka
        await self.kafka_producer.send(
            topic=topic,
            key=str(event.account_id) if hasattr(event, 'account_id') else None,
            value=json.dumps(event_dict),
            headers={
                'event_type': event.event_type,
                'event_id': str(event.event_id),
                'tenant_id': str(event.tenant_id),
                'correlation_id': str(event.correlation_id) if event.correlation_id else None,
            }
        )
    
    async def publish_account_event(self, event: BaseEvent) -> None:
        """Publish account lifecycle event"""
        await self.publish_event(event, self.TOPIC_ACCOUNT_LIFECYCLE)
    
    async def publish_transaction_event(self, event: BaseEvent) -> None:
        """Publish transaction event"""
        await self.publish_event(event, self.TOPIC_TRANSACTIONS)
    
    async def publish_interest_event(self, event: BaseEvent) -> None:
        """Publish interest event"""
        await self.publish_event(event, self.TOPIC_INTEREST)
    
    async def publish_fee_event(self, event: BaseEvent) -> None:
        """Publish fee event"""
        await self.publish_event(event, self.TOPIC_FEES)
    
    async def publish_compliance_event(self, event: BaseEvent) -> None:
        """Publish compliance event"""
        await self.publish_event(event, self.TOPIC_COMPLIANCE)
    
    @staticmethod
    def _serialize_uuids(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert UUIDs to strings for JSON serialization"""
        result = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = SavingsEventProducer._serialize_uuids(value)
            elif isinstance(value, list):
                result[key] = [
                    SavingsEventProducer._serialize_uuids(item) if isinstance(item, dict)
                    else str(item) if isinstance(item, UUID)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


# Singleton instance
_event_producer: SavingsEventProducer = None


def get_event_producer() -> SavingsEventProducer:
    """Get singleton event producer instance"""
    global _event_producer
    if _event_producer is None:
        _event_producer = SavingsEventProducer()
    return _event_producer


def set_event_producer(producer: SavingsEventProducer) -> None:
    """Set event producer instance (for dependency injection)"""
    global _event_producer
    _event_producer = producer

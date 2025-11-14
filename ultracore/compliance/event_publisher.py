"""
Compliance Event Publisher (Kafka-First)
"""

import logging
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json

from ultracore.compliance.events import ComplianceEvent, ComplianceTopic

logger = logging.getLogger(__name__)


class ComplianceEventPublisher:
    """Publishes compliance events to Kafka"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[KafkaProducer] = None
    
    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
                compression_type='gzip'
            )
        return self._producer
    
    def publish(self, topic: ComplianceTopic, event: ComplianceEvent) -> bool:
        try:
            producer = self._get_producer()
            partition_key = event.aggregate_id
            event_dict = event.dict()
            
            future = producer.send(
                topic=topic.value,
                key=partition_key,
                value=event_dict
            )
            
            record_metadata = future.get(timeout=10)
            logger.info(f"Published {event.event_type} to {topic.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    def close(self):
        if self._producer:
            self._producer.flush()
            self._producer.close()


_publisher: Optional[ComplianceEventPublisher] = None

def get_event_publisher() -> ComplianceEventPublisher:
    global _publisher
    if _publisher is None:
        _publisher = ComplianceEventPublisher()
    return _publisher

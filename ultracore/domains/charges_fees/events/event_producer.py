"""
Fee Event Producer
Publishes fee events to Kafka
"""

from typing import Optional
import logging

# Import base Kafka producer
try:
    from src.ultracore.events.kafka_producer import KafkaEventProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka producer not available")

from ultracore.domains.charges_fees.events.fee_events import (
    FeeAppliedEvent,
    FeeWaivedEvent,
    FeeRefundedEvent,
    FeeRevenueRecognizedEvent,
    ChargingRuleCreatedEvent,
    ChargingRuleActivatedEvent,
    ChargingRuleDeactivatedEvent,
    FeeRevenueCalculatedEvent,
    FeeTopics,
)

logger = logging.getLogger(__name__)


class FeeEventProducer:
    """
    Fee Event Producer
    
    Publishes fee events to Kafka for real-time processing
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        if KAFKA_AVAILABLE:
            self.producer = KafkaEventProducer(bootstrap_servers=bootstrap_servers)
        else:
            self.producer = None
            logger.warning("Kafka not available - events will not be published")
    
    async def publish_fee_applied(
        self,
        event: FeeAppliedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish FeeApplied event"""
        
        if not self.producer:
            logger.warning("Event not published - Kafka unavailable")
            return None
        
        aggregate_id = str(event.account_id or event.loan_id or event.fee_id)
        
        return await self.producer.publish_event(
            topic=FeeTopics.APPLIED,
            event_type="FeeApplied",
            aggregate_type="Fee",
            aggregate_id=aggregate_id,
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_fee_waived(
        self,
        event: FeeWaivedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish FeeWaived event"""
        
        if not self.producer:
            return None
        
        aggregate_id = str(event.account_id or event.loan_id or event.fee_id)
        
        return await self.producer.publish_event(
            topic=FeeTopics.WAIVED,
            event_type="FeeWaived",
            aggregate_type="Fee",
            aggregate_id=aggregate_id,
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_fee_refunded(
        self,
        event: FeeRefundedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish FeeRefunded event"""
        
        if not self.producer:
            return None
        
        aggregate_id = str(event.account_id or event.loan_id or event.fee_id)
        
        return await self.producer.publish_event(
            topic=FeeTopics.REFUNDED,
            event_type="FeeRefunded",
            aggregate_type="Fee",
            aggregate_id=aggregate_id,
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_revenue_recognized(
        self,
        event: FeeRevenueRecognizedEvent,
        user_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish FeeRevenueRecognized event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=FeeTopics.REVENUE,
            event_type="FeeRevenueRecognized",
            aggregate_type="Fee",
            aggregate_id=str(event.fee_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
        )
    
    async def publish_charging_rule_created(
        self,
        event: ChargingRuleCreatedEvent,
        user_id: str
    ) -> Optional[str]:
        """Publish ChargingRuleCreated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=FeeTopics.RULES,
            event_type="ChargingRuleCreated",
            aggregate_type="ChargingRule",
            aggregate_id=str(event.rule_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
        )
    
    async def publish_charging_rule_activated(
        self,
        event: ChargingRuleActivatedEvent,
        user_id: str
    ) -> Optional[str]:
        """Publish ChargingRuleActivated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=FeeTopics.RULES,
            event_type="ChargingRuleActivated",
            aggregate_type="ChargingRule",
            aggregate_id=str(event.rule_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
        )
    
    async def publish_fee_revenue_calculated(
        self,
        event: FeeRevenueCalculatedEvent,
        user_id: str
    ) -> Optional[str]:
        """Publish FeeRevenueCalculated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=FeeTopics.REVENUE,
            event_type="FeeRevenueCalculated",
            aggregate_type="FeeRevenue",
            aggregate_id=str(event.revenue_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
        )
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()

"""
Delinquency Event Producer
Publishes delinquency events to Kafka
"""

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

# Import base Kafka producer (from existing implementation)
try:
    from src.ultracore.events.kafka_producer import KafkaEventProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka producer not available")

from ultracore.domains.delinquency.events.delinquency_events import (
    LoanBecameDelinquentEvent,
    DelinquencyBucketChangedEvent,
    DelinquencyCuredEvent,
    LoanDefaultedEvent,
    LateFeeAppliedEvent,
    PaymentReminderSentEvent,
    CollectionNoticeIssuedEvent,
    ProvisioningUpdatedEvent,
    LoanWrittenOffEvent,
    PortfolioAtRiskCalculatedEvent,
    DelinquencyStatusUpdatedEvent,
    DelinquencyTopics,
)

logger = logging.getLogger(__name__)


class DelinquencyEventProducer:
    """
    Delinquency Event Producer
    
    Publishes delinquency events to Kafka for real-time processing
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        if KAFKA_AVAILABLE:
            self.producer = KafkaEventProducer(bootstrap_servers=bootstrap_servers)
        else:
            self.producer = None
            logger.warning("Kafka not available - events will not be published")
    
    async def publish_loan_became_delinquent(
        self,
        event: LoanBecameDelinquentEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish LoanBecameDelinquent event"""
        
        if not self.producer:
            logger.warning("Event not published - Kafka unavailable")
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.STATUS,
            event_type="LoanBecameDelinquent",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_bucket_changed(
        self,
        event: DelinquencyBucketChangedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish DelinquencyBucketChanged event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.BUCKETS,
            event_type="DelinquencyBucketChanged",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_delinquency_cured(
        self,
        event: DelinquencyCuredEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish DelinquencyCured event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.STATUS,
            event_type="DelinquencyCured",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_loan_defaulted(
        self,
        event: LoanDefaultedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish LoanDefaulted event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.STATUS,
            event_type="LoanDefaulted",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_late_fee_applied(
        self,
        event: LateFeeAppliedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish LateFeeApplied event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.ACTIONS,
            event_type="LateFeeApplied",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_reminder_sent(
        self,
        event: PaymentReminderSentEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish PaymentReminderSent event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.ACTIONS,
            event_type="PaymentReminderSent",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_collection_notice_issued(
        self,
        event: CollectionNoticeIssuedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish CollectionNoticeIssued event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.ACTIONS,
            event_type="CollectionNoticeIssued",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_provisioning_updated(
        self,
        event: ProvisioningUpdatedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish ProvisioningUpdated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.PROVISIONING,
            event_type="ProvisioningUpdated",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_loan_written_off(
        self,
        event: LoanWrittenOffEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish LoanWrittenOff event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.ACTIONS,
            event_type="LoanWrittenOff",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    async def publish_portfolio_at_risk_calculated(
        self,
        event: PortfolioAtRiskCalculatedEvent,
        user_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish PortfolioAtRiskCalculated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.PORTFOLIO,
            event_type="PortfolioAtRiskCalculated",
            aggregate_type="Portfolio",
            aggregate_id=str(event.tenant_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
        )
    
    async def publish_status_updated(
        self,
        event: DelinquencyStatusUpdatedEvent,
        user_id: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Optional[str]:
        """Publish DelinquencyStatusUpdated event"""
        
        if not self.producer:
            return None
        
        return await self.producer.publish_event(
            topic=DelinquencyTopics.STATUS,
            event_type="DelinquencyStatusUpdated",
            aggregate_type="Loan",
            aggregate_id=str(event.loan_id),
            event_data=event.model_dump(),
            tenant_id=str(event.tenant_id),
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()

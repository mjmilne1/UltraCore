"""
Security Event Producer

Kafka producer for intelligent security events.
"""

from typing import Optional
import json
from datetime import datetime

# Event sourcing integration - simplified for now
# from ultracore.event_sourcing.store.event_store import EventStore
from .events import (
    SecurityEvent,
    FraudDetectionEvent,
    AnomalyDetectionEvent,
    AccessControlEvent,
    RateLimitEvent,
    ThreatDetectionEvent,
    SecurityIncidentEvent,
    ModelUpdateEvent
)


class SecurityEventProducer:
    """
    Producer for security events with Kafka-first architecture.
    
    All security events are published to Kafka before any other processing.
    """
    
    def __init__(
        self,
        kafka_producer: Optional[object] = None,
        event_store: Optional[object] = None
    ):
        self.kafka_producer = kafka_producer
        self.event_store = event_store
        self.topic = "security-events"
        self.events_published = []  # Store for testing
    
    async def publish_fraud_detection(
        self,
        tenant_id: str,
        transaction_id: str,
        fraud_score: float,
        risk_factors: list[str],
        decision: str,
        amount: float,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> FraudDetectionEvent:
        """Publish fraud detection event"""
        event = FraudDetectionEvent(
            tenant_id=tenant_id,
            transaction_id=transaction_id,
            fraud_score=fraud_score,
            risk_factors=risk_factors,
            decision=decision,
            amount=amount,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_anomaly_detection(
        self,
        tenant_id: str,
        session_id: str,
        anomaly_score: float,
        anomaly_indicators: list[str],
        action_taken: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> AnomalyDetectionEvent:
        """Publish anomaly detection event"""
        event = AnomalyDetectionEvent(
            tenant_id=tenant_id,
            session_id=session_id,
            anomaly_score=anomaly_score,
            anomaly_indicators=anomaly_indicators,
            action_taken=action_taken,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_access_control(
        self,
        tenant_id: str,
        resource_id: str,
        resource_type: str,
        action_requested: str,
        decision: str,
        risk_score: float,
        reasoning: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> AccessControlEvent:
        """Publish access control event"""
        event = AccessControlEvent(
            tenant_id=tenant_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action_requested=action_requested,
            decision=decision,
            risk_score=risk_score,
            reasoning=reasoning,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_rate_limit(
        self,
        tenant_id: str,
        endpoint: str,
        request_rate: float,
        action: str,
        rate_multiplier: float,
        reasoning: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> RateLimitEvent:
        """Publish rate limit event"""
        event = RateLimitEvent(
            tenant_id=tenant_id,
            endpoint=endpoint,
            request_rate=request_rate,
            action=action,
            rate_multiplier=rate_multiplier,
            reasoning=reasoning,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_threat_detection(
        self,
        tenant_id: str,
        threat_type: str,
        severity: str,
        source_ip: str,
        target: str,
        action_taken: str,
        details: dict,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> ThreatDetectionEvent:
        """Publish threat detection event"""
        event = ThreatDetectionEvent(
            tenant_id=tenant_id,
            threat_type=threat_type,
            severity=severity,
            source_ip=source_ip,
            target=target,
            action_taken=action_taken,
            details=details,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_security_incident(
        self,
        tenant_id: str,
        incident_id: str,
        incident_type: str,
        severity: str,
        status: str,
        description: str,
        affected_resources: list[str],
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> SecurityIncidentEvent:
        """Publish security incident event"""
        event = SecurityIncidentEvent(
            tenant_id=tenant_id,
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            status=status,
            description=description,
            affected_resources=affected_resources,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def publish_model_update(
        self,
        tenant_id: str,
        model_name: str,
        model_version: str,
        update_type: str,
        metrics: dict,
        metadata: Optional[dict] = None
    ) -> ModelUpdateEvent:
        """Publish model update event"""
        event = ModelUpdateEvent(
            tenant_id=tenant_id,
            model_name=model_name,
            model_version=model_version,
            update_type=update_type,
            metrics=metrics,
            metadata=metadata or {}
        )
        
        await self._publish_event(event)
        return event
    
    async def _publish_event(self, event: SecurityEvent):
        """
        Publish event to Kafka (Kafka-first architecture).
        
        Event is published to Kafka before any other processing.
        """
        # Store event for testing/verification
        self.events_published.append(event)
        
        # Publish to Kafka if available
        if self.kafka_producer:
            await self.kafka_producer.produce(
                topic=self.topic,
                key=event.tenant_id,
                value=event.model_dump_json(),
                headers={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat()
                }
            )
        
        # Store in event store if available
        if self.event_store:
            await self.event_store.append(
                stream_id=f"security-{event.tenant_id}",
                event_type=event.event_type,
                event_data=event.model_dump(),
                metadata={
                    "event_id": event.event_id,
                    "user_id": event.user_id
                }
            )
    
    async def close(self):
        """Close producer connections"""
        if self.kafka_producer:
            await self.kafka_producer.close()

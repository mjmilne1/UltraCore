"""
MFA Event Producer
Publishes MFA events to Kafka for event sourcing and analytics
"""

import json
import logging
from typing import Optional
from uuid import uuid4
from datetime import datetime

from ultracore.security.mfa.events import (
    MFAEvent,
    MFAEnabledEvent,
    MFADisabledEvent,
    MFAVerificationSuccessEvent,
    MFAVerificationFailedEvent,
    BackupCodeUsedEvent,
    BackupCodesRegeneratedEvent,
    MFABruteForceDetectedEvent,
    MFAAnomalyDetectedEvent,
    MFATopics
)

logger = logging.getLogger(__name__)


class MFAEventProducer:
    """
    Publishes MFA events to Kafka
    
    Integrates with UltraCore's event sourcing infrastructure for:
    - Complete audit trail
    - Real-time analytics
    - AI-powered anomaly detection
    - Compliance reporting
    """
    
    def __init__(self, kafka_producer=None):
        """
        Initialize MFA event producer
        
        Args:
            kafka_producer: Kafka producer instance (optional for testing)
        """
        self.kafka_producer = kafka_producer
    
    async def publish_event(
        self,
        event: MFAEvent,
        topic: str
    ) -> bool:
        """
        Publish event to Kafka
        
        Args:
            event: MFA event
            topic: Kafka topic
        
        Returns:
            True if successful
        """
        try:
            # Convert event to JSON
            event_data = event.to_dict()
            event_json = json.dumps(event_data, default=str)
            
            # Publish to Kafka (if producer is configured)
            if self.kafka_producer:
                await self.kafka_producer.send(
                    topic=topic,
                    key=str(event.user_id),
                    value=event_json
                )
                logger.info(f"Published {event.__class__.__name__} to {topic}")
            else:
                # Log event if Kafka is not configured (development mode)
                logger.info(f"[DEV MODE] {event.__class__.__name__}: {event_json}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish MFA event: {e}")
            return False
    
    # ========================================================================
    # Lifecycle Events
    # ========================================================================
    
    async def publish_mfa_enabled(
        self,
        user_id,
        tenant_id,
        backup_codes_generated: int = 10,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA enabled event"""
        event = MFAEnabledEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            backup_codes_generated=backup_codes_generated,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_LIFECYCLE)
    
    async def publish_mfa_disabled(
        self,
        user_id,
        tenant_id,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA disabled event"""
        event = MFADisabledEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            reason=reason,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_LIFECYCLE)
    
    # ========================================================================
    # Verification Events
    # ========================================================================
    
    async def publish_verification_success(
        self,
        user_id,
        tenant_id,
        verification_method: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA verification success event"""
        event = MFAVerificationSuccessEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            verification_method=verification_method,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_VERIFICATION)
    
    async def publish_verification_failed(
        self,
        user_id,
        tenant_id,
        verification_method: str,
        failure_reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA verification failed event"""
        event = MFAVerificationFailedEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            verification_method=verification_method,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_VERIFICATION)
    
    # ========================================================================
    # Backup Code Events
    # ========================================================================
    
    async def publish_backup_code_used(
        self,
        user_id,
        tenant_id,
        codes_remaining: int,
        correlation_id: Optional[str] = None
    ):
        """Publish backup code used event"""
        event = BackupCodeUsedEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            codes_remaining=codes_remaining,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_BACKUP_CODES)
    
    async def publish_backup_codes_regenerated(
        self,
        user_id,
        tenant_id,
        new_code_count: int = 10,
        correlation_id: Optional[str] = None
    ):
        """Publish backup codes regenerated event"""
        event = BackupCodesRegeneratedEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            new_code_count=new_code_count,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_BACKUP_CODES)
    
    # ========================================================================
    # Security Events
    # ========================================================================
    
    async def publish_brute_force_detected(
        self,
        user_id,
        tenant_id,
        failed_attempts: int,
        time_window_seconds: int,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA brute force detected event"""
        event = MFABruteForceDetectedEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            failed_attempts=failed_attempts,
            time_window_seconds=time_window_seconds,
            ip_address=ip_address,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_SECURITY)
    
    async def publish_anomaly_detected(
        self,
        user_id,
        tenant_id,
        anomaly_type: str,
        anomaly_score: float,
        details: dict,
        correlation_id: Optional[str] = None
    ):
        """Publish MFA anomaly detected event"""
        event = MFAAnomalyDetectedEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            anomaly_type=anomaly_type,
            anomaly_score=anomaly_score,
            details=details,
            correlation_id=correlation_id
        )
        await self.publish_event(event, MFATopics.MFA_SECURITY)


# ============================================================================
# Factory Function
# ============================================================================

def create_mfa_event_producer(kafka_producer=None) -> MFAEventProducer:
    """
    Factory function to create MFA event producer
    
    Args:
        kafka_producer: Kafka producer instance (optional)
    
    Returns:
        Configured MFA event producer
    """
    return MFAEventProducer(kafka_producer=kafka_producer)

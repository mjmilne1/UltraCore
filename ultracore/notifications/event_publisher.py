"""
Notification Event Publisher
Kafka-first event publishing for notification system
"""

from typing import Any, Optional
import logging
from datetime import datetime

from ultracore.event_sourcing.store.event_store import get_event_store

logger = logging.getLogger(__name__)


class NotificationEventPublisher:
    """
    Kafka-first event publisher for notifications
    
    Topics:
    - notifications.alerts - Price, portfolio, and news alerts
    - notifications.delivery - Notification delivery events
    - notifications.preferences - User preferences
    - notifications.summaries - Portfolio summaries and predictions
    - notifications.compliance - Consent and audit logs
    """
    
    def __init__(self):
        self.event_store = get_event_store()
        self.topics = {
            "alerts": "notifications.alerts",
            "delivery": "notifications.delivery",
            "preferences": "notifications.preferences",
            "summaries": "notifications.summaries",
            "compliance": "notifications.compliance"
        }
        logger.info("NotificationEventPublisher initialized")
    
    def publish_alert_event(
        self,
        event: Any,
        aggregate_id: str,
        tenant_id: str
    ) -> bool:
        """
        Publish alert event to Kafka
        
        Args:
            event: Alert event (PriceAlertCreated, PortfolioAlertTriggered, etc.)
            aggregate_id: Alert ID
            tenant_id: Tenant ID
        
        Returns:
            True if published successfully
        """
        try:
            self.event_store.append_event(
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.__dict__,
                tenant_id=tenant_id,
                topic=self.topics["alerts"]
            )
            logger.info(f"Published {event.event_type} to {self.topics['alerts']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish alert event: {str(e)}")
            return False
    
    def publish_delivery_event(
        self,
        event: Any,
        aggregate_id: str,
        tenant_id: str
    ) -> bool:
        """
        Publish delivery event to Kafka
        
        Args:
            event: Delivery event (NotificationSent, NotificationDelivered, etc.)
            aggregate_id: Notification ID
            tenant_id: Tenant ID
        
        Returns:
            True if published successfully
        """
        try:
            self.event_store.append_event(
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.__dict__,
                tenant_id=tenant_id,
                topic=self.topics["delivery"]
            )
            logger.info(f"Published {event.event_type} to {self.topics['delivery']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish delivery event: {str(e)}")
            return False
    
    def publish_preference_event(
        self,
        event: Any,
        aggregate_id: str,
        tenant_id: str
    ) -> bool:
        """
        Publish preference event to Kafka
        
        Args:
            event: Preference event (NotificationPreferenceSet, etc.)
            aggregate_id: Preference ID
            tenant_id: Tenant ID
        
        Returns:
            True if published successfully
        """
        try:
            self.event_store.append_event(
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.__dict__,
                tenant_id=tenant_id,
                topic=self.topics["preferences"]
            )
            logger.info(f"Published {event.event_type} to {self.topics['preferences']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish preference event: {str(e)}")
            return False
    
    def publish_summary_event(
        self,
        event: Any,
        aggregate_id: str,
        tenant_id: str
    ) -> bool:
        """
        Publish summary event to Kafka
        
        Args:
            event: Summary event (PortfolioSummaryGenerated, MLPredictionGenerated)
            aggregate_id: Summary/Prediction ID
            tenant_id: Tenant ID
        
        Returns:
            True if published successfully
        """
        try:
            self.event_store.append_event(
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.__dict__,
                tenant_id=tenant_id,
                topic=self.topics["summaries"]
            )
            logger.info(f"Published {event.event_type} to {self.topics['summaries']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish summary event: {str(e)}")
            return False
    
    def publish_compliance_event(
        self,
        event: Any,
        aggregate_id: str,
        tenant_id: str
    ) -> bool:
        """
        Publish compliance event to Kafka
        
        Args:
            event: Compliance event (ConsentRecorded, NotificationAuditLogged)
            aggregate_id: Consent/Audit ID
            tenant_id: Tenant ID
        
        Returns:
            True if published successfully
        """
        try:
            self.event_store.append_event(
                aggregate_id=aggregate_id,
                event_type=event.event_type,
                event_data=event.__dict__,
                tenant_id=tenant_id,
                topic=self.topics["compliance"]
            )
            logger.info(f"Published {event.event_type} to {self.topics['compliance']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish compliance event: {str(e)}")
            return False


# Singleton instance
_publisher: Optional[NotificationEventPublisher] = None


def get_notification_event_publisher() -> NotificationEventPublisher:
    """Get notification event publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = NotificationEventPublisher()
    return _publisher

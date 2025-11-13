"""
Notification Aggregates
Event-sourced aggregates for notifications, preferences, and delivery tracking
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.notifications.events import (
    NotificationCreated,
    NotificationScheduled,
    NotificationSent,
    NotificationDelivered,
    NotificationRead,
    NotificationFailed,
    NotificationPreferenceSet,
    NotificationPreferenceUpdated,
    PortfolioSummaryGenerated,
    MLPredictionGenerated,
    ConsentRecorded,
    ConsentWithdrawn,
    NotificationAuditLogged,
    NotificationType,
    AlertPriority,
    DeliveryChannel,
    DeliveryStatus
)
from ultracore.notifications.event_publisher import get_notification_event_publisher


class NotificationAggregate:
    """
    Notification Aggregate
    
    Manages notification lifecycle and multi-channel delivery
    """
    
    def __init__(self, notification_id: str, tenant_id: str):
        self.notification_id = notification_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.notification_type: Optional[NotificationType] = None
        self.priority: Optional[AlertPriority] = None
        self.title: Optional[str] = None
        self.message: Optional[str] = None
        self.data: Dict[str, Any] = {}
        self.channels: List[DeliveryChannel] = []
        self.delivery_status: Dict[DeliveryChannel, DeliveryStatus] = {}
        self.scheduled_for: Optional[datetime] = None
        self.created_at: Optional[datetime] = None
        self.sent_at: Optional[datetime] = None
        self.delivered_at: Optional[datetime] = None
        self.read_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def create_notification(
        self,
        client_id: str,
        notification_type: NotificationType,
        priority: AlertPriority,
        title: str,
        message: str,
        data: Dict[str, Any],
        channels: List[DeliveryChannel]
    ) -> None:
        """
        Create notification
        
        Args:
            client_id: Client ID
            notification_type: Type of notification
            priority: Alert priority
            title: Notification title
            message: Notification message
            data: Additional data
            channels: Delivery channels
        """
        event = NotificationCreated(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data,
            channels=channels,
            created_at=datetime.utcnow()
        )
        
        self._apply_notification_created(event)
        self.uncommitted_events.append(event)
    
    def schedule_notification(
        self,
        scheduled_for: datetime,
        channels: List[DeliveryChannel]
    ) -> None:
        """Schedule notification for future delivery"""
        event = NotificationScheduled(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            scheduled_for=scheduled_for,
            channels=channels,
            scheduled_at=datetime.utcnow()
        )
        
        self._apply_notification_scheduled(event)
        self.uncommitted_events.append(event)
    
    def mark_sent(
        self,
        channel: DeliveryChannel,
        recipient: str
    ) -> None:
        """Mark notification as sent"""
        event = NotificationSent(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            channel=channel,
            recipient=recipient,
            sent_at=datetime.utcnow()
        )
        
        self._apply_notification_sent(event)
        self.uncommitted_events.append(event)
    
    def mark_delivered(self, channel: DeliveryChannel) -> None:
        """Mark notification as delivered"""
        event = NotificationDelivered(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            channel=channel,
            delivered_at=datetime.utcnow()
        )
        
        self._apply_notification_delivered(event)
        self.uncommitted_events.append(event)
    
    def mark_read(self) -> None:
        """Mark notification as read"""
        event = NotificationRead(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            read_at=datetime.utcnow()
        )
        
        self._apply_notification_read(event)
        self.uncommitted_events.append(event)
    
    def mark_failed(
        self,
        channel: DeliveryChannel,
        error_code: str,
        error_message: str
    ) -> None:
        """Mark notification delivery as failed"""
        event = NotificationFailed(
            event_id=str(uuid4()),
            notification_id=self.notification_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            channel=channel,
            error_code=error_code,
            error_message=error_message,
            failed_at=datetime.utcnow()
        )
        
        self._apply_notification_failed(event)
        self.uncommitted_events.append(event)
    
    def _apply_notification_created(self, event: NotificationCreated) -> None:
        """Apply NotificationCreated event"""
        self.client_id = event.client_id
        self.notification_type = event.notification_type
        self.priority = event.priority
        self.title = event.title
        self.message = event.message
        self.data = event.data
        self.channels = event.channels
        self.created_at = event.created_at
        
        # Initialize delivery status
        for channel in event.channels:
            self.delivery_status[channel] = DeliveryStatus.PENDING
    
    def _apply_notification_scheduled(self, event: NotificationScheduled) -> None:
        """Apply NotificationScheduled event"""
        self.scheduled_for = event.scheduled_for
    
    def _apply_notification_sent(self, event: NotificationSent) -> None:
        """Apply NotificationSent event"""
        self.sent_at = event.sent_at
        self.delivery_status[event.channel] = DeliveryStatus.SENT
    
    def _apply_notification_delivered(self, event: NotificationDelivered) -> None:
        """Apply NotificationDelivered event"""
        self.delivered_at = event.delivered_at
        self.delivery_status[event.channel] = DeliveryStatus.DELIVERED
    
    def _apply_notification_read(self, event: NotificationRead) -> None:
        """Apply NotificationRead event"""
        self.read_at = event.read_at
    
    def _apply_notification_failed(self, event: NotificationFailed) -> None:
        """Apply NotificationFailed event"""
        self.delivery_status[event.channel] = DeliveryStatus.FAILED
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_delivery_event(
                event=event,
                aggregate_id=self.notification_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True


class NotificationPreferenceAggregate:
    """
    Notification Preference Aggregate
    
    Manages user notification preferences and consent (Australian Privacy Act compliance)
    """
    
    def __init__(self, preference_id: str, tenant_id: str):
        self.preference_id = preference_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.notification_type: Optional[NotificationType] = None
        self.enabled: bool = True
        self.channels: List[DeliveryChannel] = []
        self.quiet_hours_start: Optional[str] = None
        self.quiet_hours_end: Optional[str] = None
        self.frequency: str = "immediate"  # immediate, daily_digest, weekly_digest
        self.consent_given: bool = False
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def set_preference(
        self,
        user_id: str,
        client_id: str,
        notification_type: NotificationType,
        enabled: bool,
        channels: List[DeliveryChannel],
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        frequency: str = "immediate"
    ) -> None:
        """
        Set notification preference
        
        Args:
            user_id: User ID
            client_id: Client ID
            notification_type: Type of notification
            enabled: Whether notifications are enabled
            channels: Delivery channels
            quiet_hours_start: Quiet hours start (HH:MM)
            quiet_hours_end: Quiet hours end (HH:MM)
            frequency: Notification frequency
        """
        event = NotificationPreferenceSet(
            event_id=str(uuid4()),
            preference_id=self.preference_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            user_id=user_id,
            notification_type=notification_type,
            enabled=enabled,
            channels=channels,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            frequency=frequency,
            set_at=datetime.utcnow()
        )
        
        self._apply_preference_set(event)
        self.uncommitted_events.append(event)
    
    def update_preference(
        self,
        user_id: str,
        changes: Dict[str, Any]
    ) -> None:
        """
        Update notification preference
        
        Args:
            user_id: User ID
            changes: Dictionary of changes
        """
        event = NotificationPreferenceUpdated(
            event_id=str(uuid4()),
            preference_id=self.preference_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            user_id=user_id,
            changes=changes,
            updated_at=datetime.utcnow()
        )
        
        self._apply_preference_updated(event)
        self.uncommitted_events.append(event)
    
    def _apply_preference_set(self, event: NotificationPreferenceSet) -> None:
        """Apply NotificationPreferenceSet event"""
        self.client_id = event.client_id
        self.notification_type = event.notification_type
        self.enabled = event.enabled
        self.channels = event.channels
        self.quiet_hours_start = event.quiet_hours_start
        self.quiet_hours_end = event.quiet_hours_end
        self.frequency = event.frequency
        self.created_at = event.set_at
    
    def _apply_preference_updated(self, event: NotificationPreferenceUpdated) -> None:
        """Apply NotificationPreferenceUpdated event"""
        for key, value in event.changes.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = event.updated_at
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_preference_event(
                event=event,
                aggregate_id=self.preference_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True


class ConsentAggregate:
    """
    Consent Aggregate
    
    Manages notification consent (Australian Privacy Act 1988 compliance)
    """
    
    def __init__(self, consent_id: str, tenant_id: str):
        self.consent_id = consent_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.notification_types: List[NotificationType] = []
        self.channels: List[DeliveryChannel] = []
        self.consent_given: bool = False
        self.consent_text: Optional[str] = None
        self.recorded_at: Optional[datetime] = None
        self.withdrawn_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def record_consent(
        self,
        user_id: str,
        client_id: str,
        notification_types: List[NotificationType],
        channels: List[DeliveryChannel],
        consent_given: bool,
        consent_text: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Record notification consent (Privacy Act compliance)
        
        Args:
            user_id: User ID
            client_id: Client ID
            notification_types: Types of notifications consented to
            channels: Channels consented to
            consent_given: Whether consent was given
            consent_text: Consent text shown to user
            ip_address: IP address of user
        """
        event = ConsentRecorded(
            event_id=str(uuid4()),
            consent_id=self.consent_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            user_id=user_id,
            notification_types=notification_types,
            channels=channels,
            consent_given=consent_given,
            consent_text=consent_text,
            ip_address=ip_address,
            recorded_at=datetime.utcnow()
        )
        
        self._apply_consent_recorded(event)
        self.uncommitted_events.append(event)
    
    def withdraw_consent(
        self,
        user_id: str,
        notification_types: List[NotificationType]
    ) -> None:
        """
        Withdraw notification consent
        
        Args:
            user_id: User ID
            notification_types: Types to withdraw consent for
        """
        event = ConsentWithdrawn(
            event_id=str(uuid4()),
            consent_id=self.consent_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            user_id=user_id,
            notification_types=notification_types,
            withdrawn_at=datetime.utcnow()
        )
        
        self._apply_consent_withdrawn(event)
        self.uncommitted_events.append(event)
    
    def _apply_consent_recorded(self, event: ConsentRecorded) -> None:
        """Apply ConsentRecorded event"""
        self.client_id = event.client_id
        self.notification_types = event.notification_types
        self.channels = event.channels
        self.consent_given = event.consent_given
        self.consent_text = event.consent_text
        self.recorded_at = event.recorded_at
    
    def _apply_consent_withdrawn(self, event: ConsentWithdrawn) -> None:
        """Apply ConsentWithdrawn event"""
        self.consent_given = False
        self.withdrawn_at = event.withdrawn_at
        # Remove withdrawn types
        self.notification_types = [
            nt for nt in self.notification_types
            if nt not in event.notification_types
        ]
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_compliance_event(
                event=event,
                aggregate_id=self.consent_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True

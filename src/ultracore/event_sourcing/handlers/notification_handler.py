"""Notification Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class NotificationEventHandler(EventHandler):
    """Notification event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.NOTIFICATION_SENT,
        EventType.NOTIFICATION_DELIVERED,
        EventType.NOTIFICATION_FAILED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle notification event."""
        logger.info(f"Handling {event.metadata.event_type} for notification {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

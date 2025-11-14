"""Audit Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class AuditEventHandler(EventHandler):
    """Audit event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.AUDIT_LOG_CREATED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle audit event."""
        logger.info(f"Handling {event.metadata.event_type} for audit {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

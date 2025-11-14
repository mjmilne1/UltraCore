"""System Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class SystemEventHandler(EventHandler):
    """System event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.SYSTEM_SNAPSHOT_CREATED,
        EventType.SYSTEM_MIGRATION_COMPLETED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle system event."""
        logger.info(f"Handling {event.metadata.event_type} for system {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

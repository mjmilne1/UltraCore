"""Analytics Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class AnalyticsEventHandler(EventHandler):
    """Analytics event handler."""
    HANDLED_EVENTS: Set[EventType] = set()  # Processes all events for analytics
    
    async def handle(self, event: Event) -> None:
        """Handle analytics event."""
        logger.info(f"Handling {event.metadata.event_type} for analytics {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

"""Collateral Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class CollateralEventHandler(EventHandler):
    """Collateral event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.COLLATERAL_PLEDGED,
        EventType.COLLATERAL_RELEASED,
        EventType.COLLATERAL_VALUED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle collateral event."""
        logger.info(f"Handling {event.metadata.event_type} for collateral {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

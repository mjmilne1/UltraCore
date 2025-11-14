"""Risk Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class RiskEventHandler(EventHandler):
    """Risk event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.RISK_ASSESSMENT_COMPLETED,
        EventType.RISK_LIMIT_BREACHED,
        EventType.FRAUD_DETECTED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle risk event."""
        logger.info(f"Handling {event.metadata.event_type} for risk {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

"""Investment Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class InvestmentEventHandler(EventHandler):
    HANDLED_EVENTS: Set[EventType] = {
        EventType.INVESTMENT_POD_CREATED, EventType.INVESTMENT_CONTRIBUTED,
        EventType.INVESTMENT_WITHDRAWN, EventType.INVESTMENT_REBALANCED,
    }
    async def handle(self, event: Event) -> None:
        logger.info(f"Handling {event.metadata.event_type} for investment {event.metadata.aggregate_id}")
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

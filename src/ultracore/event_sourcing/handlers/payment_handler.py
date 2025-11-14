"""Payment Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class PaymentEventHandler(EventHandler):
    HANDLED_EVENTS: Set[EventType] = {
        EventType.PAYMENT_INITIATED, EventType.PAYMENT_AUTHORIZED,
        EventType.PAYMENT_COMPLETED, EventType.PAYMENT_FAILED, EventType.PAYMENT_REFUNDED,
    }
    async def handle(self, event: Event) -> None:
        logger.info(f"Handling {event.metadata.event_type} for payment {event.metadata.aggregate_id}")
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

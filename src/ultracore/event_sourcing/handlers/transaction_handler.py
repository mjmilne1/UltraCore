"""Transaction Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class TransactionEventHandler(EventHandler):
    """Transaction event handler."""
    
    HANDLED_EVENTS: Set[EventType] = {
        EventType.TRANSACTION_CREATED,
        EventType.TRANSACTION_POSTED,
        EventType.TRANSACTION_REVERSED,
        EventType.TRANSACTION_SETTLED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle transaction event."""
        logger.info(f"Handling {event.metadata.event_type} for transaction {event.metadata.aggregate_id}")
        # Update TransactionHistory data product
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

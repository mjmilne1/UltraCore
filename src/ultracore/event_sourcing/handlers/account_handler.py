"""Account Event Handler."""

import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class AccountEventHandler(EventHandler):
    """Account event handler."""
    
    HANDLED_EVENTS: Set[EventType] = {
        EventType.ACCOUNT_OPENED,
        EventType.ACCOUNT_CLOSED,
        EventType.ACCOUNT_FROZEN,
        EventType.ACCOUNT_UNFROZEN,
        EventType.ACCOUNT_BALANCE_UPDATED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle account event."""
        event_type = event.metadata.event_type
        account_id = event.metadata.aggregate_id
        data = event.data
        
        logger.info(f"Handling {event_type} for account {account_id}")
        
        # Update AccountBalances data product
        # await account_read_model.update(account_id, data)
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.HANDLED_EVENTS

"""Loan Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class LoanEventHandler(EventHandler):
    HANDLED_EVENTS: Set[EventType] = {
        EventType.LOAN_APPLICATION_SUBMITTED, EventType.LOAN_APPROVED,
        EventType.LOAN_REJECTED, EventType.LOAN_DISBURSED,
        EventType.LOAN_REPAYMENT_MADE, EventType.LOAN_DEFAULTED,
    }
    async def handle(self, event: Event) -> None:
        logger.info(f"Handling {event.metadata.event_type} for loan {event.metadata.aggregate_id}")
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

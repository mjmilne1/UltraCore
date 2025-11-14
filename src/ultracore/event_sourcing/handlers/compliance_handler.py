"""Compliance Event Handler."""
import logging
from typing import Set
from ..base import Event, EventHandler, EventType

logger = logging.getLogger(__name__)

class ComplianceEventHandler(EventHandler):
    """Compliance event handler."""
    HANDLED_EVENTS: Set[EventType] = {
        EventType.COMPLIANCE_CHECK_INITIATED,
        EventType.COMPLIANCE_CHECK_PASSED,
        EventType.COMPLIANCE_CHECK_FAILED,
        EventType.SUSPICIOUS_ACTIVITY_DETECTED,
        EventType.REGULATORY_REPORT_FILED,
    }
    
    async def handle(self, event: Event) -> None:
        """Handle compliance event."""
        logger.info(f"Handling {event.metadata.event_type} for compliance {event.metadata.aggregate_id}")
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in self.HANDLED_EVENTS

"""
Customer Event Handler.

Handles customer domain events.
"""

import logging
from typing import Set

from ..base import Event, EventHandler, EventType


logger = logging.getLogger(__name__)


class CustomerEventHandler(EventHandler):
    """
    Customer event handler.
    
    Processes customer-related events and updates read models.
    """
    
    HANDLED_EVENTS: Set[EventType] = {
        EventType.CUSTOMER_CREATED,
        EventType.CUSTOMER_UPDATED,
        EventType.CUSTOMER_DELETED,
        EventType.CUSTOMER_KYC_COMPLETED,
        EventType.CUSTOMER_RISK_ASSESSED,
    }
    
    async def handle(self, event: Event) -> None:
        """
        Handle customer event.
        
        Args:
            event: Customer event to handle
        """
        event_type = event.metadata.event_type
        
        if event_type == EventType.CUSTOMER_CREATED:
            await self._handle_customer_created(event)
        elif event_type == EventType.CUSTOMER_UPDATED:
            await self._handle_customer_updated(event)
        elif event_type == EventType.CUSTOMER_DELETED:
            await self._handle_customer_deleted(event)
        elif event_type == EventType.CUSTOMER_KYC_COMPLETED:
            await self._handle_kyc_completed(event)
        elif event_type == EventType.CUSTOMER_RISK_ASSESSED:
            await self._handle_risk_assessed(event)
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.HANDLED_EVENTS
    
    async def _handle_customer_created(self, event: Event) -> None:
        """Handle customer created event."""
        customer_id = event.metadata.aggregate_id
        data = event.data
        
        logger.info(
            f"Customer created: {customer_id}, "
            f"name: {data.get('name')}, "
            f"email: {data.get('email')}"
        )
        
        # Update read model (Customer360 data product)
        # In production, this would update database/cache
        # await customer_read_model.create(customer_id, data)
    
    async def _handle_customer_updated(self, event: Event) -> None:
        """Handle customer updated event."""
        customer_id = event.metadata.aggregate_id
        data = event.data
        
        logger.info(
            f"Customer updated: {customer_id}, "
            f"fields: {list(data.keys())}"
        )
        
        # Update read model
        # await customer_read_model.update(customer_id, data)
    
    async def _handle_customer_deleted(self, event: Event) -> None:
        """Handle customer deleted event."""
        customer_id = event.metadata.aggregate_id
        
        logger.info(f"Customer deleted: {customer_id}")
        
        # Update read model (soft delete)
        # await customer_read_model.delete(customer_id)
    
    async def _handle_kyc_completed(self, event: Event) -> None:
        """Handle KYC completed event."""
        customer_id = event.metadata.aggregate_id
        data = event.data
        
        logger.info(
            f"KYC completed for customer: {customer_id}, "
            f"status: {data.get('status')}, "
            f"risk_level: {data.get('risk_level')}"
        )
        
        # Update read model with KYC status
        # await customer_read_model.update_kyc_status(customer_id, data)
        
        # Trigger downstream processes
        # - Enable account features
        # - Send welcome email
        # - Update compliance records
    
    async def _handle_risk_assessed(self, event: Event) -> None:
        """Handle risk assessed event."""
        customer_id = event.metadata.aggregate_id
        data = event.data
        
        logger.info(
            f"Risk assessed for customer: {customer_id}, "
            f"risk_score: {data.get('risk_score')}, "
            f"risk_level: {data.get('risk_level')}"
        )
        
        # Update read model with risk assessment
        # await customer_read_model.update_risk_assessment(customer_id, data)
        
        # Trigger alerts if high risk
        if data.get('risk_level') == 'high':
            logger.warning(f"High risk customer detected: {customer_id}")
            # await alert_service.send_high_risk_alert(customer_id)

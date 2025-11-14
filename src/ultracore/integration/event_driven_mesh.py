"""Event-Driven Data Mesh Integration"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class EventDrivenDataMesh:
    """Update data mesh on events."""
    
    def __init__(self, registry, event_store):
        self.registry = registry
        self.event_store = event_store
        self.event_product_map = {
            "CUSTOMER_UPDATED": ["customer_360"],
            "TRANSACTION_POSTED": ["transaction_history", "account_balances"],
            "PAYMENT_COMPLETED": ["payment_analytics"],
            "LOAN_DISBURSED": ["loan_portfolio"],
        }
        logger.info("EventDrivenDataMesh initialized")
    
    async def handle_event(self, event):
        """Handle event and update products."""
        event_type = event.metadata.event_type
        product_ids = self.event_product_map.get(event_type, [])
        
        for product_id in product_ids:
            await self.registry.refresh_product(product_id)
            await self._update_lineage(product_id, event)
        
        logger.info(f"Updated {len(product_ids)} products for event {event_type}")
    
    async def _update_lineage(self, product_id: str, event):
        """Update product lineage with event."""
        product = self.registry.get_product(product_id)
        if product and hasattr(product, 'lineage'):
            product.lineage.add_event(
                event_id=event.metadata.event_id,
                event_type=event.metadata.event_type,
                timestamp=event.metadata.timestamp
            )

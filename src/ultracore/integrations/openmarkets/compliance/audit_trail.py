"""Complete Audit Trail Management using Event Sourcing"""
from ultracore.audit.base import AuditManager
from ..events import OpenMarketsEventStore


class AuditTrailManager(AuditManager):
    """
    Manage complete audit trail for all trading activities.
    
    Event sourcing ensures:
    - Immutable audit log
    - Temporal queries (what was state at time T?)
    - Complete reconstruction of any transaction
    - Regulatory compliance
    """
    
    def __init__(self, event_store: OpenMarketsEventStore):
        super().__init__(audit_name="openmarkets_trading")
        self.event_store = event_store
    
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str = "order"
    ) -> List:
        """Get complete audit trail for an entity."""
        if entity_type == "order":
            return await self.event_store.get_order_history(entity_id)
        
        return []

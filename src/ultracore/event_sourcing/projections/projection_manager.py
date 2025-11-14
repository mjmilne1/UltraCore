"""
Projection Manager.

Manages CQRS projections and read model updates.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..base import Event, EventType
from ..store.event_store import KafkaEventStore


logger = logging.getLogger(__name__)


class Projection:
    """Base projection class."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_processed_version: Dict[str, int] = {}
        self.last_updated_at: Optional[datetime] = None
    
    async def project(self, event: Event) -> None:
        """
        Project an event onto the read model.
        
        Args:
            event: Event to project
        """
        raise NotImplementedError
    
    def can_project(self, event_type: EventType) -> bool:
        """
        Check if projection can handle event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            True if projection can handle event type
        """
        raise NotImplementedError


class ProjectionManager:
    """
    Projection manager.
    
    Manages projections and rebuilds read models from event store.
    """
    
    def __init__(self, event_store: KafkaEventStore):
        """
        Initialize projection manager.
        
        Args:
            event_store: Event store to read from
        """
        self.event_store = event_store
        self.projections: List[Projection] = []
    
    def register_projection(self, projection: Projection) -> None:
        """
        Register a projection.
        
        Args:
            projection: Projection to register
        """
        self.projections.append(projection)
        logger.info(f"Registered projection: {projection.name}")
    
    async def project_event(self, event: Event) -> None:
        """
        Project an event to all applicable projections.
        
        Args:
            event: Event to project
        """
        for projection in self.projections:
            if projection.can_project(event.metadata.event_type):
                try:
                    await projection.project(event)
                    projection.last_processed_version[event.metadata.aggregate_id] = event.metadata.version
                    projection.last_updated_at = datetime.utcnow()
                except Exception as e:
                    logger.error(
                        f"Failed to project event {event.metadata.event_id} "
                        f"to projection {projection.name}: {e}"
                    )
    
    async def rebuild_projection(
        self,
        projection: Projection,
        aggregate_id: Optional[str] = None
    ) -> None:
        """
        Rebuild a projection from event store.
        
        Args:
            projection: Projection to rebuild
            aggregate_id: Optional aggregate ID to rebuild (None for all)
        """
        logger.info(
            f"Rebuilding projection {projection.name}"
            f"{' for aggregate ' + aggregate_id if aggregate_id else ''}"
        )
        
        if aggregate_id:
            # Rebuild for specific aggregate
            events = await self.event_store.get_events(aggregate_id)
            for event in events:
                if projection.can_project(event.metadata.event_type):
                    await projection.project(event)
        else:
            # Rebuild for all aggregates
            aggregate_ids = await self.event_store.get_all_aggregate_ids()
            for agg_id in aggregate_ids:
                events = await self.event_store.get_events(agg_id)
                for event in events:
                    if projection.can_project(event.metadata.event_type):
                        await projection.project(event)
        
        logger.info(f"Projection {projection.name} rebuilt successfully")
    
    async def rebuild_all_projections(self) -> None:
        """Rebuild all projections from event store."""
        logger.info("Rebuilding all projections")
        
        for projection in self.projections:
            await self.rebuild_projection(projection)
        
        logger.info("All projections rebuilt successfully")
    
    def get_projection_status(self) -> List[Dict[str, any]]:
        """
        Get status of all projections.
        
        Returns:
            List of projection status dictionaries
        """
        status = []
        
        for projection in self.projections:
            status.append({
                "name": projection.name,
                "last_updated_at": projection.last_updated_at,
                "aggregates_processed": len(projection.last_processed_version),
            })
        
        return status

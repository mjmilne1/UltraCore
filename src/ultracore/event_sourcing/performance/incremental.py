"""Incremental Projection Updates"""
import logging

logger = logging.getLogger(__name__)

class IncrementalProjection:
    """Incremental projection updates."""
    
    def __init__(self, projection):
        self.projection = projection
        self.watermark = {}
        logger.info(f"IncrementalProjection initialized for {projection.__class__.__name__}")
    
    async def update(self, event):
        """Update projection incrementally."""
        aggregate_id = event.metadata.aggregate_id
        last_version = self.watermark.get(aggregate_id, 0)
        
        if event.metadata.version > last_version:
            await self.projection.project(event)
            self.watermark[aggregate_id] = event.metadata.version
            logger.debug(f"Updated projection for {aggregate_id} to version {event.metadata.version}")
    
    def needs_rebuild(self, aggregate_id: str, current_version: int) -> bool:
        """Check if projection needs rebuild."""
        last_version = self.watermark.get(aggregate_id, 0)
        gap = current_version - last_version
        return gap > 100
    
    def get_watermark(self, aggregate_id: str) -> int:
        """Get current watermark for aggregate."""
        return self.watermark.get(aggregate_id, 0)

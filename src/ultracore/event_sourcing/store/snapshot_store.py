"""
Snapshot Store.

Stores aggregate snapshots for performance optimization.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from ..base import Snapshot


logger = logging.getLogger(__name__)


class SnapshotStore:
    """
    Snapshot store for aggregate state.
    
    Snapshots allow rebuilding aggregate state without replaying all events.
    """
    
    def __init__(self):
        """Initialize snapshot store."""
        # In-memory storage (in production, use database or S3)
        self._snapshots: Dict[str, Snapshot] = {}
    
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """
        Save a snapshot.
        
        Args:
            snapshot: Snapshot to save
        """
        self._snapshots[snapshot.aggregate_id] = snapshot
        
        logger.info(
            f"Saved snapshot for aggregate {snapshot.aggregate_id} "
            f"at version {snapshot.version}"
        )
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """
        Get the latest snapshot for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            
        Returns:
            Latest snapshot or None
        """
        snapshot = self._snapshots.get(aggregate_id)
        
        if snapshot:
            logger.debug(
                f"Retrieved snapshot for aggregate {aggregate_id} "
                f"at version {snapshot.version}"
            )
        
        return snapshot
    
    async def delete_snapshot(self, aggregate_id: str) -> bool:
        """
        Delete snapshot for an aggregate.
        
        Args:
            aggregate_id: Aggregate ID
            
        Returns:
            True if deleted, False if not found
        """
        if aggregate_id in self._snapshots:
            del self._snapshots[aggregate_id]
            logger.info(f"Deleted snapshot for aggregate {aggregate_id}")
            return True
        
        return False
    
    async def get_all_snapshots(self) -> list[Snapshot]:
        """
        Get all snapshots.
        
        Returns:
            List of all snapshots
        """
        return list(self._snapshots.values())
    
    async def cleanup_old_snapshots(self, days: int = 30) -> int:
        """
        Cleanup snapshots older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of snapshots deleted
        """
        cutoff_date = datetime.utcnow()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        
        to_delete = []
        for aggregate_id, snapshot in self._snapshots.items():
            if snapshot.timestamp < cutoff_date:
                to_delete.append(aggregate_id)
        
        for aggregate_id in to_delete:
            del self._snapshots[aggregate_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old snapshots")
        
        return len(to_delete)

"""Saved Search Aggregate"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from ..events import *

@dataclass
class SavedSearchAggregate:
    """Event-sourced saved search aggregate"""
    saved_search_id: str
    user_id: str = ""
    tenant_id: str = ""
    search_name: str = ""
    search_type: Optional[SearchType] = None
    criteria: Dict = field(default_factory=dict)
    is_shared: bool = False
    shared_with_user_ids: List[str] = field(default_factory=list)
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    events: List = field(default_factory=list)
    
    def create(self, user_id: str, tenant_id: str, search_name: str,
               search_type: SearchType, criteria: Dict, is_shared: bool,
               created_by: str) -> 'SavedSearchAggregate':
        """Create saved search"""
        event = SavedSearchCreatedEvent(
            saved_search_id=self.saved_search_id,
            user_id=user_id,
            tenant_id=tenant_id,
            search_name=search_name,
            search_type=search_type,
            criteria=criteria,
            is_shared=is_shared,
            created_by=created_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def update(self, search_name: Optional[str] = None,
               criteria: Optional[Dict] = None,
               is_shared: Optional[bool] = None,
               updated_by: str = "") -> 'SavedSearchAggregate':
        """Update saved search"""
        event = SavedSearchUpdatedEvent(
            saved_search_id=self.saved_search_id,
            search_name=search_name,
            criteria=criteria,
            is_shared=is_shared,
            updated_by=updated_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def execute(self, user_id: str, result_count: int,
                execution_time_ms: float) -> 'SavedSearchAggregate':
        """Record search execution"""
        event = SavedSearchExecutedEvent(
            saved_search_id=self.saved_search_id,
            user_id=user_id,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def share(self, shared_with_user_ids: List[str],
              shared_by: str) -> 'SavedSearchAggregate':
        """Share search with users"""
        event = SavedSearchSharedEvent(
            saved_search_id=self.saved_search_id,
            shared_with_user_ids=shared_with_user_ids,
            shared_by=shared_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def delete(self, deleted_by: str) -> 'SavedSearchAggregate':
        """Delete saved search"""
        event = SavedSearchDeletedEvent(
            saved_search_id=self.saved_search_id,
            deleted_by=deleted_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def _apply_event(self, event) -> 'SavedSearchAggregate':
        """Apply event to aggregate"""
        new_aggregate = SavedSearchAggregate(
            saved_search_id=self.saved_search_id,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            search_name=self.search_name,
            search_type=self.search_type,
            criteria=self.criteria.copy(),
            is_shared=self.is_shared,
            shared_with_user_ids=self.shared_with_user_ids.copy(),
            execution_count=self.execution_count,
            last_executed_at=self.last_executed_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            events=self.events.copy()
        )
        
        if isinstance(event, SavedSearchCreatedEvent):
            new_aggregate.user_id = event.user_id
            new_aggregate.tenant_id = event.tenant_id
            new_aggregate.search_name = event.search_name
            new_aggregate.search_type = event.search_type
            new_aggregate.criteria = event.criteria
            new_aggregate.is_shared = event.is_shared
            new_aggregate.created_at = event.timestamp
            new_aggregate.updated_at = event.timestamp
        
        elif isinstance(event, SavedSearchUpdatedEvent):
            if event.search_name:
                new_aggregate.search_name = event.search_name
            if event.criteria:
                new_aggregate.criteria = event.criteria
            if event.is_shared is not None:
                new_aggregate.is_shared = event.is_shared
            new_aggregate.updated_at = event.timestamp
        
        elif isinstance(event, SavedSearchExecutedEvent):
            new_aggregate.execution_count += 1
            new_aggregate.last_executed_at = event.timestamp
        
        elif isinstance(event, SavedSearchSharedEvent):
            new_aggregate.shared_with_user_ids.extend(event.shared_with_user_ids)
        
        new_aggregate.events.append(event)
        return new_aggregate

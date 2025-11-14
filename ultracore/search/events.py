"""Advanced Search & Filtering Events"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class SearchType(Enum):
    """Search types"""
    ETF = "etf"
    PORTFOLIO = "portfolio"
    TRANSACTION = "transaction"
    SECURITY = "security"
    CLIENT = "client"

class SearchOperator(Enum):
    """Search operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"

@dataclass
class SearchExecutedEvent:
    """Search executed"""
    search_id: str
    user_id: str
    tenant_id: str
    search_type: SearchType
    criteria: Dict
    result_count: int
    execution_time_ms: float
    timestamp: datetime
    
@dataclass
class SavedSearchCreatedEvent:
    """Saved search created"""
    saved_search_id: str
    user_id: str
    tenant_id: str
    search_name: str
    search_type: SearchType
    criteria: Dict
    is_shared: bool
    created_by: str
    timestamp: datetime

@dataclass
class SavedSearchUpdatedEvent:
    """Saved search updated"""
    saved_search_id: str
    search_name: Optional[str]
    criteria: Optional[Dict]
    is_shared: Optional[bool]
    updated_by: str
    timestamp: datetime

@dataclass
class SavedSearchExecutedEvent:
    """Saved search executed"""
    saved_search_id: str
    user_id: str
    result_count: int
    execution_time_ms: float
    timestamp: datetime

@dataclass
class SavedSearchSharedEvent:
    """Saved search shared with users"""
    saved_search_id: str
    shared_with_user_ids: List[str]
    shared_by: str
    timestamp: datetime

@dataclass
class SavedSearchDeletedEvent:
    """Saved search deleted"""
    saved_search_id: str
    deleted_by: str
    timestamp: datetime

@dataclass
class SearchIndexUpdatedEvent:
    """Search index updated"""
    index_name: str
    document_count: int
    updated_documents: int
    timestamp: datetime

@dataclass
class SearchAnalyticsRecordedEvent:
    """Search analytics recorded"""
    search_type: SearchType
    criteria_hash: str
    result_count: int
    execution_time_ms: float
    user_id: str
    timestamp: datetime

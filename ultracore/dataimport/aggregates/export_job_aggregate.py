"""Export Job Aggregate"""
from typing import List, Dict, Optional
from datetime import datetime
from ..events import *

class ExportJobAggregate:
    """Event-sourced export job aggregate"""
    
    def __init__(self, export_job_id: str):
        self.export_job_id = export_job_id
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.export_type: Optional[str] = None
        self.format: Optional[ExportFormat] = None
        self.parameters: Dict = {}
        self.file_url: Optional[str] = None
        self.record_count: int = 0
        self.status: str = "pending"
        self.created_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.events: List = []
    
    def apply_event(self, event):
        """Apply event to aggregate state"""
        if isinstance(event, ExportJobCreatedEvent):
            self.tenant_id = event.tenant_id
            self.user_id = event.user_id
            self.export_type = event.export_type
            self.format = event.format
            self.parameters = event.parameters
            self.created_at = event.timestamp
            self.status = "pending"
        
        elif isinstance(event, ExportJobCompletedEvent):
            self.file_url = event.file_url
            self.record_count = event.record_count
            self.status = "completed"
            self.completed_at = event.timestamp
        
        elif isinstance(event, ExportJobFailedEvent):
            self.status = "failed"
            self.completed_at = event.timestamp
        
        self.events.append(event)
    
    def rebuild_from_events(self, events: List):
        """Rebuild aggregate from event stream"""
        for event in events:
            self.apply_event(event)

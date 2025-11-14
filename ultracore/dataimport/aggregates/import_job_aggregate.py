"""Import Job Aggregate"""
from typing import List, Dict, Optional
from datetime import datetime
from ..events import *

class ImportJobAggregate:
    """Event-sourced import job aggregate"""
    
    def __init__(self, import_job_id: str):
        self.import_job_id = import_job_id
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.file_url: Optional[str] = None
        self.format: Optional[ImportFormat] = None
        self.status: ImportStatus = ImportStatus.PENDING
        self.total_rows: int = 0
        self.processed_rows: int = 0
        self.failed_rows: int = 0
        self.errors: List[Dict] = []
        self.created_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.events: List = []
    
    def apply_event(self, event):
        """Apply event to aggregate state"""
        if isinstance(event, ImportJobCreatedEvent):
            self.tenant_id = event.tenant_id
            self.user_id = event.user_id
            self.file_url = event.file_url
            self.format = event.format
            self.total_rows = event.total_rows
            self.created_at = event.timestamp
            self.status = ImportStatus.PENDING
        
        elif isinstance(event, ImportJobValidationStartedEvent):
            self.status = ImportStatus.VALIDATING
        
        elif isinstance(event, ImportJobValidationCompletedEvent):
            self.errors.extend(event.errors)
        
        elif isinstance(event, ImportJobProcessingStartedEvent):
            self.status = ImportStatus.PROCESSING
        
        elif isinstance(event, ImportJobRowProcessedEvent):
            if event.success:
                self.processed_rows += 1
            else:
                self.failed_rows += 1
                if event.error:
                    self.errors.append({
                        "row": event.row_number,
                        "error": event.error
                    })
        
        elif isinstance(event, ImportJobCompletedEvent):
            self.status = ImportStatus.COMPLETED
            self.processed_rows = event.processed_rows
            self.failed_rows = event.failed_rows
            self.completed_at = event.timestamp
        
        elif isinstance(event, ImportJobFailedEvent):
            self.status = ImportStatus.FAILED
            self.completed_at = event.timestamp
        
        self.events.append(event)
    
    def rebuild_from_events(self, events: List):
        """Rebuild aggregate from event stream"""
        for event in events:
            self.apply_event(event)

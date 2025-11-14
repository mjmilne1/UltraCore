"""Job Aggregate"""
from typing import List, Dict, Optional
from datetime import datetime
from ..events import *

class JobAggregate:
    """Event-sourced job aggregate"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.tenant_id: Optional[str] = None
        self.job_type: Optional[str] = None
        self.frequency: Optional[JobFrequency] = None
        self.cron_expression: Optional[str] = None
        self.parameters: Dict = {}
        self.status: str = "active"
        self.is_paused: bool = False
        self.last_execution_at: Optional[datetime] = None
        self.next_execution_at: Optional[datetime] = None
        self.total_executions: int = 0
        self.successful_executions: int = 0
        self.failed_executions: int = 0
        self.created_at: Optional[datetime] = None
        self.events: List = []
    
    def apply_event(self, event):
        """Apply event to aggregate state"""
        if isinstance(event, JobScheduledEvent):
            self.tenant_id = event.tenant_id
            self.job_type = event.job_type
            self.frequency = event.frequency
            self.cron_expression = event.cron_expression
            self.parameters = event.parameters
            self.created_at = event.timestamp
            self.status = "active"
        
        elif isinstance(event, JobExecutionStartedEvent):
            self.last_execution_at = event.timestamp
            self.total_executions += 1
        
        elif isinstance(event, JobExecutionCompletedEvent):
            self.successful_executions += 1
        
        elif isinstance(event, JobExecutionFailedEvent):
            self.failed_executions += 1
        
        elif isinstance(event, JobPausedEvent):
            self.is_paused = True
            self.status = "paused"
        
        elif isinstance(event, JobResumedEvent):
            self.is_paused = False
            self.status = "active"
        
        elif isinstance(event, JobCancelledEvent):
            self.status = "cancelled"
        
        elif isinstance(event, JobRescheduledEvent):
            self.frequency = event.new_frequency
            self.cron_expression = event.new_cron_expression
        
        elif isinstance(event, JobDeletedEvent):
            self.status = "deleted"
        
        self.events.append(event)
    
    def rebuild_from_events(self, events: List):
        """Rebuild aggregate from event stream"""
        for event in events:
            self.apply_event(event)
    
    def get_success_rate(self) -> float:
        """Calculate job success rate"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

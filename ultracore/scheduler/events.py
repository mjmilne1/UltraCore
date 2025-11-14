"""Scheduled Jobs Event Schemas"""
from enum import Enum
from datetime import datetime
from typing import Dict, Optional

class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobFrequency(str, Enum):
    """Job frequency"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"

# Event schemas
class JobScheduledEvent:
    """Job scheduled"""
    def __init__(self, job_id: str, tenant_id: str,
                 job_type: str, frequency: JobFrequency,
                 cron_expression: Optional[str], parameters: Dict):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.job_type = job_type
        self.frequency = frequency
        self.cron_expression = cron_expression
        self.parameters = parameters
        self.timestamp = datetime.utcnow()

class JobExecutionStartedEvent:
    """Job execution started"""
    def __init__(self, job_id: str, execution_id: str, tenant_id: str):
        self.job_id = job_id
        self.execution_id = execution_id
        self.tenant_id = tenant_id
        self.timestamp = datetime.utcnow()

class JobExecutionCompletedEvent:
    """Job execution completed"""
    def __init__(self, job_id: str, execution_id: str, tenant_id: str,
                 duration_seconds: float, result: Dict):
        self.job_id = job_id
        self.execution_id = execution_id
        self.tenant_id = tenant_id
        self.duration_seconds = duration_seconds
        self.result = result
        self.timestamp = datetime.utcnow()

class JobExecutionFailedEvent:
    """Job execution failed"""
    def __init__(self, job_id: str, execution_id: str, tenant_id: str,
                 error_message: str, stack_trace: Optional[str]):
        self.job_id = job_id
        self.execution_id = execution_id
        self.tenant_id = tenant_id
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.timestamp = datetime.utcnow()

class JobPausedEvent:
    """Job paused"""
    def __init__(self, job_id: str, tenant_id: str, reason: str):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.reason = reason
        self.timestamp = datetime.utcnow()

class JobResumedEvent:
    """Job resumed"""
    def __init__(self, job_id: str, tenant_id: str):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.timestamp = datetime.utcnow()

class JobCancelledEvent:
    """Job cancelled"""
    def __init__(self, job_id: str, tenant_id: str, reason: str):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.reason = reason
        self.timestamp = datetime.utcnow()

class JobRescheduledEvent:
    """Job rescheduled"""
    def __init__(self, job_id: str, tenant_id: str,
                 new_frequency: JobFrequency,
                 new_cron_expression: Optional[str]):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.new_frequency = new_frequency
        self.new_cron_expression = new_cron_expression
        self.timestamp = datetime.utcnow()

class JobRetryScheduledEvent:
    """Job retry scheduled"""
    def __init__(self, job_id: str, execution_id: str, tenant_id: str,
                 retry_attempt: int, retry_at: datetime):
        self.job_id = job_id
        self.execution_id = execution_id
        self.tenant_id = tenant_id
        self.retry_attempt = retry_attempt
        self.retry_at = retry_at
        self.timestamp = datetime.utcnow()

class JobDeletedEvent:
    """Job deleted"""
    def __init__(self, job_id: str, tenant_id: str):
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.timestamp = datetime.utcnow()

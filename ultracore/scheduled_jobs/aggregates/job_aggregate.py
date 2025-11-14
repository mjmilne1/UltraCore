"""Job Execution Aggregate"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Dict
from ultracore.scheduled_jobs.events import *
from ultracore.scheduled_jobs.event_publisher import get_jobs_event_publisher

@dataclass
class JobAggregate:
    tenant_id: str
    job_id: str
    job_type: JobType = JobType.CUSTOM
    status: JobStatus = JobStatus.SCHEDULED
    retry_count: int = 0
    _events: List[Any] = field(default_factory=list)
    
    def schedule(self, schedule_id: str, scheduled_time: datetime,
                priority: JobPriority, parameters: Dict):
        event = JobScheduled(
            tenant_id=self.tenant_id, job_id=self.job_id,
            schedule_id=schedule_id, job_type=self.job_type,
            scheduled_time=scheduled_time, priority=priority,
            parameters=parameters, scheduled_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def start(self, executor_id: str):
        event = JobStarted(
            tenant_id=self.tenant_id, job_id=self.job_id,
            job_type=self.job_type, executor_id=executor_id,
            started_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def update_progress(self, progress_pct: int, current_step: str, details: Dict):
        event = JobProgressUpdated(
            tenant_id=self.tenant_id, job_id=self.job_id,
            progress_percentage=progress_pct, current_step=current_step,
            details=details, updated_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def complete(self, result: Dict, duration_seconds: float):
        event = JobCompleted(
            tenant_id=self.tenant_id, job_id=self.job_id,
            job_type=self.job_type, status=JobStatus.COMPLETED,
            result=result, duration_seconds=duration_seconds,
            completed_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def fail(self, error_message: str, error_details: Dict, will_retry: bool):
        event = JobFailed(
            tenant_id=self.tenant_id, job_id=self.job_id,
            job_type=self.job_type, error_message=error_message,
            error_details=error_details, retry_count=self.retry_count,
            will_retry=will_retry, failed_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def retry(self, next_retry_at: datetime):
        event = JobRetried(
            tenant_id=self.tenant_id, job_id=self.job_id,
            retry_count=self.retry_count + 1, next_retry_at=next_retry_at,
            retried_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def cancel(self, reason: str, cancelled_by: str):
        event = JobCancelled(
            tenant_id=self.tenant_id, job_id=self.job_id,
            reason=reason, cancelled_by=cancelled_by,
            cancelled_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_job_event(event)
    
    def _apply(self, event):
        if isinstance(event, JobScheduled):
            self.job_type, self.status = event.job_type, JobStatus.SCHEDULED
        elif isinstance(event, JobStarted):
            self.status = JobStatus.RUNNING
        elif isinstance(event, JobCompleted):
            self.status = JobStatus.COMPLETED
        elif isinstance(event, JobFailed):
            self.status = JobStatus.FAILED
        elif isinstance(event, JobRetried):
            self.retry_count = event.retry_count
            self.status = JobStatus.RETRYING
        elif isinstance(event, JobCancelled):
            self.status = JobStatus.CANCELLED
        self._events.append(event)

@dataclass
class ScheduleAggregate:
    tenant_id: str
    schedule_id: str
    job_type: JobType = JobType.CUSTOM
    enabled: bool = True
    _events: List[Any] = field(default_factory=list)
    
    def create(self, job_type: JobType, schedule_type: ScheduleType,
              cron_expression: str, interval_seconds: int, scheduled_time: datetime,
              enabled: bool, priority: JobPriority, parameters: Dict, created_by: str):
        event = JobScheduleCreated(
            tenant_id=self.tenant_id, schedule_id=self.schedule_id,
            job_type=job_type, schedule_type=schedule_type,
            cron_expression=cron_expression, interval_seconds=interval_seconds,
            scheduled_time=scheduled_time, enabled=enabled, priority=priority,
            parameters=parameters, created_by=created_by, created_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_schedule_event(event)
    
    def enable(self, enabled_by: str):
        event = ScheduleEnabled(
            tenant_id=self.tenant_id, schedule_id=self.schedule_id,
            enabled_by=enabled_by, enabled_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_schedule_event(event)
    
    def disable(self, disabled_by: str):
        event = ScheduleDisabled(
            tenant_id=self.tenant_id, schedule_id=self.schedule_id,
            disabled_by=disabled_by, disabled_at=datetime.utcnow()
        )
        self._apply(event)
        get_jobs_event_publisher().publish_schedule_event(event)
    
    def _apply(self, event):
        if isinstance(event, JobScheduleCreated):
            self.job_type, self.enabled = event.job_type, event.enabled
        elif isinstance(event, ScheduleEnabled):
            self.enabled = True
        elif isinstance(event, ScheduleDisabled):
            self.enabled = False
        self._events.append(event)

"""Tests for Job Aggregate"""
import pytest
from ultracore.scheduler.aggregates import JobAggregate
from ultracore.scheduler.events import *

def test_job_lifecycle():
    """Test complete job lifecycle"""
    job = JobAggregate("job_001")
    
    # Schedule
    scheduled = JobScheduledEvent(
        job_id="job_001",
        tenant_id="tenant_001",
        job_type="portfolio_valuation",
        frequency=JobFrequency.DAILY,
        cron_expression="0 2 * * *",
        parameters={}
    )
    job.apply_event(scheduled)
    
    assert job.status == "active"
    assert job.frequency == JobFrequency.DAILY
    
    # Execute
    execution_started = JobExecutionStartedEvent(
        job_id="job_001",
        execution_id="exec_001",
        tenant_id="tenant_001"
    )
    job.apply_event(execution_started)
    
    assert job.total_executions == 1
    
    # Complete
    execution_completed = JobExecutionCompletedEvent(
        job_id="job_001",
        execution_id="exec_001",
        tenant_id="tenant_001",
        duration_seconds=10.5,
        result={"records_processed": 150}
    )
    job.apply_event(execution_completed)
    
    assert job.successful_executions == 1
    assert job.get_success_rate() == 1.0

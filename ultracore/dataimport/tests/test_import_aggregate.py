"""Tests for Import Job Aggregate"""
import pytest
from ultracore.dataimport.aggregates import ImportJobAggregate
from ultracore.dataimport.events import *

def test_import_job_lifecycle():
    """Test complete import job lifecycle"""
    job = ImportJobAggregate("import_001")
    
    # Create
    created = ImportJobCreatedEvent(
        import_job_id="import_001",
        tenant_id="tenant_001",
        user_id="user_001",
        file_url="s3://bucket/file.csv",
        format=ImportFormat.COMMSEC_CSV,
        total_rows=150
    )
    job.apply_event(created)
    
    assert job.status == ImportStatus.PENDING
    assert job.total_rows == 150
    
    # Start validation
    validation_started = ImportJobValidationStartedEvent(
        import_job_id="import_001",
        tenant_id="tenant_001"
    )
    job.apply_event(validation_started)
    
    assert job.status == ImportStatus.VALIDATING
    
    # Complete
    completed = ImportJobCompletedEvent(
        import_job_id="import_001",
        tenant_id="tenant_001",
        total_rows=150,
        processed_rows=150,
        failed_rows=0
    )
    job.apply_event(completed)
    
    assert job.status == ImportStatus.COMPLETED
    assert job.processed_rows == 150

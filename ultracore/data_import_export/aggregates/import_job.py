"""Import Job Aggregate"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Dict
from ultracore.data_import_export.events import *
from ultracore.data_import_export.event_publisher import get_data_event_publisher

@dataclass
class ImportJobAggregate:
    tenant_id: str
    import_job_id: str
    user_id: str = ""
    status: ImportStatus = ImportStatus.PENDING
    total_rows: int = 0
    processed_rows: int = 0
    _events: List[Any] = field(default_factory=list)
    
    def create(self, user_id: str, file_url: str, broker_format: BrokerFormat,
               data_type: DataType, total_rows: int, created_by: str):
        event = ImportJobCreated(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            user_id=user_id, file_url=file_url, broker_format=broker_format,
            data_type=data_type, total_rows=total_rows, created_by=created_by,
            created_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def start_validation(self, validation_rules: List[str]):
        event = ImportValidationStarted(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            validation_rules=validation_rules, started_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def complete_validation(self, is_valid: bool, errors: List[Dict], warnings: List[Dict], validated_rows: int):
        event = ImportValidationCompleted(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            is_valid=is_valid, errors=errors, warnings=warnings,
            validated_rows=validated_rows, completed_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def start_processing(self, total_rows: int):
        event = ImportProcessingStarted(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            total_rows=total_rows, started_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def process_row(self, row_number: int, data: Dict, success: bool, error: Optional[str]):
        event = ImportRowProcessed(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            row_number=row_number, data=data, success=success,
            error=error, processed_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def complete(self, status: ImportStatus, failed_rows: int, errors_json: Dict):
        event = ImportJobCompleted(
            tenant_id=self.tenant_id, import_job_id=self.import_job_id,
            status=status, total_rows=self.total_rows,
            processed_rows=self.processed_rows, failed_rows=failed_rows,
            errors_json=errors_json, completed_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_import_event(event)
    
    def _apply(self, event):
        if isinstance(event, ImportJobCreated):
            self.user_id, self.total_rows = event.user_id, event.total_rows
            self.status = ImportStatus.PENDING
        elif isinstance(event, ImportValidationStarted):
            self.status = ImportStatus.VALIDATING
        elif isinstance(event, ImportProcessingStarted):
            self.status = ImportStatus.PROCESSING
        elif isinstance(event, ImportRowProcessed):
            if event.success:
                self.processed_rows += 1
        elif isinstance(event, ImportJobCompleted):
            self.status = event.status
        self._events.append(event)

@dataclass
class ExportJobAggregate:
    tenant_id: str
    export_job_id: str
    user_id: str = ""
    status: ExportStatus = ExportStatus.PENDING
    _events: List[Any] = field(default_factory=list)
    
    def create(self, user_id: str, export_type: DataType, export_format: ExportFormat,
               parameters: Dict, created_by: str):
        event = ExportJobCreated(
            tenant_id=self.tenant_id, export_job_id=self.export_job_id,
            user_id=user_id, export_type=export_type, export_format=export_format,
            parameters=parameters, created_by=created_by, created_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_export_event(event)
    
    def start_generation(self, estimated_rows: int):
        event = ExportGenerationStarted(
            tenant_id=self.tenant_id, export_job_id=self.export_job_id,
            estimated_rows=estimated_rows, started_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_export_event(event)
    
    def complete_generation(self, file_url: str, file_size_bytes: int, rows_exported: int):
        event = ExportGenerationCompleted(
            tenant_id=self.tenant_id, export_job_id=self.export_job_id,
            file_url=file_url, file_size_bytes=file_size_bytes,
            rows_exported=rows_exported, completed_at=datetime.utcnow()
        )
        self._apply(event)
        get_data_event_publisher().publish_export_event(event)
    
    def _apply(self, event):
        if isinstance(event, ExportJobCreated):
            self.user_id = event.user_id
            self.status = ExportStatus.PENDING
        elif isinstance(event, ExportGenerationStarted):
            self.status = ExportStatus.GENERATING
        elif isinstance(event, ExportGenerationCompleted):
            self.status = ExportStatus.COMPLETED
        self._events.append(event)

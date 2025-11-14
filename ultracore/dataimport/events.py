"""Data Import/Export Event Schemas"""
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

class ImportFormat(str, Enum):
    """Supported import formats"""
    VANGUARD_CSV = "vanguard_csv"
    FIDELITY_CSV = "fidelity_csv"
    COMMSEC_CSV = "commsec_csv"
    NABTRADE_CSV = "nabtrade_csv"
    GENERIC_CSV = "generic_csv"
    EXCEL = "excel"
    JSON = "json"

class ImportStatus(str, Enum):
    """Import job status"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"

# Event schemas
class ImportJobCreatedEvent:
    """Import job created"""
    def __init__(self, import_job_id: str, tenant_id: str, user_id: str,
                 file_url: str, format: ImportFormat, total_rows: int):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.file_url = file_url
        self.format = format
        self.total_rows = total_rows
        self.timestamp = datetime.utcnow()

class ImportJobValidationStartedEvent:
    """Import validation started"""
    def __init__(self, import_job_id: str, tenant_id: str):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.timestamp = datetime.utcnow()

class ImportJobValidationCompletedEvent:
    """Import validation completed"""
    def __init__(self, import_job_id: str, tenant_id: str,
                 valid_rows: int, invalid_rows: int, errors: List[Dict]):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.valid_rows = valid_rows
        self.invalid_rows = invalid_rows
        self.errors = errors
        self.timestamp = datetime.utcnow()

class ImportJobProcessingStartedEvent:
    """Import processing started"""
    def __init__(self, import_job_id: str, tenant_id: str):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.timestamp = datetime.utcnow()

class ImportJobRowProcessedEvent:
    """Import row processed"""
    def __init__(self, import_job_id: str, tenant_id: str,
                 row_number: int, success: bool, error: Optional[str] = None):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.row_number = row_number
        self.success = success
        self.error = error
        self.timestamp = datetime.utcnow()

class ImportJobCompletedEvent:
    """Import job completed"""
    def __init__(self, import_job_id: str, tenant_id: str,
                 total_rows: int, processed_rows: int, failed_rows: int):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.total_rows = total_rows
        self.processed_rows = processed_rows
        self.failed_rows = failed_rows
        self.timestamp = datetime.utcnow()

class ImportJobFailedEvent:
    """Import job failed"""
    def __init__(self, import_job_id: str, tenant_id: str,
                 error_message: str):
        self.import_job_id = import_job_id
        self.tenant_id = tenant_id
        self.error_message = error_message
        self.timestamp = datetime.utcnow()

class ExportJobCreatedEvent:
    """Export job created"""
    def __init__(self, export_job_id: str, tenant_id: str, user_id: str,
                 export_type: str, format: ExportFormat, parameters: Dict):
        self.export_job_id = export_job_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.export_type = export_type
        self.format = format
        self.parameters = parameters
        self.timestamp = datetime.utcnow()

class ExportJobCompletedEvent:
    """Export job completed"""
    def __init__(self, export_job_id: str, tenant_id: str,
                 file_url: str, record_count: int):
        self.export_job_id = export_job_id
        self.tenant_id = tenant_id
        self.file_url = file_url
        self.record_count = record_count
        self.timestamp = datetime.utcnow()

class ExportJobFailedEvent:
    """Export job failed"""
    def __init__(self, export_job_id: str, tenant_id: str,
                 error_message: str):
        self.export_job_id = export_job_id
        self.tenant_id = tenant_id
        self.error_message = error_message
        self.timestamp = datetime.utcnow()

class DataMappingCreatedEvent:
    """Data mapping created"""
    def __init__(self, mapping_id: str, tenant_id: str,
                 source_format: ImportFormat, field_mappings: Dict):
        self.mapping_id = mapping_id
        self.tenant_id = tenant_id
        self.source_format = source_format
        self.field_mappings = field_mappings
        self.timestamp = datetime.utcnow()

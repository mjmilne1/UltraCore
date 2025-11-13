"""Data Import/Export Events - Kafka schemas for data migration"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal


class ImportStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class ExportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class BrokerFormat(str, Enum):
    VANGUARD = "vanguard"
    FIDELITY = "fidelity"
    SCHWAB = "schwab"
    ETRADE = "etrade"
    INTERACTIVE_BROKERS = "interactive_brokers"
    COMMSEC = "commsec"  # Australian
    NABTRADE = "nabtrade"  # Australian
    SELFWEALTH = "selfwealth"  # Australian
    GENERIC_CSV = "generic_csv"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


class DataType(str, Enum):
    TRANSACTIONS = "transactions"
    HOLDINGS = "holdings"
    PORTFOLIO = "portfolio"
    DIVIDENDS = "dividends"
    CORPORATE_ACTIONS = "corporate_actions"
    TAX_LOTS = "tax_lots"


@dataclass
class ImportJobCreated:
    tenant_id: str
    import_job_id: str
    user_id: str
    file_url: str
    broker_format: BrokerFormat
    data_type: DataType
    total_rows: int
    created_by: str
    created_at: datetime


@dataclass
class ImportValidationStarted:
    tenant_id: str
    import_job_id: str
    validation_rules: List[str]
    started_at: datetime


@dataclass
class ImportValidationCompleted:
    tenant_id: str
    import_job_id: str
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    validated_rows: int
    completed_at: datetime


@dataclass
class ImportProcessingStarted:
    tenant_id: str
    import_job_id: str
    total_rows: int
    started_at: datetime


@dataclass
class ImportRowProcessed:
    tenant_id: str
    import_job_id: str
    row_number: int
    data: Dict[str, Any]
    success: bool
    error: Optional[str]
    processed_at: datetime


@dataclass
class ImportJobCompleted:
    tenant_id: str
    import_job_id: str
    status: ImportStatus
    total_rows: int
    processed_rows: int
    failed_rows: int
    errors_json: Dict[str, Any]
    completed_at: datetime


@dataclass
class ExportJobCreated:
    tenant_id: str
    export_job_id: str
    user_id: str
    export_type: DataType
    export_format: ExportFormat
    parameters: Dict[str, Any]
    created_by: str
    created_at: datetime


@dataclass
class ExportGenerationStarted:
    tenant_id: str
    export_job_id: str
    estimated_rows: int
    started_at: datetime


@dataclass
class ExportGenerationCompleted:
    tenant_id: str
    export_job_id: str
    file_url: str
    file_size_bytes: int
    rows_exported: int
    completed_at: datetime


@dataclass
class DataMappingCreated:
    tenant_id: str
    mapping_id: str
    source_format: BrokerFormat
    target_schema: str
    field_mappings: Dict[str, str]
    transformation_rules: Dict[str, Any]
    created_by: str
    created_at: datetime


@dataclass
class DataMappingApplied:
    tenant_id: str
    import_job_id: str
    mapping_id: str
    rows_transformed: int
    applied_at: datetime

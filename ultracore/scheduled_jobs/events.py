"""Scheduled Jobs & Automation Events - Kafka schemas"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class JobStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ScheduleType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"


class JobType(str, Enum):
    # Portfolio & Valuation
    PORTFOLIO_VALUATION = "portfolio_valuation"
    PERFORMANCE_CALCULATION = "performance_calculation"
    
    # Fees & Billing
    FEE_CHARGING = "fee_charging"
    SUBSCRIPTION_BILLING = "subscription_billing"
    HIGH_WATER_MARK_UPDATE = "high_water_mark_update"
    
    # Trading & Rebalancing
    AUTO_REBALANCING = "auto_rebalancing"
    TAX_LOSS_HARVESTING = "tax_loss_harvesting"
    
    # Compliance & Risk
    AML_CTF_MONITORING = "aml_ctf_monitoring"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_AUDIT = "compliance_audit"
    
    # Data Management
    DATA_CLEANUP = "data_cleanup"
    DATA_ARCHIVAL = "data_archival"
    DATA_QUALITY_CHECK = "data_quality_check"
    
    # Market Data
    EXCHANGE_RATE_UPDATE = "exchange_rate_update"
    PRICE_ALERT_CHECK = "price_alert_check"
    MARKET_DATA_REFRESH = "market_data_refresh"
    
    # ML & AI
    ML_MODEL_RETRAINING = "ml_model_retraining"
    ML_MODEL_EVALUATION = "ml_model_evaluation"
    
    # Notifications
    NOTIFICATION_DIGEST = "notification_digest"
    
    # Reporting
    REPORT_GENERATION = "report_generation"
    
    # Custom
    CUSTOM = "custom"


@dataclass
class JobScheduleCreated:
    tenant_id: str
    schedule_id: str
    job_type: JobType
    schedule_type: ScheduleType
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    scheduled_time: Optional[datetime]
    enabled: bool
    priority: JobPriority
    parameters: Dict[str, Any]
    created_by: str
    created_at: datetime


@dataclass
class JobScheduled:
    tenant_id: str
    job_id: str
    schedule_id: str
    job_type: JobType
    scheduled_time: datetime
    priority: JobPriority
    parameters: Dict[str, Any]
    scheduled_at: datetime


@dataclass
class JobStarted:
    tenant_id: str
    job_id: str
    job_type: JobType
    executor_id: str
    started_at: datetime


@dataclass
class JobProgressUpdated:
    tenant_id: str
    job_id: str
    progress_percentage: int
    current_step: str
    details: Dict[str, Any]
    updated_at: datetime


@dataclass
class JobCompleted:
    tenant_id: str
    job_id: str
    job_type: JobType
    status: JobStatus
    result: Dict[str, Any]
    duration_seconds: float
    completed_at: datetime


@dataclass
class JobFailed:
    tenant_id: str
    job_id: str
    job_type: JobType
    error_message: str
    error_details: Dict[str, Any]
    retry_count: int
    will_retry: bool
    failed_at: datetime


@dataclass
class JobRetried:
    tenant_id: str
    job_id: str
    retry_count: int
    next_retry_at: datetime
    retried_at: datetime


@dataclass
class JobCancelled:
    tenant_id: str
    job_id: str
    reason: str
    cancelled_by: str
    cancelled_at: datetime


@dataclass
class ScheduleEnabled:
    tenant_id: str
    schedule_id: str
    enabled_by: str
    enabled_at: datetime


@dataclass
class ScheduleDisabled:
    tenant_id: str
    schedule_id: str
    disabled_by: str
    disabled_at: datetime

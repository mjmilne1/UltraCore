"""
Reporting Events
Kafka event schemas for reporting system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class ReportType(str, Enum):
    """Report type enumeration"""
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    TAX_REPORT = "tax_report"
    HOLDINGS_SUMMARY = "holdings_summary"
    TRANSACTION_HISTORY = "transaction_history"
    PERFORMANCE_ATTRIBUTION = "performance_attribution"
    RISK_ANALYSIS = "risk_analysis"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report format enumeration"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportFrequency(str, Enum):
    """Report frequency enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"


class ReportStatus(str, Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    DELIVERED = "delivered"


class TaxReportType(str, Enum):
    """Tax report type enumeration"""
    CAPITAL_GAINS = "capital_gains"
    DIVIDEND_INCOME = "dividend_income"
    INTEREST_INCOME = "interest_income"
    WASH_SALES = "wash_sales"
    ANNUAL_TAX_SUMMARY = "annual_tax_summary"
    CGT_STATEMENT = "cgt_statement"  # Australian Capital Gains Tax


# ============================================================================
# REPORT TEMPLATE EVENTS
# ============================================================================

@dataclass
class ReportTemplateCreated:
    """Report template created event"""
    tenant_id: str
    template_id: str
    name: str
    report_type: ReportType
    description: Optional[str]
    sections: List[str]
    metrics: List[str]
    filters: Dict[str, Any]
    format_options: Dict[str, Any]
    created_by: str
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "template_id": self.template_id,
            "name": self.name,
            "report_type": self.report_type.value,
            "description": self.description,
            "sections": self.sections,
            "metrics": self.metrics,
            "filters": self.filters,
            "format_options": self.format_options,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ReportTemplateUpdated:
    """Report template updated event"""
    tenant_id: str
    template_id: str
    name: Optional[str]
    description: Optional[str]
    sections: Optional[List[str]]
    metrics: Optional[List[str]]
    filters: Optional[Dict[str, Any]]
    format_options: Optional[Dict[str, Any]]
    updated_by: str
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "sections": self.sections,
            "metrics": self.metrics,
            "filters": self.filters,
            "format_options": self.format_options,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# SCHEDULED REPORT EVENTS
# ============================================================================

@dataclass
class ScheduledReportCreated:
    """Scheduled report created event"""
    tenant_id: str
    schedule_id: str
    client_id: str
    template_id: str
    frequency: ReportFrequency
    delivery_channels: List[str]  # email, portal, etc.
    recipients: List[str]
    parameters: Dict[str, Any]
    next_run_at: datetime
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "schedule_id": self.schedule_id,
            "client_id": self.client_id,
            "template_id": self.template_id,
            "frequency": self.frequency.value,
            "delivery_channels": self.delivery_channels,
            "recipients": self.recipients,
            "parameters": self.parameters,
            "next_run_at": self.next_run_at.isoformat(),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ScheduledReportExecuted:
    """Scheduled report executed event"""
    tenant_id: str
    schedule_id: str
    report_id: str
    executed_at: datetime
    next_run_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "schedule_id": self.schedule_id,
            "report_id": self.report_id,
            "executed_at": self.executed_at.isoformat(),
            "next_run_at": self.next_run_at.isoformat()
        }


# ============================================================================
# REPORT GENERATION EVENTS
# ============================================================================

@dataclass
class ReportGenerationRequested:
    """Report generation requested event"""
    tenant_id: str
    report_id: str
    client_id: str
    report_type: ReportType
    template_id: Optional[str]
    format: ReportFormat
    parameters: Dict[str, Any]
    requested_by: str
    requested_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "client_id": self.client_id,
            "report_type": self.report_type.value,
            "template_id": self.template_id,
            "format": self.format.value,
            "parameters": self.parameters,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat()
        }


@dataclass
class ReportGenerationStarted:
    """Report generation started event"""
    tenant_id: str
    report_id: str
    started_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "started_at": self.started_at.isoformat()
        }


@dataclass
class ReportGenerationCompleted:
    """Report generation completed event"""
    tenant_id: str
    report_id: str
    file_url: str
    file_size_bytes: int
    page_count: Optional[int]
    completed_at: datetime
    generation_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "file_url": self.file_url,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "completed_at": self.completed_at.isoformat(),
            "generation_time_ms": self.generation_time_ms
        }


@dataclass
class ReportGenerationFailed:
    """Report generation failed event"""
    tenant_id: str
    report_id: str
    error_message: str
    error_details: Optional[Dict[str, Any]]
    failed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "failed_at": self.failed_at.isoformat()
        }


# ============================================================================
# REPORT DELIVERY EVENTS
# ============================================================================

@dataclass
class ReportDelivered:
    """Report delivered event"""
    tenant_id: str
    report_id: str
    delivery_channel: str
    recipient: str
    delivered_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "delivery_channel": self.delivery_channel,
            "recipient": self.recipient,
            "delivered_at": self.delivered_at.isoformat()
        }


# ============================================================================
# TAX REPORT EVENTS
# ============================================================================

@dataclass
class TaxReportGenerated:
    """Tax report generated event"""
    tenant_id: str
    report_id: str
    client_id: str
    tax_year: int
    tax_report_type: TaxReportType
    total_capital_gains: Optional[float]
    total_dividends: Optional[float]
    total_interest: Optional[float]
    wash_sales_count: Optional[int]
    file_url: str
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "report_id": self.report_id,
            "client_id": self.client_id,
            "tax_year": self.tax_year,
            "tax_report_type": self.tax_report_type.value,
            "total_capital_gains": self.total_capital_gains,
            "total_dividends": self.total_dividends,
            "total_interest": self.total_interest,
            "wash_sales_count": self.wash_sales_count,
            "file_url": self.file_url,
            "generated_at": self.generated_at.isoformat()
        }


# Kafka topics
REPORT_TOPICS = {
    "templates": "reporting.templates",
    "schedules": "reporting.schedules",
    "reports": "reporting.reports",
    "tax_reports": "reporting.tax_reports",
    "delivery": "reporting.delivery"
}

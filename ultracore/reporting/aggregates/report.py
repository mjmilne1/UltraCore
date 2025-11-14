"""
Report Generation Aggregates
Event-sourced aggregates for report generation and delivery
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..events import (
    ReportType,
    ReportFormat,
    ReportStatus,
    TaxReportType,
    ReportGenerationRequested,
    ReportGenerationStarted,
    ReportGenerationCompleted,
    ReportGenerationFailed,
    ReportDelivered,
    TaxReportGenerated
)
from ..event_publisher import get_reporting_event_publisher


@dataclass
class ReportAggregate:
    """
    Report Aggregate
    Manages report generation lifecycle with event sourcing
    """
    tenant_id: str
    report_id: str
    client_id: str = ""
    report_type: Optional[ReportType] = None
    template_id: Optional[str] = None
    format: Optional[ReportFormat] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ReportStatus = ReportStatus.PENDING
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    requested_by: Optional[str] = None
    requested_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    generation_time_ms: Optional[int] = None
    delivered_to: List[str] = field(default_factory=list)
    
    # Event sourcing
    uncommitted_events: List[Any] = field(default_factory=list)
    version: int = 0
    
    def request(
        self,
        client_id: str,
        report_type: ReportType,
        format: ReportFormat,
        template_id: Optional[str],
        parameters: Dict[str, Any],
        requested_by: str
    ) -> None:
        """Request report generation"""
        event = ReportGenerationRequested(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            client_id=client_id,
            report_type=report_type,
            template_id=template_id,
            format=format,
            parameters=parameters,
            requested_by=requested_by,
            requested_at=datetime.utcnow()
        )
        
        self._apply_report_requested(event)
        self.uncommitted_events.append(event)
    
    def start_generation(self) -> None:
        """Start report generation"""
        event = ReportGenerationStarted(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            started_at=datetime.utcnow()
        )
        
        self._apply_report_started(event)
        self.uncommitted_events.append(event)
    
    def complete_generation(
        self,
        file_url: str,
        file_size_bytes: int,
        page_count: Optional[int] = None
    ) -> None:
        """Complete report generation"""
        completed_at = datetime.utcnow()
        generation_time = int((completed_at - self.started_at).total_seconds() * 1000) if self.started_at else 0
        
        event = ReportGenerationCompleted(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            file_url=file_url,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            completed_at=completed_at,
            generation_time_ms=generation_time
        )
        
        self._apply_report_completed(event)
        self.uncommitted_events.append(event)
    
    def fail_generation(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Fail report generation"""
        event = ReportGenerationFailed(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            error_message=error_message,
            error_details=error_details,
            failed_at=datetime.utcnow()
        )
        
        self._apply_report_failed(event)
        self.uncommitted_events.append(event)
    
    def mark_delivered(self, delivery_channel: str, recipient: str) -> None:
        """Mark report as delivered"""
        event = ReportDelivered(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            delivery_channel=delivery_channel,
            recipient=recipient,
            delivered_at=datetime.utcnow()
        )
        
        self._apply_report_delivered(event)
        self.uncommitted_events.append(event)
    
    def _apply_report_requested(self, event: ReportGenerationRequested) -> None:
        """Apply report requested event"""
        self.client_id = event.client_id
        self.report_type = event.report_type
        self.template_id = event.template_id
        self.format = event.format
        self.parameters = event.parameters
        self.requested_by = event.requested_by
        self.requested_at = event.requested_at
        self.status = ReportStatus.PENDING
        self.version += 1
    
    def _apply_report_started(self, event: ReportGenerationStarted) -> None:
        """Apply report started event"""
        self.started_at = event.started_at
        self.status = ReportStatus.GENERATING
        self.version += 1
    
    def _apply_report_completed(self, event: ReportGenerationCompleted) -> None:
        """Apply report completed event"""
        self.file_url = event.file_url
        self.file_size_bytes = event.file_size_bytes
        self.page_count = event.page_count
        self.completed_at = event.completed_at
        self.generation_time_ms = event.generation_time_ms
        self.status = ReportStatus.COMPLETED
        self.version += 1
    
    def _apply_report_failed(self, event: ReportGenerationFailed) -> None:
        """Apply report failed event"""
        self.error_message = event.error_message
        self.status = ReportStatus.FAILED
        self.version += 1
    
    def _apply_report_delivered(self, event: ReportDelivered) -> None:
        """Apply report delivered event"""
        recipient_key = f"{event.delivery_channel}:{event.recipient}"
        if recipient_key not in self.delivered_to:
            self.delivered_to.append(recipient_key)
        self.status = ReportStatus.DELIVERED
        self.version += 1
    
    def commit(self) -> None:
        """Commit uncommitted events to event store"""
        publisher = get_reporting_event_publisher()
        
        for event in self.uncommitted_events:
            if isinstance(event, ReportGenerationRequested):
                publisher.publish_report_requested(event)
            elif isinstance(event, ReportGenerationStarted):
                publisher.publish_report_started(event)
            elif isinstance(event, ReportGenerationCompleted):
                publisher.publish_report_completed(event)
            elif isinstance(event, ReportGenerationFailed):
                publisher.publish_report_failed(event)
            elif isinstance(event, ReportDelivered):
                publisher.publish_report_delivered(event)
        
        self.uncommitted_events.clear()


@dataclass
class TaxReportAggregate:
    """
    Tax Report Aggregate
    Manages tax report generation with Australian compliance
    """
    tenant_id: str
    report_id: str
    client_id: str = ""
    tax_year: int = 0
    tax_report_type: Optional[TaxReportType] = None
    total_capital_gains: Optional[float] = None
    total_dividends: Optional[float] = None
    total_interest: Optional[float] = None
    wash_sales_count: Optional[int] = None
    file_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    
    # Australian tax-specific fields
    cgt_discount_applied: bool = False  # 50% CGT discount for assets held >12 months
    franking_credits: Optional[float] = None  # Australian dividend franking credits
    tfn_withheld: Optional[float] = None  # Tax File Number withholding
    
    # Event sourcing
    uncommitted_events: List[Any] = field(default_factory=list)
    version: int = 0
    
    def generate(
        self,
        client_id: str,
        tax_year: int,
        tax_report_type: TaxReportType,
        total_capital_gains: Optional[float],
        total_dividends: Optional[float],
        total_interest: Optional[float],
        wash_sales_count: Optional[int],
        file_url: str,
        cgt_discount_applied: bool = False,
        franking_credits: Optional[float] = None,
        tfn_withheld: Optional[float] = None
    ) -> None:
        """Generate tax report"""
        event = TaxReportGenerated(
            tenant_id=self.tenant_id,
            report_id=self.report_id,
            client_id=client_id,
            tax_year=tax_year,
            tax_report_type=tax_report_type,
            total_capital_gains=total_capital_gains,
            total_dividends=total_dividends,
            total_interest=total_interest,
            wash_sales_count=wash_sales_count,
            file_url=file_url,
            generated_at=datetime.utcnow()
        )
        
        self._apply_tax_report_generated(event)
        self.cgt_discount_applied = cgt_discount_applied
        self.franking_credits = franking_credits
        self.tfn_withheld = tfn_withheld
        self.uncommitted_events.append(event)
    
    def _apply_tax_report_generated(self, event: TaxReportGenerated) -> None:
        """Apply tax report generated event"""
        self.client_id = event.client_id
        self.tax_year = event.tax_year
        self.tax_report_type = event.tax_report_type
        self.total_capital_gains = event.total_capital_gains
        self.total_dividends = event.total_dividends
        self.total_interest = event.total_interest
        self.wash_sales_count = event.wash_sales_count
        self.file_url = event.file_url
        self.generated_at = event.generated_at
        self.version += 1
    
    def commit(self) -> None:
        """Commit uncommitted events to event store"""
        publisher = get_reporting_event_publisher()
        
        for event in self.uncommitted_events:
            if isinstance(event, TaxReportGenerated):
                publisher.publish_tax_report_generated(event)
        
        self.uncommitted_events.clear()

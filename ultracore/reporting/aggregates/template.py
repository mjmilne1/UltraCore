"""
Report Template and Schedule Aggregates
Event-sourced aggregates for report templates and scheduled reports
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

from ..events import (
    ReportType,
    ReportFrequency,
    ReportTemplateCreated,
    ReportTemplateUpdated,
    ScheduledReportCreated,
    ScheduledReportExecuted
)
from ..event_publisher import get_reporting_event_publisher


@dataclass
class ReportTemplateAggregate:
    """
    Report Template Aggregate
    Manages report templates with event sourcing
    """
    tenant_id: str
    template_id: str
    name: str = ""
    report_type: Optional[ReportType] = None
    description: Optional[str] = None
    sections: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    format_options: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Event sourcing
    uncommitted_events: List[Any] = field(default_factory=list)
    version: int = 0
    
    def create(
        self,
        name: str,
        report_type: ReportType,
        description: Optional[str],
        sections: List[str],
        metrics: List[str],
        filters: Dict[str, Any],
        format_options: Dict[str, Any],
        created_by: str
    ) -> None:
        """Create report template"""
        event = ReportTemplateCreated(
            tenant_id=self.tenant_id,
            template_id=self.template_id,
            name=name,
            report_type=report_type,
            description=description,
            sections=sections,
            metrics=metrics,
            filters=filters,
            format_options=format_options,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self._apply_template_created(event)
        self.uncommitted_events.append(event)
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sections: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        format_options: Optional[Dict[str, Any]] = None,
        updated_by: str = None
    ) -> None:
        """Update report template"""
        event = ReportTemplateUpdated(
            tenant_id=self.tenant_id,
            template_id=self.template_id,
            name=name,
            description=description,
            sections=sections,
            metrics=metrics,
            filters=filters,
            format_options=format_options,
            updated_by=updated_by,
            updated_at=datetime.utcnow()
        )
        
        self._apply_template_updated(event)
        self.uncommitted_events.append(event)
    
    def _apply_template_created(self, event: ReportTemplateCreated) -> None:
        """Apply template created event"""
        self.name = event.name
        self.report_type = event.report_type
        self.description = event.description
        self.sections = event.sections
        self.metrics = event.metrics
        self.filters = event.filters
        self.format_options = event.format_options
        self.created_by = event.created_by
        self.created_at = event.created_at
        self.updated_at = event.created_at
        self.version += 1
    
    def _apply_template_updated(self, event: ReportTemplateUpdated) -> None:
        """Apply template updated event"""
        if event.name is not None:
            self.name = event.name
        if event.description is not None:
            self.description = event.description
        if event.sections is not None:
            self.sections = event.sections
        if event.metrics is not None:
            self.metrics = event.metrics
        if event.filters is not None:
            self.filters = event.filters
        if event.format_options is not None:
            self.format_options = event.format_options
        self.updated_at = event.updated_at
        self.version += 1
    
    def commit(self) -> None:
        """Commit uncommitted events to event store"""
        publisher = get_reporting_event_publisher()
        
        for event in self.uncommitted_events:
            if isinstance(event, ReportTemplateCreated):
                publisher.publish_template_created(event)
            elif isinstance(event, ReportTemplateUpdated):
                publisher.publish_template_updated(event)
        
        self.uncommitted_events.clear()


@dataclass
class ScheduledReportAggregate:
    """
    Scheduled Report Aggregate
    Manages scheduled reports with event sourcing
    """
    tenant_id: str
    schedule_id: str
    client_id: str = ""
    template_id: str = ""
    frequency: Optional[ReportFrequency] = None
    delivery_channels: List[str] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    active: bool = True
    
    # Event sourcing
    uncommitted_events: List[Any] = field(default_factory=list)
    version: int = 0
    
    def create(
        self,
        client_id: str,
        template_id: str,
        frequency: ReportFrequency,
        delivery_channels: List[str],
        recipients: List[str],
        parameters: Dict[str, Any]
    ) -> None:
        """Create scheduled report"""
        next_run = self._calculate_next_run(frequency, datetime.utcnow())
        
        event = ScheduledReportCreated(
            tenant_id=self.tenant_id,
            schedule_id=self.schedule_id,
            client_id=client_id,
            template_id=template_id,
            frequency=frequency,
            delivery_channels=delivery_channels,
            recipients=recipients,
            parameters=parameters,
            next_run_at=next_run,
            created_at=datetime.utcnow()
        )
        
        self._apply_schedule_created(event)
        self.uncommitted_events.append(event)
    
    def execute(self, report_id: str) -> None:
        """Execute scheduled report"""
        now = datetime.utcnow()
        next_run = self._calculate_next_run(self.frequency, now)
        
        event = ScheduledReportExecuted(
            tenant_id=self.tenant_id,
            schedule_id=self.schedule_id,
            report_id=report_id,
            executed_at=now,
            next_run_at=next_run
        )
        
        self._apply_schedule_executed(event)
        self.uncommitted_events.append(event)
    
    def _calculate_next_run(self, frequency: ReportFrequency, from_time: datetime) -> datetime:
        """Calculate next run time based on frequency"""
        if frequency == ReportFrequency.DAILY:
            return from_time + timedelta(days=1)
        elif frequency == ReportFrequency.WEEKLY:
            return from_time + timedelta(weeks=1)
        elif frequency == ReportFrequency.MONTHLY:
            # Approximate - add 30 days
            return from_time + timedelta(days=30)
        elif frequency == ReportFrequency.QUARTERLY:
            return from_time + timedelta(days=90)
        elif frequency == ReportFrequency.ANNUALLY:
            return from_time + timedelta(days=365)
        else:
            return from_time
    
    def _apply_schedule_created(self, event: ScheduledReportCreated) -> None:
        """Apply schedule created event"""
        self.client_id = event.client_id
        self.template_id = event.template_id
        self.frequency = event.frequency
        self.delivery_channels = event.delivery_channels
        self.recipients = event.recipients
        self.parameters = event.parameters
        self.next_run_at = event.next_run_at
        self.created_at = event.created_at
        self.version += 1
    
    def _apply_schedule_executed(self, event: ScheduledReportExecuted) -> None:
        """Apply schedule executed event"""
        self.last_run_at = event.executed_at
        self.next_run_at = event.next_run_at
        self.version += 1
    
    def commit(self) -> None:
        """Commit uncommitted events to event store"""
        publisher = get_reporting_event_publisher()
        
        for event in self.uncommitted_events:
            if isinstance(event, ScheduledReportCreated):
                publisher.publish_schedule_created(event)
            elif isinstance(event, ScheduledReportExecuted):
                publisher.publish_schedule_executed(event)
        
        self.uncommitted_events.clear()

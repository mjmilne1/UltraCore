"""
Reporting Event Publisher
Kafka-first event publisher for reporting system
"""

from typing import Any, Dict
from datetime import datetime

from ultracore.event_sourcing.store.event_store import get_event_store
from .events import (
    REPORT_TOPICS,
    ReportTemplateCreated,
    ReportTemplateUpdated,
    ScheduledReportCreated,
    ScheduledReportExecuted,
    ReportGenerationRequested,
    ReportGenerationStarted,
    ReportGenerationCompleted,
    ReportGenerationFailed,
    ReportDelivered,
    TaxReportGenerated
)


class ReportingEventPublisher:
    """
    Kafka-first event publisher for reporting system
    All state changes flow through Kafka events
    """
    
    def __init__(self):
        self.event_store = get_event_store()
    
    def publish_template_created(self, event: ReportTemplateCreated) -> None:
        """Publish report template created event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["templates"],
            key=event.template_id,
            value=event.to_dict(),
            headers={"event_type": "ReportTemplateCreated"}
        )
    
    def publish_template_updated(self, event: ReportTemplateUpdated) -> None:
        """Publish report template updated event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["templates"],
            key=event.template_id,
            value=event.to_dict(),
            headers={"event_type": "ReportTemplateUpdated"}
        )
    
    def publish_schedule_created(self, event: ScheduledReportCreated) -> None:
        """Publish scheduled report created event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["schedules"],
            key=event.schedule_id,
            value=event.to_dict(),
            headers={"event_type": "ScheduledReportCreated"}
        )
    
    def publish_schedule_executed(self, event: ScheduledReportExecuted) -> None:
        """Publish scheduled report executed event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["schedules"],
            key=event.schedule_id,
            value=event.to_dict(),
            headers={"event_type": "ScheduledReportExecuted"}
        )
    
    def publish_report_requested(self, event: ReportGenerationRequested) -> None:
        """Publish report generation requested event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["reports"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "ReportGenerationRequested"}
        )
    
    def publish_report_started(self, event: ReportGenerationStarted) -> None:
        """Publish report generation started event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["reports"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "ReportGenerationStarted"}
        )
    
    def publish_report_completed(self, event: ReportGenerationCompleted) -> None:
        """Publish report generation completed event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["reports"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "ReportGenerationCompleted"}
        )
    
    def publish_report_failed(self, event: ReportGenerationFailed) -> None:
        """Publish report generation failed event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["reports"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "ReportGenerationFailed"}
        )
    
    def publish_report_delivered(self, event: ReportDelivered) -> None:
        """Publish report delivered event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["delivery"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "ReportDelivered"}
        )
    
    def publish_tax_report_generated(self, event: TaxReportGenerated) -> None:
        """Publish tax report generated event"""
        self.event_store.publish(
            topic=REPORT_TOPICS["tax_reports"],
            key=event.report_id,
            value=event.to_dict(),
            headers={"event_type": "TaxReportGenerated"}
        )


# Global instance
_publisher = None

def get_reporting_event_publisher() -> ReportingEventPublisher:
    """Get global reporting event publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = ReportingEventPublisher()
    return _publisher

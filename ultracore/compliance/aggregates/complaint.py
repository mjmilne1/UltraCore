"""
Complaint Aggregate (Dispute Resolution)
Event-sourced complaint handling for AFCA compliance
"""

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from ultracore.compliance.events import (
    ComplianceEvent,
    ComplaintSubmittedEvent,
    ComplaintAcknowledgedEvent,
    ComplaintResolvedEvent,
    ComplaintEscalatedAFCAEvent
)
from ultracore.compliance.event_publisher import get_event_publisher, ComplianceTopic


class ComplaintAggregate:
    """
    Complaint aggregate for IDR and AFCA compliance
    Implements ASIC RG 271 requirements
    """
    
    def __init__(self, complaint_id: str, tenant_id: str):
        self.complaint_id = complaint_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ComplianceEvent] = []
        
        # State
        self.complaint_reference: Optional[str] = None
        self.category: Optional[str] = None
        self.subject: Optional[str] = None
        self.description: Optional[str] = None
        self.priority: str = "medium"
        self.status: str = "submitted"
        self.submitted_at: Optional[datetime] = None
        self.acknowledged_at: Optional[datetime] = None
        self.resolved_at: Optional[datetime] = None
        self.escalated_at: Optional[datetime] = None
        self.afca_reference: Optional[str] = None
        self.resolution: Optional[str] = None
        self.compensation_amount: Optional[float] = None
    
    def submit(
        self,
        user_id: str,
        category: str,
        subject: str,
        description: str,
        priority: str = "medium"
    ):
        """Submit new complaint"""
        complaint_ref = f"COMP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        event = ComplaintSubmittedEvent(
            aggregate_id=self.complaint_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "complaint_reference": complaint_ref,
                "category": category,
                "subject": subject,
                "description": description,
                "priority": priority
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def acknowledge(self, user_id: str):
        """Acknowledge complaint (24-hour requirement)"""
        event = ComplaintAcknowledgedEvent(
            aggregate_id=self.complaint_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "acknowledged_by": user_id,
                "acknowledgment_sent": True
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def resolve(
        self,
        user_id: str,
        resolution: str,
        compensation_amount: Optional[float] = None
    ):
        """Resolve complaint (30-day deadline)"""
        within_deadline = False
        if self.submitted_at:
            deadline = self.submitted_at + timedelta(days=30)
            within_deadline = datetime.utcnow() <= deadline
        
        event = ComplaintResolvedEvent(
            aggregate_id=self.complaint_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "resolution": resolution,
                "resolved_by": user_id,
                "compensation_amount": compensation_amount,
                "within_deadline": within_deadline
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def escalate_to_afca(self, user_id: str, escalation_reason: str):
        """Escalate to AFCA"""
        afca_ref = f"AFCA-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        event = ComplaintEscalatedAFCAEvent(
            aggregate_id=self.complaint_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "afca_reference": afca_ref,
                "escalation_reason": escalation_reason,
                "escalated_by": user_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ComplianceEvent):
        """Apply event to update state"""
        if isinstance(event, ComplaintSubmittedEvent):
            self.complaint_reference = event.event_data["complaint_reference"]
            self.category = event.event_data["category"]
            self.subject = event.event_data["subject"]
            self.description = event.event_data["description"]
            self.priority = event.event_data["priority"]
            self.status = "submitted"
            self.submitted_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ComplaintAcknowledgedEvent):
            self.status = "acknowledged"
            self.acknowledged_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ComplaintResolvedEvent):
            self.status = "resolved"
            self.resolution = event.event_data["resolution"]
            self.compensation_amount = event.event_data.get("compensation_amount")
            self.resolved_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ComplaintEscalatedAFCAEvent):
            self.status = "escalated_afca"
            self.afca_reference = event.event_data["afca_reference"]
            self.escalated_at = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ComplianceTopic.DISPUTES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, complaint_id: str, tenant_id: str, events: List[ComplianceEvent]) -> 'ComplaintAggregate':
        aggregate = cls(complaint_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

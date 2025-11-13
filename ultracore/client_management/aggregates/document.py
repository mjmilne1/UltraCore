"""
Document Aggregate
Event-sourced document upload and verification for KYC
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.events import (
    ClientManagementEvent,
    DocumentUploadedEvent,
    DocumentVerifiedEvent,
    DocumentRejectedEvent,
    DocumentExpiredEvent
)
from ultracore.client_management.event_publisher import get_event_publisher, ClientManagementTopic


class DocumentAggregate:
    """
    Document aggregate for KYC verification
    Implements event sourcing pattern
    """
    
    def __init__(self, document_id: str, tenant_id: str):
        self.document_id = document_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.document_type: Optional[str] = None  # id, proof_of_address, tax_form, bank_statement
        self.document_url: Optional[str] = None
        self.file_name: Optional[str] = None
        self.file_size: Optional[int] = None
        self.mime_type: Optional[str] = None
        self.verification_status: str = "pending"  # pending, verified, rejected, expired
        self.verification_method: Optional[str] = None
        self.verified_by: Optional[str] = None
        self.verified_at: Optional[datetime] = None
        self.rejection_reason: Optional[str] = None
        self.expiry_date: Optional[datetime] = None
        self.uploaded_at: Optional[datetime] = None
    
    def upload(
        self,
        user_id: str,
        client_id: str,
        document_type: str,
        document_url: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        expiry_date: Optional[datetime] = None
    ):
        """Upload document"""
        event = DocumentUploadedEvent(
            aggregate_id=self.document_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "document_type": document_type,
                "document_url": document_url,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": mime_type,
                "expiry_date": expiry_date.isoformat() if expiry_date else None
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def verify(
        self,
        user_id: str,
        verification_method: str = "manual"
    ):
        """Verify document"""
        event = DocumentVerifiedEvent(
            aggregate_id=self.document_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "verification_method": verification_method,
                "verified_by": user_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def reject(
        self,
        user_id: str,
        rejection_reason: str
    ):
        """Reject document"""
        event = DocumentRejectedEvent(
            aggregate_id=self.document_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "rejection_reason": rejection_reason,
                "rejected_by": user_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def mark_expired(self, user_id: str):
        """Mark document as expired"""
        event = DocumentExpiredEvent(
            aggregate_id=self.document_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "expired_at": datetime.utcnow().isoformat()
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, DocumentUploadedEvent):
            self.client_id = event.event_data["client_id"]
            self.document_type = event.event_data["document_type"]
            self.document_url = event.event_data["document_url"]
            self.file_name = event.event_data["file_name"]
            self.file_size = event.event_data["file_size"]
            self.mime_type = event.event_data["mime_type"]
            self.verification_status = "pending"
            if event.event_data.get("expiry_date"):
                self.expiry_date = datetime.fromisoformat(event.event_data["expiry_date"])
            self.uploaded_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, DocumentVerifiedEvent):
            self.verification_status = "verified"
            self.verification_method = event.event_data["verification_method"]
            self.verified_by = event.event_data["verified_by"]
            self.verified_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, DocumentRejectedEvent):
            self.verification_status = "rejected"
            self.rejection_reason = event.event_data["rejection_reason"]
        
        elif isinstance(event, DocumentExpiredEvent):
            self.verification_status = "expired"
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.DOCUMENTS, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, document_id: str, tenant_id: str, events: List[ClientManagementEvent]) -> 'DocumentAggregate':
        """Rebuild aggregate from event history"""
        aggregate = cls(document_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

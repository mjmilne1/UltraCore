"""
UltraCore Document Management System - Core

Enterprise document management with:
- Version control and audit trails
- Metadata management
- Access control and security
- Full-text search
- Event-sourced document lifecycle
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from decimal import Decimal
from enum import Enum
import hashlib
import mimetypes
from dataclasses import dataclass, field
import asyncio

from ultracore.events.kafka_store import get_production_kafka_store


# ============================================================================
# Enums and Constants
# ============================================================================

class DocumentType(str, Enum):
    """Document types in the financial system"""
    # Customer Documents
    IDENTITY_DOCUMENT = "IDENTITY_DOCUMENT"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"
    BANK_STATEMENT = "BANK_STATEMENT"
    TAX_RETURN = "TAX_RETURN"
    
    # Regulatory Documents
    COMPLIANCE_REPORT = "COMPLIANCE_REPORT"
    REGULATORY_FILING = "REGULATORY_FILING"
    AUDIT_REPORT = "AUDIT_REPORT"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    
    # Financial Documents
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    CONTRACT = "CONTRACT"
    
    # Operations Documents
    POLICY_DOCUMENT = "POLICY_DOCUMENT"
    PROCEDURE = "PROCEDURE"
    TRAINING_MATERIAL = "TRAINING_MATERIAL"
    MEETING_MINUTES = "MEETING_MINUTES"
    
    # Legal Documents
    LEGAL_AGREEMENT = "LEGAL_AGREEMENT"
    NDA = "NDA"
    TERMS_CONDITIONS = "TERMS_CONDITIONS"


class DocumentStatus(str, Enum):
    """Document lifecycle status"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ClassificationLevel(str, Enum):
    """Document security classification"""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class ProcessingStatus(str, Enum):
    """AI/ML processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DocumentMetadata:
    """Rich metadata for document management"""
    title: str
    document_type: DocumentType
    classification: ClassificationLevel
    owner: str
    department: str
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    retention_period_days: Optional[int] = None
    regulatory_category: Optional[str] = None


@dataclass
class DocumentVersion:
    """Document version tracking"""
    version_number: int
    content_hash: str
    file_size_bytes: int
    mime_type: str
    created_at: datetime
    created_by: str
    change_summary: str
    storage_path: str


@dataclass
class Document:
    """Core document entity"""
    document_id: str
    metadata: DocumentMetadata
    current_version: int
    versions: List[DocumentVersion]
    status: DocumentStatus
    processing_status: ProcessingStatus
    
    # AI/ML Enrichment
    extracted_text: Optional[str] = None
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    classification_confidence: Optional[float] = None
    sentiment_score: Optional[float] = None
    key_phrases: List[str] = field(default_factory=list)
    
    # Access Control
    access_list: List[str] = field(default_factory=list)
    access_groups: List[str] = field(default_factory=list)
    
    # Audit Trail
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_by: List[Dict[str, Any]] = field(default_factory=list)
    
    # Data Mesh
    domain: str = "general"
    data_product_id: Optional[str] = None


# ============================================================================
# Document Store
# ============================================================================

class DocumentStore:
    """
    Core document storage and retrieval
    Manages document lifecycle and versioning
    """
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._index: Dict[str, List[str]] = {}  # tag -> document_ids
    
    async def create_document(
        self,
        content: bytes,
        metadata: DocumentMetadata,
        created_by: str,
        storage_path: str
    ) -> Document:
        """Create a new document with initial version"""
        
        # Generate document ID
        document_id = f"DOC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Detect MIME type
        mime_type = mimetypes.guess_type(storage_path)[0] or 'application/octet-stream'
        
        # Create initial version
        version = DocumentVersion(
            version_number=1,
            content_hash=content_hash,
            file_size_bytes=len(content),
            mime_type=mime_type,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            change_summary="Initial version",
            storage_path=storage_path
        )
        
        # Create document
        document = Document(
            document_id=document_id,
            metadata=metadata,
            current_version=1,
            versions=[version],
            status=DocumentStatus.DRAFT,
            processing_status=ProcessingStatus.PENDING,
            access_list=[created_by],
            access_groups=[metadata.department],
            domain=metadata.department.lower()
        )
        
        # Store document
        self._documents[document_id] = document
        
        # Index by tags
        for tag in metadata.tags:
            if tag not in self._index:
                self._index[tag] = []
            self._index[tag].append(document_id)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='documents',
            event_type='document_created',
            event_data={
                'document_id': document_id,
                'title': metadata.title,
                'type': metadata.document_type,
                'classification': metadata.classification,
                'created_by': created_by,
                'version': 1
            },
            aggregate_id=document_id
        )
        
        return document
    
    async def add_version(
        self,
        document_id: str,
        content: bytes,
        created_by: str,
        storage_path: str,
        change_summary: str
    ) -> DocumentVersion:
        """Add a new version to an existing document"""
        
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Check if content is different
        if document.versions[-1].content_hash == content_hash:
            raise ValueError("Content is identical to current version")
        
        # Detect MIME type
        mime_type = mimetypes.guess_type(storage_path)[0] or 'application/octet-stream'
        
        # Create new version
        version = DocumentVersion(
            version_number=document.current_version + 1,
            content_hash=content_hash,
            file_size_bytes=len(content),
            mime_type=mime_type,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            change_summary=change_summary,
            storage_path=storage_path
        )
        
        # Update document
        document.versions.append(version)
        document.current_version = version.version_number
        document.updated_at = datetime.now(timezone.utc)
        document.processing_status = ProcessingStatus.PENDING  # Reprocess
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='documents',
            event_type='document_version_added',
            event_data={
                'document_id': document_id,
                'version': version.version_number,
                'created_by': created_by,
                'change_summary': change_summary
            },
            aggregate_id=document_id
        )
        
        return version
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID"""
        document = self._documents.get(document_id)
        
        if document:
            # Record access
            document.accessed_by.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action': 'READ'
            })
        
        return document
    
    async def search_documents(
        self,
        query: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        classification: Optional[ClassificationLevel] = None,
        tags: Optional[List[str]] = None,
        status: Optional[DocumentStatus] = None,
        domain: Optional[str] = None
    ) -> List[Document]:
        """Search documents with multiple filters"""
        
        results = list(self._documents.values())
        
        # Filter by document type
        if document_type:
            results = [d for d in results if d.metadata.document_type == document_type]
        
        # Filter by classification
        if classification:
            results = [d for d in results if d.metadata.classification == classification]
        
        # Filter by status
        if status:
            results = [d for d in results if d.status == status]
        
        # Filter by domain
        if domain:
            results = [d for d in results if d.domain == domain]
        
        # Filter by tags
        if tags:
            results = [d for d in results if any(tag in d.metadata.tags for tag in tags)]
        
        # Full-text search (simplified - would use Elasticsearch in production)
        if query:
            query_lower = query.lower()
            results = [
                d for d in results 
                if (query_lower in d.metadata.title.lower() or
                    (d.extracted_text and query_lower in d.extracted_text.lower()))
            ]
        
        return results
    
    async def update_status(
        self,
        document_id: str,
        new_status: DocumentStatus,
        updated_by: str
    ) -> Document:
        """Update document status"""
        
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        old_status = document.status
        document.status = new_status
        document.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='documents',
            event_type='document_status_changed',
            event_data={
                'document_id': document_id,
                'old_status': old_status,
                'new_status': new_status,
                'updated_by': updated_by
            },
            aggregate_id=document_id
        )
        
        return document
    
    async def grant_access(
        self,
        document_id: str,
        user_id: str,
        granted_by: str
    ) -> Document:
        """Grant access to a document"""
        
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if user_id not in document.access_list:
            document.access_list.append(user_id)
            document.updated_at = datetime.now(timezone.utc)
            
            # Publish event
            kafka_store = get_production_kafka_store()
            await kafka_store.append_event(
                entity='documents',
                event_type='document_access_granted',
                event_data={
                    'document_id': document_id,
                    'user_id': user_id,
                    'granted_by': granted_by
                },
                aggregate_id=document_id
            )
        
        return document
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        
        total_docs = len(self._documents)
        total_size = sum(
            v.file_size_bytes 
            for doc in self._documents.values() 
            for v in doc.versions
        )
        
        by_type = {}
        by_status = {}
        by_classification = {}
        
        for doc in self._documents.values():
            # Count by type
            doc_type = doc.metadata.document_type
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            
            # Count by status
            status = doc.status
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by classification
            classification = doc.metadata.classification
            by_classification[classification] = by_classification.get(classification, 0) + 1
        
        return {
            'total_documents': total_docs,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_type': by_type,
            'by_status': by_status,
            'by_classification': by_classification,
            'processing_pending': len([
                d for d in self._documents.values() 
                if d.processing_status == ProcessingStatus.PENDING
            ])
        }


# Global store instance
_document_store: Optional[DocumentStore] = None

def get_document_store() -> DocumentStore:
    """Get the singleton document store instance"""
    global _document_store
    if _document_store is None:
        _document_store = DocumentStore()
    return _document_store

"""
Document Storage Service
S3/MinIO integration with event-driven architecture

Uses Data Mesh: Each document type is a data product
"""
from typing import Optional, Dict, List, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid
import mimetypes

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class DocumentType(str, Enum):
    # KYC Documents
    PASSPORT = 'PASSPORT'
    DRIVERS_LICENSE = 'DRIVERS_LICENSE'
    NATIONAL_ID = 'NATIONAL_ID'
    PROOF_OF_ADDRESS = 'PROOF_OF_ADDRESS'
    
    # Financial Documents
    BANK_STATEMENT = 'BANK_STATEMENT'
    PAYSLIP = 'PAYSLIP'
    TAX_RETURN = 'TAX_RETURN'
    CREDIT_REPORT = 'CREDIT_REPORT'
    
    # Loan Documents
    LOAN_APPLICATION = 'LOAN_APPLICATION'
    LOAN_AGREEMENT = 'LOAN_AGREEMENT'
    PROMISSORY_NOTE = 'PROMISSORY_NOTE'
    LOAN_DISCLOSURE = 'LOAN_DISCLOSURE'
    
    # Account Documents
    ACCOUNT_OPENING_FORM = 'ACCOUNT_OPENING_FORM'
    TERMS_AND_CONDITIONS = 'TERMS_AND_CONDITIONS'
    
    # Other
    CORRESPONDENCE = 'CORRESPONDENCE'
    REGULATORY_REPORT = 'REGULATORY_REPORT'
    GENERAL = 'GENERAL'


class DocumentStatus(str, Enum):
    UPLOADED = 'UPLOADED'
    PROCESSING = 'PROCESSING'
    CLASSIFIED = 'CLASSIFIED'
    EXTRACTED = 'EXTRACTED'
    VERIFIED = 'VERIFIED'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    ARCHIVED = 'ARCHIVED'


class Document:
    """
    Document model
    
    Data Mesh: Each document is a data product with lineage
    """
    
    def __init__(
        self,
        document_id: str,
        file_name: str,
        document_type: DocumentType,
        owner_id: str,
        mime_type: str,
        file_size: int,
        storage_path: str
    ):
        self.document_id = document_id
        self.file_name = file_name
        self.document_type = document_type
        self.owner_id = owner_id  # Customer/user who owns this document
        self.mime_type = mime_type
        self.file_size = file_size
        self.storage_path = storage_path
        self.status = DocumentStatus.UPLOADED
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.version = 1
        self.checksum: Optional[str] = None
        self.encrypted = True
        self.retention_until: Optional[datetime] = None
        self.tags: List[str] = []
        self.metadata: Dict = {}
        self.extracted_data: Optional[Dict] = None
        self.confidence_scores: Optional[Dict] = None
        self.fraud_score: Optional[float] = None


class DocumentStorage:
    """
    Document Storage Service
    
    Abstraction over S3/MinIO with event-driven processing
    """
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        # In production: Use boto3 for S3 or MinIO client
        self.storage_backend = "S3"  # or MinIO
        self.bucket_name = "ultracore-documents"
    
    async def upload_document(
        self,
        file: BinaryIO,
        file_name: str,
        document_type: DocumentType,
        owner_id: str,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        Upload document with automatic processing pipeline
        
        Event-driven: Triggers OCR → Classification → Extraction → Fraud Detection
        """
        # Generate document ID
        document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        
        # Read file
        file_content = file.read()
        file_size = len(file_content)
        
        # Calculate checksum
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Generate storage path
        storage_path = f"{owner_id}/{document_type.value}/{document_id}/{file_name}"
        
        # Create document record
        document = Document(
            document_id=document_id,
            file_name=file_name,
            document_type=document_type,
            owner_id=owner_id,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path
        )
        
        document.checksum = checksum
        document.metadata = metadata or {}
        
        # Set retention period (7 years for regulatory compliance)
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=7*365)
        
        # Store document
        self.documents[document_id] = document
        
        # In production: Upload to S3/MinIO
        # await self._upload_to_s3(storage_path, file_content)
        
        # Publish event to Kafka (triggers processing pipeline)
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='document_management',
            event_type='document_uploaded',
            event_data={
                'document_id': document_id,
                'file_name': file_name,
                'document_type': document_type.value,
                'owner_id': owner_id,
                'file_size': file_size,
                'checksum': checksum,
                'storage_path': storage_path,
                'uploaded_at': document.created_at.isoformat()
            },
            aggregate_id=document_id,
            exactly_once=True
        )
        
        # Publish to Data Mesh as data product
        from ultracore.data_mesh.integration import DataMeshPublisher
        await DataMeshPublisher.publish_transaction_data(
            document_id,
            {
                'data_product': 'documents',
                'document_type': document_type.value,
                'owner_id': owner_id,
                'created_at': document.created_at.isoformat(),
                'data_classification': 'CUSTOMER_PII'  # High sensitivity
            }
        )
        
        # Trigger agentic processing pipeline
        await self._trigger_processing_pipeline(document)
        
        return document
    
    async def _trigger_processing_pipeline(self, document: Document):
        """
        Trigger autonomous processing pipeline
        
        Agentic AI: Agents process document automatically
        """
        kafka_store = get_production_kafka_store()
        
        # Trigger OCR agent
        await kafka_store.append_event(
            entity='document_management',
            event_type='trigger_ocr',
            event_data={
                'document_id': document.document_id,
                'document_type': document.document_type.value
            },
            aggregate_id=document.document_id
        )
    
    async def download_document(self, document_id: str) -> bytes:
        """Download document from storage"""
        document = self.documents.get(document_id)
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # In production: Download from S3/MinIO
        # return await self._download_from_s3(document.storage_path)
        
        # Log access for audit
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='document_management',
            event_type='document_accessed',
            event_data={
                'document_id': document_id,
                'accessed_at': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=document_id
        )
        
        return b''  # Placeholder
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document metadata"""
        return self.documents.get(document_id)
    
    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        extracted_data: Optional[Dict] = None
    ):
        """Update document status (from processing pipeline)"""
        document = self.documents.get(document_id)
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        document.status = status
        document.updated_at = datetime.now(timezone.utc)
        
        if extracted_data:
            document.extracted_data = extracted_data
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='document_management',
            event_type='document_status_updated',
            event_data={
                'document_id': document_id,
                'status': status.value,
                'extracted_data': extracted_data,
                'updated_at': document.updated_at.isoformat()
            },
            aggregate_id=document_id
        )


# Global storage service
_storage_service: Optional[DocumentStorage] = None


def get_storage_service() -> DocumentStorage:
    global _storage_service
    if _storage_service is None:
        _storage_service = DocumentStorage()
    return _storage_service

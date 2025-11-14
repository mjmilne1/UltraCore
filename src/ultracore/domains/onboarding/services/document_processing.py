"""
Document Processing Service.

Document upload, OCR extraction, validation, and storage.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import hashlib
import mimetypes

from ..models import (
    DocumentStatus,
    DocumentType,
    OnboardingDocument,
)


class OCREngine:
    """OCR engine for document text extraction."""
    
    def extract_text_from_passport(self, file_path: str) -> Dict:
        """
        Extract text from passport using OCR.
        
        In production, integrate with OCR service (Tesseract, AWS Textract, Google Vision API).
        """
        # Mock implementation
        extracted_data = {
            "document_type": "passport",
            "document_number": "P12345678",
            "surname": "SMITH",
            "given_names": "JOHN WILLIAM",
            "nationality": "AUS",
            "date_of_birth": "1990-01-15",
            "sex": "M",
            "place_of_birth": "SYDNEY",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "issuing_authority": "AUSTRALIA"
        }
        
        return extracted_data
    
    def extract_text_from_drivers_license(self, file_path: str) -> Dict:
        """Extract text from driver's license."""
        extracted_data = {
            "document_type": "drivers_license",
            "license_number": "12345678",
            "surname": "SMITH",
            "given_names": "JOHN WILLIAM",
            "date_of_birth": "1990-01-15",
            "address": "123 Main St, Sydney NSW 2000",
            "date_of_issue": "2020-01-01",
            "date_of_expiry": "2030-01-01",
            "state": "NSW",
            "license_class": "C"
        }
        
        return extracted_data
    
    def extract_text_from_utility_bill(self, file_path: str) -> Dict:
        """Extract text from utility bill."""
        extracted_data = {
            "document_type": "utility_bill",
            "provider": "Sydney Energy",
            "account_number": "987654321",
            "customer_name": "John Smith",
            "service_address": "123 Main St, Sydney NSW 2000",
            "billing_period_start": "2024-01-01",
            "billing_period_end": "2024-01-31",
            "issue_date": "2024-02-01",
            "due_date": "2024-02-15",
            "amount_due": "150.00"
        }
        
        return extracted_data
    
    def extract_text_from_bank_statement(self, file_path: str) -> Dict:
        """Extract text from bank statement."""
        extracted_data = {
            "document_type": "bank_statement",
            "bank_name": "Commonwealth Bank",
            "account_holder": "John Smith",
            "account_number": "123456789",
            "bsb": "062-000",
            "statement_period_start": "2024-01-01",
            "statement_period_end": "2024-01-31",
            "address": "123 Main St, Sydney NSW 2000"
        }
        
        return extracted_data


class DocumentValidator:
    """Document validation engine."""
    
    def validate_file(
        self,
        file_path: str,
        file_type: str,
        file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Returns:
            (is_valid, error_message) tuple
        """
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return False, f"File size exceeds maximum of {max_size / 1024 / 1024}MB"
        
        # Check file type
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "application/pdf"
        ]
        
        if file_type not in allowed_types:
            return False, f"File type {file_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        
        # Check file exists and is readable
        # In production, add more checks (virus scan, etc.)
        
        return True, None
    
    def validate_document_data(
        self,
        document_type: DocumentType,
        extracted_data: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate extracted document data.
        
        Returns:
            (is_valid, errors) tuple
        """
        errors = []
        
        if document_type == DocumentType.PASSPORT:
            required_fields = [
                "document_number",
                "surname",
                "given_names",
                "nationality",
                "date_of_birth",
                "date_of_expiry"
            ]
            
            for field in required_fields:
                if not extracted_data.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Check expiry date
            expiry = extracted_data.get("date_of_expiry")
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if expiry_date < datetime.utcnow():
                        errors.append("Passport has expired")
                except ValueError:
                    errors.append("Invalid expiry date format")
        
        elif document_type == DocumentType.DRIVERS_LICENSE:
            required_fields = [
                "license_number",
                "surname",
                "given_names",
                "date_of_birth",
                "address",
                "date_of_expiry"
            ]
            
            for field in required_fields:
                if not extracted_data.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Check expiry date
            expiry = extracted_data.get("date_of_expiry")
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if expiry_date < datetime.utcnow():
                        errors.append("Driver's license has expired")
                except ValueError:
                    errors.append("Invalid expiry date format")
        
        elif document_type in [DocumentType.UTILITY_BILL, DocumentType.BANK_STATEMENT]:
            required_fields = ["customer_name", "service_address", "issue_date"]
            
            for field in required_fields:
                if not extracted_data.get(field) and not extracted_data.get("address"):
                    errors.append(f"Missing required field: {field}")
            
            # Check document is recent (within 3 months)
            issue_date = extracted_data.get("issue_date")
            if issue_date:
                try:
                    doc_date = datetime.fromisoformat(issue_date)
                    days_old = (datetime.utcnow() - doc_date).days
                    if days_old > 90:
                        errors.append("Document is older than 3 months")
                except ValueError:
                    errors.append("Invalid issue date format")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def check_document_authenticity(
        self,
        file_path: str,
        document_type: DocumentType
    ) -> Tuple[bool, Decimal]:
        """
        Check document authenticity.
        
        In production, check security features, watermarks, holograms, etc.
        
        Returns:
            (is_authentic, confidence_score) tuple
        """
        # Mock implementation
        # In production, use ML models or third-party services
        
        confidence_score = Decimal("0.95")
        is_authentic = confidence_score >= Decimal("0.80")
        
        return is_authentic, confidence_score


class DocumentStorageService:
    """Document storage service."""
    
    def __init__(self, storage_backend: str = "s3"):
        self.storage_backend = storage_backend
    
    def upload_document(
        self,
        file_path: str,
        file_name: str,
        tenant_id: str,
        customer_id: str
    ) -> Tuple[str, str]:
        """
        Upload document to storage.
        
        Returns:
            (storage_path, storage_url) tuple
        """
        # Generate storage path
        # In production, use actual S3 or cloud storage
        
        # Create unique path
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_hash = hashlib.md5(f"{tenant_id}{customer_id}{file_name}{timestamp}".encode()).hexdigest()[:8]
        
        storage_path = f"documents/{tenant_id}/{customer_id}/{timestamp}_{file_hash}_{file_name}"
        storage_url = f"https://storage.ultracore.com/{storage_path}"
        
        # In production: actually upload to S3
        # s3_client.upload_file(file_path, bucket_name, storage_path)
        
        return storage_path, storage_url
    
    def delete_document(self, storage_path: str) -> bool:
        """Delete document from storage."""
        # In production: actually delete from S3
        # s3_client.delete_object(Bucket=bucket_name, Key=storage_path)
        
        return True
    
    def get_document_url(
        self,
        storage_path: str,
        expiry_seconds: int = 3600
    ) -> str:
        """
        Get temporary signed URL for document access.
        
        Args:
            storage_path: Document storage path
            expiry_seconds: URL expiry time in seconds
        
        Returns:
            Signed URL
        """
        # In production: generate actual signed URL
        # url = s3_client.generate_presigned_url(
        #     'get_object',
        #     Params={'Bucket': bucket_name, 'Key': storage_path},
        #     ExpiresIn=expiry_seconds
        # )
        
        return f"https://storage.ultracore.com/{storage_path}?expires={expiry_seconds}"


class DocumentProcessingService:
    """
    Document Processing Service.
    
    Manages document upload, OCR extraction, validation, and storage.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.ocr_engine = OCREngine()
        self.validator = DocumentValidator()
        self.storage = DocumentStorageService()
    
    def upload_document(
        self,
        onboarding_id: str,
        file_path: str,
        file_name: str,
        document_type: DocumentType,
        uploaded_by: str,
        customer_id: Optional[str] = None
    ) -> OnboardingDocument:
        """
        Upload and process document.
        
        Args:
            onboarding_id: Onboarding ID
            file_path: Local file path
            file_name: Original file name
            document_type: Type of document
            uploaded_by: User who uploaded
            customer_id: Optional customer ID
        
        Returns:
            OnboardingDocument
        """
        # Get file info
        file_size = 0  # In production: os.path.getsize(file_path)
        file_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        
        # Validate file
        is_valid, error = self.validator.validate_file(file_path, file_type, file_size)
        if not is_valid:
            raise ValueError(f"File validation failed: {error}")
        
        # Upload to storage
        storage_path, storage_url = self.storage.upload_document(
            file_path=file_path,
            file_name=file_name,
            tenant_id=self.tenant_id,
            customer_id=customer_id or onboarding_id
        )
        
        # Create document
        document = OnboardingDocument(
            tenant_id=self.tenant_id,
            onboarding_id=onboarding_id,
            customer_id=customer_id,
            document_type=document_type,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            storage_path=storage_path,
            storage_url=storage_url,
            uploaded_by=uploaded_by
        )
        
        return document
    
    def process_document(
        self,
        document: OnboardingDocument,
        file_path: str
    ) -> OnboardingDocument:
        """
        Process document (OCR, validation, verification).
        
        Args:
            document: Document to process
            file_path: Local file path
        
        Returns:
            Updated document
        """
        document.start_processing()
        
        try:
            # Extract text using OCR
            extracted_data = self._extract_text(document.document_type, file_path)
            
            # Validate extracted data
            is_valid, errors = self.validator.validate_document_data(
                document.document_type,
                extracted_data
            )
            
            if not is_valid:
                document.reject(f"Validation failed: {', '.join(errors)}")
                return document
            
            # Check authenticity
            is_authentic, confidence = self.validator.check_document_authenticity(
                file_path,
                document.document_type
            )
            
            if not is_authentic:
                document.reject("Document authenticity check failed")
                return document
            
            # Calculate expiry date if applicable
            expiry_date = None
            if "date_of_expiry" in extracted_data:
                try:
                    expiry_date = datetime.fromisoformat(extracted_data["date_of_expiry"])
                except ValueError:
                    pass
            
            # Verify document
            document.verify(
                verification_method="ocr_and_validation",
                extracted_data=extracted_data,
                expiry_date=expiry_date
            )
            
            return document
            
        except Exception as e:
            document.reject(f"Processing error: {str(e)}")
            return document
    
    def _extract_text(self, document_type: DocumentType, file_path: str) -> Dict:
        """Extract text from document based on type."""
        if document_type == DocumentType.PASSPORT:
            return self.ocr_engine.extract_text_from_passport(file_path)
        elif document_type == DocumentType.DRIVERS_LICENSE:
            return self.ocr_engine.extract_text_from_drivers_license(file_path)
        elif document_type == DocumentType.UTILITY_BILL:
            return self.ocr_engine.extract_text_from_utility_bill(file_path)
        elif document_type == DocumentType.BANK_STATEMENT:
            return self.ocr_engine.extract_text_from_bank_statement(file_path)
        else:
            return {}
    
    def get_document(self, document_id: str) -> Optional[OnboardingDocument]:
        """Get document by ID."""
        # In production: query from database
        return None
    
    def list_documents(
        self,
        onboarding_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None
    ) -> List[OnboardingDocument]:
        """List documents with optional filtering."""
        # In production: query from database with filters
        return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document."""
        # In production:
        # 1. Get document from database
        # 2. Delete from storage
        # 3. Delete from database
        return True
    
    def check_document_expiry(self, document: OnboardingDocument) -> bool:
        """
        Check if document has expired.
        
        Returns:
            True if expired
        """
        if not document.expiry_date:
            return False
        
        if document.expiry_date < datetime.utcnow():
            if not document.is_expired:
                document.mark_expired()
            return True
        
        return False
    
    def get_expiring_documents(
        self,
        days_before_expiry: int = 30
    ) -> List[OnboardingDocument]:
        """
        Get documents expiring within specified days.
        
        Args:
            days_before_expiry: Number of days before expiry
        
        Returns:
            List of expiring documents
        """
        # In production: query database for documents with expiry_date
        # within the specified range
        threshold_date = datetime.utcnow() + timedelta(days=days_before_expiry)
        
        # Mock implementation
        return []
    
    def generate_document_report(
        self,
        onboarding_id: str
    ) -> Dict:
        """Generate document status report for onboarding."""
        documents = self.list_documents(onboarding_id=onboarding_id)
        
        report = {
            "onboarding_id": onboarding_id,
            "total_documents": len(documents),
            "verified_documents": len([d for d in documents if d.verified]),
            "pending_documents": len([d for d in documents if d.status == DocumentStatus.PROCESSING]),
            "rejected_documents": len([d for d in documents if d.status == DocumentStatus.REJECTED]),
            "expired_documents": len([d for d in documents if d.is_expired]),
            "documents_by_type": {},
            "verification_rate": 0.0
        }
        
        # Calculate verification rate
        if report["total_documents"] > 0:
            report["verification_rate"] = report["verified_documents"] / report["total_documents"]
        
        # Group by type
        for doc in documents:
            doc_type = doc.document_type.value
            if doc_type not in report["documents_by_type"]:
                report["documents_by_type"][doc_type] = 0
            report["documents_by_type"][doc_type] += 1
        
        return report

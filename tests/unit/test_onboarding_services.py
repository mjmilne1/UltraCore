"""
Unit tests for Onboarding services.

Tests KYC verification, document processing, and workflow.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.ultracore.domains.onboarding.services.kyc_verification import KYCVerificationService
from src.ultracore.domains.onboarding.services.document_processing import DocumentProcessingService
from src.ultracore.domains.onboarding.services.onboarding_workflow import OnboardingWorkflowService
from src.ultracore.domains.onboarding.models import (
    CustomerOnboarding,
    KYCVerification,
    OnboardingDocument,
    OnboardingStatus,
    VerificationMethod,
    DocumentType,
)


class TestKYCVerificationService:
    """Test KYC verification service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return KYCVerificationService()
    
    def test_verify_document(self, service):
        """Test document verification."""
        verification = KYCVerification(
            tenant_id="test",
            onboarding_id="onb-001",
            verification_method=VerificationMethod.DOCUMENT,
            document_type=DocumentType.DRIVERS_LICENSE,
            document_number="DL123456"
        )
        
        result = service.verify_document(verification)
        
        assert "verification_result" in result
        assert "confidence_score" in result
    
    def test_verify_biometric(self, service):
        """Test biometric verification."""
        verification = KYCVerification(
            tenant_id="test",
            onboarding_id="onb-001",
            verification_method=VerificationMethod.BIOMETRIC
        )
        
        result = service.verify_biometric(verification, biometric_data={"face": "..."})
        
        assert "verification_result" in result
        assert "liveness_check" in result
    
    def test_verify_third_party(self, service):
        """Test third-party verification."""
        verification = KYCVerification(
            tenant_id="test",
            onboarding_id="onb-001",
            verification_method=VerificationMethod.THIRD_PARTY
        )
        
        result = service.verify_third_party(verification, provider="greenid")
        
        assert "verification_result" in result
        assert "provider_response" in result


class TestDocumentProcessingService:
    """Test document processing service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return DocumentProcessingService()
    
    def test_upload_document(self, service):
        """Test document upload."""
        document = OnboardingDocument(
            tenant_id="test",
            onboarding_id="onb-001",
            document_type=DocumentType.DRIVERS_LICENSE,
            file_name="license.jpg",
            file_size=1024000,
            mime_type="image/jpeg"
        )
        
        result = service.upload_document(document, file_data=b"...")
        
        assert result["success"] is True
        assert "storage_url" in result
    
    def test_extract_data(self, service):
        """Test OCR data extraction."""
        document = OnboardingDocument(
            tenant_id="test",
            onboarding_id="onb-001",
            document_type=DocumentType.DRIVERS_LICENSE,
            file_name="license.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            storage_url="s3://..."
        )
        
        result = service.extract_data(document)
        
        assert "extracted_data" in result
        assert isinstance(result["extracted_data"], dict)
    
    def test_validate_document(self, service):
        """Test document validation."""
        document = OnboardingDocument(
            tenant_id="test",
            onboarding_id="onb-001",
            document_type=DocumentType.DRIVERS_LICENSE,
            file_name="license.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            storage_url="s3://...",
            extracted_data={"name": "John Smith", "license_number": "DL123456"}
        )
        
        result = service.validate_document(document)
        
        assert "is_valid" in result
        assert isinstance(result["is_valid"], bool)


class TestOnboardingWorkflowService:
    """Test onboarding workflow service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return OnboardingWorkflowService()
    
    def test_initiate_onboarding(self, service):
        """Test onboarding initiation."""
        result = service.initiate_onboarding(
            tenant_id="test",
            email="john@example.com",
            phone="+61400000000"
        )
        
        assert "onboarding_id" in result
        assert result["status"] == OnboardingStatus.INITIATED.value
    
    def test_collect_personal_info(self, service):
        """Test personal information collection."""
        onboarding = CustomerOnboarding(
            tenant_id="test",
            email="john@example.com",
            phone="+61400000000"
        )
        
        personal_info = {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1990-01-01",
            "address": "123 Main St, Sydney NSW 2000"
        }
        
        result = service.collect_personal_info(onboarding, personal_info)
        
        assert result["success"] is True
        assert onboarding.personal_info is not None
    
    def test_verify_identity(self, service):
        """Test identity verification."""
        onboarding = CustomerOnboarding(
            tenant_id="test",
            email="john@example.com",
            phone="+61400000000",
            personal_info={"first_name": "John", "last_name": "Smith"}
        )
        
        result = service.verify_identity(onboarding)
        
        assert "verification_status" in result
    
    def test_complete_onboarding(self, service):
        """Test onboarding completion."""
        onboarding = CustomerOnboarding(
            tenant_id="test",
            email="john@example.com",
            phone="+61400000000",
            status=OnboardingStatus.VERIFIED
        )
        
        result = service.complete_onboarding(onboarding)
        
        assert result["success"] is True
        assert onboarding.status == OnboardingStatus.COMPLETED

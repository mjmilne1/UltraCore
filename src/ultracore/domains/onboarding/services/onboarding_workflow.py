"""
Onboarding Workflow Service.

Orchestrates the customer onboarding process.
"""

from datetime import datetime
from typing import Dict, List, Optional

from ..models import (
    CustomerOnboarding,
    DocumentType,
    IdentityVerificationMethod,
    KYCVerification,
    OnboardingDocument,
    OnboardingStatus,
    RiskRating,
    VerificationStatus,
)
from .document_processing import DocumentProcessingService
from .kyc_verification import KYCVerificationService


class OnboardingWorkflowService:
    """
    Onboarding Workflow Service.
    
    Orchestrates the complete customer onboarding process.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.kyc_service = KYCVerificationService(tenant_id)
        self.document_service = DocumentProcessingService(tenant_id)
    
    def initiate_onboarding(
        self,
        email: str,
        phone: Optional[str] = None
    ) -> CustomerOnboarding:
        """
        Initiate customer onboarding.
        
        Args:
            email: Customer email
            phone: Optional phone number
        
        Returns:
            CustomerOnboarding instance
        """
        onboarding = CustomerOnboarding(
            tenant_id=self.tenant_id,
            email=email,
            phone=phone or ""
        )
        
        return onboarding
    
    def collect_personal_information(
        self,
        onboarding: CustomerOnboarding,
        first_name: str,
        last_name: str,
        date_of_birth: str,
        email: str,
        phone: str,
        nationality: str,
        country_of_residence: str,
        address: Dict
    ) -> CustomerOnboarding:
        """Collect personal information."""
        onboarding.collect_personal_information(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            email=email,
            phone=phone,
            nationality=nationality,
            country_of_residence=country_of_residence,
            address=address
        )
        
        return onboarding
    
    def submit_documents(
        self,
        onboarding: CustomerOnboarding,
        documents: List[Dict]
    ) -> CustomerOnboarding:
        """
        Submit documents for verification.
        
        Args:
            onboarding: Onboarding instance
            documents: List of document data with file_path, file_name, document_type
        
        Returns:
            Updated onboarding
        """
        for doc_data in documents:
            # Upload and process document
            document = self.document_service.upload_document(
                onboarding_id=onboarding.onboarding_id,
                file_path=doc_data["file_path"],
                file_name=doc_data["file_name"],
                document_type=DocumentType(doc_data["document_type"]),
                uploaded_by=onboarding.email
            )
            
            # Process document (OCR, validation)
            document = self.document_service.process_document(
                document=document,
                file_path=doc_data["file_path"]
            )
            
            # Add document to onboarding
            onboarding.submit_document(document.document_id)
        
        return onboarding
    
    def start_verification(
        self,
        onboarding: CustomerOnboarding,
        verification_method: IdentityVerificationMethod = IdentityVerificationMethod.DOCUMENT_VERIFICATION
    ) -> CustomerOnboarding:
        """Start identity verification process."""
        onboarding.start_verification()
        
        # Create KYC verification
        customer_data = {
            "full_name": f"{onboarding.first_name} {onboarding.last_name}",
            "date_of_birth": onboarding.date_of_birth,
            "address": onboarding.address,
            "nationality": onboarding.nationality
        }
        
        verification = self.kyc_service.create_verification(
            onboarding_id=onboarding.onboarding_id,
            customer_data=customer_data,
            method=verification_method
        )
        
        return onboarding
    
    def verify_identity(
        self,
        onboarding: CustomerOnboarding,
        verification_method: IdentityVerificationMethod,
        verification_data: Dict
    ) -> CustomerOnboarding:
        """
        Verify customer identity.
        
        Args:
            onboarding: Onboarding instance
            verification_method: Verification method to use
            verification_data: Data for verification (documents, biometrics, etc.)
        
        Returns:
            Updated onboarding
        """
        customer_data = {
            "full_name": f"{onboarding.first_name} {onboarding.last_name}",
            "date_of_birth": onboarding.date_of_birth,
            "address": onboarding.address,
            "nationality": onboarding.nationality
        }
        
        # Create verification
        verification = self.kyc_service.create_verification(
            onboarding_id=onboarding.onboarding_id,
            customer_data=customer_data,
            method=verification_method
        )
        
        # Perform verification based on method
        if verification_method == IdentityVerificationMethod.DOCUMENT_VERIFICATION:
            documents = verification_data.get("documents", [])
            verification = self.kyc_service.verify_with_documents(
                verification=verification,
                documents=documents
            )
        
        elif verification_method == IdentityVerificationMethod.BIOMETRIC_VERIFICATION:
            verification = self.kyc_service.verify_with_biometrics(
                verification=verification,
                document_photo=verification_data.get("document_photo", ""),
                selfie_photo=verification_data.get("selfie_photo", ""),
                liveness_video=verification_data.get("liveness_video")
            )
        
        elif verification_method == IdentityVerificationMethod.THIRD_PARTY_VERIFICATION:
            verification = self.kyc_service.verify_with_third_party(
                verification=verification,
                provider=verification_data.get("provider", "onfido"),
                customer_data=customer_data
            )
        
        # Update onboarding based on verification result
        if verification.status == VerificationStatus.VERIFIED:
            onboarding.verify_identity(verification.verification_id)
            onboarding.verify_address()  # Address verified through documents
        elif verification.status == VerificationStatus.FAILED:
            onboarding.fail_verification(
                verification.failure_reason or "Identity verification failed"
            )
        elif verification.status == VerificationStatus.REQUIRES_MANUAL_REVIEW:
            onboarding.require_compliance_review()
        
        return onboarding
    
    def run_compliance_checks(
        self,
        onboarding: CustomerOnboarding
    ) -> CustomerOnboarding:
        """
        Run compliance checks (AML, sanctions, PEP).
        
        In production, integrate with compliance domain services.
        """
        # Mock compliance checks
        # In production: call compliance domain services
        
        customer_data = {
            "full_name": f"{onboarding.first_name} {onboarding.last_name}",
            "date_of_birth": onboarding.date_of_birth,
            "nationality": onboarding.nationality,
            "country_of_residence": onboarding.country_of_residence
        }
        
        # Mock check IDs
        aml_check_id = f"aml_{onboarding.onboarding_id}"
        sanctions_check_id = f"sanctions_{onboarding.onboarding_id}"
        pep_check_id = f"pep_{onboarding.onboarding_id}"
        
        # Determine risk rating
        risk_rating = self._calculate_risk_rating(customer_data)
        
        # Clear compliance
        onboarding.clear_compliance(
            aml_check_id=aml_check_id,
            sanctions_check_id=sanctions_check_id,
            pep_check_id=pep_check_id,
            risk_rating=risk_rating
        )
        
        return onboarding
    
    def _calculate_risk_rating(self, customer_data: Dict) -> RiskRating:
        """Calculate customer risk rating."""
        # Mock risk calculation
        # In production: use compliance domain risk assessment
        
        risk_score = 0
        
        # High-risk countries
        high_risk_countries = ["AF", "KP", "IR", "SY"]
        if customer_data.get("nationality") in high_risk_countries:
            risk_score += 3
        if customer_data.get("country_of_residence") in high_risk_countries:
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 4:
            return RiskRating.VERY_HIGH
        elif risk_score >= 3:
            return RiskRating.HIGH
        elif risk_score >= 1:
            return RiskRating.MEDIUM
        else:
            return RiskRating.LOW
    
    def approve_onboarding(
        self,
        onboarding: CustomerOnboarding,
        customer_id: str
    ) -> CustomerOnboarding:
        """Approve onboarding and create customer account."""
        try:
            onboarding.approve(customer_id)
        except ValueError as e:
            raise ValueError(f"Cannot approve onboarding: {str(e)}")
        
        return onboarding
    
    def reject_onboarding(
        self,
        onboarding: CustomerOnboarding,
        reason: str
    ) -> CustomerOnboarding:
        """Reject onboarding."""
        onboarding.reject(reason)
        return onboarding
    
    def complete_onboarding(
        self,
        onboarding: CustomerOnboarding
    ) -> CustomerOnboarding:
        """Complete onboarding process."""
        try:
            onboarding.complete()
        except ValueError as e:
            raise ValueError(f"Cannot complete onboarding: {str(e)}")
        
        return onboarding
    
    def assign_onboarding(
        self,
        onboarding: CustomerOnboarding,
        user_id: str
    ) -> CustomerOnboarding:
        """Assign onboarding to user for review."""
        onboarding.assign(user_id)
        return onboarding
    
    def add_note(
        self,
        onboarding: CustomerOnboarding,
        note: str,
        author: str
    ) -> CustomerOnboarding:
        """Add note to onboarding."""
        onboarding.add_note(note, author)
        return onboarding
    
    def get_onboarding_status(
        self,
        onboarding: CustomerOnboarding
    ) -> Dict:
        """Get detailed onboarding status."""
        status = {
            "onboarding_id": onboarding.onboarding_id,
            "status": onboarding.status.value,
            "current_step": onboarding.current_step,
            "completed_steps": onboarding.completed_steps,
            "progress_percentage": self._calculate_progress(onboarding),
            "identity_verified": onboarding.identity_verified,
            "address_verified": onboarding.address_verified,
            "compliance_cleared": onboarding.compliance_cleared,
            "risk_rating": onboarding.risk_rating.value,
            "can_approve": self._can_approve(onboarding),
            "next_steps": self._get_next_steps(onboarding)
        }
        
        return status
    
    def _calculate_progress(self, onboarding: CustomerOnboarding) -> float:
        """Calculate onboarding progress percentage."""
        total_steps = 5  # personal_info, documents, identity, address, compliance
        completed = len(onboarding.completed_steps)
        return (completed / total_steps) * 100
    
    def _can_approve(self, onboarding: CustomerOnboarding) -> bool:
        """Check if onboarding can be approved."""
        return (
            onboarding.identity_verified and
            onboarding.address_verified and
            onboarding.compliance_cleared and
            onboarding.status not in [
                OnboardingStatus.REJECTED,
                OnboardingStatus.COMPLETED
            ]
        )
    
    def _get_next_steps(self, onboarding: CustomerOnboarding) -> List[str]:
        """Get next steps for onboarding."""
        next_steps = []
        
        if onboarding.status == OnboardingStatus.INITIATED:
            next_steps.append("Collect personal information")
        
        if onboarding.status == OnboardingStatus.INFORMATION_COLLECTED:
            next_steps.append("Submit identity documents")
        
        if onboarding.status == OnboardingStatus.DOCUMENTS_SUBMITTED:
            next_steps.append("Start identity verification")
        
        if onboarding.status == OnboardingStatus.VERIFICATION_IN_PROGRESS:
            if not onboarding.identity_verified:
                next_steps.append("Complete identity verification")
            if not onboarding.address_verified:
                next_steps.append("Complete address verification")
        
        if onboarding.identity_verified and onboarding.address_verified:
            if not onboarding.compliance_cleared:
                next_steps.append("Run compliance checks")
        
        if self._can_approve(onboarding):
            next_steps.append("Approve onboarding")
        
        if onboarding.status == OnboardingStatus.APPROVED:
            next_steps.append("Complete onboarding")
        
        return next_steps
    
    def list_onboardings(
        self,
        status: Optional[OnboardingStatus] = None,
        assigned_to: Optional[str] = None,
        risk_rating: Optional[RiskRating] = None
    ) -> List[CustomerOnboarding]:
        """List onboardings with optional filtering."""
        # In production: query from database with filters
        return []
    
    def get_onboarding_metrics(self) -> Dict:
        """Get onboarding metrics."""
        # In production: query database for metrics
        
        metrics = {
            "total_onboardings": 0,
            "by_status": {
                "initiated": 0,
                "in_progress": 0,
                "completed": 0,
                "rejected": 0
            },
            "by_risk_rating": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "very_high": 0
            },
            "average_completion_time_hours": 0.0,
            "approval_rate": 0.0,
            "pending_review": 0
        }
        
        return metrics
    
    def get_verification_requirements(
        self,
        customer_type: str = "individual",
        risk_level: str = "medium"
    ) -> Dict:
        """Get verification requirements."""
        return self.kyc_service.get_verification_requirements(
            customer_type=customer_type,
            risk_level=risk_level
        )

"""
Onboarding Domain Models.

Customer onboarding, KYC verification, and document management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class OnboardingStatus(str, Enum):
    """Onboarding status."""
    INITIATED = "initiated"
    INFORMATION_COLLECTED = "information_collected"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
    VERIFICATION_FAILED = "verification_failed"
    COMPLIANCE_REVIEW = "compliance_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class VerificationStatus(str, Enum):
    """Verification status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class DocumentType(str, Enum):
    """Document type."""
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    PROOF_OF_ADDRESS = "proof_of_address"
    BANK_STATEMENT = "bank_statement"
    UTILITY_BILL = "utility_bill"
    TAX_RETURN = "tax_return"
    EMPLOYMENT_LETTER = "employment_letter"
    BUSINESS_REGISTRATION = "business_registration"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class IdentityVerificationMethod(str, Enum):
    """Identity verification method."""
    DOCUMENT_VERIFICATION = "document_verification"
    BIOMETRIC_VERIFICATION = "biometric_verification"
    VIDEO_VERIFICATION = "video_verification"
    IN_PERSON_VERIFICATION = "in_person_verification"
    THIRD_PARTY_VERIFICATION = "third_party_verification"


class RiskRating(str, Enum):
    """Risk rating."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CustomerOnboarding:
    """
    Customer onboarding aggregate.
    
    Manages the customer onboarding process including information collection,
    document verification, and compliance checks.
    """
    
    # Identity
    tenant_id: str
    onboarding_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Customer information
    customer_id: Optional[str] = None
    email: str = ""
    phone: str = ""
    first_name: str = ""
    last_name: str = ""
    date_of_birth: Optional[str] = None
    nationality: str = ""
    country_of_residence: str = ""
    address: Dict = field(default_factory=dict)
    
    # Onboarding state
    status: OnboardingStatus = OnboardingStatus.INITIATED
    current_step: str = "personal_information"
    completed_steps: List[str] = field(default_factory=list)
    
    # Verification
    identity_verified: bool = False
    address_verified: bool = False
    compliance_cleared: bool = False
    risk_rating: RiskRating = RiskRating.MEDIUM
    
    # Documents
    submitted_documents: List[str] = field(default_factory=list)  # Document IDs
    
    # Compliance
    kyc_check_id: Optional[str] = None
    aml_check_id: Optional[str] = None
    sanctions_check_id: Optional[str] = None
    pep_check_id: Optional[str] = None
    
    # Workflow
    assigned_to: Optional[str] = None
    notes: List[Dict] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    version: int = 1
    
    def collect_personal_information(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: str,
        email: str,
        phone: str,
        nationality: str,
        country_of_residence: str,
        address: Dict
    ) -> None:
        """Collect personal information."""
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.email = email
        self.phone = phone
        self.nationality = nationality
        self.country_of_residence = country_of_residence
        self.address = address
        
        self.complete_step("personal_information")
        self.status = OnboardingStatus.INFORMATION_COLLECTED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def submit_document(self, document_id: str) -> None:
        """Submit document for verification."""
        if document_id not in self.submitted_documents:
            self.submitted_documents.append(document_id)
        
        self.status = OnboardingStatus.DOCUMENTS_SUBMITTED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def start_verification(self) -> None:
        """Start verification process."""
        self.status = OnboardingStatus.VERIFICATION_IN_PROGRESS
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def verify_identity(self, check_id: str) -> None:
        """Mark identity as verified."""
        self.identity_verified = True
        self.kyc_check_id = check_id
        self.complete_step("identity_verification")
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def verify_address(self) -> None:
        """Mark address as verified."""
        self.address_verified = True
        self.complete_step("address_verification")
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def clear_compliance(
        self,
        aml_check_id: str,
        sanctions_check_id: str,
        pep_check_id: str,
        risk_rating: RiskRating
    ) -> None:
        """Mark compliance checks as cleared."""
        self.compliance_cleared = True
        self.aml_check_id = aml_check_id
        self.sanctions_check_id = sanctions_check_id
        self.pep_check_id = pep_check_id
        self.risk_rating = risk_rating
        self.complete_step("compliance_checks")
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def fail_verification(self, reason: str) -> None:
        """Mark verification as failed."""
        self.status = OnboardingStatus.VERIFICATION_FAILED
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def require_compliance_review(self) -> None:
        """Require manual compliance review."""
        self.status = OnboardingStatus.COMPLIANCE_REVIEW
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def approve(self, customer_id: str) -> None:
        """Approve onboarding."""
        if not self.identity_verified:
            raise ValueError("Identity not verified")
        if not self.address_verified:
            raise ValueError("Address not verified")
        if not self.compliance_cleared:
            raise ValueError("Compliance not cleared")
        
        self.customer_id = customer_id
        self.status = OnboardingStatus.APPROVED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def reject(self, reason: str) -> None:
        """Reject onboarding."""
        self.status = OnboardingStatus.REJECTED
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def complete(self) -> None:
        """Complete onboarding."""
        if self.status != OnboardingStatus.APPROVED:
            raise ValueError(f"Cannot complete onboarding in status: {self.status}")
        
        self.status = OnboardingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def complete_step(self, step: str) -> None:
        """Mark step as completed."""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
    
    def assign(self, user_id: str) -> None:
        """Assign onboarding to user."""
        self.assigned_to = user_id
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_note(self, note: str, author: str) -> None:
        """Add note to onboarding."""
        self.notes.append({
            "note": note,
            "author": author,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "onboarding_id": self.onboarding_id,
            "customer_id": self.customer_id,
            "email": self.email,
            "phone": self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "nationality": self.nationality,
            "country_of_residence": self.country_of_residence,
            "address": self.address,
            "status": self.status.value,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "identity_verified": self.identity_verified,
            "address_verified": self.address_verified,
            "compliance_cleared": self.compliance_cleared,
            "risk_rating": self.risk_rating.value,
            "submitted_documents": self.submitted_documents,
            "kyc_check_id": self.kyc_check_id,
            "aml_check_id": self.aml_check_id,
            "sanctions_check_id": self.sanctions_check_id,
            "pep_check_id": self.pep_check_id,
            "assigned_to": self.assigned_to,
            "notes": self.notes,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "version": self.version
        }


@dataclass
class KYCVerification:
    """
    KYC (Know Your Customer) verification.
    
    Manages identity verification process.
    """
    
    # Identity
    tenant_id: str
    verification_id: str = field(default_factory=lambda: str(uuid4()))
    onboarding_id: str = ""
    customer_id: Optional[str] = None
    
    # Verification details
    method: IdentityVerificationMethod = IdentityVerificationMethod.DOCUMENT_VERIFICATION
    status: VerificationStatus = VerificationStatus.PENDING
    
    # Identity information
    provided_name: str = ""
    provided_date_of_birth: Optional[str] = None
    provided_address: Dict = field(default_factory=dict)
    provided_nationality: str = ""
    
    # Verification results
    identity_confirmed: bool = False
    address_confirmed: bool = False
    date_of_birth_confirmed: bool = False
    confidence_score: Decimal = Decimal("0")
    
    # Documents
    document_ids: List[str] = field(default_factory=list)
    
    # Third-party verification
    third_party_provider: Optional[str] = None
    third_party_reference: Optional[str] = None
    third_party_response: Dict = field(default_factory=dict)
    
    # Manual review
    requires_manual_review: bool = False
    reviewed_by: Optional[str] = None
    review_notes: str = ""
    
    # Failure details
    failure_reason: Optional[str] = None
    failure_details: Dict = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    version: int = 1
    
    def start_verification(self) -> None:
        """Start verification."""
        self.status = VerificationStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def verify(
        self,
        identity_confirmed: bool,
        address_confirmed: bool,
        date_of_birth_confirmed: bool,
        confidence_score: Decimal
    ) -> None:
        """Complete verification."""
        self.identity_confirmed = identity_confirmed
        self.address_confirmed = address_confirmed
        self.date_of_birth_confirmed = date_of_birth_confirmed
        self.confidence_score = confidence_score
        
        # Determine if verification passed
        if identity_confirmed and address_confirmed and confidence_score >= Decimal("0.8"):
            self.status = VerificationStatus.VERIFIED
            self.verified_at = datetime.utcnow()
        elif confidence_score < Decimal("0.6"):
            self.status = VerificationStatus.FAILED
            self.failure_reason = "Low confidence score"
        else:
            self.status = VerificationStatus.REQUIRES_MANUAL_REVIEW
            self.requires_manual_review = True
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def fail(self, reason: str, details: Optional[Dict] = None) -> None:
        """Mark verification as failed."""
        self.status = VerificationStatus.FAILED
        self.failure_reason = reason
        if details:
            self.failure_details = details
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def require_manual_review(self, reason: str) -> None:
        """Require manual review."""
        self.status = VerificationStatus.REQUIRES_MANUAL_REVIEW
        self.requires_manual_review = True
        self.review_notes = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def complete_manual_review(
        self,
        reviewer_id: str,
        approved: bool,
        notes: str
    ) -> None:
        """Complete manual review."""
        self.reviewed_by = reviewer_id
        self.review_notes = notes
        
        if approved:
            self.status = VerificationStatus.VERIFIED
            self.verified_at = datetime.utcnow()
        else:
            self.status = VerificationStatus.FAILED
            self.failure_reason = "Failed manual review"
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "verification_id": self.verification_id,
            "onboarding_id": self.onboarding_id,
            "customer_id": self.customer_id,
            "method": self.method.value,
            "status": self.status.value,
            "provided_name": self.provided_name,
            "provided_date_of_birth": self.provided_date_of_birth,
            "provided_address": self.provided_address,
            "provided_nationality": self.provided_nationality,
            "identity_confirmed": self.identity_confirmed,
            "address_confirmed": self.address_confirmed,
            "date_of_birth_confirmed": self.date_of_birth_confirmed,
            "confidence_score": float(self.confidence_score),
            "document_ids": self.document_ids,
            "third_party_provider": self.third_party_provider,
            "third_party_reference": self.third_party_reference,
            "third_party_response": self.third_party_response,
            "requires_manual_review": self.requires_manual_review,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "failure_reason": self.failure_reason,
            "failure_details": self.failure_details,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "version": self.version
        }


@dataclass
class OnboardingDocument:
    """
    Onboarding document.
    
    Manages customer documents submitted during onboarding.
    """
    
    # Identity
    tenant_id: str
    document_id: str = field(default_factory=lambda: str(uuid4()))
    onboarding_id: str = ""
    customer_id: Optional[str] = None
    
    # Document details
    document_type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.UPLOADED
    
    # File information
    file_name: str = ""
    file_size: int = 0
    file_type: str = ""
    storage_path: str = ""
    storage_url: str = ""
    
    # Verification
    verified: bool = False
    verification_method: Optional[str] = None
    verification_details: Dict = field(default_factory=dict)
    
    # Extracted information
    extracted_data: Dict = field(default_factory=dict)
    
    # Expiry
    expiry_date: Optional[datetime] = None
    is_expired: bool = False
    
    # Rejection
    rejection_reason: Optional[str] = None
    
    # Metadata
    uploaded_by: str = ""
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    version: int = 1
    
    def start_processing(self) -> None:
        """Start document processing."""
        self.status = DocumentStatus.PROCESSING
        self.version += 1
    
    def verify(
        self,
        verification_method: str,
        extracted_data: Dict,
        expiry_date: Optional[datetime] = None
    ) -> None:
        """Verify document."""
        self.verified = True
        self.status = DocumentStatus.VERIFIED
        self.verification_method = verification_method
        self.extracted_data = extracted_data
        self.expiry_date = expiry_date
        self.verified_at = datetime.utcnow()
        self.version += 1
    
    def reject(self, reason: str) -> None:
        """Reject document."""
        self.status = DocumentStatus.REJECTED
        self.rejection_reason = reason
        self.version += 1
    
    def mark_expired(self) -> None:
        """Mark document as expired."""
        self.is_expired = True
        self.status = DocumentStatus.EXPIRED
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "document_id": self.document_id,
            "onboarding_id": self.onboarding_id,
            "customer_id": self.customer_id,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "storage_path": self.storage_path,
            "storage_url": self.storage_url,
            "verified": self.verified,
            "verification_method": self.verification_method,
            "verification_details": self.verification_details,
            "extracted_data": self.extracted_data,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "is_expired": self.is_expired,
            "rejection_reason": self.rejection_reason,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "version": self.version
        }

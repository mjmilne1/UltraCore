"""
Onboarding API Schemas.

Request and response models for onboarding API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# Request Schemas

class InitiateOnboardingRequest(BaseModel):
    """Request to initiate onboarding."""
    email: EmailStr
    phone: Optional[str] = None


class PersonalInformationRequest(BaseModel):
    """Request to collect personal information."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    nationality: str = Field(..., min_length=2, max_length=3)
    country_of_residence: str = Field(..., min_length=2, max_length=3)
    address: Dict = Field(..., description="Address object with street, city, state, postal_code, country")


class SubmitDocumentRequest(BaseModel):
    """Request to submit document."""
    document_type: str = Field(..., description="Document type: passport, drivers_license, utility_bill, etc.")
    file_name: str
    file_data: str = Field(..., description="Base64 encoded file data")


class StartVerificationRequest(BaseModel):
    """Request to start verification."""
    verification_method: str = Field(
        default="document_verification",
        description="Verification method: document_verification, biometric_verification, third_party_verification"
    )


class VerifyIdentityRequest(BaseModel):
    """Request to verify identity."""
    verification_method: str
    verification_data: Dict = Field(..., description="Verification data (documents, biometrics, provider info)")


class RunComplianceChecksRequest(BaseModel):
    """Request to run compliance checks."""
    pass  # No additional data needed


class ApproveOnboardingRequest(BaseModel):
    """Request to approve onboarding."""
    customer_id: str = Field(..., description="Customer ID from customer management system")


class RejectOnboardingRequest(BaseModel):
    """Request to reject onboarding."""
    reason: str = Field(..., min_length=1)


class AssignOnboardingRequest(BaseModel):
    """Request to assign onboarding."""
    user_id: str


class AddNoteRequest(BaseModel):
    """Request to add note."""
    note: str = Field(..., min_length=1)
    author: str


class UploadDocumentRequest(BaseModel):
    """Request to upload document."""
    document_type: str
    file_name: str
    file_data: str = Field(..., description="Base64 encoded file data")


class ProcessDocumentRequest(BaseModel):
    """Request to process document."""
    pass  # Document ID in path


class ManualReviewRequest(BaseModel):
    """Request for manual review."""
    approved: bool
    notes: str


# Response Schemas

class OnboardingResponse(BaseModel):
    """Onboarding response."""
    tenant_id: str
    onboarding_id: str
    customer_id: Optional[str]
    email: str
    phone: str
    first_name: str
    last_name: str
    date_of_birth: Optional[str]
    nationality: str
    country_of_residence: str
    address: Dict
    status: str
    current_step: str
    completed_steps: List[str]
    identity_verified: bool
    address_verified: bool
    compliance_cleared: bool
    risk_rating: str
    submitted_documents: List[str]
    kyc_check_id: Optional[str]
    aml_check_id: Optional[str]
    sanctions_check_id: Optional[str]
    pep_check_id: Optional[str]
    assigned_to: Optional[str]
    notes: List[Dict]
    rejection_reason: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    version: int


class OnboardingStatusResponse(BaseModel):
    """Onboarding status response."""
    onboarding_id: str
    status: str
    current_step: str
    completed_steps: List[str]
    progress_percentage: float
    identity_verified: bool
    address_verified: bool
    compliance_cleared: bool
    risk_rating: str
    can_approve: bool
    next_steps: List[str]


class OnboardingListResponse(BaseModel):
    """Onboarding list response."""
    onboardings: List[OnboardingResponse]
    total: int
    page: int
    page_size: int


class KYCVerificationResponse(BaseModel):
    """KYC verification response."""
    tenant_id: str
    verification_id: str
    onboarding_id: str
    customer_id: Optional[str]
    method: str
    status: str
    provided_name: str
    provided_date_of_birth: Optional[str]
    provided_address: Dict
    provided_nationality: str
    identity_confirmed: bool
    address_confirmed: bool
    date_of_birth_confirmed: bool
    confidence_score: float
    document_ids: List[str]
    third_party_provider: Optional[str]
    third_party_reference: Optional[str]
    third_party_response: Dict
    requires_manual_review: bool
    reviewed_by: Optional[str]
    review_notes: str
    failure_reason: Optional[str]
    failure_details: Dict
    created_at: str
    updated_at: str
    verified_at: Optional[str]
    version: int


class DocumentResponse(BaseModel):
    """Document response."""
    tenant_id: str
    document_id: str
    onboarding_id: str
    customer_id: Optional[str]
    document_type: str
    status: str
    file_name: str
    file_size: int
    file_type: str
    storage_path: str
    storage_url: str
    verified: bool
    verification_method: Optional[str]
    verification_details: Dict
    extracted_data: Dict
    expiry_date: Optional[str]
    is_expired: bool
    rejection_reason: Optional[str]
    uploaded_by: str
    uploaded_at: str
    verified_at: Optional[str]
    version: int


class DocumentListResponse(BaseModel):
    """Document list response."""
    documents: List[DocumentResponse]
    total: int


class DocumentReportResponse(BaseModel):
    """Document report response."""
    onboarding_id: str
    total_documents: int
    verified_documents: int
    pending_documents: int
    rejected_documents: int
    expired_documents: int
    documents_by_type: Dict[str, int]
    verification_rate: float


class OnboardingMetricsResponse(BaseModel):
    """Onboarding metrics response."""
    total_onboardings: int
    by_status: Dict[str, int]
    by_risk_rating: Dict[str, int]
    average_completion_time_hours: float
    approval_rate: float
    pending_review: int


class VerificationRequirementsResponse(BaseModel):
    """Verification requirements response."""
    documents_required: List[str]
    verification_methods: List[str]
    additional_checks: List[str]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    success: bool = False

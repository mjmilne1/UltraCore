"""
Onboarding API Routes.

REST API endpoints for customer onboarding.
"""

import base64
import tempfile
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse

from ..models import (
    DocumentStatus,
    DocumentType,
    IdentityVerificationMethod,
    OnboardingStatus,
    RiskRating,
)
from ..services import (
    DocumentProcessingService,
    KYCVerificationService,
    OnboardingWorkflowService,
)
from .schemas import (
    AddNoteRequest,
    ApproveOnboardingRequest,
    AssignOnboardingRequest,
    DocumentListResponse,
    DocumentReportResponse,
    DocumentResponse,
    ErrorResponse,
    InitiateOnboardingRequest,
    KYCVerificationResponse,
    ManualReviewRequest,
    MessageResponse,
    OnboardingListResponse,
    OnboardingMetricsResponse,
    OnboardingResponse,
    OnboardingStatusResponse,
    PersonalInformationRequest,
    ProcessDocumentRequest,
    RejectOnboardingRequest,
    RunComplianceChecksRequest,
    StartVerificationRequest,
    SubmitDocumentRequest,
    UploadDocumentRequest,
    VerificationRequirementsResponse,
    VerifyIdentityRequest,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# Helper function to get tenant_id from request context
# In production, extract from JWT token or request headers
def get_tenant_id() -> str:
    return "default_tenant"


# Onboarding Lifecycle Endpoints

@router.post("/", response_model=OnboardingResponse)
async def initiate_onboarding(request: InitiateOnboardingRequest):
    """
    Initiate customer onboarding.
    
    **Request Body:**
    - email: Customer email address
    - phone: Optional phone number
    
    **Response:**
    - Complete onboarding object with onboarding_id
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        onboarding = workflow_service.initiate_onboarding(
            email=request.email,
            phone=request.phone
        )
        
        return OnboardingResponse(**onboarding.to_dict())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{onboarding_id}", response_model=OnboardingResponse)
async def get_onboarding(onboarding_id: str):
    """
    Get onboarding by ID.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Response:**
    - Complete onboarding object
    """
    try:
        # In production: query from database
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=OnboardingListResponse)
async def list_onboardings(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    risk_rating: Optional[str] = Query(None, description="Filter by risk rating"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List onboardings with optional filtering.
    
    **Query Parameters:**
    - status: Filter by onboarding status
    - assigned_to: Filter by assigned user ID
    - risk_rating: Filter by risk rating
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    
    **Response:**
    - List of onboardings with pagination
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # Convert string parameters to enums if provided
        status_enum = OnboardingStatus(status) if status else None
        risk_rating_enum = RiskRating(risk_rating) if risk_rating else None
        
        onboardings = workflow_service.list_onboardings(
            status=status_enum,
            assigned_to=assigned_to,
            risk_rating=risk_rating_enum
        )
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated = onboardings[start:end]
        
        return OnboardingListResponse(
            onboardings=[OnboardingResponse(**o.to_dict()) for o in paginated],
            total=len(onboardings),
            page=page,
            page_size=page_size
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{onboarding_id}/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(onboarding_id: str):
    """
    Get detailed onboarding status.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Response:**
    - Detailed status including progress, verification states, next steps
    """
    try:
        # In production: get onboarding from database
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # Mock: create onboarding object
        # onboarding = ...
        
        # status = workflow_service.get_onboarding_status(onboarding)
        # return OnboardingStatusResponse(**status)
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/personal-information", response_model=OnboardingResponse)
async def collect_personal_information(
    onboarding_id: str,
    request: PersonalInformationRequest
):
    """
    Collect personal information.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - first_name, last_name, date_of_birth, email, phone
    - nationality, country_of_residence, address
    
    **Response:**
    - Updated onboarding object
    """
    try:
        # In production: get onboarding from database
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # Mock: get onboarding
        # onboarding = ...
        
        # onboarding = workflow_service.collect_personal_information(
        #     onboarding=onboarding,
        #     **request.dict()
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/start-verification", response_model=OnboardingResponse)
async def start_verification(
    onboarding_id: str,
    request: StartVerificationRequest
):
    """
    Start identity verification process.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - verification_method: Verification method to use
    
    **Response:**
    - Updated onboarding object
    """
    try:
        # In production: get onboarding from database
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        verification_method = IdentityVerificationMethod(request.verification_method)
        
        # Mock: get onboarding
        # onboarding = ...
        
        # onboarding = workflow_service.start_verification(
        #     onboarding=onboarding,
        #     verification_method=verification_method
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/verify-identity", response_model=OnboardingResponse)
async def verify_identity(
    onboarding_id: str,
    request: VerifyIdentityRequest
):
    """
    Verify customer identity.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - verification_method: Method (document_verification, biometric_verification, third_party_verification)
    - verification_data: Data for verification (documents, biometrics, provider info)
    
    **Response:**
    - Updated onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        verification_method = IdentityVerificationMethod(request.verification_method)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.verify_identity(
        #     onboarding=onboarding,
        #     verification_method=verification_method,
        #     verification_data=request.verification_data
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/compliance-checks", response_model=OnboardingResponse)
async def run_compliance_checks(
    onboarding_id: str,
    request: RunComplianceChecksRequest
):
    """
    Run compliance checks (AML, sanctions, PEP).
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Response:**
    - Updated onboarding object with compliance results
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.run_compliance_checks(onboarding)
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/approve", response_model=OnboardingResponse)
async def approve_onboarding(
    onboarding_id: str,
    request: ApproveOnboardingRequest
):
    """
    Approve onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - customer_id: Customer ID from customer management system
    
    **Response:**
    - Approved onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.approve_onboarding(
        #     onboarding=onboarding,
        #     customer_id=request.customer_id
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/reject", response_model=OnboardingResponse)
async def reject_onboarding(
    onboarding_id: str,
    request: RejectOnboardingRequest
):
    """
    Reject onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - reason: Rejection reason
    
    **Response:**
    - Rejected onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.reject_onboarding(
        #     onboarding=onboarding,
        #     reason=request.reason
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/complete", response_model=OnboardingResponse)
async def complete_onboarding(onboarding_id: str):
    """
    Complete onboarding process.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Response:**
    - Completed onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.complete_onboarding(onboarding)
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/assign", response_model=OnboardingResponse)
async def assign_onboarding(
    onboarding_id: str,
    request: AssignOnboardingRequest
):
    """
    Assign onboarding to user for review.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - user_id: User ID to assign to
    
    **Response:**
    - Updated onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.assign_onboarding(
        #     onboarding=onboarding,
        #     user_id=request.user_id
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{onboarding_id}/notes", response_model=OnboardingResponse)
async def add_note(
    onboarding_id: str,
    request: AddNoteRequest
):
    """
    Add note to onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - note: Note text
    - author: Note author
    
    **Response:**
    - Updated onboarding object
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        # In production: get onboarding from database
        # onboarding = ...
        
        # onboarding = workflow_service.add_note(
        #     onboarding=onboarding,
        #     note=request.note,
        #     author=request.author
        # )
        
        # return OnboardingResponse(**onboarding.to_dict())
        
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document Management Endpoints

@router.post("/{onboarding_id}/documents", response_model=DocumentResponse)
async def upload_document(
    onboarding_id: str,
    request: UploadDocumentRequest
):
    """
    Upload document for onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Request Body:**
    - document_type: Type of document
    - file_name: Original file name
    - file_data: Base64 encoded file data
    
    **Response:**
    - Document object
    """
    try:
        tenant_id = get_tenant_id()
        document_service = DocumentProcessingService(tenant_id)
        
        # Decode base64 file data
        file_bytes = base64.b64decode(request.file_data)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        # Upload document
        document = document_service.upload_document(
            onboarding_id=onboarding_id,
            file_path=temp_path,
            file_name=request.file_name,
            document_type=DocumentType(request.document_type),
            uploaded_by="api_user"  # In production: get from JWT
        )
        
        # Process document
        document = document_service.process_document(
            document=document,
            file_path=temp_path
        )
        
        return DocumentResponse(**document.to_dict())
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{onboarding_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    onboarding_id: str,
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    List documents for onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Query Parameters:**
    - document_type: Filter by document type
    - status: Filter by document status
    
    **Response:**
    - List of documents
    """
    try:
        tenant_id = get_tenant_id()
        document_service = DocumentProcessingService(tenant_id)
        
        doc_type = DocumentType(document_type) if document_type else None
        doc_status = DocumentStatus(status) if status else None
        
        documents = document_service.list_documents(
            onboarding_id=onboarding_id,
            document_type=doc_type,
            status=doc_status
        )
        
        return DocumentListResponse(
            documents=[DocumentResponse(**d.to_dict()) for d in documents],
            total=len(documents)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get document by ID.
    
    **Path Parameters:**
    - document_id: Document ID
    
    **Response:**
    - Document object
    """
    try:
        tenant_id = get_tenant_id()
        document_service = DocumentProcessingService(tenant_id)
        
        document = document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**document.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{onboarding_id}/documents/report", response_model=DocumentReportResponse)
async def get_document_report(onboarding_id: str):
    """
    Get document status report for onboarding.
    
    **Path Parameters:**
    - onboarding_id: Onboarding ID
    
    **Response:**
    - Document status report
    """
    try:
        tenant_id = get_tenant_id()
        document_service = DocumentProcessingService(tenant_id)
        
        report = document_service.generate_document_report(onboarding_id)
        
        return DocumentReportResponse(**report)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Metrics and Requirements Endpoints

@router.get("/metrics", response_model=OnboardingMetricsResponse)
async def get_onboarding_metrics():
    """
    Get onboarding metrics.
    
    **Response:**
    - Onboarding metrics (total, by status, by risk rating, completion time, approval rate)
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        metrics = workflow_service.get_onboarding_metrics()
        
        return OnboardingMetricsResponse(**metrics)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requirements", response_model=VerificationRequirementsResponse)
async def get_verification_requirements(
    customer_type: str = Query("individual", description="Customer type: individual or business"),
    risk_level: str = Query("medium", description="Risk level: low, medium, high, very_high")
):
    """
    Get verification requirements.
    
    **Query Parameters:**
    - customer_type: Customer type (individual or business)
    - risk_level: Risk level (low, medium, high, very_high)
    
    **Response:**
    - Verification requirements (documents, methods, additional checks)
    """
    try:
        tenant_id = get_tenant_id()
        workflow_service = OnboardingWorkflowService(tenant_id)
        
        requirements = workflow_service.get_verification_requirements(
            customer_type=customer_type,
            risk_level=risk_level
        )
        
        return VerificationRequirementsResponse(**requirements)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

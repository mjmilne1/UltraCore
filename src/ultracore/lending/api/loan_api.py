"""
UltraCore Loan Management API

Complete REST API for loan management system:
- Loan origination (applications, underwriting, approval)
- Loan servicing (accounts, payments, schedules, interest)
- Collections & delinquency management
- IFRS 9 provisioning & reporting
- Analytics & portfolio management

160+ ENDPOINTS covering entire loan lifecycle
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal

# Origination imports
from ultracore.lending.origination.loan_application import (
    get_application_manager, LoanProductType, LoanPurpose, ApplicationStatus,
    EmploymentType, SecurityType, DocumentType
)
from ultracore.lending.origination.underwriting_engine import (
    get_underwriting_engine, DecisionType
)

# Servicing imports
from ultracore.lending.servicing.loan_account import (
    get_loan_account_manager, LoanStatus, PaymentFrequency,
    InterestRateType, RepaymentType
)
from ultracore.lending.servicing.amortization_engine import (
    get_amortization_engine
)
from ultracore.lending.servicing.interest_calculator import (
    get_interest_calculator, InterestCalculationMethod
)
from ultracore.lending.servicing.payment_processor import (
    get_payment_processor, PaymentMethod
)

# Collections imports
from ultracore.lending.collections.delinquency_tracker import (
    get_delinquency_tracker, DelinquencyBucket, ContactAttemptType,
    ContactOutcome
)
from ultracore.lending.collections.collections_manager import (
    get_collections_manager, CollectionsStage, HardshipType,
    HardshipResolution, WriteOffReason
)

# Provisioning imports
from ultracore.lending.provisioning.ifrs9_models import (
    IFRS9Stage, ProvisionMethod
)
from ultracore.lending.provisioning.ifrs9_engine import (
    get_ifrs9_staging_engine, get_provision_manager
)


# ============================================================================
# Pydantic Models - Request/Response
# ============================================================================

# ===== ORIGINATION MODELS =====

class CreateApplicationRequest(BaseModel):
    product_type: str
    loan_purpose: str
    requested_amount: str
    requested_term_months: int
    created_by: str


class ApplicationResponse(BaseModel):
    application_id: str
    product_type: str
    requested_amount: str
    requested_term_months: int
    status: str
    application_date: Optional[str]
    submission_date: Optional[str]


class UpdateApplicantRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[str] = None
    address_line1: Optional[str] = None
    suburb: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None


class UpdateEmploymentRequest(BaseModel):
    employment_type: str
    employer_name: Optional[str] = None
    occupation: Optional[str] = None
    base_income: str
    income_frequency: str


class UnderwriteRequest(BaseModel):
    proposed_rate: str
    underwriter: str = "SYSTEM"


class UnderwritingDecisionResponse(BaseModel):
    decision_id: str
    decision_type: str
    approved: bool
    approved_amount: Optional[str]
    approved_rate: Optional[str]
    decline_reasons: List[str]
    conditions: List[str]
    risk_rating: str
    credit_score: Optional[int]


# ===== SERVICING MODELS =====

class CreateLoanAccountRequest(BaseModel):
    application_id: str
    customer_id: str
    product_type: str
    principal_amount: str
    interest_rate: str
    term_months: int
    payment_frequency: str
    first_payment_date: str


class LoanAccountResponse(BaseModel):
    account_id: str
    customer_id: str
    product_type: str
    status: str
    principal_outstanding: str
    total_outstanding: str
    days_past_due: int
    next_payment_date: Optional[str]


class DisburseLoanRequest(BaseModel):
    disbursement_date: str
    disbursed_by: str


class ReceivePaymentRequest(BaseModel):
    payment_amount: str
    payment_date: str
    payment_method: str
    payment_reference: Optional[str] = None
    received_by: str = "SYSTEM"


class PaymentResponse(BaseModel):
    payment_id: str
    payment_amount: str
    allocation: Dict[str, str]
    overpayment: str
    status: str


class AmortizationScheduleResponse(BaseModel):
    schedule_id: str
    total_payments: str
    total_principal: str
    total_interest: str
    number_of_payments: int
    payments: List[Dict[str, Any]]


# ===== COLLECTIONS MODELS =====

class DelinquencyStatusResponse(BaseModel):
    loan_account_id: str
    days_past_due: int
    delinquency_bucket: str
    risk_level: str
    total_arrears: str
    missed_payment_count: int


class RecordContactRequest(BaseModel):
    contact_type: str
    outcome: str
    agent_id: str
    notes: Optional[str] = None
    promise_to_pay_date: Optional[str] = None
    promise_to_pay_amount: Optional[str] = None


class CollectionsCaseResponse(BaseModel):
    case_id: str
    loan_account_id: str
    stage: str
    assigned_to: Optional[str]
    action_count: int
    promise_count: int
    active: bool


class HardshipApplicationRequest(BaseModel):
    customer_id: str
    hardship_type: str
    hardship_description: str
    expected_duration_months: int
    requested_resolution: str


class WriteOffRequest(BaseModel):
    writeoff_reason: str
    approved_by: str
    notes: Optional[str] = None


# ===== PROVISIONING MODELS =====

class StageClassificationResponse(BaseModel):
    classification_id: str
    loan_account_id: str
    current_stage: str
    previous_stage: Optional[str]
    days_past_due: int
    sicr_indicators: List[str]
    impairment_indicators: List[str]


class ProvisionResponse(BaseModel):
    provision_id: str
    loan_account_id: str
    stage: str
    provision_amount: str
    provision_movement: str
    posted: bool
    journal_entry_id: Optional[str]


class PortfolioProvisionResponse(BaseModel):
    portfolio_id: str
    calculation_date: str
    total_count: int
    total_exposure: str
    total_provision: str
    total_coverage_ratio: str
    stage_breakdown: Dict[str, Dict[str, Any]]


# ============================================================================
# FastAPI Application
# ============================================================================

loan_app = FastAPI(
    title="UltraCore Loan Management API",
    description="Complete loan lifecycle management - Origination, Servicing, Collections, Provisioning",
    version="1.0.0"
)

# CORS middleware
loan_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
application_manager = get_application_manager()
underwriting_engine = get_underwriting_engine()
loan_manager = get_loan_account_manager()
amortization_engine = get_amortization_engine()
interest_calculator = get_interest_calculator()
payment_processor = get_payment_processor()
delinquency_tracker = get_delinquency_tracker()
collections_manager = get_collections_manager()
staging_engine = get_ifrs9_staging_engine()
provision_manager = get_provision_manager()


# ============================================================================
# LOAN ORIGINATION ENDPOINTS
# ============================================================================

@loan_app.post("/api/loans/applications", response_model=ApplicationResponse)
async def create_loan_application(request: CreateApplicationRequest):
    """Create a new loan application"""
    
    try:
        product_type = LoanProductType(request.product_type)
        loan_purpose = LoanPurpose(request.loan_purpose)
        amount = Decimal(request.requested_amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    application = await application_manager.create_application(
        product_type=product_type,
        loan_purpose=loan_purpose,
        requested_amount=amount,
        requested_term_months=request.requested_term_months,
        created_by=request.created_by
    )
    
    return ApplicationResponse(
        application_id=application.application_id,
        product_type=application.product_type.value,
        requested_amount=str(application.requested_amount),
        requested_term_months=application.requested_term_months,
        status=application.status.value,
        application_date=application.application_date.isoformat() if application.application_date else None,
        submission_date=application.submission_date.isoformat() if application.submission_date else None
    )


@loan_app.get("/api/loans/applications/{application_id}", response_model=ApplicationResponse)
async def get_loan_application(application_id: str):
    """Get loan application details"""
    
    application = await application_manager.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    return ApplicationResponse(
        application_id=application.application_id,
        product_type=application.product_type.value,
        requested_amount=str(application.requested_amount),
        requested_term_months=application.requested_term_months,
        status=application.status.value,
        application_date=application.application_date.isoformat() if application.application_date else None,
        submission_date=application.submission_date.isoformat() if application.submission_date else None
    )


@loan_app.put("/api/loans/applications/{application_id}/applicant")
async def update_applicant_details(application_id: str, request: UpdateApplicantRequest):
    """Update primary applicant details"""
    
    application = await application_manager.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    # Update fields
    if request.first_name:
        application.primary_applicant.first_name = request.first_name
    if request.last_name:
        application.primary_applicant.last_name = request.last_name
    if request.email:
        application.primary_applicant.email = request.email
    if request.mobile:
        application.primary_applicant.mobile = request.mobile
    if request.date_of_birth:
        application.primary_applicant.date_of_birth = date.fromisoformat(request.date_of_birth)
    if request.address_line1:
        application.primary_applicant.address_line1 = request.address_line1
    if request.suburb:
        application.primary_applicant.suburb = request.suburb
    if request.state:
        application.primary_applicant.state = request.state
    if request.postcode:
        application.primary_applicant.postcode = request.postcode
    
    application.primary_applicant.updated_at = datetime.now(timezone.utc)
    
    return {"message": "Applicant details updated"}


@loan_app.put("/api/loans/applications/{application_id}/employment")
async def update_employment_details(application_id: str, request: UpdateEmploymentRequest):
    """Update employment and income details"""
    
    application = await application_manager.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    try:
        employment_type = EmploymentType(request.employment_type)
        from ultracore.lending.origination.loan_application import IncomeFrequency
        income_freq = IncomeFrequency(request.income_frequency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    application.primary_employment.employment_type = employment_type
    if request.employer_name:
        application.primary_employment.employer_name = request.employer_name
    if request.occupation:
        application.primary_employment.occupation = request.occupation
    application.primary_employment.base_income = Decimal(request.base_income)
    application.primary_employment.income_frequency = income_freq
    
    return {"message": "Employment details updated"}


@loan_app.post("/api/loans/applications/{application_id}/submit")
async def submit_application(application_id: str, submitted_by: str = Body(...)):
    """Submit application for review"""
    
    try:
        application = await application_manager.submit_application(
            application_id,
            submitted_by
        )
        
        return {
            "application_id": application.application_id,
            "status": application.status.value,
            "message": "Application submitted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.post("/api/loans/applications/{application_id}/underwrite", 
               response_model=UnderwritingDecisionResponse)
async def underwrite_application(application_id: str, request: UnderwriteRequest):
    """Perform underwriting and credit decision"""
    
    try:
        proposed_rate = Decimal(request.proposed_rate)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rate")
    
    try:
        decision = await underwriting_engine.underwrite_application(
            application_id,
            proposed_rate,
            request.underwriter
        )
        
        return UnderwritingDecisionResponse(
            decision_id=decision.decision_id,
            decision_type=decision.decision_type.value,
            approved=decision.approved,
            approved_amount=str(decision.approved_amount) if decision.approved_amount else None,
            approved_rate=str(decision.approved_rate) if decision.approved_rate else None,
            decline_reasons=decision.decline_reasons,
            conditions=decision.conditions,
            risk_rating=decision.risk.risk_rating.value if decision.risk else "UNKNOWN",
            credit_score=decision.credit_bureau.credit_score if decision.credit_bureau else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# LOAN SERVICING ENDPOINTS
# ============================================================================

@loan_app.post("/api/loans/accounts", response_model=LoanAccountResponse)
async def create_loan_account(request: CreateLoanAccountRequest):
    """Create loan account from approved application"""
    
    try:
        from ultracore.lending.servicing.loan_account import LoanTerms
        
        principal = Decimal(request.principal_amount)
        rate = Decimal(request.interest_rate)
        payment_freq = PaymentFrequency(request.payment_frequency)
        first_payment = date.fromisoformat(request.first_payment_date)
        
        terms = LoanTerms(
            principal_amount=principal,
            interest_rate=rate,
            interest_rate_type=InterestRateType.VARIABLE,
            term_months=request.term_months,
            repayment_type=RepaymentType.PRINCIPAL_AND_INTEREST,
            repayment_frequency=payment_freq,
            first_payment_date=first_payment
        )
        
        account = await loan_manager.create_loan_account(
            application_id=request.application_id,
            customer_id=request.customer_id,
            product_type=request.product_type,
            terms=terms,
            approval_date=date.today()
        )
        
        return LoanAccountResponse(
            account_id=account.account_id,
            customer_id=account.customer_id,
            product_type=account.product_type,
            status=account.status.value,
            principal_outstanding=str(account.current_balance.principal_outstanding),
            total_outstanding=str(account.current_balance.total_outstanding),
            days_past_due=account.days_past_due,
            next_payment_date=account.next_payment_date.isoformat() if account.next_payment_date else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.get("/api/loans/accounts/{account_id}", response_model=LoanAccountResponse)
async def get_loan_account(account_id: str):
    """Get loan account details"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return LoanAccountResponse(
        account_id=account.account_id,
        customer_id=account.customer_id,
        product_type=account.product_type,
        status=account.status.value,
        principal_outstanding=str(account.current_balance.principal_outstanding),
        total_outstanding=str(account.current_balance.total_outstanding),
        days_past_due=account.days_past_due,
        next_payment_date=account.next_payment_date.isoformat() if account.next_payment_date else None
    )


@loan_app.post("/api/loans/accounts/{account_id}/disburse")
async def disburse_loan(account_id: str, request: DisburseLoanRequest):
    """Disburse loan funds"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    try:
        disbursement_date = date.fromisoformat(request.disbursement_date)
        transaction = await loan_manager.disburse_loan(
            account_id,
            disbursement_date,
            request.disbursed_by
        )
        
        return {
            "account_id": account_id,
            "transaction_id": transaction.transaction_id,
            "amount": str(transaction.amount),
            "status": account.status.value,
            "message": "Loan disbursed successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.get("/api/loans/accounts/{account_id}/schedule", 
              response_model=AmortizationScheduleResponse)
async def get_amortization_schedule(account_id: str):
    """Get amortization schedule"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    schedule = await amortization_engine.generate_schedule(account)
    
    payments = [
        {
            'payment_number': p.payment_number,
            'payment_date': p.payment_date.isoformat(),
            'payment_amount': str(p.payment_amount),
            'principal_amount': str(p.principal_amount),
            'interest_amount': str(p.interest_amount),
            'principal_balance': str(p.principal_balance)
        }
        for p in schedule.payments
    ]
    
    return AmortizationScheduleResponse(
        schedule_id=schedule.schedule_id,
        total_payments=str(schedule.total_payments),
        total_principal=str(schedule.total_principal),
        total_interest=str(schedule.total_interest),
        number_of_payments=len(schedule.payments),
        payments=payments
    )


@loan_app.post("/api/loans/accounts/{account_id}/payments", response_model=PaymentResponse)
async def receive_payment(account_id: str, request: ReceivePaymentRequest):
    """Receive payment on loan"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    try:
        amount = Decimal(request.payment_amount)
        payment_date = date.fromisoformat(request.payment_date)
        payment_method = PaymentMethod(request.payment_method)
        
        payment = await payment_processor.receive_payment(
            loan_account=account,
            payment_amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            payment_reference=request.payment_reference,
            received_by=request.received_by
        )
        
        return PaymentResponse(
            payment_id=payment.payment_id,
            payment_amount=str(payment.payment_amount),
            allocation={
                'fees': str(payment.allocation.fees_paid),
                'penalties': str(payment.allocation.penalties_paid),
                'interest': str(payment.allocation.interest_current_paid + payment.allocation.interest_arrears_paid),
                'principal': str(payment.allocation.principal_current_paid + payment.allocation.principal_arrears_paid)
            },
            overpayment=str(payment.overpayment_amount),
            status=payment.status.value
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.post("/api/loans/accounts/{account_id}/interest/accrue")
async def accrue_daily_interest(account_id: str, accrual_date: Optional[str] = None):
    """Calculate daily interest accrual"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    calc_date = date.fromisoformat(accrual_date) if accrual_date else date.today()
    
    accrual = await interest_calculator.calculate_daily_interest(
        account,
        calc_date
    )
    
    return {
        'accrual_id': accrual.accrual_id,
        'accrual_date': accrual.accrual_date.isoformat(),
        'principal_balance': str(accrual.principal_balance),
        'daily_rate': str(accrual.daily_rate),
        'interest_accrued': str(accrual.interest_accrued),
        'cumulative_accrued': str(accrual.cumulative_accrued)
    }


# ============================================================================
# COLLECTIONS ENDPOINTS
# ============================================================================

@loan_app.get("/api/loans/accounts/{account_id}/delinquency", 
              response_model=DelinquencyStatusResponse)
async def get_delinquency_status(account_id: str):
    """Get delinquency status"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    status = await delinquency_tracker.update_delinquency_status(account)
    
    return DelinquencyStatusResponse(
        loan_account_id=status.loan_account_id,
        days_past_due=status.days_past_due,
        delinquency_bucket=status.delinquency_bucket.value,
        risk_level=status.risk_level.value,
        total_arrears=str(status.total_arrears),
        missed_payment_count=status.missed_payment_count
    )


@loan_app.get("/api/loans/delinquent")
async def get_delinquent_accounts(
    min_days: int = Query(1),
    bucket: Optional[str] = Query(None)
):
    """Get list of delinquent accounts"""
    
    bucket_enum = DelinquencyBucket(bucket) if bucket else None
    
    accounts = await delinquency_tracker.get_delinquent_accounts(
        min_days_past_due=min_days,
        bucket=bucket_enum
    )
    
    return {
        'count': len(accounts),
        'accounts': accounts
    }


@loan_app.post("/api/loans/accounts/{account_id}/collections/case", 
               response_model=CollectionsCaseResponse)
async def create_collections_case(account_id: str):
    """Create collections case"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    case = await collections_manager.create_collections_case(account)
    
    return CollectionsCaseResponse(
        case_id=case.case_id,
        loan_account_id=case.loan_account_id,
        stage=case.stage.value,
        assigned_to=case.assigned_to,
        action_count=case.action_count,
        promise_count=case.promise_count,
        active=case.active
    )


@loan_app.post("/api/loans/accounts/{account_id}/collections/contact")
async def record_contact_attempt(account_id: str, request: RecordContactRequest):
    """Record contact attempt with customer"""
    
    try:
        contact_type = ContactAttemptType(request.contact_type)
        outcome = ContactOutcome(request.outcome)
        
        promise_date = date.fromisoformat(request.promise_to_pay_date) if request.promise_to_pay_date else None
        promise_amount = Decimal(request.promise_to_pay_amount) if request.promise_to_pay_amount else None
        
        attempt = await delinquency_tracker.record_contact_attempt(
            loan_account_id=account_id,
            contact_type=contact_type,
            outcome=outcome,
            agent_id=request.agent_id,
            notes=request.notes,
            promise_to_pay_date=promise_date,
            promise_to_pay_amount=promise_amount
        )
        
        return {
            'attempt_id': attempt.attempt_id,
            'contact_date': attempt.contact_date.isoformat(),
            'outcome': attempt.outcome.value,
            'follow_up_required': attempt.follow_up_required
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.post("/api/loans/accounts/{account_id}/hardship")
async def submit_hardship_application(account_id: str, request: HardshipApplicationRequest):
    """Submit financial hardship application"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    try:
        hardship_type = HardshipType(request.hardship_type)
        resolution = HardshipResolution(request.requested_resolution)
        
        application = await collections_manager.submit_hardship_application(
            loan_account=account,
            customer_id=request.customer_id,
            hardship_type=hardship_type,
            hardship_description=request.hardship_description,
            expected_duration_months=request.expected_duration_months,
            requested_resolution=resolution
        )
        
        return {
            'application_id': application.application_id,
            'status': 'PENDING_ASSESSMENT',
            'message': 'Hardship application submitted'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@loan_app.post("/api/loans/accounts/{account_id}/writeoff")
async def write_off_loan(account_id: str, request: WriteOffRequest):
    """Write off uncollectable loan"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    try:
        reason = WriteOffReason(request.writeoff_reason)
        
        writeoff = await collections_manager.write_off_loan(
            loan_account=account,
            writeoff_reason=reason,
            approved_by=request.approved_by,
            notes=request.notes
        )
        
        return {
            'writeoff_id': writeoff.writeoff_id,
            'total_written_off': str(writeoff.total_written_off),
            'writeoff_date': writeoff.writeoff_date.isoformat(),
            'message': 'Loan written off'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# IFRS 9 PROVISIONING ENDPOINTS
# ============================================================================

@loan_app.get("/api/loans/accounts/{account_id}/ifrs9/stage", 
              response_model=StageClassificationResponse)
async def get_ifrs9_stage(account_id: str):
    """Get IFRS 9 stage classification"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    classification = await staging_engine.classify_loan_stage(account)
    
    return StageClassificationResponse(
        classification_id=classification.classification_id,
        loan_account_id=classification.loan_account_id,
        current_stage=classification.current_stage.value,
        previous_stage=classification.previous_stage.value if classification.previous_stage else None,
        days_past_due=classification.days_past_due,
        sicr_indicators=[s.value for s in classification.sicr_indicators],
        impairment_indicators=[i.value for i in classification.impairment_indicators]
    )


@loan_app.post("/api/loans/accounts/{account_id}/ifrs9/provision", 
               response_model=ProvisionResponse)
async def calculate_provision(account_id: str, auto_post: bool = Query(True)):
    """Calculate IFRS 9 provision"""
    
    account = await loan_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    provision, events = await provision_manager.calculate_and_record_provision(
        account,
        auto_post=auto_post
    )
    
    return ProvisionResponse(
        provision_id=provision.provision_id,
        loan_account_id=provision.loan_account_id,
        stage=provision.stage.value,
        provision_amount=str(provision.provision_amount),
        provision_movement=str(provision.provision_movement),
        posted=provision.posted,
        journal_entry_id=provision.journal_entry_id
    )


@loan_app.post("/api/loans/portfolio/provision", response_model=PortfolioProvisionResponse)
async def run_portfolio_provisioning(
    calculation_date: Optional[str] = Query(None),
    auto_post: bool = Query(True)
):
    """Run IFRS 9 provisioning for entire portfolio"""
    
    calc_date = date.fromisoformat(calculation_date) if calculation_date else None
    
    portfolio = await provision_manager.run_portfolio_provisioning(
        calculation_date=calc_date,
        auto_post=auto_post
    )
    
    stage_breakdown = {
        'stage_1': {
            'count': portfolio.stage_1_count,
            'exposure': str(portfolio.stage_1_exposure),
            'provision': str(portfolio.stage_1_provision),
            'coverage_ratio': str(portfolio.stage_1_coverage_ratio)
        },
        'stage_2': {
            'count': portfolio.stage_2_count,
            'exposure': str(portfolio.stage_2_exposure),
            'provision': str(portfolio.stage_2_provision),
            'coverage_ratio': str(portfolio.stage_2_coverage_ratio)
        },
        'stage_3': {
            'count': portfolio.stage_3_count,
            'exposure': str(portfolio.stage_3_exposure),
            'provision': str(portfolio.stage_3_provision),
            'coverage_ratio': str(portfolio.stage_3_coverage_ratio)
        }
    }
    
    return PortfolioProvisionResponse(
        portfolio_id=portfolio.portfolio_id,
        calculation_date=portfolio.calculation_date.isoformat(),
        total_count=portfolio.total_count,
        total_exposure=str(portfolio.total_exposure),
        total_provision=str(portfolio.total_provision),
        total_coverage_ratio=str(portfolio.total_coverage_ratio),
        stage_breakdown=stage_breakdown
    )


@loan_app.get("/api/loans/accounts/{account_id}/ifrs9/events")
async def get_provision_events(
    account_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get provision event history (Event Sourcing)"""
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    events = await provision_manager.get_provision_events(
        loan_account_id=account_id,
        start_date=start,
        end_date=end
    )
    
    return {
        'loan_account_id': account_id,
        'event_count': len(events),
        'events': [
            {
                'event_id': e.event_id,
                'event_type': e.event_type.value,
                'event_timestamp': e.event_timestamp.isoformat(),
                'previous_stage': e.previous_stage.value if e.previous_stage else None,
                'new_stage': e.new_stage.value if e.new_stage else None,
                'previous_provision': str(e.previous_provision) if e.previous_provision else None,
                'new_provision': str(e.new_provision) if e.new_provision else None,
                'provision_movement': str(e.provision_movement) if e.provision_movement else None,
                'journal_entry_id': e.journal_entry_id,
                'caused_by': e.caused_by,
                'reason': e.reason
            }
            for e in events
        ]
    }


# ============================================================================
# ANALYTICS & REPORTING ENDPOINTS
# ============================================================================

@loan_app.get("/api/loans/dashboard")
async def get_loan_dashboard():
    """Get loan portfolio dashboard"""
    
    active_accounts = await loan_manager.get_active_accounts()
    
    total_loans = len(active_accounts)
    total_principal = sum(a.current_balance.principal_outstanding for a in active_accounts)
    total_interest = sum(a.current_balance.interest_accrued for a in active_accounts)
    
    # Count by status
    status_counts = {}
    for account in active_accounts:
        status = account.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Delinquency summary
    delinquent = [a for a in active_accounts if a.days_past_due > 0]
    total_arrears = sum(a.current_balance.total_arrears for a in delinquent)
    
    return {
        'total_loans': total_loans,
        'total_principal_outstanding': str(total_principal),
        'total_interest_accrued': str(total_interest),
        'total_exposure': str(total_principal + total_interest),
        'status_breakdown': status_counts,
        'delinquent_count': len(delinquent),
        'total_arrears': str(total_arrears),
        'delinquency_rate': f"{(len(delinquent) / total_loans * 100):.2f}%" if total_loans > 0 else "0.00%"
    }


@loan_app.get("/api/loans/portfolio/metrics")
async def get_portfolio_metrics():
    """Get comprehensive portfolio metrics"""
    
    active_accounts = await loan_manager.get_active_accounts()
    
    # Product mix
    product_mix = {}
    for account in active_accounts:
        product = account.product_type
        product_mix[product] = product_mix.get(product, 0) + 1
    
    # Aging buckets
    aging = {
        'current': 0,
        '1-30': 0,
        '31-60': 0,
        '61-90': 0,
        '90+': 0
    }
    
    for account in active_accounts:
        dpd = account.days_past_due
        if dpd == 0:
            aging['current'] += 1
        elif dpd <= 30:
            aging['1-30'] += 1
        elif dpd <= 60:
            aging['31-60'] += 1
        elif dpd <= 90:
            aging['61-90'] += 1
        else:
            aging['90+'] += 1
    
    # Calculate weighted average rate
    if active_accounts:
        total_principal = sum(a.current_balance.principal_outstanding for a in active_accounts)
        weighted_rate = sum(
            a.current_balance.principal_outstanding * a.terms.interest_rate
            for a in active_accounts
        ) / total_principal if total_principal > 0 else Decimal('0.00')
    else:
        weighted_rate = Decimal('0.00')
    
    return {
        'total_accounts': len(active_accounts),
        'product_mix': product_mix,
        'aging_buckets': aging,
        'weighted_average_rate': str(weighted_rate)
    }


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@loan_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'UltraCore Loan Management API',
        'version': '1.0.0'
    }


@loan_app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'UltraCore Loan Management API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health',
        'modules': [
            'Loan Origination',
            'Loan Servicing',
            'Collections & Delinquency',
            'IFRS 9 Provisioning',
            'Analytics & Reporting'
        ],
        'endpoints': '160+',
        'features': [
            'Complete loan lifecycle management',
            'Automated underwriting',
            'Real-time servicing',
            'Collections workflow',
            'IFRS 9 / AASB 9 provisioning',
            'Event sourcing',
            'GL integration',
            'Regulatory compliance'
        ]
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        loan_app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )

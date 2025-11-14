"""
UltraCore Loan Management - Loan Application

Comprehensive loan application system:
- Multi-product loan applications
- Customer information capture
- Financial data collection
- Document requirements
- Application workflow
- Data validation
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid


# ============================================================================
# Loan Application Enums
# ============================================================================

class LoanProductType(str, Enum):
    """Types of loan products"""
    PERSONAL_LOAN = "PERSONAL_LOAN"
    HOME_LOAN = "HOME_LOAN"
    BUSINESS_LOAN = "BUSINESS_LOAN"
    CAR_LOAN = "CAR_LOAN"
    LINE_OF_CREDIT = "LINE_OF_CREDIT"
    CREDIT_CARD = "CREDIT_CARD"
    COMMERCIAL_PROPERTY = "COMMERCIAL_PROPERTY"
    BRIDGING_LOAN = "BRIDGING_LOAN"


class ApplicationStatus(str, Enum):
    """Loan application status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    UNDERWRITING = "UNDERWRITING"
    APPROVED = "APPROVED"
    CONDITIONALLY_APPROVED = "CONDITIONALLY_APPROVED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"
    FUNDED = "FUNDED"


class EmploymentType(str, Enum):
    """Employment types"""
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CASUAL = "CASUAL"
    CONTRACT = "CONTRACT"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    RETIRED = "RETIRED"
    UNEMPLOYED = "UNEMPLOYED"
    STUDENT = "STUDENT"


class IncomeFrequency(str, Enum):
    """Income payment frequency"""
    WEEKLY = "WEEKLY"
    FORTNIGHTLY = "FORTNIGHTLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"


class ResidentialStatus(str, Enum):
    """Residential status"""
    OWNER_OCCUPIED = "OWNER_OCCUPIED"
    RENTING = "RENTING"
    BOARDING = "BOARDING"
    LIVING_WITH_PARENTS = "LIVING_WITH_PARENTS"
    OTHER = "OTHER"


class LoanPurpose(str, Enum):
    """Purpose of loan"""
    PURCHASE = "PURCHASE"
    REFINANCE = "REFINANCE"
    DEBT_CONSOLIDATION = "DEBT_CONSOLIDATION"
    HOME_IMPROVEMENT = "HOME_IMPROVEMENT"
    INVESTMENT = "INVESTMENT"
    BUSINESS_EXPANSION = "BUSINESS_EXPANSION"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    EQUIPMENT_PURCHASE = "EQUIPMENT_PURCHASE"
    PERSONAL_USE = "PERSONAL_USE"
    OTHER = "OTHER"


class SecurityType(str, Enum):
    """Type of security/collateral"""
    RESIDENTIAL_PROPERTY = "RESIDENTIAL_PROPERTY"
    COMMERCIAL_PROPERTY = "COMMERCIAL_PROPERTY"
    VEHICLE = "VEHICLE"
    EQUIPMENT = "EQUIPMENT"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    SHARES = "SHARES"
    UNSECURED = "UNSECURED"


class DocumentType(str, Enum):
    """Required document types"""
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    PASSPORT = "PASSPORT"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    MEDICARE_CARD = "MEDICARE_CARD"
    PAYSLIP = "PAYSLIP"
    TAX_RETURN = "TAX_RETURN"
    BANK_STATEMENT = "BANK_STATEMENT"
    EMPLOYMENT_LETTER = "EMPLOYMENT_LETTER"
    ABN_REGISTRATION = "ABN_REGISTRATION"
    FINANCIAL_STATEMENTS = "FINANCIAL_STATEMENTS"
    PROPERTY_VALUATION = "PROPERTY_VALUATION"
    CONTRACT_OF_SALE = "CONTRACT_OF_SALE"
    RATES_NOTICE = "RATES_NOTICE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ApplicantPersonalInfo:
    """Personal information of loan applicant"""
    applicant_id: str
    
    # Name
    title: Optional[str] = None  # Mr, Mrs, Ms, Dr, etc.
    first_name: str = ""
    middle_name: Optional[str] = None
    last_name: str = ""
    previous_name: Optional[str] = None
    
    # Contact
    email: str = ""
    mobile: str = ""
    phone: Optional[str] = None
    
    # Identity
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    number_of_dependents: int = 0
    
    # Residential
    residential_status: Optional[ResidentialStatus] = None
    years_at_address: Optional[int] = None
    
    # Current address
    address_line1: str = ""
    address_line2: Optional[str] = None
    suburb: str = ""
    state: str = ""
    postcode: str = ""
    country: str = "Australia"
    
    # Previous address (if < 3 years at current)
    previous_address: Optional[Dict[str, str]] = None
    
    # Identification
    drivers_license_number: Optional[str] = None
    drivers_license_state: Optional[str] = None
    passport_number: Optional[str] = None
    medicare_number: Optional[str] = None
    
    # Credit consent
    credit_check_consent: bool = False
    credit_check_consent_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmploymentInfo:
    """Employment and income information"""
    employment_id: str
    applicant_id: str
    
    # Employment
    employment_type: EmploymentType
    employer_name: str = ""
    occupation: str = ""
    industry: Optional[str] = None
    years_employed: Optional[int] = None
    months_employed: Optional[int] = None
    
    # Contact
    employer_phone: Optional[str] = None
    employer_address: Optional[str] = None
    
    # Income
    base_income: Decimal = Decimal('0.00')
    income_frequency: IncomeFrequency = IncomeFrequency.MONTHLY
    overtime_income: Decimal = Decimal('0.00')
    bonus_income: Decimal = Decimal('0.00')
    commission_income: Decimal = Decimal('0.00')
    rental_income: Decimal = Decimal('0.00')
    investment_income: Decimal = Decimal('0.00')
    other_income: Decimal = Decimal('0.00')
    
    # Self-employed specific
    abn: Optional[str] = None
    business_name: Optional[str] = None
    years_in_business: Optional[int] = None
    
    # Previous employment (if < 2 years in current)
    previous_employment: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def total_annual_income(self) -> Decimal:
        """Calculate total annual income"""
        # Convert base income to annual
        multiplier = {
            IncomeFrequency.WEEKLY: 52,
            IncomeFrequency.FORTNIGHTLY: 26,
            IncomeFrequency.MONTHLY: 12,
            IncomeFrequency.QUARTERLY: 4,
            IncomeFrequency.ANNUALLY: 1
        }
        
        annual_base = self.base_income * Decimal(multiplier[self.income_frequency])
        
        # Add other income (assuming already annualized)
        total = (
            annual_base +
            self.overtime_income +
            self.bonus_income +
            self.commission_income +
            self.rental_income +
            self.investment_income +
            self.other_income
        )
        
        return total


@dataclass
class FinancialPosition:
    """Financial position - assets and liabilities"""
    position_id: str
    applicant_id: str
    
    # Assets
    savings_balance: Decimal = Decimal('0.00')
    transaction_balance: Decimal = Decimal('0.00')
    term_deposit_balance: Decimal = Decimal('0.00')
    shares_value: Decimal = Decimal('0.00')
    super_balance: Decimal = Decimal('0.00')
    property_value: Decimal = Decimal('0.00')
    vehicle_value: Decimal = Decimal('0.00')
    other_assets: Decimal = Decimal('0.00')
    
    # Liabilities
    home_loan_balance: Decimal = Decimal('0.00')
    home_loan_repayment: Decimal = Decimal('0.00')
    personal_loan_balance: Decimal = Decimal('0.00')
    personal_loan_repayment: Decimal = Decimal('0.00')
    credit_card_limit: Decimal = Decimal('0.00')
    credit_card_balance: Decimal = Decimal('0.00')
    other_debt_balance: Decimal = Decimal('0.00')
    other_debt_repayment: Decimal = Decimal('0.00')
    
    # Expenses
    rent_mortgage: Decimal = Decimal('0.00')
    utilities: Decimal = Decimal('0.00')
    groceries: Decimal = Decimal('0.00')
    transport: Decimal = Decimal('0.00')
    insurance: Decimal = Decimal('0.00')
    childcare: Decimal = Decimal('0.00')
    education: Decimal = Decimal('0.00')
    entertainment: Decimal = Decimal('0.00')
    other_expenses: Decimal = Decimal('0.00')
    
    # Metadata
    as_of_date: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def total_assets(self) -> Decimal:
        """Calculate total assets"""
        return (
            self.savings_balance +
            self.transaction_balance +
            self.term_deposit_balance +
            self.shares_value +
            self.super_balance +
            self.property_value +
            self.vehicle_value +
            self.other_assets
        )
    
    def total_liabilities(self) -> Decimal:
        """Calculate total liabilities"""
        return (
            self.home_loan_balance +
            self.personal_loan_balance +
            self.credit_card_balance +
            self.other_debt_balance
        )
    
    def net_worth(self) -> Decimal:
        """Calculate net worth"""
        return self.total_assets() - self.total_liabilities()
    
    def total_monthly_repayments(self) -> Decimal:
        """Calculate total monthly debt repayments"""
        return (
            self.home_loan_repayment +
            self.personal_loan_repayment +
            (self.credit_card_limit * Decimal('0.03')) +  # 3% of limit
            self.other_debt_repayment
        )
    
    def total_monthly_expenses(self) -> Decimal:
        """Calculate total monthly living expenses"""
        return (
            self.rent_mortgage +
            self.utilities +
            self.groceries +
            self.transport +
            self.insurance +
            self.childcare +
            self.education +
            self.entertainment +
            self.other_expenses
        )


@dataclass
class LoanSecurity:
    """Security/collateral for loan"""
    security_id: str
    application_id: str
    
    # Security type
    security_type: SecurityType
    
    # Property details (if applicable)
    property_address: Optional[str] = None
    property_type: Optional[str] = None  # House, Unit, Townhouse, etc.
    estimated_value: Decimal = Decimal('0.00')
    purchase_price: Optional[Decimal] = None
    
    # Vehicle details (if applicable)
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_vin: Optional[str] = None
    
    # Valuation
    valuation_date: Optional[date] = None
    valuation_amount: Optional[Decimal] = None
    valuer_name: Optional[str] = None
    
    # Insurance
    insured: bool = False
    insurer_name: Optional[str] = None
    policy_number: Optional[str] = None
    sum_insured: Optional[Decimal] = None
    
    # Priority
    priority: int = 1  # 1st mortgage, 2nd mortgage, etc.
    existing_mortgages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoanDocument:
    """Document attached to loan application"""
    document_id: str
    application_id: str
    
    # Document details
    document_type: DocumentType
    document_name: str
    file_path: str
    file_size: int  # bytes
    mime_type: str
    
    # Status
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    uploaded_by: str = ""
    verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoanApplication:
    """Complete loan application"""
    application_id: str
    
    # Product
    product_type: LoanProductType
    loan_purpose: LoanPurpose
    
    # Loan details
    requested_amount: Decimal
    requested_term_months: int
    requested_rate: Optional[Decimal] = None
    interest_rate_type: str = "VARIABLE"  # VARIABLE, FIXED
    repayment_frequency: str = "MONTHLY"
    
    # Applicants
    primary_applicant: ApplicantPersonalInfo
    primary_employment: EmploymentInfo
    primary_financial: FinancialPosition
    
    # Joint applicant (optional)
    joint_applicant: Optional[ApplicantPersonalInfo] = None
    joint_employment: Optional[EmploymentInfo] = None
    joint_financial: Optional[FinancialPosition] = None
    
    # Security
    securities: List[LoanSecurity] = field(default_factory=list)
    
    # Documents
    documents: List[LoanDocument] = field(default_factory=list)
    
    # Status
    status: ApplicationStatus = ApplicationStatus.DRAFT
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Dates
    application_date: Optional[datetime] = None
    submission_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    settlement_date: Optional[date] = None
    
    # Decision
    approved_amount: Optional[Decimal] = None
    approved_term_months: Optional[int] = None
    approved_rate: Optional[Decimal] = None
    decline_reason: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    
    # Referrals
    broker_id: Optional[str] = None
    referrer_id: Optional[str] = None
    
    # Customer
    customer_id: Optional[str] = None
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def change_status(
        self,
        new_status: ApplicationStatus,
        changed_by: str,
        notes: Optional[str] = None
    ):
        """Change application status and record history"""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        self.status_history.append({
            'from_status': old_status.value,
            'to_status': new_status.value,
            'changed_at': self.updated_at.isoformat(),
            'changed_by': changed_by,
            'notes': notes
        })
    
    def total_household_income(self) -> Decimal:
        """Calculate total household income"""
        primary = self.primary_employment.total_annual_income()
        joint = self.joint_employment.total_annual_income() if self.joint_employment else Decimal('0.00')
        return primary + joint
    
    def loan_to_value_ratio(self) -> Optional[Decimal]:
        """Calculate LTV ratio"""
        if not self.securities:
            return None
        
        total_security_value = sum(s.estimated_value for s in self.securities)
        if total_security_value == 0:
            return None
        
        requested_amount = self.approved_amount or self.requested_amount
        return (requested_amount / total_security_value) * Decimal('100')
    
    def debt_to_income_ratio(self) -> Decimal:
        """Calculate debt-to-income ratio"""
        total_income = self.total_household_income()
        if total_income == 0:
            return Decimal('0.00')
        
        # Annual debt service
        monthly_repayments = self.primary_financial.total_monthly_repayments()
        if self.joint_financial:
            monthly_repayments += self.joint_financial.total_monthly_repayments()
        
        annual_debt = monthly_repayments * Decimal('12')
        
        return (annual_debt / total_income) * Decimal('100')


# ============================================================================
# Loan Application Manager
# ============================================================================

class LoanApplicationManager:
    """
    Manages loan applications
    Handles creation, updates, document management
    """
    
    def __init__(self):
        self.applications: Dict[str, LoanApplication] = {}
        self.applicants: Dict[str, ApplicantPersonalInfo] = {}
        self.employment_records: Dict[str, EmploymentInfo] = {}
        self.financial_records: Dict[str, FinancialPosition] = {}
    
    async def create_application(
        self,
        product_type: LoanProductType,
        loan_purpose: LoanPurpose,
        requested_amount: Decimal,
        requested_term_months: int,
        created_by: str
    ) -> LoanApplication:
        """Create a new loan application"""
        
        application_id = f"APP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        applicant_id = f"APL-{uuid.uuid4().hex[:12].upper()}"
        employment_id = f"EMP-{uuid.uuid4().hex[:12].upper()}"
        financial_id = f"FIN-{uuid.uuid4().hex[:12].upper()}"
        
        # Create primary applicant
        primary_applicant = ApplicantPersonalInfo(applicant_id=applicant_id)
        primary_employment = EmploymentInfo(
            employment_id=employment_id,
            applicant_id=applicant_id,
            employment_type=EmploymentType.FULL_TIME
        )
        primary_financial = FinancialPosition(
            position_id=financial_id,
            applicant_id=applicant_id
        )
        
        # Create application
        application = LoanApplication(
            application_id=application_id,
            product_type=product_type,
            loan_purpose=loan_purpose,
            requested_amount=requested_amount,
            requested_term_months=requested_term_months,
            primary_applicant=primary_applicant,
            primary_employment=primary_employment,
            primary_financial=primary_financial,
            created_by=created_by,
            application_date=datetime.now(timezone.utc)
        )
        
        # Store
        self.applications[application_id] = application
        self.applicants[applicant_id] = primary_applicant
        self.employment_records[employment_id] = primary_employment
        self.financial_records[financial_id] = primary_financial
        
        return application
    
    async def get_application(self, application_id: str) -> Optional[LoanApplication]:
        """Get application by ID"""
        return self.applications.get(application_id)
    
    async def add_joint_applicant(
        self,
        application_id: str
    ) -> Tuple[ApplicantPersonalInfo, EmploymentInfo, FinancialPosition]:
        """Add joint applicant to application"""
        
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        if application.joint_applicant:
            raise ValueError("Joint applicant already exists")
        
        # Create joint applicant
        applicant_id = f"APL-{uuid.uuid4().hex[:12].upper()}"
        employment_id = f"EMP-{uuid.uuid4().hex[:12].upper()}"
        financial_id = f"FIN-{uuid.uuid4().hex[:12].upper()}"
        
        joint_applicant = ApplicantPersonalInfo(applicant_id=applicant_id)
        joint_employment = EmploymentInfo(
            employment_id=employment_id,
            applicant_id=applicant_id,
            employment_type=EmploymentType.FULL_TIME
        )
        joint_financial = FinancialPosition(
            position_id=financial_id,
            applicant_id=applicant_id
        )
        
        # Update application
        application.joint_applicant = joint_applicant
        application.joint_employment = joint_employment
        application.joint_financial = joint_financial
        application.updated_at = datetime.now(timezone.utc)
        
        # Store
        self.applicants[applicant_id] = joint_applicant
        self.employment_records[employment_id] = joint_employment
        self.financial_records[financial_id] = joint_financial
        
        return joint_applicant, joint_employment, joint_financial
    
    async def add_security(
        self,
        application_id: str,
        security_type: SecurityType,
        estimated_value: Decimal,
        **kwargs
    ) -> LoanSecurity:
        """Add security to application"""
        
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        security_id = f"SEC-{uuid.uuid4().hex[:12].upper()}"
        
        security = LoanSecurity(
            security_id=security_id,
            application_id=application_id,
            security_type=security_type,
            estimated_value=estimated_value,
            **kwargs
        )
        
        application.securities.append(security)
        application.updated_at = datetime.now(timezone.utc)
        
        return security
    
    async def upload_document(
        self,
        application_id: str,
        document_type: DocumentType,
        document_name: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        uploaded_by: str
    ) -> LoanDocument:
        """Upload document to application"""
        
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        
        document = LoanDocument(
            document_id=document_id,
            application_id=application_id,
            document_type=document_type,
            document_name=document_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=uploaded_by
        )
        
        application.documents.append(document)
        application.updated_at = datetime.now(timezone.utc)
        
        return document
    
    async def submit_application(
        self,
        application_id: str,
        submitted_by: str
    ) -> LoanApplication:
        """Submit application for review"""
        
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Application is already {application.status}")
        
        # Validate required fields
        errors = await self._validate_application(application)
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")
        
        # Change status
        application.change_status(
            ApplicationStatus.SUBMITTED,
            submitted_by,
            "Application submitted for review"
        )
        application.submission_date = datetime.now(timezone.utc)
        
        return application
    
    async def _validate_application(
        self,
        application: LoanApplication
    ) -> List[str]:
        """Validate application before submission"""
        
        errors = []
        
        # Primary applicant validation
        if not application.primary_applicant.first_name:
            errors.append("Primary applicant first name required")
        if not application.primary_applicant.last_name:
            errors.append("Primary applicant last name required")
        if not application.primary_applicant.email:
            errors.append("Primary applicant email required")
        if not application.primary_applicant.date_of_birth:
            errors.append("Primary applicant date of birth required")
        if not application.primary_applicant.credit_check_consent:
            errors.append("Credit check consent required")
        
        # Employment validation
        if not application.primary_employment.employer_name:
            errors.append("Primary applicant employer name required")
        if application.primary_employment.base_income <= 0:
            errors.append("Primary applicant income required")
        
        # Loan amount validation
        if application.requested_amount <= 0:
            errors.append("Loan amount must be greater than zero")
        if application.requested_term_months <= 0:
            errors.append("Loan term must be greater than zero")
        
        # Security validation (if secured loan)
        if application.product_type in [
            LoanProductType.HOME_LOAN,
            LoanProductType.CAR_LOAN,
            LoanProductType.COMMERCIAL_PROPERTY
        ]:
            if not application.securities:
                errors.append("Security required for this loan type")
        
        # Document validation
        required_docs = self._get_required_documents(application.product_type)
        uploaded_types = {doc.document_type for doc in application.documents}
        missing_docs = required_docs - uploaded_types
        if missing_docs:
            errors.append(f"Missing documents: {', '.join([d.value for d in missing_docs])}")
        
        return errors
    
    def _get_required_documents(
        self,
        product_type: LoanProductType
    ) -> set:
        """Get required document types for product"""
        
        base_docs = {
            DocumentType.DRIVERS_LICENSE,
            DocumentType.PAYSLIP,
            DocumentType.BANK_STATEMENT
        }
        
        if product_type == LoanProductType.HOME_LOAN:
            base_docs.add(DocumentType.PROPERTY_VALUATION)
            base_docs.add(DocumentType.RATES_NOTICE)
        
        elif product_type == LoanProductType.BUSINESS_LOAN:
            base_docs.add(DocumentType.ABN_REGISTRATION)
            base_docs.add(DocumentType.FINANCIAL_STATEMENTS)
        
        return base_docs
    
    async def withdraw_application(
        self,
        application_id: str,
        withdrawn_by: str,
        reason: Optional[str] = None
    ) -> LoanApplication:
        """Withdraw application"""
        
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        if application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.DECLINED,
            ApplicationStatus.FUNDED
        ]:
            raise ValueError(f"Cannot withdraw application in {application.status} status")
        
        application.change_status(
            ApplicationStatus.WITHDRAWN,
            withdrawn_by,
            reason or "Application withdrawn by applicant"
        )
        
        return application


# ============================================================================
# Global Application Manager
# ============================================================================

_application_manager: Optional[LoanApplicationManager] = None

def get_application_manager() -> LoanApplicationManager:
    """Get the singleton application manager"""
    global _application_manager
    if _application_manager is None:
        _application_manager = LoanApplicationManager()
    return _application_manager

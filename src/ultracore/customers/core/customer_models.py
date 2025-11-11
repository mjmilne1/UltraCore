"""
UltraCore Customer Management - Core Models

Next-generation customer models with:
- Graph database relationships
- Vector embeddings for semantic search
- Event sourcing support
- Multi-tenancy
- Privacy-first design
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid


# ============================================================================
# Customer Enums
# ============================================================================

class CustomerType(str, Enum):
    """Type of customer"""
    INDIVIDUAL = "INDIVIDUAL"
    SOLE_TRADER = "SOLE_TRADER"
    COMPANY = "COMPANY"
    PARTNERSHIP = "PARTNERSHIP"
    TRUST = "TRUST"
    SUPER_FUND = "SUPER_FUND"
    ASSOCIATION = "ASSOCIATION"
    GOVERNMENT = "GOVERNMENT"


class CustomerSegment(str, Enum):
    """Customer segmentation"""
    RETAIL = "RETAIL"
    AFFLUENT = "AFFLUENT"
    HIGH_NET_WORTH = "HIGH_NET_WORTH"
    SMALL_BUSINESS = "SMALL_BUSINESS"
    SME = "SME"
    CORPORATE = "CORPORATE"
    INSTITUTIONAL = "INSTITUTIONAL"


class CustomerStatus(str, Enum):
    """Customer lifecycle status"""
    PROSPECT = "PROSPECT"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    DECEASED = "DECEASED"


class RiskRating(str, Enum):
    """Customer risk rating"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNACCEPTABLE = "UNACCEPTABLE"


class IdentificationType(str, Enum):
    """Types of identification"""
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    MEDICARE_CARD = "MEDICARE_CARD"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    CITIZENSHIP_CERTIFICATE = "CITIZENSHIP_CERTIFICATE"
    COMPANY_EXTRACT = "COMPANY_EXTRACT"
    TRUST_DEED = "TRUST_DEED"


class RelationshipType(str, Enum):
    """Types of customer relationships (for graph)"""
    SPOUSE = "SPOUSE"
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    BUSINESS_PARTNER = "BUSINESS_PARTNER"
    DIRECTOR = "DIRECTOR"
    SHAREHOLDER = "SHAREHOLDER"
    TRUSTEE = "TRUSTEE"
    BENEFICIARY = "BENEFICIARY"
    BENEFICIAL_OWNER = "BENEFICIAL_OWNER"
    AUTHORISED_REP = "AUTHORISED_REP"
    GUARANTOR = "GUARANTOR"
    CO_APPLICANT = "CO_APPLICANT"


class KYCStatus(str, Enum):
    """KYC verification status"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class DueDiligenceLevel(str, Enum):
    """Level of due diligence required"""
    STANDARD = "STANDARD"  # Standard CDD
    SIMPLIFIED = "SIMPLIFIED"  # Simplified DD
    ENHANCED = "ENHANCED"  # Enhanced DD (high risk)


class PEPStatus(str, Enum):
    """Politically Exposed Person status"""
    NOT_PEP = "NOT_PEP"
    DOMESTIC_PEP = "DOMESTIC_PEP"
    FOREIGN_PEP = "FOREIGN_PEP"
    INTERNATIONAL_ORG = "INTERNATIONAL_ORG"
    PEP_ASSOCIATE = "PEP_ASSOCIATE"


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class Address:
    """Physical address"""
    address_id: str
    address_type: str  # HOME, WORK, POSTAL, REGISTERED
    address_line1: str
    address_line2: Optional[str] = None
    suburb: str = ""
    state: str = ""
    postcode: str = ""
    country: str = "AU"
    is_primary: bool = False
    valid_from: date = field(default_factory=date.today)
    valid_to: Optional[date] = None
    verification_status: str = "UNVERIFIED"
    verification_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactDetails:
    """Contact information"""
    email: Optional[str] = None
    mobile: Optional[str] = None
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    preferred_contact: str = "EMAIL"  # EMAIL, MOBILE, PHONE, MAIL
    email_verified: bool = False
    mobile_verified: bool = False
    do_not_call: bool = False
    do_not_email: bool = False
    do_not_mail: bool = False
    consent_marketing: bool = False
    consent_data_sharing: bool = False
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Identification:
    """Identification document"""
    identification_id: str
    id_type: IdentificationType
    id_number: str
    issuing_country: str = "AU"
    issuing_state: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = None
    verified: bool = False
    verification_date: Optional[date] = None
    verification_method: Optional[str] = None  # MANUAL, AUTOMATED, BIOMETRIC
    verification_score: Optional[Decimal] = None  # AI confidence score
    is_primary: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KYCRecord:
    """KYC verification record"""
    kyc_id: str
    customer_id: str
    kyc_status: KYCStatus
    due_diligence_level: DueDiligenceLevel
    
    # Verification details
    verification_date: Optional[date] = None
    verified_by: Optional[str] = None
    expiry_date: Optional[date] = None
    
    # Risk factors
    pep_status: PEPStatus = PEPStatus.NOT_PEP
    sanctions_screening: bool = False
    sanctions_hit: bool = False
    adverse_media_screening: bool = False
    adverse_media_hit: bool = False
    
    # Source of wealth/funds
    source_of_wealth: Optional[str] = None
    source_of_funds: Optional[str] = None
    occupation: Optional[str] = None
    industry: Optional[str] = None
    
    # Expected activity
    expected_turnover: Optional[Decimal] = None
    expected_transaction_count: Optional[int] = None
    
    # Documents
    documents_verified: List[str] = field(default_factory=list)
    
    # AI/ML scores
    risk_score: Optional[Decimal] = None  # 0-100
    fraud_score: Optional[Decimal] = None  # 0-100
    
    # Review
    next_review_date: Optional[date] = None
    review_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerRelationship:
    """
    Graph relationship between customers
    Enables beneficial ownership, family trees, business networks
    """
    relationship_id: str
    from_customer_id: str
    to_customer_id: str
    relationship_type: RelationshipType
    
    # Relationship details
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    is_active: bool = True
    
    # Ownership/control (for corporate structures)
    ownership_percentage: Optional[Decimal] = None
    control_percentage: Optional[Decimal] = None
    voting_rights: Optional[Decimal] = None
    
    # Verification
    verified: bool = False
    verification_date: Optional[date] = None
    verification_source: Optional[str] = None
    
    # Graph properties
    strength: Decimal = Decimal('1.0')  # Relationship strength (0-1)
    bidirectional: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorEmbedding:
    """
    Vector embedding for semantic search and similarity
    Enables: customer matching, fraud detection, recommendation
    """
    embedding_id: str
    entity_id: str  # customer_id
    entity_type: str  # CUSTOMER, TRANSACTION, etc.
    
    # Embedding vector (typically 384 or 768 dimensions)
    embedding: List[float] = field(default_factory=list)
    embedding_model: str = "all-MiniLM-L6-v2"  # Model used
    embedding_version: str = "v1.0"
    
    # What was embedded
    source_text: Optional[str] = None
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    # Usage
    use_case: str = "CUSTOMER_MATCHING"  # MATCHING, SEARCH, RECOMMENDATION, FRAUD
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CustomerSegmentProfile:
    """ML-powered customer segmentation"""
    profile_id: str
    customer_id: str
    
    # Segment
    segment: CustomerSegment
    segment_score: Decimal  # Confidence score
    
    # Clustering (from ML model)
    cluster_id: Optional[int] = None
    cluster_name: Optional[str] = None
    
    # Behavioral features
    avg_balance: Decimal = Decimal('0.00')
    transaction_frequency: Decimal = Decimal('0.00')
    product_count: int = 0
    relationship_length_months: int = 0
    digital_adoption_score: Decimal = Decimal('0.00')
    
    # Predictive scores
    churn_probability: Optional[Decimal] = None
    lifetime_value: Optional[Decimal] = None
    cross_sell_propensity: Optional[Decimal] = None
    
    # Model info
    model_version: str = "v1.0"
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    next_calculation: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Main Customer Entity (Aggregate Root)
# ============================================================================

@dataclass
class Customer:
    """
    Core Customer entity - Aggregate Root
    
    Features:
    - Graph relationships (beneficial ownership, networks)
    - Vector embeddings (semantic search)
    - Event sourcing (all changes as events)
    - Multi-tenancy support
    - Privacy-first design
    """
    
    # Core identity
    customer_id: str
    customer_type: CustomerType
    customer_status: CustomerStatus
    
    # Tenant (for multi-tenancy)
    tenant_id: str = "default"
    
    # Individual details
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    
    # Business details (for non-individuals)
    business_name: Optional[str] = None
    trading_name: Optional[str] = None
    abn: Optional[str] = None
    acn: Optional[str] = None
    business_structure: Optional[str] = None
    incorporation_date: Optional[date] = None
    
    # Contact & Address
    contact_details: ContactDetails = field(default_factory=ContactDetails)
    addresses: List[Address] = field(default_factory=list)
    
    # Identification
    identifications: List[Identification] = field(default_factory=list)
    
    # KYC/AML
    kyc_records: List[KYCRecord] = field(default_factory=list)
    current_kyc_status: KYCStatus = KYCStatus.NOT_STARTED
    
    # Risk & Compliance
    risk_rating: RiskRating = RiskRating.MEDIUM
    pep_status: PEPStatus = PEPStatus.NOT_PEP
    sanctions_screening_date: Optional[date] = None
    sanctions_hit: bool = False
    
    # Segmentation
    segment: CustomerSegment = CustomerSegment.RETAIL
    segment_profile: Optional[CustomerSegmentProfile] = None
    
    # Relationships (Graph)
    relationship_ids: Set[str] = field(default_factory=set)  # References to CustomerRelationship
    
    # Vector embedding
    embedding_id: Optional[str] = None  # Reference to VectorEmbedding
    
    # Product holdings
    account_ids: Set[str] = field(default_factory=set)
    loan_ids: Set[str] = field(default_factory=set)
    card_ids: Set[str] = field(default_factory=set)
    
    # Preferences
    preferred_language: str = "en"
    preferred_branch: Optional[str] = None
    communication_preferences: Dict[str, bool] = field(default_factory=dict)
    
    # Lifecycle dates
    prospect_date: Optional[date] = None
    onboarding_date: Optional[date] = None
    activation_date: Optional[date] = None
    closure_date: Optional[date] = None
    closure_reason: Optional[str] = None
    
    # Value & Behavior
    customer_lifetime_value: Optional[Decimal] = None
    last_activity_date: Optional[datetime] = None
    last_login_date: Optional[datetime] = None
    
    # Marketing
    acquisition_channel: Optional[str] = None
    acquisition_campaign: Optional[str] = None
    referral_source: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "SYSTEM"
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = "SYSTEM"
    version: int = 1  # For optimistic locking
    
    # Tags (for flexible categorization)
    tags: Set[str] = field(default_factory=set)
    
    # Extended attributes (for extensibility)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def get_full_name(self) -> str:
        """Get full name"""
        if self.customer_type == CustomerType.INDIVIDUAL:
            parts = [self.title, self.first_name, self.middle_name, self.last_name]
            return " ".join(p for p in parts if p)
        else:
            return self.business_name or self.trading_name or ""
    
    def get_display_name(self) -> str:
        """Get display name"""
        if self.preferred_name:
            return self.preferred_name
        return self.get_full_name()
    
    def get_primary_address(self) -> Optional[Address]:
        """Get primary address"""
        for addr in self.addresses:
            if addr.is_primary:
                return addr
        return self.addresses[0] if self.addresses else None
    
    def get_primary_identification(self) -> Optional[Identification]:
        """Get primary ID"""
        for id_doc in self.identifications:
            if id_doc.is_primary:
                return id_doc
        return self.identifications[0] if self.identifications else None
    
    def get_current_kyc(self) -> Optional[KYCRecord]:
        """Get current KYC record"""
        if not self.kyc_records:
            return None
        return max(self.kyc_records, key=lambda k: k.created_at)
    
    def is_high_risk(self) -> bool:
        """Check if customer is high risk"""
        return (
            self.risk_rating in [RiskRating.HIGH, RiskRating.VERY_HIGH, RiskRating.UNACCEPTABLE] or
            self.pep_status != PEPStatus.NOT_PEP or
            self.sanctions_hit
        )
    
    def requires_enhanced_dd(self) -> bool:
        """Check if requires enhanced due diligence"""
        current_kyc = self.get_current_kyc()
        if current_kyc:
            return current_kyc.due_diligence_level == DueDiligenceLevel.ENHANCED
        return self.is_high_risk()
    
    def is_active(self) -> bool:
        """Check if customer is active"""
        return self.customer_status == CustomerStatus.ACTIVE
    
    def add_relationship(self, relationship_id: str):
        """Add relationship reference"""
        self.relationship_ids.add(relationship_id)
        self.updated_at = datetime.utcnow()
    
    def add_account(self, account_id: str):
        """Add account reference"""
        self.account_ids.add(account_id)
        self.updated_at = datetime.utcnow()
    
    def add_loan(self, loan_id: str):
        """Add loan reference"""
        self.loan_ids.add(loan_id)
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add tag"""
        self.tags.add(tag.upper())
        self.updated_at = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity"""
        self.last_activity_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()


# ============================================================================
# Event Models (for Event Sourcing)
# ============================================================================

class CustomerEventType(str, Enum):
    """Types of customer events"""
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    CUSTOMER_VERIFIED = "CUSTOMER_VERIFIED"
    KYC_COMPLETED = "KYC_COMPLETED"
    RISK_RATING_CHANGED = "RISK_RATING_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    RELATIONSHIP_ADDED = "RELATIONSHIP_ADDED"
    PRODUCT_ADDED = "PRODUCT_ADDED"
    SEGMENT_CHANGED = "SEGMENT_CHANGED"
    PEP_STATUS_CHANGED = "PEP_STATUS_CHANGED"
    SANCTIONS_SCREENED = "SANCTIONS_SCREENED"


@dataclass
class CustomerEvent:
    """
    Customer event for event sourcing
    Immutable record of all customer changes
    """
    event_id: str
    event_type: CustomerEventType
    event_timestamp: datetime
    
    # Aggregate
    customer_id: str
    tenant_id: str
    
    # Event data
    event_data: Dict[str, Any] = field(default_factory=dict)
    
    # Previous state (for some events)
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    
    # Causation
    caused_by: str = "SYSTEM"
    caused_by_event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

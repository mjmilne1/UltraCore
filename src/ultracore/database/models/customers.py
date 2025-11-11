"""
UltraCore Database Models - Customers

Customer domain models:
- Customer (individual/business)
- KYC verification
- Risk assessment
- Customer relationships (for graph sync)
"""

from sqlalchemy import Column, String, Date, DateTime, Boolean, Enum, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import date

from ultracore.database.models.base import BaseModel
import enum


class CustomerTypeEnum(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class CustomerStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class RiskRatingEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KYCStatusEnum(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class Customer(BaseModel):
    """
    Customer entity
    
    Represents individual or business customers
    """
    
    __tablename__ = "customers"
    __table_args__ = (
        Index('idx_customers_tenant_type', 'tenant_id', 'customer_type'),
        Index('idx_customers_email', 'tenant_id', 'email'),
        Index('idx_customers_mobile', 'tenant_id', 'mobile'),
        Index('idx_customers_status', 'tenant_id', 'status'),
        {'schema': 'customers', 'comment': 'Customer master data'}
    )
    
    # Customer identifiers
    customer_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Business customer ID (CUST-xxx)"
    )
    
    # Customer type
    customer_type = Column(
        Enum(CustomerTypeEnum, name='customer_type_enum'),
        nullable=False,
        comment="Individual or Business"
    )
    
    status = Column(
        Enum(CustomerStatusEnum, name='customer_status_enum'),
        nullable=False,
        default=CustomerStatusEnum.ACTIVE,
        comment="Customer status"
    )
    
    # Individual fields
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    # Business fields
    business_name = Column(String(200), nullable=True)
    business_registration = Column(String(100), nullable=True)
    abn = Column(String(11), nullable=True, index=True)
    acn = Column(String(9), nullable=True)
    
    # Contact
    email = Column(String(255), nullable=False, index=True)
    mobile = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Address
    street_address = Column(String(255), nullable=True)
    suburb = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(10), nullable=True)
    country = Column(String(2), nullable=False, default='AU')
    
    # Risk & Compliance
    risk_rating = Column(
        Enum(RiskRatingEnum, name='risk_rating_enum'),
        nullable=False,
        default=RiskRatingEnum.MEDIUM
    )
    
    kyc_status = Column(
        Enum(KYCStatusEnum, name='kyc_status_enum'),
        nullable=False,
        default=KYCStatusEnum.NOT_STARTED
    )
    
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    kyc_expiry_date = Column(Date, nullable=True)
    
    is_pep = Column(Boolean, default=False, comment="Politically Exposed Person")
    sanction_screening_date = Column(DateTime(timezone=True), nullable=True)
    
    # Segmentation
    customer_segment = Column(String(50), nullable=True)
    acquisition_channel = Column(String(50), nullable=True)
    
    # Relationships (back-populate from accounts, loans)
    accounts = relationship("Account", back_populates="customer", lazy="dynamic")
    loans = relationship("Loan", back_populates="customer", lazy="dynamic")
    
    def __repr__(self):
        name = self.business_name or f"{self.first_name} {self.last_name}"
        return f"<Customer(id={self.customer_id}, name={name})>"


class CustomerRelationship(BaseModel):
    """
    Customer relationships (for graph database sync)
    
    Tracks relationships between customers:
    - Beneficial ownership
    - Directors
    - Authorized signers
    - Family members
    """
    
    __tablename__ = "customer_relationships"
    __table_args__ = (
        Index('idx_relationships_from', 'tenant_id', 'from_customer_id'),
        Index('idx_relationships_to', 'tenant_id', 'to_customer_id'),
        {'schema': 'customers', 'comment': 'Customer relationships'}
    )
    
    from_customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey('customers.customers.id', ondelete='CASCADE'),
        nullable=False
    )
    
    to_customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey('customers.customers.id', ondelete='CASCADE'),
        nullable=False
    )
    
    relationship_type = Column(
        String(50),
        nullable=False,
        comment="BENEFICIAL_OWNER, DIRECTOR, AUTHORIZED_SIGNER, etc."
    )
    
    ownership_percentage = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Ownership percentage (for beneficial ownership)"
    )
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    # Graph sync status
    synced_to_graph = Column(Boolean, default=False)
    graph_sync_at = Column(DateTime(timezone=True), nullable=True)

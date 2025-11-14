"""
Collateral Management Models
Manages security/collateral for secured loans
"""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class CollateralType(str, Enum):
    """Types of collateral"""
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    SECURITIES = "securities"
    CASH_DEPOSIT = "cash_deposit"
    GUARANTEE = "guarantee"
    OTHER = "other"


class CollateralStatus(str, Enum):
    """Collateral statuses"""
    PENDING_VALUATION = "pending_valuation"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    RELEASED = "released"
    LIQUIDATED = "liquidated"
    DISPUTED = "disputed"


class ValuationMethod(str, Enum):
    """Valuation methods"""
    PROFESSIONAL_VALUATION = "professional_valuation"
    AUTOMATED_VALUATION = "automated_valuation"  # AVM
    MARKET_PRICE = "market_price"
    BOOK_VALUE = "book_value"
    CUSTOMER_DECLARED = "customer_declared"


# ============================================================================
# COLLATERAL
# ============================================================================

class Collateral(BaseModel):
    """
    Collateral/Security for a loan
    
    Represents an asset pledged as security for a loan
    """
    collateral_id: str
    external_id: Optional[str] = None
    
    # Type and description
    collateral_type: CollateralType
    description: str
    
    # Ownership
    owner_name: str
    owner_client_id: Optional[str] = None
    
    # Valuation
    current_value: Decimal
    valuation_date: date
    valuation_method: ValuationMethod
    valuation_currency: str = "AUD"
    
    # For vehicles
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None  # Vehicle Identification Number
    registration: Optional[str] = None
    odometer: Optional[int] = None
    
    # For real estate
    property_address: Optional[str] = None
    property_type: Optional[str] = None  # house, apartment, land
    land_size_sqm: Optional[Decimal] = None
    building_size_sqm: Optional[Decimal] = None
    title_reference: Optional[str] = None
    
    # For securities
    security_type: Optional[str] = None  # shares, bonds, etc.
    issuer: Optional[str] = None
    quantity: Optional[Decimal] = None
    
    # Status
    status: CollateralStatus = CollateralStatus.PENDING_VALUATION
    
    # Insurance
    is_insured: bool = False
    insurance_policy_number: Optional[str] = None
    insurance_value: Optional[Decimal] = None
    insurance_expiry: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# LOAN COLLATERAL LINK
# ============================================================================

class LoanCollateral(BaseModel):
    """
    Link between a loan and its collateral
    
    A loan can have multiple collateral items
    A collateral item can secure multiple loans
    """
    link_id: str
    loan_account_id: str
    collateral_id: str
    
    # Allocation
    allocated_value: Decimal  # How much of collateral value is allocated to this loan
    allocation_percentage: Decimal  # Percentage of collateral allocated
    
    # LVR
    loan_amount: Decimal
    collateral_value: Decimal
    lvr: Decimal  # Loan-to-Value Ratio
    
    # Priority
    priority: int = 1  # 1 = first charge, 2 = second charge, etc.
    
    # Dates
    secured_date: date
    release_date: Optional[date] = None
    
    # Status
    is_active: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# VALUATION
# ============================================================================

class CollateralValuation(BaseModel):
    """Valuation record for collateral"""
    valuation_id: str
    collateral_id: str
    
    valuation_date: date
    valuation_method: ValuationMethod
    valued_amount: Decimal
    
    # Valuer details
    valuer_name: Optional[str] = None
    valuer_license: Optional[str] = None
    valuation_report_url: Optional[str] = None
    
    # Market data
    comparable_sales: Optional[List[Dict]] = None
    market_conditions: Optional[str] = None
    
    # Adjustments
    condition_adjustment: Decimal = Decimal("0")
    location_adjustment: Decimal = Decimal("0")
    market_adjustment: Decimal = Decimal("0")
    
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# PPSR (Personal Property Securities Register)
# ============================================================================

class PPSRRegistration(BaseModel):
    """
    PPSR Registration
    
    Australian Personal Property Securities Register registration
    Required for security interests in personal property
    """
    registration_id: str
    collateral_id: str
    
    # PPSR details
    ppsr_registration_number: str
    registration_date: date
    expiry_date: Optional[date] = None
    
    # Secured party
    secured_party_name: str
    secured_party_abn: Optional[str] = None
    
    # Grantor (borrower)
    grantor_name: str
    grantor_abn_acn: Optional[str] = None
    
    # Collateral description
    collateral_class: str  # Motor vehicle, other goods, etc.
    serial_number: Optional[str] = None
    
    # Status
    is_active: bool = True
    is_discharged: bool = False
    discharge_date: Optional[date] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateCollateralRequest(BaseModel):
    """Request to create collateral"""
    collateral_type: CollateralType
    description: str
    owner_name: str
    owner_client_id: Optional[str] = None
    current_value: Decimal
    valuation_method: ValuationMethod
    created_by: str
    
    # Optional fields based on type
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    property_address: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class LinkCollateralToLoanRequest(BaseModel):
    """Request to link collateral to loan"""
    loan_account_id: str
    collateral_id: str
    allocated_value: Decimal
    priority: int = 1
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CreateValuationRequest(BaseModel):
    """Request to create valuation"""
    collateral_id: str
    valuation_date: date
    valuation_method: ValuationMethod
    valued_amount: Decimal
    valuer_name: Optional[str] = None
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class RegisterPPSRRequest(BaseModel):
    """Request to register PPSR"""
    collateral_id: str
    ppsr_registration_number: str
    registration_date: date
    secured_party_name: str
    grantor_name: str
    collateral_class: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }

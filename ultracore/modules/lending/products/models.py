"""
Loan Product Models
Defines loan products, interest rate charts, and product configurations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class LoanProductType(str, Enum):
    """Types of loan products"""
    PERSONAL = "personal"
    HOME = "home"
    CAR = "car"
    BUSINESS = "business"
    DEBT_CONSOLIDATION = "debt_consolidation"
    INVESTMENT = "investment"
    GREEN = "green"  # Green/sustainable loans


class InterestRateType(str, Enum):
    """Interest rate calculation methods"""
    FIXED = "fixed"
    VARIABLE = "variable"
    SPLIT = "split"  # Part fixed, part variable
    DISCOUNT_VARIABLE = "discount_variable"  # Variable with discount


class RepaymentFrequency(str, Enum):
    """Loan repayment frequencies"""
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class AmortizationType(str, Enum):
    """Loan amortization methods"""
    PRINCIPAL_AND_INTEREST = "principal_and_interest"
    INTEREST_ONLY = "interest_only"
    BALLOON_PAYMENT = "balloon_payment"
    REDUCING_BALANCE = "reducing_balance"


class LoanPurpose(str, Enum):
    """Purpose of the loan"""
    PERSONAL_USE = "personal_use"
    HOME_PURCHASE = "home_purchase"
    HOME_RENOVATION = "home_renovation"
    VEHICLE_PURCHASE = "vehicle_purchase"
    DEBT_CONSOLIDATION = "debt_consolidation"
    BUSINESS_EXPANSION = "business_expansion"
    INVESTMENT = "investment"
    EDUCATION = "education"
    MEDICAL = "medical"
    OTHER = "other"


class FeeType(str, Enum):
    """Types of fees"""
    APPLICATION_FEE = "application_fee"
    ESTABLISHMENT_FEE = "establishment_fee"
    MONTHLY_FEE = "monthly_fee"
    ANNUAL_FEE = "annual_fee"
    EARLY_REPAYMENT_FEE = "early_repayment_fee"
    LATE_PAYMENT_FEE = "late_payment_fee"
    DISHONOUR_FEE = "dishonour_fee"
    VARIATION_FEE = "variation_fee"
    DISCHARGE_FEE = "discharge_fee"


# ============================================================================
# INTEREST RATE CHARTS
# ============================================================================

class InterestRateChartSlab(BaseModel):
    """
    A slab in an interest rate chart
    
    Defines interest rate for a specific range of loan amounts, terms, or LVRs
    """
    slab_id: str
    from_amount: Optional[Decimal] = None
    to_amount: Optional[Decimal] = None
    from_term_months: Optional[int] = None
    to_term_months: Optional[int] = None
    from_lvr: Optional[Decimal] = None  # Loan-to-Value Ratio
    to_lvr: Optional[Decimal] = None
    interest_rate: Decimal = Field(..., description="Annual interest rate as decimal (e.g., 0.0550 for 5.50%)")
    comparison_rate: Decimal = Field(..., description="Comparison rate including fees")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class InterestRateChart(BaseModel):
    """
    Interest Rate Chart
    
    Defines interest rates based on loan amount, term, LVR, and other factors
    """
    chart_id: str
    chart_name: str
    effective_from: date
    effective_to: Optional[date] = None
    rate_type: InterestRateType
    slabs: List[InterestRateChartSlab] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_applicable_rate(
        self,
        loan_amount: Decimal,
        term_months: int,
        lvr: Optional[Decimal] = None
    ) -> Optional[InterestRateChartSlab]:
        """
        Get the applicable interest rate slab for given parameters
        
        Args:
            loan_amount: Loan amount
            term_months: Loan term in months
            lvr: Loan-to-Value Ratio (optional)
            
        Returns:
            Applicable slab or None
        """
        for slab in self.slabs:
            # Check amount range
            if slab.from_amount is not None and loan_amount < slab.from_amount:
                continue
            if slab.to_amount is not None and loan_amount > slab.to_amount:
                continue
            
            # Check term range
            if slab.from_term_months is not None and term_months < slab.from_term_months:
                continue
            if slab.to_term_months is not None and term_months > slab.to_term_months:
                continue
            
            # Check LVR range
            if lvr is not None:
                if slab.from_lvr is not None and lvr < slab.from_lvr:
                    continue
                if slab.to_lvr is not None and lvr > slab.to_lvr:
                    continue
            
            return slab
        
        return None


# ============================================================================
# FEES AND CHARGES
# ============================================================================

class LoanFee(BaseModel):
    """Fee configuration for a loan product"""
    fee_id: str
    fee_type: FeeType
    fee_name: str
    amount: Decimal
    is_percentage: bool = False  # If True, amount is percentage of loan amount
    is_capitalised: bool = False  # If True, added to loan principal
    is_waivable: bool = False
    description: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# ============================================================================
# LOAN PRODUCT
# ============================================================================

class LoanProduct(BaseModel):
    """
    Loan Product Configuration
    
    Defines a loan product with all its characteristics, rules, and constraints
    """
    product_id: str
    product_code: str = Field(..., description="Unique product code (e.g., 'PL-STANDARD-001')")
    product_name: str
    product_type: LoanProductType
    description: str
    
    # Availability
    is_active: bool = True
    available_from: date
    available_to: Optional[date] = None
    
    # Loan amount constraints
    min_loan_amount: Decimal
    max_loan_amount: Decimal
    default_loan_amount: Optional[Decimal] = None
    
    # Term constraints
    min_term_months: int
    max_term_months: int
    default_term_months: int
    
    # Interest rate
    interest_rate_chart_id: str
    rate_type: InterestRateType
    base_interest_rate: Decimal = Field(..., description="Base rate before adjustments")
    
    # Repayment
    allowed_repayment_frequencies: List[RepaymentFrequency]
    default_repayment_frequency: RepaymentFrequency
    amortization_type: AmortizationType
    
    # Security/Collateral
    requires_security: bool = False
    min_lvr: Optional[Decimal] = None  # Minimum LVR (e.g., 0.60 for 60%)
    max_lvr: Optional[Decimal] = None  # Maximum LVR (e.g., 0.80 for 80%)
    
    # Fees
    fees: List[LoanFee] = []
    
    # Eligibility
    min_age: int = 18
    max_age: int = 75
    min_income: Optional[Decimal] = None
    requires_australian_residency: bool = True
    allowed_purposes: List[LoanPurpose] = []
    
    # Features
    allows_extra_repayments: bool = True
    allows_redraw: bool = False
    allows_offset_account: bool = False
    allows_repayment_holiday: bool = False
    
    # Australian Compliance
    nccp_regulated: bool = True  # Subject to NCCP Act
    requires_responsible_lending_assessment: bool = True
    credit_guide_required: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }
    
    @validator('product_code')
    def validate_product_code(cls, v):
        """Ensure product code is uppercase and follows convention"""
        return v.upper()
    
    def calculate_comparison_rate(
        self,
        loan_amount: Decimal,
        term_months: int
    ) -> Decimal:
        """
        Calculate comparison rate including fees
        
        Australian law requires comparison rate disclosure
        
        Args:
            loan_amount: Loan amount
            term_months: Loan term
            
        Returns:
            Comparison rate as decimal
        """
        # Get base rate from chart
        chart = None  # Would be loaded from database
        
        # Calculate total fees
        total_fees = Decimal("0")
        for fee in self.fees:
            if fee.is_percentage:
                total_fees += loan_amount * (fee.amount / Decimal("100"))
            else:
                total_fees += fee.amount
        
        # Simplified comparison rate calculation
        # In production, use proper APR calculation
        effective_amount = loan_amount + total_fees
        rate_adjustment = (total_fees / loan_amount) / (term_months / 12)
        
        comparison_rate = self.base_interest_rate + rate_adjustment
        
        return comparison_rate
    
    def is_eligible(
        self,
        applicant_age: int,
        applicant_income: Decimal,
        is_australian_resident: bool,
        loan_purpose: LoanPurpose
    ) -> tuple[bool, List[str]]:
        """
        Check if applicant is eligible for this product
        
        Returns:
            (is_eligible, reasons)
        """
        reasons = []
        
        # Age check
        if applicant_age < self.min_age:
            reasons.append(f"Applicant must be at least {self.min_age} years old")
        if applicant_age > self.max_age:
            reasons.append(f"Applicant must be under {self.max_age} years old")
        
        # Income check
        if self.min_income and applicant_income < self.min_income:
            reasons.append(f"Minimum income requirement not met (${self.min_income:,.2f})")
        
        # Residency check
        if self.requires_australian_residency and not is_australian_resident:
            reasons.append("Australian residency required")
        
        # Purpose check
        if self.allowed_purposes and loan_purpose not in self.allowed_purposes:
            reasons.append(f"Loan purpose '{loan_purpose.value}' not allowed for this product")
        
        return (len(reasons) == 0, reasons)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateLoanProductRequest(BaseModel):
    """Request to create a new loan product"""
    product_code: str
    product_name: str
    product_type: LoanProductType
    description: str
    min_loan_amount: Decimal
    max_loan_amount: Decimal
    min_term_months: int
    max_term_months: int
    default_term_months: int
    base_interest_rate: Decimal
    rate_type: InterestRateType
    allowed_repayment_frequencies: List[RepaymentFrequency]
    default_repayment_frequency: RepaymentFrequency
    amortization_type: AmortizationType
    requires_security: bool
    created_by: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CreateInterestRateChartRequest(BaseModel):
    """Request to create interest rate chart"""
    chart_name: str
    effective_from: date
    rate_type: InterestRateType
    slabs: List[InterestRateChartSlab]


class GetApplicableRateRequest(BaseModel):
    """Request to get applicable interest rate"""
    product_id: str
    loan_amount: Decimal
    term_months: int
    lvr: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }

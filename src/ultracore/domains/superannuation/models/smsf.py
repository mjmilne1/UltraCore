"""SMSF Core Models - Event-Sourced"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from pydantic import BaseModel

from .enums import TrusteeType, MemberType, SMSFPhase, ComplianceStatus


class SMSF(BaseModel):
    """
    Self-Managed Super Fund (Event-Sourced).
    
    Reconstructed from events.
    UltraLedger provides authoritative balances.
    
    Australian SMSF Context:
    - Maximum 6 members (as of July 2021)
    - Trustees are members (or corporate trustee)
    - Sole purpose: Retirement benefits
    - Annual audit requirement
    - ATO oversight
    
    Phases:
    - Accumulation: 15% tax on earnings
    - Pension: 0% tax on earnings! ??
    
    Average SMSF:
    - Balance: $796,000
    - Members: 2.2
    - Age: 50-65 years
    """
    
    # Identity
    smsf_id: str
    fund_name: str
    
    # Registration
    abn: str  # Australian Business Number
    tfn: str  # Tax File Number (encrypted)
    
    # Trustee structure
    trustee_type: TrusteeType
    corporate_trustee_name: Optional[str] = None
    corporate_trustee_acn: Optional[str] = None
    
    # Members (max 6)
    members: List['SMSFMember'] = []
    member_count: int = 0
    
    # Balances (from UltraLedger)
    total_balance: Decimal  # All members
    accumulation_balance: Decimal  # 15% tax phase
    pension_balance: Decimal  # 0% tax phase
    
    # Investment strategy
    investment_strategy: str
    risk_tolerance: str
    
    # Compliance
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    last_audit_date: Optional[date] = None
    next_audit_due: Optional[date] = None
    auditor_name: Optional[str] = None
    
    # ATO
    ato_registered: bool = True
    annual_return_lodged: bool = False
    annual_return_due: Optional[date] = None
    
    # Bank account
    operating_account_id: str
    investment_account_id: Optional[str] = None
    
    # Dates
    establishment_date: date
    current_financial_year: str  # 2024-25
    
    # Integration
    wealth_portfolio_id: Optional[str] = None  # Link to wealth management
    
    # Version
    version: int = 0
    updated_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class SMSFMember(BaseModel):
    """
    SMSF member (trustee and beneficiary).
    
    Member Requirements:
    - Must be trustee (individual structure)
    - Or director of corporate trustee
    - Related parties (family members typically)
    - Under 18: Parent as representative
    """
    
    # Identity
    member_id: str
    customer_id: str  # Link to customer
    smsf_id: str
    
    # Personal
    first_name: str
    last_name: str
    date_of_birth: date
    tfn: str  # Encrypted
    
    # Membership
    join_date: date
    member_type: MemberType
    
    # Trustee
    is_trustee: bool = True
    trustee_type: str  # individual, director
    
    # Accounts
    accumulation_account_id: str
    pension_account_id: Optional[str] = None
    
    # Balances (from UltraLedger)
    accumulation_balance: Decimal = Decimal("0.00")
    pension_balance: Decimal = Decimal("0.00")
    total_balance: Decimal = Decimal("0.00")
    
    # Contributions (YTD)
    concessional_contributions_ytd: Decimal = Decimal("0.00")
    non_concessional_contributions_ytd: Decimal = Decimal("0.00")
    
    # Pension (if commenced)
    pension_commenced: bool = False
    pension_commencement_date: Optional[date] = None
    minimum_pension_required: Decimal = Decimal("0.00")
    pension_paid_ytd: Decimal = Decimal("0.00")
    
    # Total Super Balance (TSB)
    total_super_balance: Decimal = Decimal("0.00")
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class TrusteeStructure(BaseModel):
    """
    Trustee structure details.
    
    Individual Trustees:
    - Each member is a trustee
    - Equal responsibilities
    - Unanimous decisions required
    - Simpler structure
    
    Corporate Trustee:
    - Company acts as trustee
    - Members are directors
    - Better protection
    - Easier succession
    - Professional appearance
    - Annual ASIC fee ($58)
    """
    
    trustee_type: TrusteeType
    
    # Individual trustees
    individual_trustees: List[str] = []  # Member IDs
    
    # Corporate trustee
    company_name: Optional[str] = None
    acn: Optional[str] = None  # Australian Company Number
    directors: List[str] = []  # Member IDs
    
    # Appointment
    appointed_date: date

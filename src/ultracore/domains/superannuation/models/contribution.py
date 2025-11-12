"""Contribution Models"""
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from .enums import ContributionType


class Contribution(BaseModel):
    """
    Contribution to SMSF member account.
    
    Contribution Caps (2024-25):
    - Concessional: $30,000 p.a. (before-tax)
    - Non-concessional: $120,000 p.a. (after-tax)
    - Bring-forward: $360,000 over 3 years (non-concessional)
    """
    
    contribution_id: str
    smsf_id: str
    member_id: str
    
    # Details
    contribution_type: ContributionType
    amount: Decimal
    
    # Tax
    contributions_tax: Decimal
    net_contribution: Decimal
    
    # Caps
    financial_year: str
    cap_amount: Decimal
    ytd_contributions: Decimal
    cap_exceeded: bool = False
    
    # Date
    received_date: date
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class ContributionCaps(BaseModel):
    """
    Contribution caps for a financial year.
    
    Annual Caps:
    - Concessional: $30,000 (indexed)
    - Non-concessional: $120,000 (indexed)
    - Bring-forward: $360,000 (if eligible)
    
    Unused Cap Carry-Forward:
    - Available if TSB < $500,000
    - Up to 5 years
    """
    
    financial_year: str
    
    # Concessional
    concessional_cap: Decimal = Decimal("30000")
    concessional_used: Decimal = Decimal("0")
    concessional_available: Decimal
    
    # Unused carry-forward
    unused_concessional_carryforward: Decimal = Decimal("0")
    
    # Non-concessional
    non_concessional_cap: Decimal = Decimal("120000")
    non_concessional_used: Decimal = Decimal("0")
    non_concessional_available: Decimal
    
    # Bring-forward
    bring_forward_available: bool = False
    bring_forward_cap: Decimal = Decimal("360000")
    bring_forward_triggered: bool = False
    
    class Config:
        json_encoders = {
            Decimal: str
        }

"""Pension Models"""
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from .enums import PensionType


class Pension(BaseModel):
    """
    Retirement pension (income stream).
    
    Pension Phase Benefits:
    - 0% tax on earnings! ??
    - Tax-free payments if 60+
    - Must meet minimum drawdown
    """
    
    pension_id: str
    smsf_id: str
    member_id: str
    
    # Type
    pension_type: PensionType
    
    # Balance
    balance: Decimal
    
    # Drawdown
    minimum_percentage: Decimal
    minimum_annual: Decimal
    maximum_annual: Optional[Decimal] = None  # TTR only
    
    # Payments
    payment_frequency: str  # monthly, quarterly, annually
    payment_amount: Decimal
    ytd_payments: Decimal = Decimal("0")
    
    # Tax
    tax_free_component: Decimal
    taxable_component: Decimal
    
    # Dates
    commencement_date: date
    financial_year: str
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class MinimumPension(BaseModel):
    """
    Minimum pension requirements by age.
    
    Age-Based Minimums:
    - Under 65: 4%
    - 65-74: 5%
    - 75-79: 6%
    - 80-84: 7%
    - 85-89: 9%
    - 90-94: 11%
    - 95+: 14%
    """
    
    age: int
    minimum_percentage: Decimal
    
    @staticmethod
    def get_minimum_for_age(age: int) -> Decimal:
        """Calculate minimum percentage for age."""
        if age < 65:
            return Decimal("0.04")
        elif age < 75:
            return Decimal("0.05")
        elif age < 80:
            return Decimal("0.06")
        elif age < 85:
            return Decimal("0.07")
        elif age < 90:
            return Decimal("0.09")
        elif age < 95:
            return Decimal("0.11")
        else:
            return Decimal("0.14")

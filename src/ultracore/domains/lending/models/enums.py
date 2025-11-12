"""Lending Enumerations"""
from enum import Enum


class LoanType(str, Enum):
    """Loan product types."""
    PERSONAL = "personal"
    HOME = "home"
    BUSINESS = "business"
    LINE_OF_CREDIT = "line_of_credit"
    BNPL = "bnpl"


class LoanStatus(str, Enum):
    """Loan status."""
    APPLICATION = "application"
    APPROVED = "approved"
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    WRITTEN_OFF = "written_off"
    IN_RESTRUCTURING = "in_restructuring"


class LoanPurpose(str, Enum):
    """Loan purpose (NCCP requirement)."""
    # Personal
    DEBT_CONSOLIDATION = "debt_consolidation"
    CAR_PURCHASE = "car_purchase"
    HOME_IMPROVEMENT = "home_improvement"
    EDUCATION = "education"
    WEDDING = "wedding"
    HOLIDAY = "holiday"
    MEDICAL = "medical"
    OTHER_PERSONAL = "other_personal"
    
    # Home
    HOME_PURCHASE = "home_purchase"
    REFINANCE = "refinance"
    CONSTRUCTION = "construction"
    
    # Business
    WORKING_CAPITAL = "working_capital"
    EQUIPMENT_PURCHASE = "equipment_purchase"
    BUSINESS_EXPANSION = "business_expansion"
    COMMERCIAL_PROPERTY = "commercial_property"


class RepaymentFrequency(str, Enum):
    """Repayment frequency."""
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"


class PropertyUsage(str, Enum):
    """Property usage (for home loans)."""
    OWNER_OCCUPIED = "owner_occupied"
    INVESTMENT = "investment"

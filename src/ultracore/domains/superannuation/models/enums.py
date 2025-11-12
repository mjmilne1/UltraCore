"""SuperAnnuation Enumerations"""
from enum import Enum


class TrusteeType(str, Enum):
    """Trustee structure type."""
    INDIVIDUAL = "individual"  # Members as individual trustees
    CORPORATE = "corporate"    # Corporate trustee structure


class MemberType(str, Enum):
    """Member type."""
    ADULT = "adult"      # 18+ years
    CHILD = "child"      # Under 18 years


class ContributionType(str, Enum):
    """Contribution type."""
    CONCESSIONAL = "concessional"  # Before-tax (15% tax)
    NON_CONCESSIONAL = "non_concessional"  # After-tax (0% tax)
    EMPLOYER = "employer"  # SG contributions
    SALARY_SACRIFICE = "salary_sacrifice"
    PERSONAL_DEDUCTIBLE = "personal_deductible"
    SPOUSE = "spouse"
    GOVERNMENT_COCONTRIBUTION = "government_cocontribution"


class PensionType(str, Enum):
    """Pension type."""
    ACCOUNT_BASED = "account_based"  # Standard retirement pension
    TTR = "ttr"  # Transition to Retirement
    ALLOCATED = "allocated"


class SMSFPhase(str, Enum):
    """SMSF phase for tax treatment."""
    ACCUMULATION = "accumulation"  # 15% tax on earnings
    PENSION = "pension"  # 0% tax on earnings! ??


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    RECTIFIED = "rectified"

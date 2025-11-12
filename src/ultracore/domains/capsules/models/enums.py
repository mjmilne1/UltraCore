"""Capsules Enumerations"""
from enum import Enum


class RiskLevel(str, Enum):
    """Risk levels for capsules."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"
    VERY_HIGH = "very_high"


class InvestmentGoal(str, Enum):
    """Investment goals."""
    WEALTH_ACCUMULATION = "wealth_accumulation"
    RETIREMENT = "retirement"
    INCOME_GENERATION = "income_generation"
    CAPITAL_PRESERVATION = "capital_preservation"
    TAX_EFFICIENCY = "tax_efficiency"
    ESG_IMPACT = "esg_impact"
    SPECULATION = "speculation"


class RebalanceFrequency(str, Enum):
    """Rebalancing frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class AssetClass(str, Enum):
    """Asset classes."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"
    CRYPTOCURRENCY = "cryptocurrency"
    CASH = "cash"
    ALTERNATIVE = "alternative"


class CapsuleStatus(str, Enum):
    """Capsule status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


class CapsuleStrategy(str, Enum):
    """Investment strategies."""
    DIVIDEND_GROWTH = "dividend_growth"
    VALUE = "value"
    GROWTH = "growth"
    MOMENTUM = "momentum"
    BALANCED = "balanced"
    AGGRESSIVE_GROWTH = "aggressive_growth"
    CONSERVATIVE = "conservative"
    ESG = "esg"
    THEMATIC = "thematic"
    GLOBAL_DIVERSIFIED = "global_diversified"

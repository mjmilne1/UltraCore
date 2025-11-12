"""Wealth Management Enumerations"""
from enum import Enum


class PortfolioType(str, Enum):
    """Portfolio type."""
    DIRECT = "direct"  # Direct shares
    MANAGED = "managed"  # Managed funds
    ETF = "etf"  # Exchange traded funds
    BALANCED = "balanced"  # Mixed portfolio
    SUPER = "super"  # Superannuation (SMSF)


class InvestmentStrategy(str, Enum):
    """Investment strategy."""
    CONSERVATIVE = "conservative"  # Low risk, capital preservation
    BALANCED = "balanced"  # Moderate risk, balanced growth
    GROWTH = "growth"  # Higher risk, capital growth
    AGGRESSIVE = "aggressive"  # High risk, maximum growth


class RiskTolerance(str, Enum):
    """Risk tolerance level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssetClass(str, Enum):
    """Asset class."""
    AUSTRALIAN_SHARES = "australian_shares"
    INTERNATIONAL_SHARES = "international_shares"
    PROPERTY = "property"
    FIXED_INCOME = "fixed_income"
    CASH = "cash"
    ALTERNATIVES = "alternatives"


class TradeSide(str, Enum):
    """Trade side."""
    BUY = "buy"
    SELL = "sell"


class SecurityType(str, Enum):
    """Security type."""
    SHARE = "share"  # ASX listed stock
    ETF = "etf"  # Exchange traded fund
    MANAGED_FUND = "managed_fund"
    BOND = "bond"
    TERM_DEPOSIT = "term_deposit"

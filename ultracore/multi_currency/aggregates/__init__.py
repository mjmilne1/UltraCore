"""
Multi-Currency Aggregates
Event-sourced aggregates for currency management
"""

from .currency import CurrencyAggregate, ExchangeRateAggregate
from .conversion import (
    CurrencyConversionAggregate,
    ForexTradeAggregate,
    CurrencyPreferenceAggregate,
    PortfolioValuationAggregate
)

__all__ = [
    "CurrencyAggregate",
    "ExchangeRateAggregate",
    "CurrencyConversionAggregate",
    "ForexTradeAggregate",
    "CurrencyPreferenceAggregate",
    "PortfolioValuationAggregate"
]

"""
Multi-Currency Support Module
Comprehensive multi-currency system with event sourcing, AI agents, and ML models
"""

from .events import (
    CurrencyAdded,
    CurrencyUpdated,
    CurrencyDeactivated,
    ExchangeRateUpdated,
    ExchangeRateBatchFetched,
    CurrencyConversionExecuted,
    CurrencyPreferenceSet,
    PortfolioValuationCalculated
)

from .aggregates import (
    CurrencyAggregate,
    ExchangeRateAggregate,
    CurrencyConversionAggregate,
    CurrencyPreferenceAggregate,
    PortfolioValuationAggregate
)

__all__ = [
    # Events
    "CurrencyAdded",
    "CurrencyUpdated",
    "CurrencyDeactivated",
    "ExchangeRateUpdated",
    "ExchangeRateBatchFetched",
    "CurrencyConversionExecuted",
    "CurrencyPreferenceSet",
    "PortfolioValuationCalculated",
    
    # Aggregates
    "CurrencyAggregate",
    "ExchangeRateAggregate",
    "CurrencyConversionAggregate",
    "CurrencyPreferenceAggregate",
    "PortfolioValuationAggregate"
]

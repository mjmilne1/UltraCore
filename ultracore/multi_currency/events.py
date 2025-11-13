"""
Multi-Currency Events
Kafka event schemas for currency management, exchange rates, and forex trading
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class CurrencyTopic(str, Enum):
    """Kafka topics for multi-currency events"""
    CURRENCIES = "multi_currency.currencies"
    EXCHANGE_RATES = "multi_currency.exchange_rates"
    CONVERSIONS = "multi_currency.conversions"
    FOREX_TRADES = "multi_currency.forex_trades"
    PREFERENCES = "multi_currency.preferences"


@dataclass
class MultiCurrencyEvent:
    """Base class for multi-currency events"""
    event_id: str
    event_type: str
    event_timestamp: str
    aggregate_id: str
    tenant_id: str
    user_id: str
    event_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for Kafka"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_timestamp": self.event_timestamp,
            "aggregate_id": self.aggregate_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "event_data": self.event_data
        }


# ============================================================================
# CURRENCY EVENTS
# ============================================================================

@dataclass
class CurrencyAddedEvent(MultiCurrencyEvent):
    """
    Currency added to system
    
    Event Data:
    - currency_code: str (ISO 4217, e.g., USD, EUR, GBP)
    - currency_name: str (e.g., US Dollar, Euro, British Pound)
    - currency_symbol: str (e.g., $, €, £)
    - decimal_places: int (typically 2)
    - is_active: bool
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"currency_added_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="CurrencyAdded",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class CurrencyUpdatedEvent(MultiCurrencyEvent):
    """Currency information updated"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"currency_updated_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="CurrencyUpdated",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class CurrencyDeactivatedEvent(MultiCurrencyEvent):
    """Currency deactivated"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"currency_deactivated_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="CurrencyDeactivated",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


# ============================================================================
# EXCHANGE RATE EVENTS
# ============================================================================

@dataclass
class ExchangeRateUpdatedEvent(MultiCurrencyEvent):
    """
    Exchange rate updated from external API
    
    Event Data:
    - base_currency: str (e.g., USD)
    - target_currency: str (e.g., EUR)
    - rate: float (e.g., 0.85)
    - inverse_rate: float (e.g., 1.176)
    - source: str (e.g., "exchangerate-api", "forex_api")
    - bid: Optional[float] (for forex trading)
    - ask: Optional[float] (for forex trading)
    - spread: Optional[float] (ask - bid)
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"exchange_rate_updated_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ExchangeRateUpdated",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class ExchangeRateFetchedEvent(MultiCurrencyEvent):
    """Batch exchange rates fetched from API"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"exchange_rate_fetched_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ExchangeRateFetched",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


# ============================================================================
# CURRENCY CONVERSION EVENTS
# ============================================================================

@dataclass
class CurrencyConversionExecutedEvent(MultiCurrencyEvent):
    """
    Currency conversion executed
    
    Event Data:
    - conversion_id: str
    - from_currency: str
    - to_currency: str
    - from_amount: float
    - to_amount: float
    - exchange_rate: float
    - conversion_fee: float
    - conversion_type: str (portfolio_valuation, forex_trade, user_conversion)
    - client_id: Optional[str]
    - portfolio_id: Optional[str]
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"conversion_executed_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="CurrencyConversionExecuted",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class ConversionHistoryRecordedEvent(MultiCurrencyEvent):
    """Conversion history recorded for audit trail"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"conversion_history_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ConversionHistoryRecorded",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


# ============================================================================
# FOREX TRADING EVENTS
# ============================================================================

@dataclass
class ForexTradeExecutedEvent(MultiCurrencyEvent):
    """
    Forex trade executed
    
    Event Data:
    - trade_id: str
    - client_id: str
    - currency_pair: str (e.g., EUR/USD)
    - trade_type: str (buy, sell)
    - amount: float
    - entry_rate: float
    - exit_rate: Optional[float]
    - leverage: float (e.g., 1.0, 10.0, 50.0)
    - profit_loss: Optional[float]
    - status: str (open, closed)
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"forex_trade_executed_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ForexTradeExecuted",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class ForexTradeClosedEvent(MultiCurrencyEvent):
    """Forex trade closed"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"forex_trade_closed_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ForexTradeClosed",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class ForexPositionUpdatedEvent(MultiCurrencyEvent):
    """Forex position updated (mark-to-market)"""
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"forex_position_updated_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="ForexPositionUpdated",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


# ============================================================================
# CURRENCY PREFERENCE EVENTS
# ============================================================================

@dataclass
class CurrencyPreferenceSetEvent(MultiCurrencyEvent):
    """
    User currency preference set
    
    Event Data:
    - client_id: str
    - display_currency: str (e.g., USD, EUR, AUD)
    - auto_convert: bool
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"currency_preference_set_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="CurrencyPreferenceSet",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )


@dataclass
class PortfolioValuationCalculatedEvent(MultiCurrencyEvent):
    """
    Multi-currency portfolio valuation calculated
    
    Event Data:
    - portfolio_id: str
    - client_id: str
    - display_currency: str
    - total_value: float
    - currency_breakdown: Dict[str, float] (e.g., {"USD": 10000, "EUR": 5000})
    - converted_values: Dict[str, float] (all in display currency)
    - exchange_rates_used: Dict[str, float]
    """
    def __init__(self, aggregate_id: str, tenant_id: str, user_id: str, event_data: Dict[str, Any]):
        super().__init__(
            event_id=f"portfolio_valuation_{aggregate_id}_{datetime.utcnow().timestamp()}",
            event_type="PortfolioValuationCalculated",
            event_timestamp=datetime.utcnow().isoformat(),
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_data=event_data
        )

"""
Currency and ExchangeRate Aggregates
Event-sourced currency management and exchange rate tracking
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.multi_currency.events import (
    MultiCurrencyEvent,
    CurrencyAddedEvent,
    CurrencyUpdatedEvent,
    CurrencyDeactivatedEvent,
    ExchangeRateUpdatedEvent,
    ExchangeRateFetchedEvent
)
from ultracore.multi_currency.event_publisher import get_event_publisher, CurrencyTopic


class CurrencyAggregate:
    """
    Currency aggregate for managing supported currencies
    Implements event sourcing pattern
    """
    
    def __init__(self, currency_code: str, tenant_id: str):
        self.currency_code = currency_code  # ISO 4217 code (USD, EUR, etc.)
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.currency_name: Optional[str] = None
        self.currency_symbol: Optional[str] = None
        self.decimal_places: int = 2
        self.is_active: bool = True
        self.added_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def add_currency(
        self,
        user_id: str,
        currency_name: str,
        currency_symbol: str,
        decimal_places: int = 2
    ):
        """Add new currency to system"""
        event = CurrencyAddedEvent(
            aggregate_id=self.currency_code,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "currency_code": self.currency_code,
                "currency_name": currency_name,
                "currency_symbol": currency_symbol,
                "decimal_places": decimal_places,
                "is_active": True
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_currency(
        self,
        user_id: str,
        **updates
    ):
        """Update currency information"""
        event = CurrencyUpdatedEvent(
            aggregate_id=self.currency_code,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=updates
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def deactivate(self, user_id: str):
        """Deactivate currency"""
        event = CurrencyDeactivatedEvent(
            aggregate_id=self.currency_code,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={}
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, CurrencyAddedEvent):
            self.currency_name = event.event_data["currency_name"]
            self.currency_symbol = event.event_data["currency_symbol"]
            self.decimal_places = event.event_data["decimal_places"]
            self.is_active = event.event_data["is_active"]
            self.added_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, CurrencyUpdatedEvent):
            for key, value in event.event_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, CurrencyDeactivatedEvent):
            self.is_active = False
            self.updated_at = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.CURRENCIES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success


class ExchangeRateAggregate:
    """
    Exchange Rate aggregate for tracking currency exchange rates
    Implements event sourcing pattern
    """
    
    def __init__(self, rate_id: str, tenant_id: str):
        self.rate_id = rate_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.base_currency: Optional[str] = None
        self.target_currency: Optional[str] = None
        self.rate: Optional[float] = None
        self.inverse_rate: Optional[float] = None
        self.source: Optional[str] = None
        self.bid: Optional[float] = None  # For forex trading
        self.ask: Optional[float] = None  # For forex trading
        self.spread: Optional[float] = None  # ask - bid
        self.last_updated: Optional[datetime] = None
        self.rate_history: List[Dict[str, Any]] = []
    
    def update_rate(
        self,
        user_id: str,
        base_currency: str,
        target_currency: str,
        rate: float,
        source: str,
        bid: Optional[float] = None,
        ask: Optional[float] = None
    ):
        """Update exchange rate from external source"""
        inverse_rate = 1 / rate if rate > 0 else 0
        spread = (ask - bid) if (bid and ask) else None
        
        event = ExchangeRateUpdatedEvent(
            aggregate_id=self.rate_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "base_currency": base_currency,
                "target_currency": target_currency,
                "rate": rate,
                "inverse_rate": inverse_rate,
                "source": source,
                "bid": bid,
                "ask": ask,
                "spread": spread
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def fetch_batch_rates(
        self,
        user_id: str,
        base_currency: str,
        rates: Dict[str, float],
        source: str
    ):
        """Fetch batch exchange rates from API"""
        event = ExchangeRateFetchedEvent(
            aggregate_id=self.rate_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "base_currency": base_currency,
                "rates": rates,
                "source": source,
                "fetched_at": datetime.utcnow().isoformat()
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, ExchangeRateUpdatedEvent):
            self.base_currency = event.event_data["base_currency"]
            self.target_currency = event.event_data["target_currency"]
            self.rate = event.event_data["rate"]
            self.inverse_rate = event.event_data["inverse_rate"]
            self.source = event.event_data["source"]
            self.bid = event.event_data.get("bid")
            self.ask = event.event_data.get("ask")
            self.spread = event.event_data.get("spread")
            self.last_updated = datetime.fromisoformat(event.event_timestamp)
            
            # Add to history
            self.rate_history.append({
                "rate": self.rate,
                "timestamp": event.event_timestamp,
                "source": self.source
            })
        
        elif isinstance(event, ExchangeRateFetchedEvent):
            self.base_currency = event.event_data["base_currency"]
            self.source = event.event_data["source"]
            self.last_updated = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.EXCHANGE_RATES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    def get_current_rate(self) -> Optional[float]:
        """Get current exchange rate"""
        return self.rate
    
    def get_rate_at_time(self, timestamp: datetime) -> Optional[float]:
        """Get exchange rate at specific time (from history)"""
        for record in reversed(self.rate_history):
            if datetime.fromisoformat(record["timestamp"]) <= timestamp:
                return record["rate"]
        return None

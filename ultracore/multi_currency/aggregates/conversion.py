"""
Currency Conversion and Forex Trade Aggregates
Event-sourced currency conversions and forex trading
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.multi_currency.events import (
    MultiCurrencyEvent,
    CurrencyConversionExecutedEvent,
    ConversionHistoryRecordedEvent,
    ForexTradeExecutedEvent,
    ForexTradeClosedEvent,
    ForexPositionUpdatedEvent,
    CurrencyPreferenceSetEvent,
    PortfolioValuationCalculatedEvent
)
from ultracore.multi_currency.event_publisher import get_event_publisher, CurrencyTopic


class CurrencyConversionAggregate:
    """
    Currency Conversion aggregate for tracking currency conversions
    Implements event sourcing pattern
    """
    
    def __init__(self, conversion_id: str, tenant_id: str):
        self.conversion_id = conversion_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.from_currency: Optional[str] = None
        self.to_currency: Optional[str] = None
        self.from_amount: Optional[float] = None
        self.to_amount: Optional[float] = None
        self.exchange_rate: Optional[float] = None
        self.conversion_fee: float = 0.0
        self.conversion_type: Optional[str] = None  # portfolio_valuation, forex_trade, user_conversion
        self.client_id: Optional[str] = None
        self.portfolio_id: Optional[str] = None
        self.executed_at: Optional[datetime] = None
        self.conversion_history: List[Dict[str, Any]] = []
    
    def execute_conversion(
        self,
        user_id: str,
        from_currency: str,
        to_currency: str,
        from_amount: float,
        exchange_rate: float,
        conversion_type: str,
        conversion_fee: float = 0.0,
        client_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ):
        """Execute currency conversion"""
        to_amount = from_amount * exchange_rate - conversion_fee
        
        event = CurrencyConversionExecutedEvent(
            aggregate_id=self.conversion_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "conversion_id": self.conversion_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "from_amount": from_amount,
                "to_amount": to_amount,
                "exchange_rate": exchange_rate,
                "conversion_fee": conversion_fee,
                "conversion_type": conversion_type,
                "client_id": client_id,
                "portfolio_id": portfolio_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
        
        # Record in history
        self.record_history(user_id)
    
    def record_history(self, user_id: str):
        """Record conversion in history for audit trail"""
        event = ConversionHistoryRecordedEvent(
            aggregate_id=self.conversion_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "conversion_id": self.conversion_id,
                "from_currency": self.from_currency,
                "to_currency": self.to_currency,
                "from_amount": self.from_amount,
                "to_amount": self.to_amount,
                "exchange_rate": self.exchange_rate,
                "executed_at": self.executed_at.isoformat() if self.executed_at else None
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, CurrencyConversionExecutedEvent):
            self.from_currency = event.event_data["from_currency"]
            self.to_currency = event.event_data["to_currency"]
            self.from_amount = event.event_data["from_amount"]
            self.to_amount = event.event_data["to_amount"]
            self.exchange_rate = event.event_data["exchange_rate"]
            self.conversion_fee = event.event_data["conversion_fee"]
            self.conversion_type = event.event_data["conversion_type"]
            self.client_id = event.event_data.get("client_id")
            self.portfolio_id = event.event_data.get("portfolio_id")
            self.executed_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ConversionHistoryRecordedEvent):
            self.conversion_history.append({
                "conversion_id": event.event_data["conversion_id"],
                "from_currency": event.event_data["from_currency"],
                "to_currency": event.event_data["to_currency"],
                "from_amount": event.event_data["from_amount"],
                "to_amount": event.event_data["to_amount"],
                "exchange_rate": event.event_data["exchange_rate"],
                "executed_at": event.event_data["executed_at"]
            })
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.CONVERSIONS, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success


class ForexTradeAggregate:
    """
    Forex Trade aggregate for forex trading
    Implements event sourcing pattern
    """
    
    def __init__(self, trade_id: str, tenant_id: str):
        self.trade_id = trade_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.currency_pair: Optional[str] = None  # e.g., EUR/USD
        self.trade_type: Optional[str] = None  # buy, sell
        self.amount: Optional[float] = None
        self.entry_rate: Optional[float] = None
        self.exit_rate: Optional[float] = None
        self.leverage: float = 1.0
        self.profit_loss: Optional[float] = None
        self.status: str = "open"  # open, closed
        self.opened_at: Optional[datetime] = None
        self.closed_at: Optional[datetime] = None
        self.current_rate: Optional[float] = None
        self.unrealized_pnl: Optional[float] = None
    
    def execute_trade(
        self,
        user_id: str,
        client_id: str,
        currency_pair: str,
        trade_type: str,
        amount: float,
        entry_rate: float,
        leverage: float = 1.0
    ):
        """Execute forex trade"""
        event = ForexTradeExecutedEvent(
            aggregate_id=self.trade_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "trade_id": self.trade_id,
                "client_id": client_id,
                "currency_pair": currency_pair,
                "trade_type": trade_type,
                "amount": amount,
                "entry_rate": entry_rate,
                "leverage": leverage,
                "status": "open"
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def close_trade(
        self,
        user_id: str,
        exit_rate: float
    ):
        """Close forex trade"""
        # Calculate profit/loss
        if self.trade_type == "buy":
            profit_loss = (exit_rate - self.entry_rate) * self.amount * self.leverage
        else:  # sell
            profit_loss = (self.entry_rate - exit_rate) * self.amount * self.leverage
        
        event = ForexTradeClosedEvent(
            aggregate_id=self.trade_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "trade_id": self.trade_id,
                "exit_rate": exit_rate,
                "profit_loss": profit_loss,
                "status": "closed"
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_position(
        self,
        user_id: str,
        current_rate: float
    ):
        """Update forex position with current market rate (mark-to-market)"""
        # Calculate unrealized P&L
        if self.trade_type == "buy":
            unrealized_pnl = (current_rate - self.entry_rate) * self.amount * self.leverage
        else:  # sell
            unrealized_pnl = (self.entry_rate - current_rate) * self.amount * self.leverage
        
        event = ForexPositionUpdatedEvent(
            aggregate_id=self.trade_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "trade_id": self.trade_id,
                "current_rate": current_rate,
                "unrealized_pnl": unrealized_pnl
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, ForexTradeExecutedEvent):
            self.client_id = event.event_data["client_id"]
            self.currency_pair = event.event_data["currency_pair"]
            self.trade_type = event.event_data["trade_type"]
            self.amount = event.event_data["amount"]
            self.entry_rate = event.event_data["entry_rate"]
            self.leverage = event.event_data["leverage"]
            self.status = event.event_data["status"]
            self.opened_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ForexTradeClosedEvent):
            self.exit_rate = event.event_data["exit_rate"]
            self.profit_loss = event.event_data["profit_loss"]
            self.status = event.event_data["status"]
            self.closed_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ForexPositionUpdatedEvent):
            self.current_rate = event.event_data["current_rate"]
            self.unrealized_pnl = event.event_data["unrealized_pnl"]
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.FOREX_TRADES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success


class CurrencyPreferenceAggregate:
    """
    Currency Preference aggregate for user currency preferences
    Implements event sourcing pattern
    """
    
    def __init__(self, preference_id: str, tenant_id: str):
        self.preference_id = preference_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.display_currency: str = "USD"  # Default
        self.auto_convert: bool = True
        self.set_at: Optional[datetime] = None
    
    def set_preference(
        self,
        user_id: str,
        client_id: str,
        display_currency: str,
        auto_convert: bool = True
    ):
        """Set user currency preference"""
        event = CurrencyPreferenceSetEvent(
            aggregate_id=self.preference_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "display_currency": display_currency,
                "auto_convert": auto_convert
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, CurrencyPreferenceSetEvent):
            self.client_id = event.event_data["client_id"]
            self.display_currency = event.event_data["display_currency"]
            self.auto_convert = event.event_data["auto_convert"]
            self.set_at = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.PREFERENCES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success


class PortfolioValuationAggregate:
    """
    Portfolio Valuation aggregate for multi-currency portfolio valuation
    Implements event sourcing pattern
    """
    
    def __init__(self, valuation_id: str, tenant_id: str):
        self.valuation_id = valuation_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[MultiCurrencyEvent] = []
        
        # State
        self.portfolio_id: Optional[str] = None
        self.client_id: Optional[str] = None
        self.display_currency: Optional[str] = None
        self.total_value: Optional[float] = None
        self.currency_breakdown: Dict[str, float] = {}
        self.converted_values: Dict[str, float] = {}
        self.exchange_rates_used: Dict[str, float] = {}
        self.calculated_at: Optional[datetime] = None
    
    def calculate_valuation(
        self,
        user_id: str,
        portfolio_id: str,
        client_id: str,
        display_currency: str,
        currency_breakdown: Dict[str, float],
        exchange_rates: Dict[str, float]
    ):
        """Calculate multi-currency portfolio valuation"""
        # Convert all currencies to display currency
        converted_values = {}
        total_value = 0.0
        
        for currency, amount in currency_breakdown.items():
            if currency == display_currency:
                converted_value = amount
            else:
                rate = exchange_rates.get(f"{currency}/{display_currency}", 1.0)
                converted_value = amount * rate
            
            converted_values[currency] = converted_value
            total_value += converted_value
        
        event = PortfolioValuationCalculatedEvent(
            aggregate_id=self.valuation_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "portfolio_id": portfolio_id,
                "client_id": client_id,
                "display_currency": display_currency,
                "total_value": total_value,
                "currency_breakdown": currency_breakdown,
                "converted_values": converted_values,
                "exchange_rates_used": exchange_rates
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: MultiCurrencyEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, PortfolioValuationCalculatedEvent):
            self.portfolio_id = event.event_data["portfolio_id"]
            self.client_id = event.event_data["client_id"]
            self.display_currency = event.event_data["display_currency"]
            self.total_value = event.event_data["total_value"]
            self.currency_breakdown = event.event_data["currency_breakdown"]
            self.converted_values = event.event_data["converted_values"]
            self.exchange_rates_used = event.event_data["exchange_rates_used"]
            self.calculated_at = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(CurrencyTopic.PREFERENCES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success

"""Event Sourcing Integration for OpenMarkets"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from ultracore.events.base import DomainEvent
from ultracore.infrastructure.event_store import EventStore
from .models import OrderSide, OrderType, OrderStatus, Exchange


class OpenMarketsEvent(DomainEvent):
    """Base class for OpenMarkets events."""
    
    aggregate_type: str = "OpenMarkets"
    source: str = "openmarkets"


class OrderPlacedEvent(OpenMarketsEvent):
    """Event emitted when an order is placed."""
    
    event_type: str = "OrderPlaced"
    
    order_id: str
    client_order_id: Optional[str]
    account_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    exchange: Exchange
    time_in_force: str
    placed_at: datetime
    
    # AI/Agent context
    agent_id: Optional[str] = None
    natural_language_request: Optional[str] = None
    confidence_score: Optional[float] = None


class OrderExecutedEvent(OpenMarketsEvent):
    """Event emitted when an order is executed (fully or partially)."""
    
    event_type: str = "OrderExecuted"
    
    order_id: str
    trade_id: str
    account_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    commission: Decimal
    gst: Decimal
    net_value: Decimal
    exchange: Exchange
    executed_at: datetime
    settlement_date: datetime
    
    # Order status after execution
    remaining_quantity: int
    filled_quantity: int
    status: OrderStatus


class OrderCancelledEvent(OpenMarketsEvent):
    """Event emitted when an order is cancelled."""
    
    event_type: str = "OrderCancelled"
    
    order_id: str
    account_id: str
    symbol: str
    cancelled_at: datetime
    cancellation_reason: Optional[str]
    filled_quantity: int
    remaining_quantity: int


class OrderRejectedEvent(OpenMarketsEvent):
    """Event emitted when an order is rejected."""
    
    event_type: str = "OrderRejected"
    
    order_id: str
    account_id: str
    symbol: str
    rejection_reason: str
    rejected_at: datetime


class TradeSettledEvent(OpenMarketsEvent):
    """Event emitted when a trade settles (T+2 for ASX)."""
    
    event_type: str = "TradeSettled"
    
    trade_id: str
    order_id: str
    account_id: str
    symbol: str
    quantity: int
    settlement_amount: Decimal
    settled_at: datetime


class PositionUpdatedEvent(OpenMarketsEvent):
    """Event emitted when a position is updated."""
    
    event_type: str = "PositionUpdated"
    
    account_id: str
    symbol: str
    quantity: int
    average_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    updated_at: datetime


class MarketDataReceivedEvent(OpenMarketsEvent):
    """Event emitted when market data is received (for ML training)."""
    
    event_type: str = "MarketDataReceived"
    
    symbol: str
    exchange: Exchange
    last_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    volume: int
    vwap: Decimal
    timestamp: datetime


class AccountOpenedEvent(OpenMarketsEvent):
    """Event emitted when a new trading account is opened."""
    
    event_type: str = "AccountOpened"
    
    account_id: str
    hin: str
    customer_id: str
    account_type: str
    opened_at: datetime
    kyc_verification_id: str


class KYCVerificationCompletedEvent(OpenMarketsEvent):
    """Event emitted when KYC verification is completed."""
    
    event_type: str = "KYCVerificationCompleted"
    
    verification_id: str
    customer_id: str
    status: str  # approved, rejected
    verified_at: datetime
    rejection_reason: Optional[str]


# Event Store Integration
class OpenMarketsEventStore:
    """Event store wrapper for OpenMarkets events."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.topic = "openmarkets.trading.events"
    
    async def append_event(self, event: OpenMarketsEvent) -> None:
        """Append event to event store."""
        await self.event_store.append(
            aggregate_id=event.aggregate_id,
            event_type=event.event_type,
            event_data=event.dict(),
            metadata={
                "source": "openmarkets",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def get_order_history(self, order_id: str) -> list[OpenMarketsEvent]:
        """Get complete event history for an order."""
        events = await self.event_store.get_events(
            aggregate_id=order_id,
            aggregate_type="OpenMarkets"
        )
        return events
    
    async def get_account_trades(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[OrderExecutedEvent]:
        """Get all trades for an account within date range."""
        # Query event store with filters
        events = await self.event_store.query(
            event_type="OrderExecuted",
            filters={"account_id": account_id},
            start_date=start_date,
            end_date=end_date
        )
        return events

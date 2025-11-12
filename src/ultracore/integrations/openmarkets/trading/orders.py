"""Event-Sourced Order Management System"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from ..client import OpenMarketsClient
from ..models import OrderRequest, OrderResponse, OrderSide, OrderType
from ..events import OrderPlacedEvent, OrderExecutedEvent, OpenMarketsEventStore
from ultracore.infrastructure.event_store import EventStore


class OrderManager:
    """
    Event-sourced order management with complete audit trail.
    
    All order operations flow through the event store for:
    - Complete audit trail
    - Temporal queries (what was the order status at time T?)
    - Event replay for analytics
    - Compliance reporting
    """
    
    def __init__(self, client: OpenMarketsClient, event_store: EventStore):
        self.client = client
        self.event_store = OpenMarketsEventStore(event_store)
    
    async def create_market_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        quantity: int,
        exchange: str = "ASX"
    ) -> OrderResponse:
        """Create a market order with immediate execution."""
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            exchange=exchange,
            time_in_force="IOC"  # Immediate or Cancel
        )
        
        return await self.client.place_order(order, account_id)
    
    async def create_limit_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: Decimal,
        exchange: str = "ASX",
        time_in_force: str = "DAY"
    ) -> OrderResponse:
        """Create a limit order at specified price."""
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            exchange=exchange,
            time_in_force=time_in_force
        )
        
        return await self.client.place_order(order, account_id)
    
    async def create_stop_loss_order(
        self,
        account_id: str,
        symbol: str,
        quantity: int,
        stop_price: Decimal,
        limit_price: Optional[Decimal] = None,
        exchange: str = "ASX"
    ) -> OrderResponse:
        """Create a stop-loss order for risk management."""
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT if limit_price else OrderType.STOP,
            quantity=quantity,
            stop_price=stop_price,
            price=limit_price,
            exchange=exchange,
            time_in_force="GTC"  # Good till cancelled
        )
        
        return await self.client.place_order(order, account_id)
    
    async def cancel_order(self, account_id: str, order_id: str) -> bool:
        """Cancel an existing order."""
        return await self.client.cancel_order(order_id, account_id)
    
    async def get_order_history(self, order_id: str) -> List[OrderPlacedEvent]:
        """Get complete event history for an order (audit trail)."""
        return await self.event_store.get_order_history(order_id)
    
    async def get_pending_orders(self, account_id: str) -> List[OrderResponse]:
        """Get all pending orders for an account."""
        return await self.client.get_orders(
            account_id=account_id,
            status="OPEN"
        )
    
    async def get_filled_orders(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[OrderExecutedEvent]:
        """Get all filled orders within date range from event store."""
        return await self.event_store.get_account_trades(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

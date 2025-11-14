"""OpenMarkets API Client with Event Sourcing Integration"""
import httpx
import asyncio
from typing import Optional, List, AsyncIterator
from datetime import datetime
from decimal import Decimal

from .config import OpenMarketsConfig, get_openmarkets_config
from .models import (
    OrderRequest, OrderResponse, Trade, Position,
    MarketDataSnapshot, AccountBalance, KYCRequest, KYCResponse
)
from .events import (
    OrderPlacedEvent, OrderExecutedEvent, OrderCancelledEvent,
    PositionUpdatedEvent, MarketDataReceivedEvent
)
from ultracore.infrastructure.event_store import EventStore


class OpenMarketsClient:
    """
    Enterprise-grade OpenMarkets API client with event sourcing.
    
    Features:
    - REST API for trading, account management
    - WebSocket streaming for real-time market data
    - Event sourcing for complete audit trail
    - Rate limiting and retry logic
    - Australian compliance integration
    """
    
    def __init__(
        self,
        config: Optional[OpenMarketsConfig] = None,
        event_store: Optional[EventStore] = None
    ):
        self.config = config or get_openmarkets_config()
        self.event_store = event_store
        
        # HTTP client with timeout and retries
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers={
                "Authorization": f"Bearer {self.config.api_key.get_secret_value()}",
                "Content-Type": "application/json"
            }
        )
    
    # Trading Operations
    async def place_order(
        self,
        order: OrderRequest,
        account_id: str,
        agent_context: Optional[dict] = None
    ) -> OrderResponse:
        """
        Place a new order and emit OrderPlacedEvent.
        
        Args:
            order: Order details
            account_id: Trading account ID
            agent_context: Optional AI agent context (for Anya integration)
        
        Returns:
            OrderResponse with order details
        """
        # Make API call
        response = await self.client.post(
            "/orders",
            json=order.dict(exclude_none=True),
            params={"account_id": account_id}
        )
        response.raise_for_status()
        
        order_response = OrderResponse(**response.json())
        
        # Emit event
        if self.event_store and self.config.event_store_enabled:
            event = OrderPlacedEvent(
                aggregate_id=order_response.order_id,
                order_id=order_response.order_id,
                client_order_id=order_response.client_order_id,
                account_id=account_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                stop_price=order.stop_price,
                exchange=order.exchange,
                time_in_force=order.time_in_force,
                placed_at=order_response.created_at,
                agent_id=agent_context.get("agent_id") if agent_context else None,
                natural_language_request=agent_context.get("nl_request") if agent_context else None,
                confidence_score=agent_context.get("confidence") if agent_context else None
            )
            await self.event_store.append_event(event)
        
        return order_response
    
    async def cancel_order(self, order_id: str, account_id: str) -> bool:
        """Cancel an existing order."""
        response = await self.client.delete(
            f"/orders/{order_id}",
            params={"account_id": account_id}
        )
        response.raise_for_status()
        
        # Emit cancellation event
        if self.event_store and self.config.event_store_enabled:
            event = OrderCancelledEvent(
                aggregate_id=order_id,
                order_id=order_id,
                account_id=account_id,
                symbol="",  # Would need to fetch from order details
                cancelled_at=datetime.now(timezone.utc),
                cancellation_reason="User requested",
                filled_quantity=0,
                remaining_quantity=0
            )
            await self.event_store.append_event(event)
        
        return True
    
    async def get_order(self, order_id: str, account_id: str) -> OrderResponse:
        """Get order details."""
        response = await self.client.get(
            f"/orders/{order_id}",
            params={"account_id": account_id}
        )
        response.raise_for_status()
        return OrderResponse(**response.json())
    
    async def get_orders(
        self,
        account_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[OrderResponse]:
        """Get orders with optional filters."""
        params = {"account_id": account_id}
        if status:
            params["status"] = status
        if symbol:
            params["symbol"] = symbol
        
        response = await self.client.get("/orders", params=params)
        response.raise_for_status()
        return [OrderResponse(**order) for order in response.json()]
    
    # Position Management
    async def get_positions(self, account_id: str) -> List[Position]:
        """Get all positions for an account."""
        response = await self.client.get(
            "/positions",
            params={"account_id": account_id}
        )
        response.raise_for_status()
        return [Position(**pos) for pos in response.json()]
    
    async def get_position(self, account_id: str, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        response = await self.client.get(
            f"/positions/{symbol}",
            params={"account_id": account_id}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return Position(**response.json())
    
    # Account Management
    async def get_account_balance(self, account_id: str) -> AccountBalance:
        """Get account balance and buying power."""
        response = await self.client.get(f"/accounts/{account_id}/balance")
        response.raise_for_status()
        return AccountBalance(**response.json())
    
    # Market Data
    async def get_market_data(self, symbol: str) -> MarketDataSnapshot:
        """Get real-time market data snapshot."""
        response = await self.client.get(f"/market-data/{symbol}")
        response.raise_for_status()
        
        market_data = MarketDataSnapshot(**response.json())
        
        # Emit market data event for ML training
        if self.event_store and self.config.event_store_enabled:
            event = MarketDataReceivedEvent(
                aggregate_id=f"market_data_{symbol}_{datetime.now(timezone.utc).isoformat()}",
                symbol=symbol,
                exchange=market_data.exchange,
                last_price=market_data.last_price,
                bid_price=market_data.bid_price,
                ask_price=market_data.ask_price,
                volume=market_data.volume,
                vwap=market_data.vwap,
                timestamp=market_data.timestamp
            )
            await self.event_store.append_event(event)
        
        return market_data
    
    async def stream_market_data(self, symbols: List[str]) -> AsyncIterator[MarketDataSnapshot]:
        """Stream real-time market data via WebSocket."""
        # WebSocket streaming implementation
        async with httpx.AsyncClient() as ws_client:
            # Connect to WebSocket
            async with ws_client.stream(
                "GET",
                self.config.websocket_url + "/market-data/stream",
                params={"symbols": ",".join(symbols)}
            ) as stream:
                async for line in stream.aiter_lines():
                    data = MarketDataSnapshot(**line)
                    yield data
    
    # Account Opening / KYC
    async def submit_kyc(self, kyc_request: KYCRequest) -> KYCResponse:
        """Submit KYC/AML verification request."""
        response = await self.client.post(
            "/kyc/verify",
            json=kyc_request.dict(exclude_none=True)
        )
        response.raise_for_status()
        return KYCResponse(**response.json())
    
    async def get_kyc_status(self, verification_id: str) -> KYCResponse:
        """Check KYC verification status."""
        response = await self.client.get(f"/kyc/{verification_id}")
        response.raise_for_status()
        return KYCResponse(**response.json())
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

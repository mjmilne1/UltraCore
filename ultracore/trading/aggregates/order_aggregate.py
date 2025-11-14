"""Order Aggregate - Event-sourced order lifecycle"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Dict, Optional
from decimal import Decimal
from ultracore.trading.events import *
from ultracore.trading.event_publisher import get_trading_event_publisher

@dataclass
class OrderAggregate:
    tenant_id: str
    order_id: str
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal("0")
    average_fill_price: Decimal = Decimal("0")
    _events: List[Any] = field(default_factory=list)
    
    def create(self, user_id: str, portfolio_id: str, symbol: str,
              order_type: OrderType, side: OrderSide, quantity: Decimal,
              limit_price: Optional[Decimal], stop_price: Optional[Decimal],
              time_in_force: TimeInForce, created_by: str):
        event = OrderCreated(
            tenant_id=self.tenant_id, order_id=self.order_id,
            user_id=user_id, portfolio_id=portfolio_id, symbol=symbol,
            order_type=order_type, side=side, quantity=quantity,
            limit_price=limit_price, stop_price=stop_price,
            time_in_force=time_in_force, created_by=created_by,
            created_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def validate(self, is_valid: bool, validation_checks: List[str], errors: List[str]):
        event = OrderValidated(
            tenant_id=self.tenant_id, order_id=self.order_id,
            is_valid=is_valid, validation_checks=validation_checks,
            errors=errors, validated_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def submit(self, venue: ExecutionVenue, venue_order_id: str):
        event = OrderSubmitted(
            tenant_id=self.tenant_id, order_id=self.order_id,
            venue=venue, venue_order_id=venue_order_id,
            submitted_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def accept(self, venue: ExecutionVenue, venue_order_id: str):
        event = OrderAccepted(
            tenant_id=self.tenant_id, order_id=self.order_id,
            venue=venue, venue_order_id=venue_order_id,
            accepted_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def reject(self, venue: ExecutionVenue, rejection_reason: str):
        event = OrderRejected(
            tenant_id=self.tenant_id, order_id=self.order_id,
            venue=venue, rejection_reason=rejection_reason,
            rejected_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def partially_fill(self, fill_id: str, filled_quantity: Decimal,
                      fill_price: Decimal, commission: Decimal, venue: ExecutionVenue):
        event = OrderPartiallyFilled(
            tenant_id=self.tenant_id, order_id=self.order_id,
            fill_id=fill_id, filled_quantity=filled_quantity,
            fill_price=fill_price, commission=commission,
            venue=venue, filled_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def fill(self, total_filled_quantity: Decimal, average_fill_price: Decimal,
            total_commission: Decimal, fills: List[Dict]):
        event = OrderFilled(
            tenant_id=self.tenant_id, order_id=self.order_id,
            total_filled_quantity=total_filled_quantity,
            average_fill_price=average_fill_price,
            total_commission=total_commission, fills=fills,
            filled_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def cancel(self, reason: str, cancelled_by: str):
        event = OrderCancelled(
            tenant_id=self.tenant_id, order_id=self.order_id,
            reason=reason, cancelled_by=cancelled_by,
            cancelled_at=datetime.utcnow()
        )
        self._apply(event)
        get_trading_event_publisher().publish_order_event(event)
    
    def _apply(self, event):
        if isinstance(event, OrderCreated):
            self.status = OrderStatus.PENDING
        elif isinstance(event, OrderSubmitted):
            self.status = OrderStatus.SUBMITTED
        elif isinstance(event, OrderAccepted):
            self.status = OrderStatus.ACCEPTED
        elif isinstance(event, OrderPartiallyFilled):
            self.status = OrderStatus.PARTIALLY_FILLED
            self.filled_quantity += event.filled_quantity
        elif isinstance(event, OrderFilled):
            self.status = OrderStatus.FILLED
            self.filled_quantity = event.total_filled_quantity
            self.average_fill_price = event.average_fill_price
        elif isinstance(event, OrderRejected):
            self.status = OrderStatus.REJECTED
        elif isinstance(event, OrderCancelled):
            self.status = OrderStatus.CANCELLED
        self._events.append(event)

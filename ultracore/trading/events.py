"""Trading & Execution Events - Kafka schemas"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    GTD = "gtd"  # Good Till Date


class ExecutionVenue(str, Enum):
    ASX = "asx"  # Australian Securities Exchange
    NYSE = "nyse"
    NASDAQ = "nasdaq"
    LSE = "lse"
    BROKER_A = "broker_a"
    BROKER_B = "broker_b"


@dataclass
class OrderCreated:
    tenant_id: str
    order_id: str
    user_id: str
    portfolio_id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: Decimal
    limit_price: Optional[Decimal]
    stop_price: Optional[Decimal]
    time_in_force: TimeInForce
    created_by: str
    created_at: datetime


@dataclass
class OrderValidated:
    tenant_id: str
    order_id: str
    is_valid: bool
    validation_checks: List[str]
    errors: List[str]
    validated_at: datetime


@dataclass
class OrderSubmitted:
    tenant_id: str
    order_id: str
    venue: ExecutionVenue
    venue_order_id: str
    submitted_at: datetime


@dataclass
class OrderAccepted:
    tenant_id: str
    order_id: str
    venue: ExecutionVenue
    venue_order_id: str
    accepted_at: datetime


@dataclass
class OrderRejected:
    tenant_id: str
    order_id: str
    venue: ExecutionVenue
    rejection_reason: str
    rejected_at: datetime


@dataclass
class OrderPartiallyFilled:
    tenant_id: str
    order_id: str
    fill_id: str
    filled_quantity: Decimal
    fill_price: Decimal
    commission: Decimal
    venue: ExecutionVenue
    filled_at: datetime


@dataclass
class OrderFilled:
    tenant_id: str
    order_id: str
    total_filled_quantity: Decimal
    average_fill_price: Decimal
    total_commission: Decimal
    fills: List[Dict[str, Any]]
    filled_at: datetime


@dataclass
class OrderCancelled:
    tenant_id: str
    order_id: str
    reason: str
    cancelled_by: str
    cancelled_at: datetime


@dataclass
class TradeExecuted:
    tenant_id: str
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    venue: ExecutionVenue
    executed_at: datetime


@dataclass
class PositionUpdated:
    tenant_id: str
    portfolio_id: str
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    updated_at: datetime


@dataclass
class RiskCheckPerformed:
    tenant_id: str
    order_id: str
    check_type: str
    passed: bool
    details: Dict[str, Any]
    checked_at: datetime

"""Pydantic models for OpenMarkets API schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Exchange(str, Enum):
    """Australian exchanges."""
    ASX = "ASX"
    CHIX = "Chi-X"
    NSX = "NSX"


class OrderRequest(BaseModel):
    """Order placement request."""
    
    symbol: str = Field(..., description="ASX ticker symbol (e.g., 'BHP')")
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: Optional[Decimal] = Field(None, description="Limit price (required for LIMIT orders)")
    stop_price: Optional[Decimal] = Field(None, description="Stop price (required for STOP orders)")
    exchange: Exchange = Field(default=Exchange.ASX)
    time_in_force: Literal["DAY", "GTC", "IOC", "FOK"] = Field(default="DAY")
    
    # Advanced order options
    iceberg_quantity: Optional[int] = Field(None, description="Iceberg order display quantity")
    client_order_id: Optional[str] = Field(None, description="Client-assigned order ID")
    
    @validator("price")
    def validate_limit_price(cls, v, values):
        """Validate price for limit orders."""
        if values.get("order_type") in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Price required for LIMIT orders")
        return v
    
    @validator("stop_price")
    def validate_stop_price(cls, v, values):
        """Validate stop price for stop orders."""
        if values.get("order_type") in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Stop price required for STOP orders")
        return v


class OrderResponse(BaseModel):
    """Order response from OpenMarkets."""
    
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    filled_quantity: int = 0
    remaining_quantity: int
    price: Optional[Decimal]
    average_price: Optional[Decimal]
    status: OrderStatus
    exchange: Exchange
    created_at: datetime
    updated_at: datetime
    
    # Trading details
    commission: Optional[Decimal] = None
    total_value: Optional[Decimal] = None


class Trade(BaseModel):
    """Trade execution details."""
    
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    value: Decimal
    commission: Decimal
    gst: Decimal
    net_value: Decimal
    exchange: Exchange
    executed_at: datetime
    settlement_date: datetime


class Position(BaseModel):
    """Current position in a security."""
    
    symbol: str
    quantity: int
    available_quantity: int  # Quantity available for trading (not locked in orders)
    average_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    day_pnl: Decimal
    exchange: Exchange
    updated_at: datetime


class MarketDataSnapshot(BaseModel):
    """Real-time market data snapshot."""
    
    symbol: str
    exchange: Exchange
    last_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    bid_size: int
    ask_size: int
    volume: int
    vwap: Decimal
    high: Decimal
    low: Decimal
    open: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: Decimal
    timestamp: datetime


class AccountBalance(BaseModel):
    """Account balance and buying power."""
    
    account_id: str
    cash_balance: Decimal
    buying_power: Decimal
    portfolio_value: Decimal
    total_equity: Decimal
    margin_used: Decimal
    margin_available: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    updated_at: datetime


class KYCRequest(BaseModel):
    """KYC/AML verification request."""
    
    first_name: str
    last_name: str
    date_of_birth: datetime
    email: str
    phone: str
    
    # Address
    street_address: str
    city: str
    state: str
    postcode: str
    country: str = "AU"
    
    # Identification
    id_type: Literal["drivers_license", "passport", "medicare"]
    id_number: str
    id_expiry: Optional[datetime]
    
    # Tax
    tfn: Optional[str] = Field(None, description="Tax File Number")
    tax_residency: List[str] = Field(default_factory=lambda: ["AU"])
    
    # Employment
    employment_status: Literal["employed", "self_employed", "retired", "student", "unemployed"]
    occupation: Optional[str]
    employer: Optional[str]
    
    # Source of wealth
    source_of_wealth: List[Literal["salary", "business", "investment", "inheritance", "other"]]
    annual_income_range: Literal["<50k", "50k-100k", "100k-250k", "250k-500k", ">500k"]


class KYCResponse(BaseModel):
    """KYC verification response."""
    
    verification_id: str
    status: Literal["pending", "approved", "rejected", "requires_documents"]
    account_id: Optional[str]
    hin: Optional[str] = Field(None, description="Holder Identification Number")
    created_at: datetime
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]

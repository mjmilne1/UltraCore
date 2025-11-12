"""Portfolio Models - Event-Sourced, UltraLedger Backed"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from pydantic import BaseModel

from .enums import (
    PortfolioType,
    InvestmentStrategy,
    RiskTolerance,
    AssetClass,
    TradeSide,
    SecurityType
)


class Portfolio(BaseModel):
    """
    Investment portfolio (Event-Sourced).
    
    Reconstructed from events.
    UltraLedger provides authoritative balances.
    
    Australian Context:
    - ASX securities (shares, ETFs)
    - CHESS sponsored holdings (HIN)
    - Franked dividends
    - Capital gains tax (CGT)
    - T+2 settlement
    """
    
    # Identity
    portfolio_id: str
    customer_id: str
    portfolio_name: str
    
    # Type and strategy
    portfolio_type: PortfolioType
    investment_strategy: InvestmentStrategy
    
    # Risk profile
    risk_tolerance: RiskTolerance
    time_horizon_years: int
    investment_objective: str
    
    # Balances (from UltraLedger)
    cash_balance: Decimal
    market_value: Decimal
    total_value: Decimal  # cash + market_value
    
    # Performance
    cost_basis: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    
    # Holdings
    holdings: List['Holding'] = []
    
    # Allocation
    target_allocation: Dict[AssetClass, Decimal] = {}
    current_allocation: Dict[AssetClass, Decimal] = {}
    
    # Linked accounts
    cash_account_id: str
    
    # Robo-advisory
    robo_managed: bool = False
    auto_rebalance: bool = False
    rebalance_threshold: Decimal = Decimal("0.05")  # 5% drift
    
    # CHESS
    hin: Optional[str] = None  # Holder Identification Number
    
    # Dates
    created_at: datetime
    updated_at: datetime
    version: int = 0
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class Holding(BaseModel):
    """
    Security holding in portfolio.
    
    Australian Securities:
    - ASX listed shares (e.g., CBA, BHP, WBC)
    - ETFs (e.g., VDHG, VAS, VGS)
    - LICs (Listed Investment Companies)
    """
    
    # Security
    security_code: str  # ASX code
    security_name: str
    security_type: SecurityType
    
    # Quantity
    quantity: int
    
    # Cost basis
    average_cost: Decimal
    total_cost: Decimal
    
    # Market value
    current_price: Decimal
    market_value: Decimal
    
    # Performance
    unrealized_gain: Decimal
    unrealized_gain_percentage: Decimal
    
    # Asset class
    asset_class: AssetClass
    
    # Dividends
    annual_dividend_yield: Decimal = Decimal("0.00")
    franking_level: Decimal = Decimal("0.00")  # 0-100%
    
    # Updated
    price_updated_at: datetime


class Trade(BaseModel):
    """
    Trade execution record.
    
    Australian Trading:
    - Market orders: Execute at best available price
    - Limit orders: Execute at specified price or better
    - ASX trading hours: 10:00am - 4:00pm AEST
    - Pre-market: 7:00am - 10:00am
    - After-market: 4:10pm - 5:00pm
    """
    
    # Identity
    trade_id: str
    portfolio_id: str
    
    # Trade
    side: TradeSide
    security_code: str
    security_name: str
    quantity: int
    price: Decimal
    
    # Costs
    trade_value: Decimal
    brokerage: Decimal
    total_cost: Decimal
    
    # Settlement
    trade_date: date
    settlement_date: date  # T+2
    settlement_status: str = "pending"  # pending, settled
    
    # CHESS
    chess_settlement: bool = True
    hin: Optional[str] = None
    
    # Tax (for sells)
    capital_gain: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    holding_period_days: Optional[int] = None
    cgt_discount: bool = False  # > 12 months = 50% discount
    
    # Executed
    executed_at: datetime
    executed_by: str
    
    # Market
    exchange: str = "ASX"
    order_type: str = "market"  # market, limit


class ManagedFund(BaseModel):
    """
    Managed fund investment.
    
    Australian Managed Funds:
    - APIR code (unique identifier)
    - Buy/sell spread
    - Management fees (MER)
    - Performance fees
    - Distribution frequency
    """
    
    # Identity
    fund_id: str
    portfolio_id: str
    
    # Fund details
    apir_code: str  # Australian fund identifier
    fund_name: str
    fund_manager: str
    
    # Holdings
    units: Decimal
    unit_price: Decimal
    market_value: Decimal
    
    # Cost
    average_cost: Decimal
    total_cost: Decimal
    
    # Performance
    unrealized_gain: Decimal
    unrealized_gain_percentage: Decimal
    
    # Fees
    management_fee: Decimal  # % p.a.
    performance_fee: Decimal  # % above benchmark
    buy_sell_spread: Decimal  # %
    
    # Distributions
    distribution_frequency: str  # quarterly, annually
    last_distribution: Optional[date] = None
    
    # Asset class
    asset_class: AssetClass
    
    # Updated
    updated_at: datetime


class MarginLoan(BaseModel):
    """
    Margin lending facility.
    
    Australian Margin Lending:
    - Borrow against portfolio value
    - LVR (Loan-to-Value Ratio) limits
    - Margin call if LVR breached
    - Interest charged on drawn balance
    """
    
    # Identity
    margin_loan_id: str
    portfolio_id: str
    customer_id: str
    
    # Facility
    approved_limit: Decimal
    drawn_balance: Decimal
    available_to_draw: Decimal
    
    # LVR (Loan-to-Value Ratio)
    portfolio_value: Decimal
    current_lvr: Decimal
    maximum_lvr: Decimal = Decimal("0.70")  # 70% typical
    buffer_lvr: Decimal = Decimal("0.75")  # 75% margin call
    
    # Interest
    interest_rate: Decimal
    interest_accrued: Decimal
    
    # Margin call
    in_margin_call: bool = False
    margin_call_amount: Optional[Decimal] = None
    margin_call_date: Optional[date] = None
    
    # Security
    secured_securities: List[str] = []  # Security codes
    
    # Dates
    created_at: datetime
    updated_at: datetime

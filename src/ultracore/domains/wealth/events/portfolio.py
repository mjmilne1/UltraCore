"""Portfolio Events - Investment Lifecycle"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import WealthEvent


class PortfolioCreatedEvent(WealthEvent):
    """
    Investment portfolio created.
    
    Portfolio types:
    - Direct shares (ASX stocks)
    - Managed funds
    - ETFs (Exchange Traded Funds)
    - Bonds and fixed income
    - International shares
    - Mixed/balanced
    """
    
    event_type: str = "PortfolioCreated"
    regulatory_event: bool = True
    
    portfolio_name: str
    portfolio_type: str  # direct, managed, etf, balanced
    investment_strategy: str  # conservative, balanced, growth, aggressive
    
    # Risk profile
    risk_tolerance: str  # low, medium, high
    time_horizon_years: int
    investment_objective: str
    
    # Linked accounts
    cash_account_id: str  # For settlements
    
    # Robo-advisory
    robo_managed: bool = False
    auto_rebalance: bool = False
    
    # Created
    created_at: datetime
    created_by: str


class PortfolioFundedEvent(WealthEvent):
    """
    Portfolio funded (cash deposit).
    
    UltraLedger:
    - DEBIT: Portfolio Cash Account (Asset)
    - CREDIT: Customer Account (Liability)
    """
    
    event_type: str = "PortfolioFunded"
    
    amount: Decimal
    source_account_id: str
    
    # Funding method
    funding_method: str = "transfer"  # transfer, direct_debit, bpay
    
    funded_at: datetime
    
    # UltraLedger
    ledger_entry_id: str


class TradeExecutedEvent(WealthEvent):
    """
    Trade executed (buy or sell).
    
    Australian Trading:
    - ASX trading hours: 10:00am - 4:00pm AEST
    - Settlement: T+2 (2 business days)
    - CHESS sponsored (HIN) or issuer sponsored (SRN)
    - Brokerage fees apply
    
    UltraLedger (Buy):
    - DEBIT: Investment Asset (cost basis)
    - DEBIT: Brokerage Expense
    - CREDIT: Portfolio Cash
    
    UltraLedger (Sell):
    - DEBIT: Portfolio Cash
    - CREDIT: Investment Asset (cost basis)
    - DEBIT/CREDIT: Capital Gain/Loss
    """
    
    event_type: str = "TradeExecuted"
    regulatory_event: bool = True
    
    trade_id: str
    
    # Trade details
    side: str  # buy, sell
    security_code: str  # ASX code (e.g., CBA, BHP, VDHG)
    security_name: str
    quantity: int
    price: Decimal
    
    # Costs
    trade_value: Decimal  # quantity * price
    brokerage: Decimal
    total_cost: Decimal  # trade_value + brokerage (buy) or - brokerage (sell)
    
    # Settlement
    trade_date: date
    settlement_date: date  # T+2
    chess_settlement: bool = True
    hin: Optional[str] = None  # Holder Identification Number
    
    # Tax (for sells)
    capital_gain: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    
    # Executed
    executed_at: datetime
    executed_by: str
    
    # Market
    exchange: str = "ASX"
    
    # UltraLedger
    ledger_entry_id: str


class DividendReceivedEvent(WealthEvent):
    """
    Dividend/distribution received.
    
    Australian Franking:
    - Fully franked: 100% franking credit
    - Partially franked: Partial franking credit
    - Unfranked: No franking credit
    
    Franking credits reduce tax payable.
    """
    
    event_type: str = "DividendReceived"
    regulatory_event: bool = True
    
    security_code: str
    security_name: str
    quantity_held: int
    
    # Dividend
    dividend_per_share: Decimal
    gross_dividend: Decimal
    
    # Franking
    franking_percentage: Decimal  # 0-100
    franking_credit: Decimal
    
    # Tax withheld (if applicable)
    tax_withheld: Decimal = Decimal("0.00")
    
    # Net payment
    net_dividend: Decimal
    
    # Dates
    ex_dividend_date: date
    payment_date: date
    
    # Received
    received_at: datetime
    
    # Reinvestment (DRP - Dividend Reinvestment Plan)
    drp_enabled: bool = False
    shares_acquired: Optional[int] = None


class RebalancedEvent(WealthEvent):
    """
    Portfolio rebalanced to target allocation.
    
    Robo-advisory trigger:
    - Drift from target allocation > threshold
    - Periodic rebalancing (quarterly/annually)
    - Market event triggered
    """
    
    event_type: str = "Rebalanced"
    
    # Rebalancing
    reason: str  # drift, periodic, market_event, manual
    
    # Allocations
    previous_allocation: Dict[str, Decimal]
    target_allocation: Dict[str, Decimal]
    new_allocation: Dict[str, Decimal]
    
    # Trades executed
    trades: List[str] = Field(default_factory=list)  # Trade IDs
    
    # Costs
    total_brokerage: Decimal
    tax_impact: Decimal = Decimal("0.00")
    
    # Rebalanced
    rebalanced_at: datetime
    rebalanced_by: str  # robo, advisor, customer

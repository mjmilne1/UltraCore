"""
UltraWealth Database Models

SQLAlchemy models for all wealth management entities
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Enum, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from decimal import Decimal
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class RiskProfile(str, enum.Enum):
    """Client risk profile"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"


class PortfolioStatus(str, enum.Enum):
    """Portfolio status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class OrderType(str, enum.Enum):
    """Order type"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    EXECUTED = "executed"
    PARTIALLY_EXECUTED = "partially_executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SOAType(str, enum.Enum):
    """Statement of Advice type"""
    INITIAL = "initial"
    REVIEW = "review"
    VARIATION = "variation"


# ============================================================================
# MODELS
# ============================================================================

class WealthClient(Base):
    """Wealth client profile"""
    __tablename__ = "wealth_clients"
    
    client_id = Column(String(50), primary_key=True)  # FK to ultracore clients
    risk_profile = Column(Enum(RiskProfile), nullable=False)
    investment_goals = Column(JSON)  # {goal_type, target_amount, target_date}
    time_horizon_years = Column(Integer)
    liquidity_needs = Column(JSON)  # {amount, frequency}
    tax_file_number = Column(String(20))
    
    # Compliance
    mda_contract_signed = Column(Boolean, default=False)
    mda_contract_date = Column(DateTime)
    soa_provided = Column(Boolean, default=False)
    best_interests_confirmed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolios = relationship("WealthPortfolio", back_populates="client")
    soas = relationship("WealthSOA", back_populates="client")


class WealthPortfolio(Base):
    """Investment portfolio"""
    __tablename__ = "wealth_portfolios"
    
    portfolio_id = Column(String(50), primary_key=True)
    client_id = Column(String(50), ForeignKey("wealth_clients.client_id"), nullable=False)
    
    # Portfolio details
    portfolio_name = Column(String(200), nullable=False)
    strategy_type = Column(String(50))  # mda, sma, etc.
    target_allocation = Column(JSON)  # {asset_class: percentage}
    
    # Status
    status = Column(Enum(PortfolioStatus), default=PortfolioStatus.PENDING)
    
    # Performance tracking
    inception_date = Column(DateTime, default=datetime.utcnow)
    current_value = Column(Numeric(precision=15, scale=2), default=0)
    total_invested = Column(Numeric(precision=15, scale=2), default=0)
    total_return = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("WealthClient", back_populates="portfolios")
    holdings = relationship("WealthHolding", back_populates="portfolio")
    orders = relationship("WealthOrder", back_populates="portfolio")
    performance_records = relationship("WealthPerformance", back_populates="portfolio")


class WealthHolding(Base):
    """Portfolio holding"""
    __tablename__ = "wealth_holdings"
    
    holding_id = Column(String(50), primary_key=True)
    portfolio_id = Column(String(50), ForeignKey("wealth_portfolios.portfolio_id"), nullable=False)
    
    # Security details
    ticker = Column(String(20), nullable=False)
    security_name = Column(String(200))
    asset_class = Column(String(50))  # equity, fixed_income, etc.
    
    # Position
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    average_cost = Column(Numeric(precision=15, scale=4), nullable=False)
    current_price = Column(Numeric(precision=15, scale=4))
    current_value = Column(Numeric(precision=15, scale=2))
    
    # Performance
    unrealized_gain_loss = Column(Numeric(precision=15, scale=2))
    unrealized_gain_loss_pct = Column(Float)
    
    # Timestamps
    acquired_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("WealthPortfolio", back_populates="holdings")


class WealthOrder(Base):
    """Trade order"""
    __tablename__ = "wealth_orders"
    
    order_id = Column(String(50), primary_key=True)
    portfolio_id = Column(String(50), ForeignKey("wealth_portfolios.portfolio_id"), nullable=False)
    
    # Order details
    ticker = Column(String(20), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    
    # Pricing
    order_price = Column(Numeric(precision=15, scale=4))  # Limit price, null for market
    executed_price = Column(Numeric(precision=15, scale=4))
    total_amount = Column(Numeric(precision=15, scale=2))
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Execution details
    broker_order_id = Column(String(100))
    executed_quantity = Column(Numeric(precision=15, scale=4), default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    # Relationships
    portfolio = relationship("WealthPortfolio", back_populates="orders")


class WealthSOA(Base):
    """Statement of Advice"""
    __tablename__ = "wealth_soa"
    
    soa_id = Column(String(50), primary_key=True)
    client_id = Column(String(50), ForeignKey("wealth_clients.client_id"), nullable=False)
    portfolio_id = Column(String(50), ForeignKey("wealth_portfolios.portfolio_id"))
    
    # SOA details
    soa_type = Column(Enum(SOAType), nullable=False)
    content = Column(JSON)  # Full SOA content
    
    # Compliance
    advisor_id = Column(String(50))
    advisor_name = Column(String(200))
    afsl_number = Column(String(20))
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    provided_to_client_at = Column(DateTime)
    client_acknowledged_at = Column(DateTime)
    
    # Relationships
    client = relationship("WealthClient", back_populates="soas")


class WealthPerformance(Base):
    """Portfolio performance record"""
    __tablename__ = "wealth_performance"
    
    performance_id = Column(String(50), primary_key=True)
    portfolio_id = Column(String(50), ForeignKey("wealth_portfolios.portfolio_id"), nullable=False)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Performance metrics
    total_return = Column(Float)  # Percentage
    benchmark_return = Column(Float)  # Percentage
    excess_return = Column(Float)  # vs benchmark
    
    # Risk metrics
    sharpe_ratio = Column(Float)
    volatility = Column(Float)  # Standard deviation
    max_drawdown = Column(Float)
    
    # Values
    start_value = Column(Numeric(precision=15, scale=2))
    end_value = Column(Numeric(precision=15, scale=2))
    net_contributions = Column(Numeric(precision=15, scale=2))
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("WealthPortfolio", back_populates="performance_records")


class WealthRebalance(Base):
    """Portfolio rebalancing record"""
    __tablename__ = "wealth_rebalances"
    
    rebalance_id = Column(String(50), primary_key=True)
    portfolio_id = Column(String(50), ForeignKey("wealth_portfolios.portfolio_id"), nullable=False)
    
    # Rebalance details
    trigger_reason = Column(String(200))  # drift, scheduled, client_request
    allocation_before = Column(JSON)
    allocation_after = Column(JSON)
    
    # Orders generated
    orders_created = Column(JSON)  # List of order IDs
    
    # Status
    status = Column(String(50))  # pending, in_progress, completed, failed
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

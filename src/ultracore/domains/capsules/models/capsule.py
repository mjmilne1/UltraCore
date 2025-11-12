"""Capsule Model - Pre-built Portfolio"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from .enums import (
    RiskLevel,
    InvestmentGoal,
    CapsuleStatus,
    CapsuleStrategy,
    RebalanceFrequency
)


class TargetAllocation(BaseModel):
    """Target allocation for a holding in capsule."""
    
    ticker: str
    asset_name: str
    target_percentage: Decimal
    min_percentage: Optional[Decimal] = None
    max_percentage: Optional[Decimal] = None
    
    class Config:
        json_encoders = {Decimal: str}


class Capsule(BaseModel):
    """
    Capsule - Pre-built Portfolio.
    
    From TuringMachines: 500 capsules, 2,428 holdings
    
    A Capsule is a pre-configured portfolio designed for
    specific investment goals, risk profiles, and strategies.
    
    Examples:
    - Aussie Dividend Champion (ASX dividend stocks)
    - Tech Titans (FAANG + tech growth)
    - ESG Future (sustainable investing)
    - Property Exposure (REITs)
    - Global Diversifier (worldwide allocation)
    - Bitcoin Futures (crypto exposure)
    
    Key Features:
    - Pre-defined asset allocation
    - Automatic rebalancing
    - Risk-managed
    - Goal-aligned
    - Transparent holdings
    
    Usage:
    1. Customer browses capsules
    2. Selects capsule matching goals/risk
    3. Invests lump sum or recurring
    4. Automatic rebalancing maintains targets
    5. Performance tracked vs benchmarks
    """
    
    # Identity
    capsule_id: str
    capsule_code: str  # e.g., "AUS-DIV-01"
    name: str
    description: str
    
    # Status
    status: CapsuleStatus = CapsuleStatus.ACTIVE
    
    # Strategy
    strategy: CapsuleStrategy
    investment_goals: List[InvestmentGoal]
    
    # Risk
    risk_level: RiskLevel
    volatility_target: Optional[Decimal] = None
    
    # Allocations
    target_allocations: List[TargetAllocation]
    total_holdings: int
    
    # Performance expectations
    expected_return_annual: Decimal  # e.g., 0.10 for 10%
    expected_volatility: Decimal
    sharpe_ratio_target: Optional[Decimal] = None
    
    # Income
    dividend_yield: Optional[Decimal] = None
    income_focus: bool = False
    
    # Rebalancing
    rebalance_frequency: RebalanceFrequency
    rebalance_threshold: Decimal  # e.g., 0.05 for 5% drift
    
    # Fees
    management_fee_annual: Decimal = Decimal("0.006")  # 0.60%
    
    # Minimum investment
    minimum_investment: Decimal = Decimal("1000")
    
    # Benchmarks
    benchmark_index: Optional[str] = None
    
    # Geography
    geographic_focus: List[str] = Field(default_factory=list)
    
    # ESG
    esg_focused: bool = False
    esg_score: Optional[Decimal] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    version: int = 1
    
    # Analytics
    total_subscribers: int = 0
    total_aum: Decimal = Decimal("0")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def risk_score(self) -> int:
        """Calculate risk score (1-100)."""
        risk_scores = {
            RiskLevel.VERY_LOW: 10,
            RiskLevel.LOW: 25,
            RiskLevel.MEDIUM: 50,
            RiskLevel.MEDIUM_HIGH: 65,
            RiskLevel.HIGH: 80,
            RiskLevel.VERY_HIGH: 95
        }
        return risk_scores.get(self.risk_level, 50)
    
    @property
    def allocation_summary(self) -> Dict[str, Decimal]:
        """Summarize allocations by asset class."""
        # Simplified - would group by actual asset classes
        return {
            "total_holdings": len(self.target_allocations),
            "total_percentage": sum(a.target_percentage for a in self.target_allocations)
        }


class CapsulePerformance(BaseModel):
    """Historical performance of a capsule."""
    
    capsule_id: str
    
    # Returns
    return_1d: Optional[Decimal] = None
    return_1w: Optional[Decimal] = None
    return_1m: Optional[Decimal] = None
    return_3m: Optional[Decimal] = None
    return_6m: Optional[Decimal] = None
    return_1y: Optional[Decimal] = None
    return_3y_annualized: Optional[Decimal] = None
    return_5y_annualized: Optional[Decimal] = None
    return_since_inception: Optional[Decimal] = None
    
    # Risk metrics
    volatility: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    
    # Benchmark comparison
    benchmark_return_1y: Optional[Decimal] = None
    alpha: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    
    # Updated
    as_of_date: datetime
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class CapsuleSubscription(BaseModel):
    """Customer subscription to a capsule."""
    
    subscription_id: str
    capsule_id: str
    customer_id: str
    portfolio_id: str
    
    # Investment
    invested_amount: Decimal
    current_value: Decimal
    units_held: Decimal
    
    # Status
    active: bool = True
    
    # Recurring
    recurring_investment: bool = False
    recurring_amount: Optional[Decimal] = None
    recurring_frequency: Optional[str] = None
    
    # Dates
    subscribed_at: datetime
    last_rebalanced_at: Optional[datetime] = None
    
    # Performance
    total_return: Decimal = Decimal("0")
    total_return_percentage: Decimal = Decimal("0")
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

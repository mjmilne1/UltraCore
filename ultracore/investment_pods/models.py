"""
Investment Pods Core Models
Data models for goal-based investment portfolios
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional
from enum import Enum


class AssetClass(Enum):
    """Asset class categories"""
    AUSTRALIAN_EQUITY = "australian_equity"
    INTERNATIONAL_EQUITY = "international_equity"
    FIXED_INCOME = "fixed_income"
    CASH = "cash"
    PROPERTY = "property"
    COMMODITIES = "commodities"


class ETFCategory(Enum):
    """ETF categories for portfolio construction"""
    AUSTRALIAN_SHARES_LARGE_CAP = "australian_shares_large_cap"
    AUSTRALIAN_SHARES_SMALL_CAP = "australian_shares_small_cap"
    INTERNATIONAL_SHARES_DEVELOPED = "international_shares_developed"
    INTERNATIONAL_SHARES_EMERGING = "international_shares_emerging"
    AUSTRALIAN_BONDS = "australian_bonds"
    INTERNATIONAL_BONDS = "international_bonds"
    AUSTRALIAN_PROPERTY = "australian_property"
    CASH_ENHANCED = "cash_enhanced"


@dataclass
class ETF:
    """ETF universe entry"""
    etf_code: str
    etf_name: str
    provider: str
    asset_class: AssetClass
    category: ETFCategory
    expense_ratio: Decimal
    aum: Decimal  # Assets Under Management
    avg_daily_volume: Decimal
    inception_date: date
    franking_yield: Decimal
    distribution_yield: Decimal
    
    # Historical performance
    returns_1y: Optional[Decimal] = None
    returns_3y: Optional[Decimal] = None
    returns_5y: Optional[Decimal] = None
    volatility: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    
    # Correlation data (for optimization)
    correlation_matrix: Optional[Dict[str, Decimal]] = None
    
    # Business rules compliance
    meets_aum_threshold: bool = True  # > $50M
    meets_volume_threshold: bool = True  # > $500K daily
    meets_expense_threshold: bool = True  # < 1.0%
    
    @property
    def is_eligible(self) -> bool:
        """Check if ETF meets all business rules"""
        return (
            self.meets_aum_threshold and
            self.meets_volume_threshold and
            self.meets_expense_threshold
        )


@dataclass
class OptimizationConstraints:
    """Portfolio optimization constraints"""
    # Asset class constraints
    min_equity: Decimal = Decimal("0")
    max_equity: Decimal = Decimal("100")
    min_defensive: Decimal = Decimal("0")
    max_defensive: Decimal = Decimal("100")
    
    # ETF constraints
    max_etfs: int = 6
    min_weight_per_etf: Decimal = Decimal("5.0")  # 5% minimum
    max_weight_per_etf: Decimal = Decimal("40.0")  # 40% maximum
    
    # Risk constraints
    max_portfolio_volatility: Optional[Decimal] = None
    max_portfolio_drawdown: Decimal = Decimal("15.0")  # Circuit breaker
    
    # Expense constraints
    max_total_expense_ratio: Decimal = Decimal("0.50")  # 0.50% max
    
    # Diversification
    max_single_provider: Decimal = Decimal("60.0")  # 60% max from one provider
    min_international_exposure: Decimal = Decimal("20.0")  # 20% min international


@dataclass
class GlidePathStrategy:
    """Glide path strategy for goal-based investing"""
    goal_type: str
    years_to_goal: int
    
    # Allocation targets by years remaining
    allocation_schedule: List[Dict]  # [{"years_remaining": 10, "equity": 80, "defensive": 20}]
    
    # Transition rules
    transition_frequency_months: int = 12  # Annual transitions
    auto_execute: bool = True
    client_approval_required: bool = False


@dataclass
class TaxOptimizationStrategy:
    """Australian tax optimization strategy"""
    # Franking credits
    target_franking_yield: Decimal = Decimal("2.0")  # 2% target
    franking_weight: Decimal = Decimal("0.3")  # 30% weight in optimization
    
    # Capital gains tax
    prefer_long_term_holdings: bool = True  # >12 months for 50% CGT discount
    harvest_losses: bool = True  # Tax loss harvesting
    
    # First Home Super Saver (FHSS)
    fhss_eligible: bool = False
    fhss_contribution_limit: Decimal = Decimal("15000")  # Annual limit
    
    # SMSF optimization
    smsf_account: bool = False
    pension_phase: bool = False


@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    current_drawdown: Decimal
    value_at_risk_95: Decimal  # 95% VaR
    conditional_var: Decimal  # CVaR
    downside_deviation: Decimal
    beta: Decimal
    
    # Risk status
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    circuit_breaker_distance: Decimal  # Distance to circuit breaker threshold


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""
    total_return: Decimal
    annualized_return: Decimal
    time_weighted_return: Decimal
    money_weighted_return: Decimal
    
    # Benchmark comparison
    benchmark_return: Decimal
    excess_return: Decimal
    tracking_error: Decimal
    information_ratio: Decimal
    
    # Tax-adjusted
    after_tax_return: Decimal
    franking_credits_value: Decimal
    cgt_liability: Decimal


@dataclass
class GoalProjection:
    """Goal projection and analysis"""
    goal_name: str
    target_amount: Decimal
    target_date: date
    current_value: Decimal
    
    # Projections
    projected_value: Decimal
    projected_completion_date: date
    probability_of_success: Decimal  # Monte Carlo simulation
    
    # Gap analysis
    shortfall: Decimal
    required_monthly_contribution: Decimal
    required_return_adjustment: Decimal
    
    # Scenarios
    best_case_value: Decimal  # 90th percentile
    worst_case_value: Decimal  # 10th percentile
    median_value: Decimal  # 50th percentile


@dataclass
class RebalancingDecision:
    """Rebalancing decision"""
    rebalance_required: bool
    rebalance_reason: str  # "drift", "glide_path", "risk_breach"
    
    # Drift analysis
    etf_drifts: List[Dict]  # [{"etf_code": "VAS", "current": 35, "target": 30, "drift": 5}]
    max_drift: Decimal
    
    # Trades required
    trades: List[Dict]  # [{"etf_code": "VAS", "action": "SELL", "units": 50, "value": 4275}]
    estimated_cost: Decimal
    estimated_cgt_impact: Decimal
    
    # Net benefit
    rebalance_benefit: Decimal
    net_benefit: Decimal  # benefit - cost - tax


@dataclass
class AnyaRecommendation:
    """Anya AI recommendation"""
    recommendation_id: str
    recommendation_type: str  # "contribution_increase", "goal_adjustment", "risk_reduction"
    title: str
    description: str
    
    # Impact analysis
    current_scenario: Dict
    recommended_scenario: Dict
    impact: Dict  # {"projected_value": 205000, "success_probability": 0.92}
    
    # Actions
    actions: List[Dict]  # [{"action": "increase_contribution", "from": 1500, "to": 1800}]
    
    # Confidence
    confidence: Decimal  # 0-1 scale
    reasoning: str
    
    # Client response
    accepted: Optional[bool] = None
    accepted_at: Optional[datetime] = None


@dataclass
class MarketConditions:
    """Current market conditions for risk assessment"""
    date: date
    
    # Market indices
    asx200_level: Decimal
    asx200_change_1d: Decimal
    asx200_change_1m: Decimal
    asx200_volatility: Decimal
    
    # Risk indicators
    vix_level: Decimal  # Volatility index
    credit_spread: Decimal
    yield_curve_slope: Decimal
    
    # Market regime
    regime: str  # "BULL", "BEAR", "SIDEWAYS", "CRISIS"
    regime_confidence: Decimal


@dataclass
class CircuitBreakerEvent:
    """Circuit breaker trigger event"""
    trigger_id: str
    pod_id: str
    triggered_at: datetime
    
    # Trigger conditions
    trigger_reason: str
    drawdown_at_trigger: Decimal
    volatility_at_trigger: Decimal
    market_conditions: MarketConditions
    
    # Defensive shift
    defensive_shift_executed: bool
    from_allocation: Dict
    to_allocation: Dict
    trades_executed: List[Dict]
    
    # Client notification
    client_notified: bool
    notification_sent_at: Optional[datetime] = None
    client_acknowledged: bool = False
    
    # Recovery
    recovery_date: Optional[date] = None
    recovery_complete: bool = False


# Business rules constants
BUSINESS_RULES = {
    "etf_selection": {
        "min_aum": Decimal("50000000"),  # $50M
        "min_daily_volume": Decimal("500000"),  # $500K
        "max_expense_ratio": Decimal("1.0"),  # 1.0%
        "min_track_record_months": 12
    },
    "portfolio_construction": {
        "max_etfs": 6,
        "min_etf_weight": Decimal("5.0"),
        "max_etf_weight": Decimal("40.0"),
        "max_single_provider": Decimal("60.0")
    },
    "risk_management": {
        "max_drawdown": Decimal("15.0"),  # Circuit breaker
        "rebalance_threshold": Decimal("5.0"),  # 5% drift
        "min_cash_buffer": Decimal("2.0")  # 2% cash
    },
    "tax_optimization": {
        "cgt_discount_holding_period_days": 365,  # 12 months
        "franking_credit_rate": Decimal("0.30"),  # 30% company tax
        "fhss_annual_limit": Decimal("15000"),
        "fhss_total_limit": Decimal("50000")
    }
}

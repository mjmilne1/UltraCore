"""
Investment Pods Event Schemas
Kafka-first event sourcing for goal-based investment portfolios
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from enum import Enum


class GoalType(Enum):
    """Types of financial goals"""
    FIRST_HOME = "first_home"
    RETIREMENT = "retirement"
    WEALTH_ACCUMULATION = "wealth_accumulation"
    EMERGENCY_FUND = "emergency_fund"
    EDUCATION = "education"
    CUSTOM = "custom"


class PodStatus(Enum):
    """Pod lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CLOSED = "closed"


class RiskTolerance(Enum):
    """Client risk tolerance levels"""
    VERY_CONSERVATIVE = 1
    CONSERVATIVE = 2
    MODERATELY_CONSERVATIVE = 3
    BALANCED = 4
    MODERATELY_AGGRESSIVE = 5
    AGGRESSIVE = 6
    VERY_AGGRESSIVE = 7


@dataclass
class PodCreated:
    """Event: Pod created"""
    pod_id: str
    tenant_id: str
    client_id: str
    goal_type: str  # GoalType
    goal_name: str
    target_amount: Decimal
    target_date: str  # ISO date
    risk_tolerance: int  # 1-10 scale
    current_value: Decimal
    monthly_contribution: Decimal
    created_at: datetime
    created_by: str  # "anya" or "client"


@dataclass
class PodOptimized:
    """Event: Pod allocation optimized"""
    pod_id: str
    tenant_id: str
    optimization_id: str
    etf_allocation: List[Dict]  # [{"etf_code": "VAS", "weight": 30.0, "expense_ratio": 0.10}]
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    total_expense_ratio: Decimal
    franking_yield: Decimal
    optimization_reason: str  # "initial", "glide_path", "parameter_change"
    optimized_at: datetime


@dataclass
class PodActivated:
    """Event: Pod activated and investments made"""
    pod_id: str
    tenant_id: str
    initial_trades: List[Dict]  # [{"etf_code": "VAS", "units": 100, "price": 85.50}]
    total_invested: Decimal
    activated_at: datetime


@dataclass
class GlidePathTransitionScheduled:
    """Event: Glide path transition scheduled"""
    pod_id: str
    tenant_id: str
    transition_id: str
    current_allocation: Dict  # {"equity": 80, "defensive": 20}
    target_allocation: Dict  # {"equity": 60, "defensive": 40}
    transition_date: str  # ISO date
    months_to_goal: int
    notification_sent: bool
    scheduled_at: datetime


@dataclass
class GlidePathTransitionExecuted:
    """Event: Glide path transition executed"""
    pod_id: str
    tenant_id: str
    transition_id: str
    from_allocation: Dict
    to_allocation: Dict
    trades_executed: List[Dict]
    total_cost: Decimal
    executed_at: datetime


@dataclass
class DownsideRiskDetected:
    """Event: Downside risk threshold breached"""
    pod_id: str
    tenant_id: str
    alert_id: str
    current_drawdown: Decimal
    max_allowed_drawdown: Decimal
    risk_status: str  # "WARNING", "BREACH"
    action_required: str  # "monitor", "defensive_shift"
    detected_at: datetime


@dataclass
class CircuitBreakerTriggered:
    """Event: Circuit breaker triggered, defensive shift executed"""
    pod_id: str
    tenant_id: str
    circuit_breaker_id: str
    trigger_reason: str  # "downside_breach", "volatility_spike"
    drawdown_at_trigger: Decimal
    defensive_shift_executed: bool
    trades_executed: List[Dict]
    client_notified: bool
    triggered_at: datetime


@dataclass
class PodRebalanced:
    """Event: Pod rebalanced due to 5% drift"""
    pod_id: str
    tenant_id: str
    rebalance_id: str
    drift_detected: List[Dict]  # [{"etf_code": "VAS", "current_weight": 35, "target_weight": 30, "drift": 5}]
    trades_executed: List[Dict]
    rebalance_cost: Decimal
    rebalanced_at: datetime


@dataclass
class ContributionMade:
    """Event: Client made contribution to Pod"""
    pod_id: str
    tenant_id: str
    contribution_id: str
    amount: Decimal
    contribution_type: str  # "monthly", "ad_hoc", "lump_sum"
    auto_allocated: bool
    allocation_trades: List[Dict]
    contributed_at: datetime


@dataclass
class WithdrawalRequested:
    """Event: Client requested withdrawal"""
    pod_id: str
    tenant_id: str
    withdrawal_id: str
    amount: Decimal
    reason: str
    impact_analysis: Dict  # {"new_projected_value": 190000, "goal_at_risk": true}
    anya_recommendation: str
    requested_at: datetime


@dataclass
class WithdrawalExecuted:
    """Event: Withdrawal executed"""
    pod_id: str
    tenant_id: str
    withdrawal_id: str
    amount: Decimal
    trades_executed: List[Dict]
    cgt_impact: Decimal
    executed_at: datetime


@dataclass
class UnderperformanceDetected:
    """Event: Pod underperforming goal"""
    pod_id: str
    tenant_id: str
    alert_id: str
    current_value: Decimal
    projected_value: Decimal
    target_value: Decimal
    shortfall: Decimal
    anya_solutions: List[Dict]  # [{"option": "increase_contribution", "new_amount": 1800, "projected": 202000}]
    detected_at: datetime


@dataclass
class GoalParametersUpdated:
    """Event: Goal parameters changed"""
    pod_id: str
    tenant_id: str
    update_id: str
    old_parameters: Dict
    new_parameters: Dict
    requires_reoptimization: bool
    updated_at: datetime
    updated_by: str  # "client" or "anya"


@dataclass
class PodProgressUpdated:
    """Event: Monthly progress update"""
    pod_id: str
    tenant_id: str
    update_id: str
    current_value: Decimal
    target_value: Decimal
    progress_percentage: Decimal
    monthly_return: Decimal
    projected_completion_date: str
    on_track: bool
    anya_message: str
    updated_at: datetime


@dataclass
class TaxOptimizationApplied:
    """Event: Tax optimization applied"""
    pod_id: str
    tenant_id: str
    optimization_id: str
    optimization_type: str  # "franking_credits", "cgt_discount", "fhss", "smsf"
    estimated_benefit: Decimal
    details: Dict
    applied_at: datetime


@dataclass
class AnyaInteraction:
    """Event: Client interacted with Anya"""
    pod_id: Optional[str]
    tenant_id: str
    interaction_id: str
    client_id: str
    interaction_type: str  # "question", "pod_creation", "goal_update"
    client_message: str
    anya_response: str
    action_taken: Optional[str]
    interacted_at: datetime


@dataclass
class PodCompleted:
    """Event: Pod reached goal"""
    pod_id: str
    tenant_id: str
    final_value: Decimal
    target_value: Decimal
    total_return: Decimal
    annualized_return: Decimal
    total_contributions: Decimal
    total_gains: Decimal
    franking_credits_earned: Decimal
    completed_at: datetime


@dataclass
class PodClosed:
    """Event: Pod closed"""
    pod_id: str
    tenant_id: str
    closure_reason: str  # "goal_completed", "client_request", "goal_abandoned"
    final_value: Decimal
    liquidation_trades: List[Dict]
    cgt_liability: Decimal
    closed_at: datetime


# Event registry for Kafka topics
EVENT_TYPES = {
    "pod.created": PodCreated,
    "pod.optimized": PodOptimized,
    "pod.activated": PodActivated,
    "pod.glide_path_transition_scheduled": GlidePathTransitionScheduled,
    "pod.glide_path_transition_executed": GlidePathTransitionExecuted,
    "pod.downside_risk_detected": DownsideRiskDetected,
    "pod.circuit_breaker_triggered": CircuitBreakerTriggered,
    "pod.rebalanced": PodRebalanced,
    "pod.contribution_made": ContributionMade,
    "pod.withdrawal_requested": WithdrawalRequested,
    "pod.withdrawal_executed": WithdrawalExecuted,
    "pod.underperformance_detected": UnderperformanceDetected,
    "pod.goal_parameters_updated": GoalParametersUpdated,
    "pod.progress_updated": PodProgressUpdated,
    "pod.tax_optimization_applied": TaxOptimizationApplied,
    "pod.anya_interaction": AnyaInteraction,
    "pod.completed": PodCompleted,
    "pod.closed": PodClosed,
}

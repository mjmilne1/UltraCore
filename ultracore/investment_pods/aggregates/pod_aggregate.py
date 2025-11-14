"""
Investment Pod Aggregate
Event-sourced aggregate for goal-based investment portfolios
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import uuid4

from ..events import (
    PodCreated, PodOptimized, PodActivated,
    GlidePathTransitionScheduled, GlidePathTransitionExecuted,
    DownsideRiskDetected, CircuitBreakerTriggered,
    PodRebalanced, ContributionMade, WithdrawalExecuted,
    GoalParametersUpdated, PodProgressUpdated,
    TaxOptimizationApplied, PodCompleted, PodClosed,
    GoalType, PodStatus, RiskTolerance
)


@dataclass
class ETFHolding:
    """ETF holding in Pod"""
    etf_code: str
    etf_name: str
    units: Decimal
    average_price: Decimal
    current_price: Decimal
    target_weight: Decimal
    current_weight: Decimal
    current_value: Decimal
    unrealized_gain: Decimal
    franking_yield: Decimal
    expense_ratio: Decimal


@dataclass
class GlidePathSchedule:
    """Glide path transition schedule"""
    transition_id: str
    transition_date: date
    months_to_goal: int
    target_equity_weight: Decimal
    target_defensive_weight: Decimal
    executed: bool
    executed_at: Optional[datetime] = None


@dataclass
class PodAggregate:
    """
    Event-sourced Pod aggregate
    Represents a goal-based investment portfolio
    """
    # Identity
    pod_id: str
    tenant_id: str
    client_id: str
    
    # Goal parameters
    goal_type: GoalType
    goal_name: str
    target_amount: Decimal
    target_date: date
    risk_tolerance: RiskTolerance
    
    # Financial state
    current_value: Decimal = Decimal("0")
    total_contributions: Decimal = Decimal("0")
    total_withdrawals: Decimal = Decimal("0")
    unrealized_gains: Decimal = Decimal("0")
    realized_gains: Decimal = Decimal("0")
    franking_credits_earned: Decimal = Decimal("0")
    
    # Contributions
    monthly_contribution: Decimal = Decimal("0")
    next_contribution_date: Optional[date] = None
    
    # Portfolio composition
    holdings: List[ETFHolding] = field(default_factory=list)
    current_allocation: Dict[str, Decimal] = field(default_factory=dict)  # {"equity": 80, "defensive": 20}
    target_allocation: Dict[str, Decimal] = field(default_factory=dict)
    
    # Optimization metrics
    expected_return: Decimal = Decimal("0")
    expected_volatility: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    current_drawdown: Decimal = Decimal("0")
    total_expense_ratio: Decimal = Decimal("0")
    
    # Glide path
    glide_path_enabled: bool = True
    glide_path_schedule: List[GlidePathSchedule] = field(default_factory=list)
    next_glide_path_date: Optional[date] = None
    
    # Risk management
    downside_protection_enabled: bool = True
    max_allowed_drawdown: Decimal = Decimal("15.0")  # 15% circuit breaker
    circuit_breaker_triggered: bool = False
    circuit_breaker_triggered_at: Optional[datetime] = None
    
    # Rebalancing
    rebalance_threshold: Decimal = Decimal("5.0")  # 5% drift
    last_rebalance_date: Optional[date] = None
    
    # Performance tracking
    inception_date: Optional[date] = None
    total_return: Decimal = Decimal("0")
    annualized_return: Decimal = Decimal("0")
    time_weighted_return: Decimal = Decimal("0")
    
    # Progress tracking
    progress_percentage: Decimal = Decimal("0")
    projected_completion_date: Optional[date] = None
    on_track: bool = True
    
    # Status
    status: PodStatus = PodStatus.DRAFT
    
    # Lifecycle
    created_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Event sourcing
    version: int = 0
    uncommitted_events: List = field(default_factory=list)
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        client_id: str,
        goal_type: GoalType,
        goal_name: str,
        target_amount: Decimal,
        target_date: date,
        risk_tolerance: RiskTolerance,
        monthly_contribution: Decimal,
        created_by: str = "anya"
    ) -> "PodAggregate":
        """Create new Pod"""
        pod_id = f"POD-{uuid4().hex[:12].upper()}"
        
        event = PodCreated(
            pod_id=pod_id,
            tenant_id=tenant_id,
            client_id=client_id,
            goal_type=goal_type.value,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date.isoformat(),
            risk_tolerance=risk_tolerance.value,
            current_value=Decimal("0"),
            monthly_contribution=monthly_contribution,
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        
        pod = cls(
            pod_id=pod_id,
            tenant_id=tenant_id,
            client_id=client_id,
            goal_type=goal_type,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date,
            risk_tolerance=risk_tolerance,
            monthly_contribution=monthly_contribution
        )
        
        pod._apply_event(event)
        return pod
    
    def optimize_allocation(
        self,
        etf_allocation: List[Dict],
        expected_return: Decimal,
        expected_volatility: Decimal,
        sharpe_ratio: Decimal,
        max_drawdown: Decimal,
        total_expense_ratio: Decimal,
        franking_yield: Decimal,
        optimization_reason: str = "initial"
    ) -> None:
        """Optimize Pod allocation"""
        optimization_id = f"OPT-{uuid4().hex[:8].upper()}"
        
        event = PodOptimized(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            optimization_id=optimization_id,
            etf_allocation=etf_allocation,
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_expense_ratio=total_expense_ratio,
            franking_yield=franking_yield,
            optimization_reason=optimization_reason,
            optimized_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def activate(self, initial_trades: List[Dict], total_invested: Decimal) -> None:
        """Activate Pod with initial investments"""
        event = PodActivated(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            initial_trades=initial_trades,
            total_invested=total_invested,
            activated_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def schedule_glide_path_transition(
        self,
        current_allocation: Dict,
        target_allocation: Dict,
        transition_date: date,
        months_to_goal: int
    ) -> None:
        """Schedule glide path transition"""
        transition_id = f"GLIDE-{uuid4().hex[:8].upper()}"
        
        event = GlidePathTransitionScheduled(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            transition_id=transition_id,
            current_allocation=current_allocation,
            target_allocation=target_allocation,
            transition_date=transition_date.isoformat(),
            months_to_goal=months_to_goal,
            notification_sent=False,
            scheduled_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def execute_glide_path_transition(
        self,
        transition_id: str,
        from_allocation: Dict,
        to_allocation: Dict,
        trades_executed: List[Dict],
        total_cost: Decimal
    ) -> None:
        """Execute glide path transition"""
        event = GlidePathTransitionExecuted(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            transition_id=transition_id,
            from_allocation=from_allocation,
            to_allocation=to_allocation,
            trades_executed=trades_executed,
            total_cost=total_cost,
            executed_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def detect_downside_risk(
        self,
        current_drawdown: Decimal,
        risk_status: str,
        action_required: str
    ) -> None:
        """Detect downside risk"""
        alert_id = f"RISK-{uuid4().hex[:8].upper()}"
        
        event = DownsideRiskDetected(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            alert_id=alert_id,
            current_drawdown=current_drawdown,
            max_allowed_drawdown=self.max_allowed_drawdown,
            risk_status=risk_status,
            action_required=action_required,
            detected_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def trigger_circuit_breaker(
        self,
        trigger_reason: str,
        drawdown_at_trigger: Decimal,
        trades_executed: List[Dict]
    ) -> None:
        """Trigger circuit breaker"""
        circuit_breaker_id = f"CB-{uuid4().hex[:8].upper()}"
        
        event = CircuitBreakerTriggered(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            circuit_breaker_id=circuit_breaker_id,
            trigger_reason=trigger_reason,
            drawdown_at_trigger=drawdown_at_trigger,
            defensive_shift_executed=True,
            trades_executed=trades_executed,
            client_notified=True,
            triggered_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def rebalance(
        self,
        drift_detected: List[Dict],
        trades_executed: List[Dict],
        rebalance_cost: Decimal
    ) -> None:
        """Rebalance Pod"""
        rebalance_id = f"REB-{uuid4().hex[:8].upper()}"
        
        event = PodRebalanced(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            rebalance_id=rebalance_id,
            drift_detected=drift_detected,
            trades_executed=trades_executed,
            rebalance_cost=rebalance_cost,
            rebalanced_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def add_contribution(
        self,
        amount: Decimal,
        contribution_type: str,
        allocation_trades: List[Dict]
    ) -> None:
        """Add contribution"""
        contribution_id = f"CONT-{uuid4().hex[:8].upper()}"
        
        event = ContributionMade(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            contribution_id=contribution_id,
            amount=amount,
            contribution_type=contribution_type,
            auto_allocated=True,
            allocation_trades=allocation_trades,
            contributed_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def update_goal_parameters(
        self,
        old_parameters: Dict,
        new_parameters: Dict,
        requires_reoptimization: bool,
        updated_by: str = "client"
    ) -> None:
        """Update goal parameters"""
        update_id = f"UPD-{uuid4().hex[:8].upper()}"
        
        event = GoalParametersUpdated(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            update_id=update_id,
            old_parameters=old_parameters,
            new_parameters=new_parameters,
            requires_reoptimization=requires_reoptimization,
            updated_at=datetime.utcnow(),
            updated_by=updated_by
        )
        
        self._apply_event(event)
    
    def update_progress(
        self,
        current_value: Decimal,
        monthly_return: Decimal,
        projected_completion_date: date,
        on_track: bool,
        anya_message: str
    ) -> None:
        """Update monthly progress"""
        update_id = f"PROG-{uuid4().hex[:8].upper()}"
        progress_percentage = (current_value / self.target_amount) * Decimal("100")
        
        event = PodProgressUpdated(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            update_id=update_id,
            current_value=current_value,
            target_value=self.target_amount,
            progress_percentage=progress_percentage,
            monthly_return=monthly_return,
            projected_completion_date=projected_completion_date.isoformat(),
            on_track=on_track,
            anya_message=anya_message,
            updated_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def apply_tax_optimization(
        self,
        optimization_type: str,
        estimated_benefit: Decimal,
        details: Dict
    ) -> None:
        """Apply tax optimization"""
        optimization_id = f"TAX-{uuid4().hex[:8].upper()}"
        
        event = TaxOptimizationApplied(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            optimization_id=optimization_id,
            optimization_type=optimization_type,
            estimated_benefit=estimated_benefit,
            details=details,
            applied_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def complete(
        self,
        final_value: Decimal,
        total_return: Decimal,
        annualized_return: Decimal
    ) -> None:
        """Complete Pod (goal reached)"""
        event = PodCompleted(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            final_value=final_value,
            target_value=self.target_amount,
            total_return=total_return,
            annualized_return=annualized_return,
            total_contributions=self.total_contributions,
            total_gains=final_value - self.total_contributions,
            franking_credits_earned=self.franking_credits_earned,
            completed_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def close(
        self,
        closure_reason: str,
        final_value: Decimal,
        liquidation_trades: List[Dict],
        cgt_liability: Decimal
    ) -> None:
        """Close Pod"""
        event = PodClosed(
            pod_id=self.pod_id,
            tenant_id=self.tenant_id,
            closure_reason=closure_reason,
            final_value=final_value,
            liquidation_trades=liquidation_trades,
            cgt_liability=cgt_liability,
            closed_at=datetime.utcnow()
        )
        
        self._apply_event(event)
    
    def _apply_event(self, event) -> None:
        """Apply event to aggregate state"""
        # Update state based on event type
        if isinstance(event, PodCreated):
            self.status = PodStatus.DRAFT
            self.created_at = event.created_at
        
        elif isinstance(event, PodOptimized):
            self.expected_return = event.expected_return
            self.expected_volatility = event.expected_volatility
            self.sharpe_ratio = event.sharpe_ratio
            self.max_drawdown = event.max_drawdown
            self.total_expense_ratio = event.total_expense_ratio
        
        elif isinstance(event, PodActivated):
            self.status = PodStatus.ACTIVE
            self.activated_at = event.activated_at
            self.inception_date = event.activated_at.date()
            self.current_value = event.total_invested
            self.total_contributions = event.total_invested
        
        elif isinstance(event, CircuitBreakerTriggered):
            self.circuit_breaker_triggered = True
            self.circuit_breaker_triggered_at = event.triggered_at
            self.status = PodStatus.PAUSED
        
        elif isinstance(event, ContributionMade):
            self.total_contributions += event.amount
            self.current_value += event.amount
        
        elif isinstance(event, PodCompleted):
            self.status = PodStatus.COMPLETED
            self.completed_at = event.completed_at
        
        elif isinstance(event, PodClosed):
            self.status = PodStatus.CLOSED
            self.closed_at = event.closed_at
        
        # Add to uncommitted events
        self.uncommitted_events.append(event)
        self.version += 1
    
    def get_uncommitted_events(self) -> List:
        """Get uncommitted events for publishing"""
        return self.uncommitted_events.copy()
    
    def mark_events_committed(self) -> None:
        """Mark events as committed"""
        self.uncommitted_events.clear()
    
    def calculate_required_monthly_contribution(self) -> Decimal:
        """Calculate required monthly contribution to reach goal"""
        months_remaining = (self.target_date.year - date.today().year) * 12 + \
                          (self.target_date.month - date.today().month)
        
        if months_remaining <= 0:
            return Decimal("0")
        
        # Future value calculation with expected return
        monthly_return = self.expected_return / Decimal("12")
        target_gap = self.target_amount - self.current_value
        
        if monthly_return == 0:
            return target_gap / Decimal(months_remaining)
        
        # PMT formula: FV = PMT * ((1 + r)^n - 1) / r
        # PMT = FV * r / ((1 + r)^n - 1)
        r = monthly_return / Decimal("100")
        n = Decimal(months_remaining)
        
        required_pmt = target_gap * r / ((Decimal("1") + r) ** n - Decimal("1"))
        return required_pmt.quantize(Decimal("0.01"))
    
    def is_on_track(self) -> bool:
        """Check if Pod is on track to reach goal"""
        required_contribution = self.calculate_required_monthly_contribution()
        return self.monthly_contribution >= required_contribution
    
    def calculate_progress_percentage(self) -> Decimal:
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return Decimal("0")
        return (self.current_value / self.target_amount * Decimal("100")).quantize(Decimal("0.01"))
    
    def needs_rebalancing(self) -> bool:
        """Check if Pod needs rebalancing"""
        for holding in self.holdings:
            drift = abs(holding.current_weight - holding.target_weight)
            if drift >= self.rebalance_threshold:
                return True
        return False
    
    def needs_glide_path_transition(self) -> bool:
        """Check if glide path transition is needed"""
        if not self.glide_path_enabled or not self.next_glide_path_date:
            return False
        return date.today() >= self.next_glide_path_date
    
    def is_downside_risk_breach(self) -> bool:
        """Check if downside risk threshold breached"""
        return self.current_drawdown >= self.max_allowed_drawdown

"""
Investment Pod Aggregate.

Goal-based investment product for UltraWealth.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class PodStatus(str, Enum):
    """Investment Pod status."""
    CREATED = "created"
    OPTIMIZED = "optimized"
    FUNDED = "funded"
    ACTIVE = "active"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    CLOSED = "closed"


class GoalType(str, Enum):
    """Investment goal types."""
    FIRST_HOME = "first_home"
    RETIREMENT = "retirement"
    WEALTH = "wealth"
    EDUCATION = "education"
    TRAVEL = "travel"
    CUSTOM = "custom"


class RiskTolerance(str, Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class InvestmentPod:
    """
    Investment Pod aggregate.
    
    Lifecycle:
    1. CREATED - Pod initialized with goal
    2. OPTIMIZED - Portfolio optimized by UltraOptimiser
    3. FUNDED - Initial deposit made
    4. ACTIVE - Pod actively managed
    5. ACHIEVED - Goal reached
    6. CLOSED - Pod closed
    """
    
    # Identity
    pod_id: str = field(default_factory=lambda: f"pod_{uuid4().hex[:12]}")
    tenant_id: str = ""
    user_id: str = ""
    
    # Goal
    goal_type: GoalType = GoalType.WEALTH
    goal_name: str = ""
    target_amount: Decimal = Decimal("0")
    target_date: Optional[datetime] = None
    
    # Contributions
    initial_deposit: Decimal = Decimal("0")
    monthly_contribution: Decimal = Decimal("0")
    current_value: Decimal = Decimal("0")
    
    # Risk
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    
    # Portfolio
    target_allocation: Dict[str, float] = field(default_factory=dict)
    current_allocation: Dict[str, Decimal] = field(default_factory=dict)
    
    # Performance
    total_return: Decimal = Decimal("0")
    total_return_pct: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    
    # Status
    status: PodStatus = PodStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    version: int = 1
    
    def __post_init__(self):
        """Initialize calculated fields."""
        if not self.goal_name:
            self.goal_name = f"{self.goal_type.value.replace('_', ' ').title()} Pod"
    
    def optimize_portfolio(
        self,
        target_allocation: Dict[str, float],
        expected_return: float,
        expected_volatility: float
    ):
        """
        Apply portfolio optimization from UltraOptimiser.
        
        Transitions: CREATED → OPTIMIZED
        """
        if self.status != PodStatus.CREATED:
            raise ValueError(f"Cannot optimize Pod in status: {self.status}")
        
        self.target_allocation = target_allocation
        self.status = PodStatus.OPTIMIZED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def fund(self, amount: Decimal):
        """
        Fund Pod with initial deposit.
        
        Transitions: OPTIMIZED → FUNDED
        """
        if self.status != PodStatus.OPTIMIZED:
            raise ValueError(f"Cannot fund Pod in status: {self.status}")
        
        if amount < self.initial_deposit:
            raise ValueError(
                f"Funding amount {amount} less than initial deposit {self.initial_deposit}"
            )
        
        self.current_value = amount
        self.status = PodStatus.FUNDED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def activate(self):
        """
        Activate Pod for trading.
        
        Transitions: FUNDED → ACTIVE
        """
        if self.status != PodStatus.FUNDED:
            raise ValueError(f"Cannot activate Pod in status: {self.status}")
        
        self.status = PodStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def update_value(self, new_value: Decimal):
        """Update current value and calculate returns."""
        if self.status not in [PodStatus.ACTIVE, PodStatus.PAUSED]:
            raise ValueError(f"Cannot update value in status: {self.status}")
        
        old_value = self.current_value
        self.current_value = new_value
        
        # Calculate returns
        total_invested = self.initial_deposit
        self.total_return = new_value - total_invested
        
        if total_invested > 0:
            self.total_return_pct = (self.total_return / total_invested) * 100
        
        # Update max drawdown
        if old_value > 0:
            drawdown = ((new_value - old_value) / old_value) * 100
            if drawdown < self.max_drawdown:
                self.max_drawdown = drawdown
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def check_circuit_breaker(self, threshold: Decimal = Decimal("15")) -> bool:
        """
        Check if circuit breaker should trigger.
        
        Circuit breaker triggers at 15% drawdown by default.
        
        Returns:
            True if circuit breaker should trigger
        """
        return abs(self.max_drawdown) >= threshold
    
    def pause(self, reason: str = ""):
        """
        Pause Pod trading.
        
        Transitions: ACTIVE → PAUSED
        """
        if self.status != PodStatus.ACTIVE:
            raise ValueError(f"Cannot pause Pod in status: {self.status}")
        
        self.status = PodStatus.PAUSED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def resume(self):
        """
        Resume Pod trading.
        
        Transitions: PAUSED → ACTIVE
        """
        if self.status != PodStatus.PAUSED:
            raise ValueError(f"Cannot resume Pod in status: {self.status}")
        
        self.status = PodStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def check_goal_achievement(self) -> bool:
        """Check if goal has been achieved."""
        return self.current_value >= self.target_amount
    
    def achieve_goal(self):
        """
        Mark goal as achieved.
        
        Transitions: ACTIVE → ACHIEVED
        """
        if self.status != PodStatus.ACTIVE:
            raise ValueError(f"Cannot achieve goal in status: {self.status}")
        
        if not self.check_goal_achievement():
            raise ValueError(
                f"Goal not achieved: current {self.current_value} < target {self.target_amount}"
            )
        
        self.status = PodStatus.ACHIEVED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def close(self):
        """
        Close Pod.
        
        Transitions: ACHIEVED/PAUSED → CLOSED
        """
        if self.status not in [PodStatus.ACHIEVED, PodStatus.PAUSED]:
            raise ValueError(f"Cannot close Pod in status: {self.status}")
        
        self.status = PodStatus.CLOSED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def calculate_progress(self) -> Decimal:
        """Calculate progress towards goal (0-100%)."""
        if self.target_amount == 0:
            return Decimal("0")
        
        progress = (self.current_value / self.target_amount) * 100
        return min(progress, Decimal("100"))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pod_id": self.pod_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "goal_type": self.goal_type.value,
            "goal_name": self.goal_name,
            "target_amount": float(self.target_amount),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "initial_deposit": float(self.initial_deposit),
            "monthly_contribution": float(self.monthly_contribution),
            "current_value": float(self.current_value),
            "risk_tolerance": self.risk_tolerance.value,
            "target_allocation": self.target_allocation,
            "current_allocation": {
                k: float(v) for k, v in self.current_allocation.items()
            },
            "total_return": float(self.total_return),
            "total_return_pct": float(self.total_return_pct),
            "max_drawdown": float(self.max_drawdown),
            "status": self.status.value,
            "progress": float(self.calculate_progress()),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }

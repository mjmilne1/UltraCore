"""
Investment Pods API Schemas.

Request and response models for Investment Pods API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# Request Schemas

class CreatePodRequest(BaseModel):
    """Request to create investment pod."""
    goal_type: str = Field(..., description="Goal type: first_home, retirement, wealth, education, travel, custom")
    goal_name: Optional[str] = Field(None, description="Custom goal name")
    target_amount: float = Field(..., gt=0, description="Target amount in AUD")
    target_date: Optional[str] = Field(None, description="Target date (ISO format)")
    initial_deposit: float = Field(..., ge=0, description="Initial deposit amount")
    monthly_contribution: float = Field(default=0, ge=0, description="Monthly contribution amount")
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance: conservative, moderate, aggressive")


class OptimizePodRequest(BaseModel):
    """Request to optimize pod portfolio."""
    target_allocation: Dict[str, float] = Field(..., description="Target allocation by asset class")
    expected_return: float = Field(..., description="Expected annual return (%)")
    expected_volatility: float = Field(..., description="Expected volatility (%)")


class FundPodRequest(BaseModel):
    """Request to fund pod."""
    amount: float = Field(..., gt=0, description="Funding amount")


class ContributePodRequest(BaseModel):
    """Request to contribute to pod."""
    amount: float = Field(..., gt=0, description="Contribution amount")


class WithdrawPodRequest(BaseModel):
    """Request to withdraw from pod."""
    amount: float = Field(..., gt=0, description="Withdrawal amount")
    reason: Optional[str] = Field(None, description="Withdrawal reason")


class RebalancePodRequest(BaseModel):
    """Request to rebalance pod."""
    target_allocation: Optional[Dict[str, float]] = Field(None, description="New target allocation (optional)")


class UpdatePodRequest(BaseModel):
    """Request to update pod settings."""
    goal_name: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[str] = None
    monthly_contribution: Optional[float] = Field(None, ge=0)
    risk_tolerance: Optional[str] = None


class PausePodRequest(BaseModel):
    """Request to pause pod."""
    reason: Optional[str] = Field(None, description="Pause reason")


# Response Schemas

class PodResponse(BaseModel):
    """Investment pod response."""
    pod_id: str
    tenant_id: str
    user_id: str
    goal_type: str
    goal_name: str
    target_amount: float
    target_date: Optional[str]
    initial_deposit: float
    monthly_contribution: float
    current_value: float
    risk_tolerance: str
    target_allocation: Dict[str, float]
    current_allocation: Dict[str, float]
    total_return: float
    total_return_pct: float
    max_drawdown: float
    status: str
    progress: float
    created_at: str
    updated_at: str
    version: int


class PodListResponse(BaseModel):
    """Pod list response."""
    pods: List[PodResponse]
    total: int
    page: int
    page_size: int


class PodPerformanceResponse(BaseModel):
    """Pod performance response."""
    pod_id: str
    current_value: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    daily_returns: List[float] = []
    cumulative_returns: List[float] = []
    timestamps: List[str] = []


class PodAllocationResponse(BaseModel):
    """Pod allocation response."""
    pod_id: str
    target_allocation: Dict[str, float]
    current_allocation: Dict[str, float]
    drift: Dict[str, float]
    needs_rebalance: bool
    rebalance_threshold: float


class PodRiskMetricsResponse(BaseModel):
    """Pod risk metrics response."""
    pod_id: str
    risk_tolerance: str
    current_volatility: float
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional Value at Risk (95%)
    max_drawdown: float
    beta: Optional[float] = None
    circuit_breaker_triggered: bool


class PodContributionResponse(BaseModel):
    """Pod contribution response."""
    contribution_id: str
    pod_id: str
    amount: float
    type: str  # initial, monthly, ad_hoc
    timestamp: str


class PodWithdrawalResponse(BaseModel):
    """Pod withdrawal response."""
    withdrawal_id: str
    pod_id: str
    amount: float
    reason: Optional[str]
    timestamp: str


class PodTransactionResponse(BaseModel):
    """Pod transaction response."""
    transaction_id: str
    pod_id: str
    type: str  # contribution, withdrawal, rebalance, dividend
    amount: float
    description: str
    timestamp: str


class PodTransactionListResponse(BaseModel):
    """Pod transaction list response."""
    transactions: List[PodTransactionResponse]
    total: int
    page: int
    page_size: int


class PodMetricsResponse(BaseModel):
    """Pod metrics response."""
    total_pods: int
    active_pods: int
    total_aum: float  # Assets Under Management
    by_goal_type: Dict[str, int]
    by_risk_tolerance: Dict[str, int]
    by_status: Dict[str, int]
    average_return_pct: float
    total_contributions: float
    total_withdrawals: float


class GlidepathResponse(BaseModel):
    """Glidepath response."""
    pod_id: str
    strategy: str  # linear, exponential, stepped
    current_allocation: Dict[str, float]
    projected_allocations: List[Dict]  # List of {date, allocation}
    years_to_target: float
    risk_reduction_rate: float


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    success: bool = False

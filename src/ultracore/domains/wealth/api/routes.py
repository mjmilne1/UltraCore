"""
Investment Pods API Routes.

REST API endpoints for Investment Pods.
"""

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..models.investment_pod import (
    GoalType,
    InvestmentPod,
    PodStatus,
    RiskTolerance,
)
from ..services.glide_path_engine import GlidePathEngine, GlidePathStrategy
from .schemas import (
    ContributePodRequest,
    CreatePodRequest,
    ErrorResponse,
    FundPodRequest,
    GlidepathResponse,
    MessageResponse,
    OptimizePodRequest,
    PausePodRequest,
    PodAllocationResponse,
    PodListResponse,
    PodMetricsResponse,
    PodPerformanceResponse,
    PodResponse,
    PodRiskMetricsResponse,
    PodTransactionListResponse,
    PodTransactionResponse,
    RebalancePodRequest,
    UpdatePodRequest,
    WithdrawPodRequest,
)

router = APIRouter(prefix="/wealth/pods", tags=["investment-pods"])


# Helper functions
def get_tenant_id() -> str:
    """Get tenant ID from request context."""
    # In production: extract from JWT token or request headers
    return "default_tenant"


def get_user_id() -> str:
    """Get user ID from request context."""
    # In production: extract from JWT token
    return "default_user"


# Pod Lifecycle Endpoints

@router.post("/", response_model=PodResponse)
async def create_pod(request: CreatePodRequest):
    """
    Create new investment pod.
    
    Creates a new goal-based investment pod with specified parameters.
    """
    try:
        tenant_id = get_tenant_id()
        user_id = get_user_id()
        
        pod = InvestmentPod(
            tenant_id=tenant_id,
            user_id=user_id,
            goal_type=GoalType(request.goal_type),
            goal_name=request.goal_name or "",
            target_amount=Decimal(str(request.target_amount)),
            initial_deposit=Decimal(str(request.initial_deposit)),
            monthly_contribution=Decimal(str(request.monthly_contribution)),
            risk_tolerance=RiskTolerance(request.risk_tolerance)
        )
        
        # In production: save to database
        
        return PodResponse(**pod.to_dict())
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PodListResponse)
async def list_pods(
    status: Optional[str] = Query(None),
    goal_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List investment pods with optional filtering."""
    try:
        # In production: query from database with filters
        pods = []
        
        return PodListResponse(
            pods=[],
            total=0,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pod_id}", response_model=PodResponse)
async def get_pod(pod_id: str):
    """Get pod by ID."""
    try:
        # In production: query from database
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{pod_id}", response_model=PodResponse)
async def update_pod(pod_id: str, request: UpdatePodRequest):
    """Update pod settings."""
    try:
        # In production: get pod, update, save
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pod_id}", response_model=MessageResponse)
async def close_pod(pod_id: str):
    """Close pod."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pod Operations

@router.post("/{pod_id}/optimize", response_model=PodResponse)
async def optimize_pod(pod_id: str, request: OptimizePodRequest):
    """Optimize pod portfolio."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/fund", response_model=PodResponse)
async def fund_pod(pod_id: str, request: FundPodRequest):
    """Fund pod with initial deposit."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/activate", response_model=PodResponse)
async def activate_pod(pod_id: str):
    """Activate pod for trading."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/contribute", response_model=PodResponse)
async def contribute_to_pod(pod_id: str, request: ContributePodRequest):
    """Add contribution to pod."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/withdraw", response_model=PodResponse)
async def withdraw_from_pod(pod_id: str, request: WithdrawPodRequest):
    """Withdraw funds from pod."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/rebalance", response_model=PodResponse)
async def rebalance_pod(pod_id: str, request: RebalancePodRequest):
    """Rebalance pod portfolio."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/pause", response_model=PodResponse)
async def pause_pod(pod_id: str, request: PausePodRequest):
    """Pause pod trading."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pod_id}/resume", response_model=PodResponse)
async def resume_pod(pod_id: str):
    """Resume pod trading."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics

@router.get("/{pod_id}/performance", response_model=PodPerformanceResponse)
async def get_pod_performance(pod_id: str):
    """Get pod performance metrics."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pod_id}/allocation", response_model=PodAllocationResponse)
async def get_pod_allocation(pod_id: str):
    """Get pod allocation details."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pod_id}/risk", response_model=PodRiskMetricsResponse)
async def get_pod_risk_metrics(pod_id: str):
    """Get pod risk metrics."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pod_id}/transactions", response_model=PodTransactionListResponse)
async def list_pod_transactions(
    pod_id: str,
    transaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List pod transactions."""
    try:
        return PodTransactionListResponse(
            transactions=[],
            total=0,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pod_id}/glidepath", response_model=GlidepathResponse)
async def get_pod_glidepath(pod_id: str):
    """Get pod glidepath projection."""
    try:
        raise HTTPException(status_code=404, detail="Pod not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=PodMetricsResponse)
async def get_pod_metrics():
    """Get aggregate pod metrics."""
    try:
        metrics = {
            "total_pods": 0,
            "active_pods": 0,
            "total_aum": 0.0,
            "by_goal_type": {},
            "by_risk_tolerance": {},
            "by_status": {},
            "average_return_pct": 0.0,
            "total_contributions": 0.0,
            "total_withdrawals": 0.0
        }
        
        return PodMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

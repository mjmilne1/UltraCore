"""
Unit tests for Investment Pods.

Tests pod models, glidepath engine, and repository.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.ultracore.domains.wealth.models.investment_pod import (
    InvestmentPod,
    GoalType,
    RiskTolerance,
    PodStatus,
)
from src.ultracore.domains.wealth.services.glide_path_engine import (
    GlidePathEngine,
    GlidePathStrategy,
)


class TestInvestmentPod:
    """Test Investment Pod model."""
    
    def test_create_pod(self):
        """Test pod creation."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.FIRST_HOME,
            goal_name="First Home Deposit",
            target_amount=Decimal("100000"),
            initial_deposit=Decimal("10000"),
            monthly_contribution=Decimal("2000"),
            risk_tolerance=RiskTolerance.MODERATE
        )
        
        assert pod.pod_id is not None
        assert pod.status == PodStatus.DRAFT
        assert pod.current_value == Decimal("0")
    
    def test_fund_pod(self):
        """Test pod funding."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.RETIREMENT,
            goal_name="Retirement Fund",
            target_amount=Decimal("500000"),
            initial_deposit=Decimal("50000"),
            monthly_contribution=Decimal("1000"),
            risk_tolerance=RiskTolerance.AGGRESSIVE
        )
        
        pod.fund(Decimal("50000"))
        
        assert pod.status == PodStatus.FUNDED
        assert pod.current_value == Decimal("50000")
        assert pod.funded_at is not None
    
    def test_activate_pod(self):
        """Test pod activation."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.WEALTH,
            goal_name="Wealth Building",
            target_amount=Decimal("1000000"),
            initial_deposit=Decimal("100000"),
            monthly_contribution=Decimal("5000"),
            risk_tolerance=RiskTolerance.AGGRESSIVE
        )
        
        pod.fund(Decimal("100000"))
        pod.activate()
        
        assert pod.status == PodStatus.ACTIVE
        assert pod.activated_at is not None
    
    def test_update_value(self):
        """Test value update."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.EDUCATION,
            goal_name="Education Fund",
            target_amount=Decimal("200000"),
            initial_deposit=Decimal("20000"),
            monthly_contribution=Decimal("1500"),
            risk_tolerance=RiskTolerance.MODERATE
        )
        
        pod.fund(Decimal("20000"))
        pod.activate()
        
        new_value = Decimal("22000")
        pod.update_value(new_value)
        
        assert pod.current_value == new_value
    
    def test_pause_resume(self):
        """Test pause and resume."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.TRAVEL,
            goal_name="Travel Fund",
            target_amount=Decimal("50000"),
            initial_deposit=Decimal("5000"),
            monthly_contribution=Decimal("500"),
            risk_tolerance=RiskTolerance.CONSERVATIVE
        )
        
        pod.fund(Decimal("5000"))
        pod.activate()
        
        pod.pause("Temporary pause")
        assert pod.status == PodStatus.PAUSED
        
        pod.resume()
        assert pod.status == PodStatus.ACTIVE
    
    def test_close_pod(self):
        """Test pod closure."""
        pod = InvestmentPod(
            tenant_id="test",
            user_id="user-001",
            goal_type=GoalType.CUSTOM,
            goal_name="Custom Goal",
            target_amount=Decimal("75000"),
            initial_deposit=Decimal("7500"),
            monthly_contribution=Decimal("750"),
            risk_tolerance=RiskTolerance.MODERATE
        )
        
        pod.fund(Decimal("7500"))
        pod.activate()
        
        pod.close()
        
        assert pod.status == PodStatus.CLOSED
        assert pod.closed_at is not None


class TestGlidePathEngine:
    """Test Glidepath Engine."""
    
    def test_linear_strategy(self):
        """Test linear glidepath strategy."""
        engine = GlidePathEngine(
            strategy=GlidePathStrategy.LINEAR,
            initial_equity_pct=0.8,
            final_equity_pct=0.3,
            years_to_target=10
        )
        
        # Test at different points
        allocation_10y = engine.get_allocation(years_remaining=10)
        assert allocation_10y["equity"] == pytest.approx(0.8, rel=0.01)
        
        allocation_5y = engine.get_allocation(years_remaining=5)
        assert allocation_5y["equity"] == pytest.approx(0.55, rel=0.01)
        
        allocation_0y = engine.get_allocation(years_remaining=0)
        assert allocation_0y["equity"] == pytest.approx(0.3, rel=0.01)
    
    def test_exponential_strategy(self):
        """Test exponential glidepath strategy."""
        engine = GlidePathEngine(
            strategy=GlidePathStrategy.EXPONENTIAL,
            initial_equity_pct=0.8,
            final_equity_pct=0.3,
            years_to_target=10
        )
        
        allocation_10y = engine.get_allocation(years_remaining=10)
        assert allocation_10y["equity"] == pytest.approx(0.8, rel=0.01)
        
        allocation_0y = engine.get_allocation(years_remaining=0)
        assert allocation_0y["equity"] == pytest.approx(0.3, rel=0.01)
    
    def test_stepped_strategy(self):
        """Test stepped glidepath strategy."""
        engine = GlidePathEngine(
            strategy=GlidePathStrategy.STEPPED,
            initial_equity_pct=0.8,
            final_equity_pct=0.3,
            years_to_target=10
        )
        
        allocation_10y = engine.get_allocation(years_remaining=10)
        allocation_9y = engine.get_allocation(years_remaining=9)
        
        # Stepped strategy should have discrete steps
        assert allocation_10y["equity"] == allocation_9y["equity"]
    
    def test_generate_glidepath(self):
        """Test glidepath generation."""
        engine = GlidePathEngine(
            strategy=GlidePathStrategy.LINEAR,
            initial_equity_pct=0.8,
            final_equity_pct=0.3,
            years_to_target=10
        )
        
        glidepath = engine.generate_glidepath()
        
        assert len(glidepath) == 11  # 0 to 10 years
        assert glidepath[0]["years_remaining"] == 10
        assert glidepath[-1]["years_remaining"] == 0
        assert glidepath[0]["equity"] == pytest.approx(0.8, rel=0.01)
        assert glidepath[-1]["equity"] == pytest.approx(0.3, rel=0.01)
    
    def test_rebalance_recommendation(self):
        """Test rebalance recommendation."""
        engine = GlidePathEngine(
            strategy=GlidePathStrategy.LINEAR,
            initial_equity_pct=0.8,
            final_equity_pct=0.3,
            years_to_target=10
        )
        
        current_allocation = {"equity": 0.75, "bonds": 0.20, "cash": 0.05}
        years_remaining = 5
        
        recommendation = engine.recommend_rebalance(current_allocation, years_remaining)
        
        assert "needs_rebalance" in recommendation
        assert "target_allocation" in recommendation
        assert "drift" in recommendation

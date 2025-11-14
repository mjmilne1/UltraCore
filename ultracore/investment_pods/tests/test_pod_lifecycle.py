"""
Investment Pods Lifecycle Tests
End-to-end tests for Pod creation, optimization, and management
"""

import sys
sys.path.append('/home/ubuntu/UltraCore')

from decimal import Decimal
from datetime import date, timedelta
import pytest

from ultracore.investment_pods.aggregates.pod_aggregate import PodAggregate
from ultracore.investment_pods.models import RiskTolerance
from ultracore.investment_pods.events import GoalType


class TestPodLifecycle:
    """Test complete Pod lifecycle"""
    
    def test_create_first_home_pod(self):
        """Test creating a first home Pod"""
        # Create Pod
        pod = PodAggregate.create(
            tenant_id="ultrawealth",
            client_id="client_123",
            goal_type=GoalType.FIRST_HOME,
            goal_name="First Home Deposit",
            target_amount=Decimal("200000"),
            target_date=date.today() + timedelta(days=5*365),  # 5 years
            risk_tolerance=RiskTolerance.BALANCED,
            monthly_contribution=Decimal("2000"),
            created_by="test"
        )
        
        assert pod.pod_id is not None
        assert pod.goal_type == GoalType.FIRST_HOME
        assert pod.target_amount == Decimal("200000")
        assert pod.monthly_contribution == Decimal("2000")
        assert pod.status.value == "active"
    
    def test_optimize_allocation(self):
        """Test portfolio optimization"""
        pod = PodAggregate.create(
            tenant_id="ultrawealth",
            client_id="client_123",
            goal_type=GoalType.WEALTH_ACCUMULATION,
            goal_name="Wealth Building",
            target_amount=Decimal("500000"),
            target_date=date.today() + timedelta(days=10*365),
            risk_tolerance=RiskTolerance.MODERATELY_AGGRESSIVE,
            monthly_contribution=Decimal("3000"),
            created_by="test"
        )
        
        # Optimize
        etf_allocation = [
            {"etf_code": "VAS", "etf_name": "Vanguard Australian Shares", "weight": Decimal("30")},
            {"etf_code": "VGS", "etf_name": "Vanguard International Shares", "weight": Decimal("40")},
            {"etf_code": "VAF", "etf_name": "Vanguard Australian Bonds", "weight": Decimal("30")}
        ]
        
        pod.optimize_allocation(
            etf_allocation=etf_allocation,
            expected_return=Decimal("9.5"),
            expected_volatility=Decimal("12.0"),
            sharpe_ratio=Decimal("0.65"),
            max_drawdown=Decimal("18.0"),
            total_expense_ratio=Decimal("0.15"),
            franking_yield=Decimal("2.5"),
            optimization_reason="initial"
        )
        
        assert pod.expected_return == Decimal("9.5")
        assert pod.expected_volatility == Decimal("12.0")
        assert len(pod.holdings) == 3
    
    def test_glide_path_transition(self):
        """Test glide path transition"""
        pod = PodAggregate.create(
            tenant_id="ultrawealth",
            client_id="client_123",
            goal_type=GoalType.RETIREMENT,
            goal_name="Retirement Fund",
            target_amount=Decimal("1000000"),
            target_date=date.today() + timedelta(days=2*365),  # 2 years
            risk_tolerance=RiskTolerance.BALANCED,
            monthly_contribution=Decimal("5000"),
            created_by="test"
        )
        
        # Trigger glide path transition
        new_allocation = {
            "equity": Decimal("40"),
            "defensive": Decimal("60")
        }
        
        pod.trigger_glide_path_transition(
            transition_date=date.today(),
            new_allocation=new_allocation,
            reason="approaching_target"
        )
        
        assert pod.current_allocation["equity"] == Decimal("40")
        assert pod.current_allocation["defensive"] == Decimal("60")
    
    def test_circuit_breaker(self):
        """Test circuit breaker activation"""
        pod = PodAggregate.create(
            tenant_id="ultrawealth",
            client_id="client_123",
            goal_type=GoalType.WEALTH_ACCUMULATION,
            goal_name="Growth Portfolio",
            target_amount=Decimal("300000"),
            target_date=date.today() + timedelta(days=7*365),
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            monthly_contribution=Decimal("2500"),
            created_by="test"
        )
        
        # Trigger circuit breaker
        pod.trigger_circuit_breaker(
            trigger_date=date.today(),
            drawdown_percentage=Decimal("16.5"),
            trigger_reason="downside_breach"
        )
        
        assert pod.circuit_breaker_active == True
        assert pod.circuit_breaker_triggered_at is not None


if __name__ == "__main__":
    # Run tests
    test = TestPodLifecycle()
    
    print("Running Investment Pods Lifecycle Tests...")
    print("=" * 60)
    
    try:
        test.test_create_first_home_pod()
        print("✅ test_create_first_home_pod PASSED")
    except Exception as e:
        print(f"❌ test_create_first_home_pod FAILED: {e}")
    
    try:
        test.test_optimize_allocation()
        print("✅ test_optimize_allocation PASSED")
    except Exception as e:
        print(f"❌ test_optimize_allocation FAILED: {e}")
    
    try:
        test.test_glide_path_transition()
        print("✅ test_glide_path_transition PASSED")
    except Exception as e:
        print(f"❌ test_glide_path_transition FAILED: {e}")
    
    try:
        test.test_circuit_breaker()
        print("✅ test_circuit_breaker PASSED")
    except Exception as e:
        print(f"❌ test_circuit_breaker FAILED: {e}")
    
    print("=" * 60)
    print("✅ All Tests Complete!")

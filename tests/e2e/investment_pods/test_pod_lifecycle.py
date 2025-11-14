"""
E2E tests for Investment Pods Lifecycle.

Tests complete Pod journey from creation to goal achievement.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import asyncio


@pytest.mark.e2e
@pytest.mark.investment_pods
@pytest.mark.slow
class TestPodLifecycle:
    """Test complete Pod lifecycle."""
    
    @pytest.mark.asyncio
    async def test_first_home_pod_complete_journey(
        self, kafka_producer, event_store, db_session
    ):
        """Test complete first home Pod journey over 5 years."""
        # Arrange
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        client_id = f"client_{uuid4().hex[:8]}"
        user_id = f"user_{uuid4().hex[:8]}"
        
        # Step 1: Create Pod
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "tenant_id": tenant_id,
                "client_id": client_id,
                "goal_type": "first_home",
                "target_amount": "100000.00",
                "target_date": (datetime.now(timezone.utc) + timedelta(days=1825)).isoformat(),
                "initial_deposit": "10000.00",
                "monthly_contribution": "1000.00",
                "risk_tolerance": "moderate"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 2: Optimize Allocation
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="AllocationOptimized",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "allocation": [
                    {"etf_code": "VAS", "weight": "40.0", "shares": 100},
                    {"etf_code": "VGS", "weight": "30.0", "shares": 75},
                    {"etf_code": "VAF", "weight": "30.0", "shares": 80}
                ],
                "expected_return": "0.08",
                "expected_volatility": "0.12"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 3: Receive Monthly Contributions (simulate 12 months)
        for month in range(12):
            await kafka_producer.publish_event(
                topic="ultracore.investment_pods.events",
                event_type="ContributionReceived",
                aggregate_type="InvestmentPod",
                aggregate_id=pod_id,
                event_data={
                    "amount": "1000.00",
                    "contribution_date": (
                        datetime.now(timezone.utc) + timedelta(days=30 * month)
                    ).isoformat(),
                    "contribution_type": "recurring"
                },
                tenant_id=tenant_id,
                user_id=user_id
            )
        
        await asyncio.sleep(2)
        
        # Step 4: Market Value Updates
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ValueUpdated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "current_value": "23500.00",
                "previous_value": "22000.00",
                "return_percentage": "6.82",
                "update_date": datetime.now(timezone.utc).isoformat()
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 5: Glide Path Adjustment (after 3 years)
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="GlidePathAdjusted",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "months_to_goal": 24,
                "previous_allocation": {
                    "equity": "70.0",
                    "defensive": "30.0"
                },
                "new_allocation": {
                    "equity": "30.0",
                    "defensive": "70.0"
                },
                "reason": "approaching_target_date"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Assert - Verify complete event stream
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        assert len(events) >= 16  # 1 created + 1 optimized + 12 contributions + 1 value + 1 glide path
        
        # Verify event types
        event_types = [e["event_type"] for e in events]
        assert "PodCreated" in event_types
        assert "AllocationOptimized" in event_types
        assert event_types.count("ContributionReceived") == 12
        assert "ValueUpdated" in event_types
        assert "GlidePathAdjusted" in event_types
    
    @pytest.mark.asyncio
    async def test_pod_with_circuit_breaker_trigger(
        self, kafka_producer, event_store
    ):
        """Test Pod lifecycle with circuit breaker activation."""
        # Arrange
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = f"user_{uuid4().hex[:8]}"
        
        # Step 1: Create Pod
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "goal_type": "retirement",
                "target_amount": "500000.00",
                "initial_deposit": "50000.00"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 2: Market Crash - 15% Drawdown
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ValueUpdated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "current_value": "42500.00",  # 15% loss
                "previous_value": "50000.00",
                "return_percentage": "-15.00",
                "drawdown": "15.00"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 3: Circuit Breaker Triggered
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="CircuitBreakerTriggered",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "drawdown": "15.00",
                "threshold": "15.00",
                "previous_allocation": {
                    "equity": "80.0",
                    "defensive": "20.0"
                },
                "defensive_allocation": {
                    "equity": "30.0",
                    "defensive": "70.0"
                },
                "reason": "downside_protection"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Assert - Verify circuit breaker event
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        circuit_breaker_events = [
            e for e in events if e["event_type"] == "CircuitBreakerTriggered"
        ]
        assert len(circuit_breaker_events) == 1
        assert circuit_breaker_events[0]["event_data"]["drawdown"] == "15.00"
    
    @pytest.mark.asyncio
    async def test_pod_goal_achievement(self, kafka_producer, event_store):
        """Test Pod reaching goal amount."""
        # Arrange
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = f"user_{uuid4().hex[:8]}"
        target_amount = Decimal("100000.00")
        
        # Step 1: Create Pod
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "goal_type": "first_home",
                "target_amount": str(target_amount),
                "initial_deposit": "95000.00"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 2: Value Update - Goal Reached
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ValueUpdated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "current_value": "100500.00",  # Exceeds target
                "previous_value": "98000.00",
                "return_percentage": "2.55"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(1)
        
        # Step 3: Goal Achieved Event
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="GoalAchieved",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "target_amount": str(target_amount),
                "final_value": "100500.00",
                "achievement_date": datetime.now(timezone.utc).isoformat(),
                "days_to_goal": 1095,  # 3 years
                "total_return": "5.79"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Assert - Verify goal achievement
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        goal_achieved_events = [
            e for e in events if e["event_type"] == "GoalAchieved"
        ]
        assert len(goal_achieved_events) == 1
        assert Decimal(goal_achieved_events[0]["event_data"]["final_value"]) >= target_amount


@pytest.mark.e2e
@pytest.mark.investment_pods
@pytest.mark.slow
class TestMultiplePods:
    """Test managing multiple Pods simultaneously."""
    
    @pytest.mark.asyncio
    async def test_client_with_multiple_pods(
        self, kafka_producer, event_store
    ):
        """Test client managing multiple Pods with different goals."""
        # Arrange
        tenant_id = "ultrawealth"
        client_id = f"client_{uuid4().hex[:8]}"
        user_id = f"user_{uuid4().hex[:8]}"
        
        # Create 3 Pods with different goals
        pod_ids = []
        goals = [
            ("first_home", "100000.00"),
            ("retirement", "500000.00"),
            ("wealth", "250000.00")
        ]
        
        for goal_type, target_amount in goals:
            pod_id = str(uuid4())
            pod_ids.append(pod_id)
            
            await kafka_producer.publish_event(
                topic="ultracore.investment_pods.events",
                event_type="PodCreated",
                aggregate_type="InvestmentPod",
                aggregate_id=pod_id,
                event_data={
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "goal_type": goal_type,
                    "target_amount": target_amount,
                    "initial_deposit": "10000.00"
                },
                tenant_id=tenant_id,
                user_id=user_id
            )
        
        await asyncio.sleep(2)
        
        # Assert - All Pods created for same client
        for pod_id in pod_ids:
            events = await event_store.get_events_by_aggregate(
                topic="ultracore.investment_pods.events",
                aggregate_id=pod_id
            )
            assert len(events) >= 1
            assert events[0]["event_type"] == "PodCreated"
            assert events[0]["event_data"]["client_id"] == client_id


@pytest.mark.e2e
@pytest.mark.investment_pods
@pytest.mark.slow
class TestPodReplay:
    """Test rebuilding Pod state from events."""
    
    @pytest.mark.asyncio
    async def test_rebuild_pod_from_event_stream(
        self, kafka_producer, event_store
    ):
        """Test rebuilding complete Pod state from events."""
        # Arrange - Create Pod with multiple events
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = f"user_{uuid4().hex[:8]}"
        
        # Publish sequence of events
        events_data = [
            ("PodCreated", {"goal_type": "first_home", "target_amount": "100000.00"}),
            ("AllocationOptimized", {"allocation": []}),
            ("ContributionReceived", {"amount": "1000.00"}),
            ("ValueUpdated", {"current_value": "11500.00"}),
        ]
        
        for event_type, event_data in events_data:
            await kafka_producer.publish_event(
                topic="ultracore.investment_pods.events",
                event_type=event_type,
                aggregate_type="InvestmentPod",
                aggregate_id=pod_id,
                event_data=event_data,
                tenant_id=tenant_id,
                user_id=user_id
            )
        
        await asyncio.sleep(2)
        
        # Act - Replay events
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        # Rebuild state from events
        pod_state = {
            "pod_id": pod_id,
            "status": "active",
            "goal_type": None,
            "target_amount": None,
            "current_value": Decimal("0.00"),
            "contributions": []
        }
        
        for event in events:
            if event["event_type"] == "PodCreated":
                pod_state["goal_type"] = event["event_data"]["goal_type"]
                pod_state["target_amount"] = Decimal(event["event_data"]["target_amount"])
            elif event["event_type"] == "ContributionReceived":
                pod_state["contributions"].append(Decimal(event["event_data"]["amount"]))
            elif event["event_type"] == "ValueUpdated":
                pod_state["current_value"] = Decimal(event["event_data"]["current_value"])
        
        # Assert - State rebuilt correctly
        assert pod_state["goal_type"] == "first_home"
        assert pod_state["target_amount"] == Decimal("100000.00")
        assert len(pod_state["contributions"]) == 1
        assert pod_state["current_value"] == Decimal("11500.00")

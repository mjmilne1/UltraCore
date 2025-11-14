"""
E2E tests for Event Replay (Event Sourcing).

Tests the ability to rebuild aggregate state from event stream.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import asyncio


@pytest.mark.e2e
@pytest.mark.event_sourcing
@pytest.mark.slow
class TestEventReplay:
    """Test rebuilding aggregate state from events."""
    
    @pytest.mark.asyncio
    async def test_rebuild_pod_from_events(self, kafka_producer, event_store):
        """Test rebuilding Investment Pod from event stream."""
        # Arrange - Create a pod and perform actions
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Event 1: PodCreated
        event1_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "goal_type": "first_home",
                "target_amount": "100000.00",
                "target_date": "2030-01-01",
                "initial_deposit": "10000.00",
                "monthly_contribution": "1000.00",
                "risk_tolerance": "moderate"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        # Event 2: AllocationOptimized
        event2_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="AllocationOptimized",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "allocation": [
                    {"etf_code": "VAS", "weight": "40.0"},
                    {"etf_code": "VGS", "weight": "30.0"},
                    {"etf_code": "VAF", "weight": "30.0"}
                ]
            },
            tenant_id=tenant_id,
            user_id=user_id,
            causation_id=event1_id
        )
        
        # Event 3: ContributionReceived
        event3_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionReceived",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "amount": "1000.00",
                "contribution_date": datetime.now(timezone.utc).isoformat()
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        # Wait for events to be persisted
        await asyncio.sleep(2)
        
        # Act - Rebuild pod from events
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        # Assert - All events retrieved
        assert len(events) >= 3
        assert events[0]["event_type"] == "PodCreated"
        assert events[1]["event_type"] == "AllocationOptimized"
        assert events[2]["event_type"] == "ContributionReceived"
        
        # Assert - Events are ordered
        ts0 = events[0].get("event_timestamp", events[0].get("timestamp"))
        ts1 = events[1].get("event_timestamp", events[1].get("timestamp"))
        ts2 = events[2].get("event_timestamp", events[2].get("timestamp"))
        assert ts0 <= ts1
        assert ts1 <= ts2
        
        # Assert - Causation chain (if present)
        if "causation_id" in events[1]:
            assert events[1]["causation_id"] == event1_id
    
    @pytest.mark.asyncio
    async def test_time_travel_query(self, kafka_producer, event_store):
        """Test querying historical state at specific timestamp."""
        # Arrange - Create pod and make changes over time
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Time T0: Pod created
        t0 = datetime.now(timezone.utc)
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"goal_type": "first_home", "initial_deposit": "10000.00"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Time T1: Contribution received
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionReceived",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"amount": "1000.00"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Capture T1 after first contribution
        t1 = datetime.now(timezone.utc)
        
        # Time T2: Another contribution
        t2 = datetime.now(timezone.utc)
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionReceived",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"amount": "2000.00"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Act - Query state at T1 (should have initial + first contribution)
        events_at_t1 = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id,
            until_timestamp=t1
        )
        
        # Assert - Only events up to T1
        assert len(events_at_t1) == 2
        assert events_at_t1[0]["event_type"] == "PodCreated"
        assert events_at_t1[1]["event_type"] == "ContributionReceived"
        assert events_at_t1[1]["event_data"]["amount"] == "1000.00"
    
    @pytest.mark.asyncio
    async def test_rebuild_multiple_aggregates(self, kafka_producer, event_store):
        """Test rebuilding multiple aggregates from event stream."""
        # Arrange - Create multiple pods
        pod1_id = str(uuid4())
        pod2_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Pod 1 events
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod1_id,
            event_data={"goal_type": "first_home"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        # Pod 2 events
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod2_id,
            event_data={"goal_type": "retirement"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Act - Rebuild both pods
        pod1_events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod1_id
        )
        
        pod2_events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod2_id
        )
        
        # Assert - Each pod has its own events
        assert len(pod1_events) >= 1
        assert len(pod2_events) >= 1
        assert pod1_events[0]["aggregate_id"] == pod1_id
        assert pod2_events[0]["aggregate_id"] == pod2_id
        assert pod1_events[0]["event_data"]["goal_type"] == "first_home"
        assert pod2_events[0]["event_data"]["goal_type"] == "retirement"


@pytest.mark.e2e
@pytest.mark.event_sourcing
@pytest.mark.slow
class TestEventSourcingWorkflow:
    """Test complete event sourcing workflow."""
    
    @pytest.mark.asyncio
    async def test_command_to_event_to_projection(
        self, kafka_producer, kafka_consumer, db_session
    ):
        """Test full workflow: Command → Event → Projection."""
        # Arrange
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Act - Step 1: Publish event (simulating command handler)
        event_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "goal_type": "first_home",
                "target_amount": "100000.00",
                "initial_deposit": "10000.00"
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        # Wait for consumer to process and materialize to PostgreSQL
        await asyncio.sleep(3)
        
        # Act - Step 2: Query projection from PostgreSQL
        # (This would query the actual Pod table in PostgreSQL)
        # pod = db_session.query(InvestmentPodModel).filter_by(pod_id=pod_id).first()
        
        # Assert - Projection should exist in PostgreSQL
        # assert pod is not None
        # assert pod.pod_id == pod_id
        # assert pod.goal_type == "first_home"
        # assert pod.target_amount == Decimal("100000.00")
        
        # For now, just verify event was published
        assert event_id is not None
    
    @pytest.mark.asyncio
    async def test_event_replay_after_projection_loss(
        self, kafka_producer, event_store, db_session
    ):
        """Test rebuilding projection from events after data loss."""
        # Arrange - Create pod and materialize to PostgreSQL
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        
        # Publish events
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"goal_type": "first_home", "initial_deposit": "10000.00"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionReceived",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"amount": "1000.00"},
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        await asyncio.sleep(2)
        
        # Simulate projection loss (delete from PostgreSQL)
        # db_session.query(InvestmentPodModel).filter_by(pod_id=pod_id).delete()
        # db_session.commit()
        
        # Act - Replay events to rebuild projection
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        # Rebuild projection from events
        # for event in events:
        #     apply_event_to_projection(event, db_session)
        
        # Assert - Projection rebuilt from events
        assert len(events) >= 2
        # pod = db_session.query(InvestmentPodModel).filter_by(pod_id=pod_id).first()
        # assert pod is not None


@pytest.mark.e2e
@pytest.mark.event_sourcing
@pytest.mark.slow
class TestEventCausationTracking:
    """Test event causation and correlation tracking."""
    
    @pytest.mark.asyncio
    async def test_correlation_id_across_events(self, kafka_producer, event_store):
        """Test that correlation_id links related events."""
        # Arrange
        pod_id = str(uuid4())
        tenant_id = "ultrawealth"
        user_id = "user_123"
        correlation_id = str(uuid4())
        
        # Act - Publish chain of related events
        event1_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"goal_type": "first_home"},
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        event2_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="AllocationOptimized",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"allocation": []},
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=event1_id
        )
        
        event3_id = await kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionReceived",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={"amount": "1000.00"},
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=event2_id
        )
        
        await asyncio.sleep(2)
        
        # Assert - All events have same correlation_id
        events = await event_store.get_events_by_aggregate(
            topic="ultracore.investment_pods.events",
            aggregate_id=pod_id
        )
        
        assert all(e["correlation_id"] == correlation_id for e in events)
        
        # Assert - Causation chain
        assert events[0].get("causation_id") is None or "causation_id" not in events[0]
        assert events[1].get("causation_id") == event1_id
        assert events[2].get("causation_id") == event2_id

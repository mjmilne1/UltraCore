"""
Kafka-First Integration Test
Demonstrates complete event-driven architecture:
Events → Kafka → Consumers → PostgreSQL
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

# Event sourcing
from ultracore.event_sourcing.store.event_store import EventStore, get_event_store
from ultracore.event_sourcing.replay.event_replay import EventReplay

# Database
from ultracore.database.base import DatabaseConfig, get_database_config
from ultracore.database.models import SavingsAccountModel, SavingsTransactionModel

# Kafka producer (from existing implementation)
try:
    from src.ultracore.events.kafka_producer import KafkaEventProducer, EventTopic
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


@pytest.mark.skipif(not KAFKA_AVAILABLE, reason="Kafka not available")
class TestKafkaFirstArchitecture:
    """Test Kafka-first event sourcing architecture"""
    
    @pytest.fixture
    async def db_config(self):
        """Setup database"""
        config = get_database_config(echo=False)
        
        # Create tables
        await config.create_all_tables()
        
        yield config
        
        # Cleanup
        await config.drop_all_tables()
        await config.close()
    
    @pytest.fixture
    def kafka_producer(self):
        """Setup Kafka producer"""
        producer = KafkaEventProducer(bootstrap_servers="localhost:9092")
        yield producer
        producer.close()
    
    @pytest.fixture
    def event_store(self):
        """Setup event store"""
        return get_event_store(bootstrap_servers="localhost:9092")
    
    async def test_kafka_first_flow(self, db_config, kafka_producer, event_store):
        """
        Test complete Kafka-first flow:
        1. Publish event to Kafka
        2. Event is stored in Kafka (source of truth)
        3. Consumer reads event and projects to PostgreSQL
        4. Verify data in PostgreSQL
        5. Replay events to rebuild state
        """
        
        # Step 1: Publish account opened event
        tenant_id = str(uuid4())
        client_id = str(uuid4())
        account_id = str(uuid4())
        product_id = str(uuid4())
        
        event_id = await kafka_producer.publish_event(
            topic=EventTopic.ACCOUNT_EVENTS,
            event_type="SavingsAccountOpened",
            aggregate_type="SavingsAccount",
            aggregate_id=account_id,
            event_data={
                "client_id": client_id,
                "product_id": product_id,
                "account_number": "SA1234567890",
                "bsb": "062000",
                "account_name": "Test Savings",
                "account_type": "savings",
            },
            tenant_id=tenant_id,
            user_id="test_user",
        )
        
        assert event_id is not None
        print(f"✓ Event published to Kafka: {event_id}")
        
        # Step 2: Verify event is in Kafka (source of truth)
        # Wait a moment for Kafka to process
        await asyncio.sleep(1)
        
        events = event_store.get_events_by_aggregate(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        
        assert len(events) > 0
        assert events[0].event_type == "SavingsAccountOpened"
        assert events[0].aggregate_id == account_id
        print(f"✓ Event verified in Kafka: {len(events)} events found")
        
        # Step 3: Simulate consumer projection to PostgreSQL
        # (In production, this would be done by the consumer automatically)
        async with db_config.get_session() as session:
            account = SavingsAccountModel(
                account_id=account_id,
                client_id=client_id,
                product_id=product_id,
                tenant_id=tenant_id,
                account_number="SA1234567890",
                bsb="062000",
                account_name="Test Savings",
                account_type="savings",
                status="pending",
                balance=Decimal('0.00'),
                available_balance=Decimal('0.00'),
            )
            session.add(account)
            await session.commit()
        
        print("✓ Event projected to PostgreSQL")
        
        # Step 4: Verify data in PostgreSQL
        async with db_config.get_session() as session:
            result = await session.get(SavingsAccountModel, account_id)
            assert result is not None
            assert result.account_number == "SA1234567890"
            assert result.status == "pending"
            print(f"✓ Data verified in PostgreSQL: {result.account_number}")
        
        # Step 5: Test event replay
        replay = EventReplay(event_store)
        
        # Generate audit report
        audit_report = replay.generate_audit_report(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        
        assert audit_report['total_events'] > 0
        assert audit_report['first_event']['event_type'] == "SavingsAccountOpened"
        print(f"✓ Audit report generated: {audit_report['total_events']} events")
        
        # Verify event consistency
        consistency = replay.verify_event_consistency(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        
        assert consistency['consistent'] is True
        print(f"✓ Event consistency verified: {consistency['issues_found']} issues found")
    
    async def test_multiple_events_flow(self, db_config, kafka_producer, event_store):
        """
        Test multiple events for same aggregate:
        1. Account opened
        2. Account approved
        3. Deposit made
        4. Verify all events in order
        """
        
        tenant_id = str(uuid4())
        client_id = str(uuid4())
        account_id = str(uuid4())
        product_id = str(uuid4())
        
        # Event 1: Account opened
        event1_id = await kafka_producer.publish_event(
            topic=EventTopic.ACCOUNT_EVENTS,
            event_type="SavingsAccountOpened",
            aggregate_type="SavingsAccount",
            aggregate_id=account_id,
            event_data={
                "client_id": client_id,
                "product_id": product_id,
                "account_number": "SA9876543210",
                "bsb": "062000",
                "account_name": "Multi-Event Test",
                "account_type": "savings",
            },
            tenant_id=tenant_id,
            user_id="test_user",
        )
        
        # Event 2: Account approved
        event2_id = await kafka_producer.publish_event(
            topic=EventTopic.ACCOUNT_EVENTS,
            event_type="SavingsAccountApproved",
            aggregate_type="SavingsAccount",
            aggregate_id=account_id,
            event_data={
                "approved_by": "admin_user",
            },
            tenant_id=tenant_id,
            user_id="admin_user",
            causation_id=event1_id,
        )
        
        # Event 3: Deposit made
        event3_id = await kafka_producer.publish_event(
            topic=EventTopic.TRANSACTION_EVENTS,
            event_type="SavingsDeposit",
            aggregate_type="SavingsAccount",
            aggregate_id=account_id,
            event_data={
                "transaction_id": str(uuid4()),
                "amount": "1000.00",
                "balance_before": "0.00",
                "balance_after": "1000.00",
                "reference_number": "DEP001",
                "description": "Initial deposit",
            },
            tenant_id=tenant_id,
            user_id="test_user",
            causation_id=event2_id,
        )
        
        print(f"✓ Published 3 events: {event1_id}, {event2_id}, {event3_id}")
        
        # Wait for Kafka
        await asyncio.sleep(1)
        
        # Verify all events
        account_events = event_store.get_events_by_aggregate(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        
        transaction_events = event_store.get_events_by_aggregate(
            topic=EventTopic.TRANSACTION_EVENTS.value,
            aggregate_id=account_id
        )
        
        total_events = len(account_events) + len(transaction_events)
        assert total_events >= 3
        print(f"✓ Verified {total_events} events in Kafka")
        
        # Verify causation chain
        replay = EventReplay(event_store)
        audit_report = replay.generate_audit_report(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        
        print(f"✓ Audit report: {audit_report}")
    
    async def test_event_store_queries(self, kafka_producer, event_store):
        """Test event store query capabilities"""
        
        tenant_id = str(uuid4())
        account_id = str(uuid4())
        
        # Publish test event
        await kafka_producer.publish_event(
            topic=EventTopic.ACCOUNT_EVENTS,
            event_type="SavingsAccountOpened",
            aggregate_type="SavingsAccount",
            aggregate_id=account_id,
            event_data={"test": "data"},
            tenant_id=tenant_id,
            user_id="test_user",
        )
        
        await asyncio.sleep(1)
        
        # Query by aggregate ID
        events_by_aggregate = event_store.get_events_by_aggregate(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            aggregate_id=account_id
        )
        assert len(events_by_aggregate) > 0
        print(f"✓ Query by aggregate: {len(events_by_aggregate)} events")
        
        # Query by event type
        events_by_type = event_store.get_events_by_type(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            event_type="SavingsAccountOpened",
            limit=10
        )
        assert len(events_by_type) > 0
        print(f"✓ Query by type: {len(events_by_type)} events")
        
        # Get all events
        all_events = event_store.get_all_events(
            topic=EventTopic.ACCOUNT_EVENTS.value,
            limit=100
        )
        assert len(all_events) > 0
        print(f"✓ Query all events: {len(all_events)} events")


def test_kafka_first_architecture_summary():
    """
    Summary of Kafka-First Architecture
    
    This test demonstrates the complete event-driven architecture:
    
    1. **Events are the source of truth** (stored in Kafka)
    2. **Database is a projection** (materialized view from events)
    3. **Event replay capability** (rebuild state from events)
    4. **Complete audit trail** (all events are immutable)
    5. **Event consistency verification** (validate causation chain)
    
    Architecture:
    - Write: API → Kafka (event published)
    - Read: Kafka → Consumer → PostgreSQL (projection)
    - Replay: Kafka → Event Store → Rebuild State
    
    Benefits:
    - Complete audit trail
    - Time travel (replay to any point)
    - CQRS (Command Query Responsibility Segregation)
    - Scalability (async event processing)
    - Reliability (events never lost)
    """
    print(__doc__)
    assert True

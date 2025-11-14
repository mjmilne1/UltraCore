"""
Integration tests for Event Sourcing.

Tests event store, handlers, projections, and Kafka integration.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from ultracore.event_sourcing import (
    Event,
    EventMetadata,
    EventType,
)
from ultracore.event_sourcing.store.event_store import KafkaEventStore
from ultracore.event_sourcing.store.snapshot_store import SnapshotStore
from ultracore.event_sourcing.handlers import (
    CustomerEventHandler,
    AccountEventHandler,
    TransactionEventHandler,
)
from ultracore.event_sourcing.projections import (
    ProjectionManager,
    CustomerReadModel,
    AccountReadModel,
    TransactionReadModel,
)


class TestEventStore:
    """Test event store functionality."""
    
    @pytest.mark.asyncio
    async def test_append_event(self):
        """Test appending event to store."""
        store = KafkaEventStore()
        
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id="CUST001",
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "name": "John Doe",
                "email": "john@example.com",
            }
        )
        
        result = await store.append_event(event)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_events(self):
        """Test retrieving events from store."""
        store = KafkaEventStore()
        aggregate_id = "CUST001"
        
        # Append event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id=aggregate_id,
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={"name": "John Doe"}
        )
        
        await store.append_event(event)
        
        # Retrieve events
        events = await store.get_events(aggregate_id)
        
        assert len(events) > 0
        assert events[0].metadata.aggregate_id == aggregate_id
    
    @pytest.mark.asyncio
    async def test_event_versioning(self):
        """Test event versioning."""
        store = KafkaEventStore()
        aggregate_id = "CUST002"
        
        # Append multiple events
        for version in range(1, 4):
            event = Event(
                metadata=EventMetadata(
                    event_id=str(uuid4()),
                    event_type=EventType.CUSTOMER_UPDATED,
                    aggregate_id=aggregate_id,
                    aggregate_type="Customer",
                    version=version,
                    timestamp=datetime.utcnow(),
                ),
                data={"update": f"version_{version}"}
            )
            await store.append_event(event)
        
        # Get events
        events = await store.get_events(aggregate_id)
        
        assert len(events) == 3
        assert events[0].metadata.version == 1
        assert events[-1].metadata.version == 3
    
    @pytest.mark.asyncio
    async def test_optimistic_concurrency(self):
        """Test optimistic concurrency control."""
        store = KafkaEventStore()
        aggregate_id = "CUST003"
        
        # Append first event
        event1 = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id=aggregate_id,
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={"name": "John"}
        )
        await store.append_event(event1)
        
        # Try to append event with same version (should fail)
        event2 = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_UPDATED,
                aggregate_id=aggregate_id,
                aggregate_type="Customer",
                version=1,  # Conflict!
                timestamp=datetime.utcnow(),
            ),
            data={"name": "Jane"}
        )
        
        with pytest.raises(Exception):
            await store.append_event(event2)


class TestSnapshotStore:
    """Test snapshot store functionality."""
    
    @pytest.mark.asyncio
    async def test_save_snapshot(self):
        """Test saving snapshot."""
        from ultracore.event_sourcing.base import Snapshot
        
        store = SnapshotStore()
        
        snapshot = Snapshot(
            aggregate_id="CUST001",
            aggregate_type="Customer",
            version=10,
            state={"name": "John Doe", "email": "john@example.com"},
            timestamp=datetime.utcnow(),
        )
        
        await store.save_snapshot(snapshot)
        
        retrieved = await store.get_snapshot("CUST001")
        
        assert retrieved is not None
        assert retrieved.version == 10
    
    @pytest.mark.asyncio
    async def test_snapshot_retrieval(self):
        """Test retrieving latest snapshot."""
        from ultracore.event_sourcing.base import Snapshot
        
        store = SnapshotStore()
        aggregate_id = "CUST002"
        
        # Save multiple snapshots
        for version in [10, 20, 30]:
            snapshot = Snapshot(
                aggregate_id=aggregate_id,
                aggregate_type="Customer",
                version=version,
                state={"version": version},
                timestamp=datetime.utcnow(),
            )
            await store.save_snapshot(snapshot)
        
        # Get latest
        latest = await store.get_snapshot(aggregate_id)
        
        assert latest is not None
        assert latest.version == 30


class TestEventHandlers:
    """Test event handlers."""
    
    @pytest.mark.asyncio
    async def test_customer_handler(self):
        """Test customer event handler."""
        handler = CustomerEventHandler()
        
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id="CUST001",
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "name": "John Doe",
                "email": "john@example.com",
            }
        )
        
        await handler.handle(event)
        
        # Handler should process without error
        assert True
    
    @pytest.mark.asyncio
    async def test_account_handler(self):
        """Test account event handler."""
        handler = AccountEventHandler()
        
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.ACCOUNT_OPENED,
                aggregate_id="ACC001",
                aggregate_type="Account",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "customer_id": "CUST001",
                "account_type": "savings",
                "initial_balance": 1000,
            }
        )
        
        await handler.handle(event)
        
        assert True
    
    @pytest.mark.asyncio
    async def test_transaction_handler(self):
        """Test transaction event handler."""
        handler = TransactionEventHandler()
        
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.TRANSACTION_CREATED,
                aggregate_id="TXN001",
                aggregate_type="Transaction",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "account_id": "ACC001",
                "amount": 100,
                "type": "debit",
            }
        )
        
        await handler.handle(event)
        
        assert True


class TestProjections:
    """Test CQRS projections."""
    
    @pytest.mark.asyncio
    async def test_customer_projection(self):
        """Test customer read model projection."""
        projection = CustomerReadModel()
        
        # Project customer created event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id="CUST001",
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "name": "John Doe",
                "email": "john@example.com",
            }
        )
        
        await projection.project(event)
        
        # Query projection
        customer = projection.get_customer("CUST001")
        
        assert customer is not None
        assert customer["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_account_projection(self):
        """Test account read model projection."""
        projection = AccountReadModel()
        
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.ACCOUNT_OPENED,
                aggregate_id="ACC001",
                aggregate_type="Account",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "customer_id": "CUST001",
                "account_type": "savings",
                "initial_balance": 1000,
            }
        )
        
        await projection.project(event)
        
        account = projection.get_account("ACC001")
        
        assert account is not None
        assert account["balance"] == 1000
    
    @pytest.mark.asyncio
    async def test_projection_manager(self):
        """Test projection manager."""
        store = KafkaEventStore()
        manager = ProjectionManager(store)
        
        # Register projections
        customer_projection = CustomerReadModel()
        manager.register_projection(customer_projection)
        
        # Project event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id="CUST001",
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={"name": "John Doe"}
        )
        
        await manager.project_event(event)
        
        # Check projection status
        status = manager.get_projection_status()
        
        assert len(status) == 1
        assert status[0]["name"] == "CustomerReadModel"


class TestEventReplay:
    """Test event replay functionality."""
    
    @pytest.mark.asyncio
    async def test_replay_events(self):
        """Test replaying events to rebuild state."""
        store = KafkaEventStore()
        aggregate_id = "CUST001"
        
        # Append multiple events
        events = [
            Event(
                metadata=EventMetadata(
                    event_id=str(uuid4()),
                    event_type=EventType.CUSTOMER_CREATED,
                    aggregate_id=aggregate_id,
                    aggregate_type="Customer",
                    version=1,
                    timestamp=datetime.utcnow(),
                ),
                data={"name": "John Doe"}
            ),
            Event(
                metadata=EventMetadata(
                    event_id=str(uuid4()),
                    event_type=EventType.CUSTOMER_UPDATED,
                    aggregate_id=aggregate_id,
                    aggregate_type="Customer",
                    version=2,
                    timestamp=datetime.utcnow(),
                ),
                data={"email": "john@example.com"}
            ),
        ]
        
        for event in events:
            await store.append_event(event)
        
        # Replay events
        replayed_events = await store.get_events(aggregate_id)
        
        assert len(replayed_events) == 2
        assert replayed_events[0].metadata.version == 1
        assert replayed_events[1].metadata.version == 2
    
    @pytest.mark.asyncio
    async def test_rebuild_projection(self):
        """Test rebuilding projection from events."""
        store = KafkaEventStore()
        manager = ProjectionManager(store)
        projection = CustomerReadModel()
        
        manager.register_projection(projection)
        
        aggregate_id = "CUST001"
        
        # Append events
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id=aggregate_id,
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={"name": "John Doe"}
        )
        
        await store.append_event(event)
        
        # Rebuild projection
        await manager.rebuild_projection(projection, aggregate_id)
        
        # Verify projection
        customer = projection.get_customer(aggregate_id)
        
        assert customer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

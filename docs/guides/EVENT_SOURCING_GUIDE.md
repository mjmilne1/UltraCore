# Event Sourcing Developer Guide

**Version:** 1.0  
**Last Updated:** January 14, 2025

---

## Overview

UltraCore's Event Sourcing framework provides a complete event-driven architecture with Kafka as the event store. This guide covers how to work with events, handlers, projections, and CQRS patterns.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Event Store](#event-store)
3. [Publishing Events](#publishing-events)
4. [Event Handlers](#event-handlers)
5. [CQRS Projections](#cqrs-projections)
6. [Event Replay](#event-replay)
7. [Snapshots](#snapshots)
8. [Best Practices](#best-practices)

---

## Core Concepts

### Event Sourcing

Event Sourcing stores all changes to application state as a sequence of events. Instead of storing current state, we store the events that led to that state.

**Benefits:**
- Complete audit trail
- Time travel (replay to any point)
- Event-driven architecture
- CQRS support
- Debugging and analysis

### CQRS (Command Query Responsibility Segregation)

CQRS separates read and write models:
- **Commands:** Write operations that generate events
- **Queries:** Read operations from optimized read models
- **Projections:** Transform events into read models

### Kafka Integration

Kafka provides:
- Durable event storage
- Event ordering guarantees
- Scalable event streaming
- Dead letter queue (DLQ) for failed events

---

## Event Store

### Event Structure

All events follow a standard structure:

```python
from ultracore.event_sourcing import Event, EventMetadata, EventType

event = Event(
    metadata=EventMetadata(
        event_id="evt_12345",
        event_type=EventType.CUSTOMER_CREATED,
        aggregate_id="CUST001",
        aggregate_type="Customer",
        version=1,
        timestamp=datetime.utcnow(),
        causation_id="cmd_67890",  # Optional: causing command
        correlation_id="req_abcde"  # Optional: request correlation
    ),
    data={
        "name": "John Doe",
        "email": "john@example.com"
    }
)
```

### Event Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | Unique event identifier |
| `event_type` | EventType | Yes | Type of event |
| `aggregate_id` | string | Yes | ID of the aggregate |
| `aggregate_type` | string | Yes | Type of aggregate |
| `version` | integer | Yes | Event version for aggregate |
| `timestamp` | datetime | Yes | When event occurred |
| `causation_id` | string | No | ID of causing event/command |
| `correlation_id` | string | No | Request correlation ID |

### Event Types

70+ event types across domains:

**Customer Events:**
- `CUSTOMER_CREATED`
- `CUSTOMER_UPDATED`
- `CUSTOMER_KYC_COMPLETED`
- `CUSTOMER_RISK_ASSESSED`
- `CUSTOMER_DEACTIVATED`

**Account Events:**
- `ACCOUNT_OPENED`
- `ACCOUNT_CLOSED`
- `ACCOUNT_BALANCE_UPDATED`
- `ACCOUNT_LIMIT_CHANGED`
- `ACCOUNT_STATUS_CHANGED`

**Transaction Events:**
- `TRANSACTION_CREATED`
- `TRANSACTION_POSTED`
- `TRANSACTION_SETTLED`
- `TRANSACTION_REVERSED`

**Payment Events:**
- `PAYMENT_INITIATED`
- `PAYMENT_AUTHORIZED`
- `PAYMENT_COMPLETED`
- `PAYMENT_FAILED`
- `PAYMENT_REFUNDED`

**Loan Events:**
- `LOAN_APPLICATION_SUBMITTED`
- `LOAN_APPROVED`
- `LOAN_REJECTED`
- `LOAN_DISBURSED`
- `LOAN_REPAYMENT_MADE`
- `LOAN_DEFAULTED`

[See full list in `event_sourcing/base.py`]

---

## Publishing Events

### Using Event Store

```python
from ultracore.event_sourcing.store.event_store import KafkaEventStore
from ultracore.event_sourcing import Event, EventMetadata, EventType
from datetime import datetime
from uuid import uuid4

# Initialize event store
event_store = KafkaEventStore()

# Create event
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
        "phone": "+61400000000"
    }
)

# Append to event store
await event_store.append_event(event)
```

### Event Versioning

Events are versioned per aggregate for optimistic concurrency control:

```python
# First event (version 1)
event1 = Event(
    metadata=EventMetadata(
        event_id=str(uuid4()),
        event_type=EventType.CUSTOMER_CREATED,
        aggregate_id="CUST001",
        aggregate_type="Customer",
        version=1,  # First version
        timestamp=datetime.utcnow(),
    ),
    data={"name": "John Doe"}
)

await event_store.append_event(event1)

# Second event (version 2)
event2 = Event(
    metadata=EventMetadata(
        event_id=str(uuid4()),
        event_type=EventType.CUSTOMER_UPDATED,
        aggregate_id="CUST001",
        aggregate_type="Customer",
        version=2,  # Incremented version
        timestamp=datetime.utcnow(),
        causation_id=event1.metadata.event_id
    ),
    data={"email": "john.doe@example.com"}
)

await event_store.append_event(event2)
```

### Causation and Correlation

Track event chains with causation and correlation IDs:

```python
# Original event
original_event = Event(
    metadata=EventMetadata(
        event_id="evt_001",
        event_type=EventType.PAYMENT_INITIATED,
        aggregate_id="PAY001",
        aggregate_type="Payment",
        version=1,
        timestamp=datetime.utcnow(),
        correlation_id="req_12345"  # Request ID
    ),
    data={"amount": 100}
)

# Caused event
caused_event = Event(
    metadata=EventMetadata(
        event_id="evt_002",
        event_type=EventType.PAYMENT_AUTHORIZED,
        aggregate_id="PAY001",
        aggregate_type="Payment",
        version=2,
        timestamp=datetime.utcnow(),
        causation_id="evt_001",  # Caused by original event
        correlation_id="req_12345"  # Same request
    ),
    data={}
)
```

---

## Event Handlers

### Creating a Handler

Event handlers process events and update read models or trigger side effects:

```python
from ultracore.event_sourcing.handlers.base import EventHandler
from ultracore.event_sourcing import Event, EventType

class MyDomainHandler(EventHandler):
    """Handler for my domain events."""
    
    def __init__(self):
        super().__init__("my_domain_handler")
        
        # Register event type handlers
        self.register_handler(
            EventType.MY_EVENT_TYPE,
            self._handle_my_event
        )
    
    async def _handle_my_event(self, event: Event):
        """Handle MY_EVENT_TYPE."""
        print(f"Processing event: {event.metadata.event_id}")
        
        # Extract data
        data = event.data
        
        # Update read model
        await self._update_read_model(event)
        
        # Trigger side effects
        await self._send_notification(event)
    
    async def _update_read_model(self, event: Event):
        """Update read model from event."""
        # Implementation here
        pass
    
    async def _send_notification(self, event: Event):
        """Send notification for event."""
        # Implementation here
        pass
```

### Using Existing Handlers

```python
from ultracore.event_sourcing.handlers import CustomerEventHandler

# Initialize handler
handler = CustomerEventHandler()

# Process event
await handler.handle(event)
```

### Available Handlers

- `CustomerEventHandler` - Customer lifecycle events
- `AccountEventHandler` - Account operations
- `TransactionEventHandler` - Transaction processing
- `PaymentEventHandler` - Payment flows
- `LoanEventHandler` - Loan lifecycle
- `InvestmentEventHandler` - Investment operations
- `ComplianceEventHandler` - Compliance checks
- `RiskEventHandler` - Risk assessments
- `CollateralEventHandler` - Collateral management
- `NotificationEventHandler` - Notification delivery
- `AuditEventHandler` - Audit logging
- `AnalyticsEventHandler` - Analytics processing
- `SystemEventHandler` - System operations

---

## CQRS Projections

### Read Models

Read models are optimized views of data built from events:

```python
from ultracore.event_sourcing.projections.read_models import CustomerReadModel

# Initialize read model
read_model = CustomerReadModel()

# Project event
await read_model.project(event)

# Query read model
customer = read_model.get_customer("CUST001")
print(customer)
# Output: {'customer_id': 'CUST001', 'name': 'John Doe', ...}

# List customers
customers = read_model.list_customers(limit=10)
```

### Projection Manager

The projection manager coordinates multiple projections:

```python
from ultracore.event_sourcing.projections import ProjectionManager
from ultracore.event_sourcing.projections.read_models import (
    CustomerReadModel,
    AccountReadModel,
    TransactionReadModel
)
from ultracore.event_sourcing.store.event_store import KafkaEventStore

# Initialize
event_store = KafkaEventStore()
manager = ProjectionManager(event_store)

# Register projections
manager.register_projection(CustomerReadModel())
manager.register_projection(AccountReadModel())
manager.register_projection(TransactionReadModel())

# Project event to all registered projections
await manager.project_event(event)

# Rebuild projection from event store
await manager.rebuild_projection(
    CustomerReadModel(),
    aggregate_id="CUST001"
)

# Get projection status
status = manager.get_projection_status()
print(status)
# Output: [{'name': 'CustomerReadModel', 'event_count': 150, ...}]
```

### Available Read Models

- `CustomerReadModel` - Customer data
- `AccountReadModel` - Account balances and status
- `TransactionReadModel` - Transaction history
- `PaymentReadModel` - Payment status
- `LoanReadModel` - Loan lifecycle

---

## Event Replay

### Replaying Events

Replay events to rebuild state or projections:

```python
# Get all events for an aggregate
events = await event_store.get_events("CUST001")

# Replay events to rebuild state
state = {}
for event in events:
    if event.metadata.event_type == EventType.CUSTOMER_CREATED:
        state = event.data
    elif event.metadata.event_type == EventType.CUSTOMER_UPDATED:
        state.update(event.data)

print(state)
```

### Rebuilding Projections

```python
# Rebuild specific projection
await manager.rebuild_projection(
    CustomerReadModel(),
    aggregate_id="CUST001"
)

# Rebuild all projections
for projection in manager.projections:
    await manager.rebuild_projection(projection)
```

### Point-in-Time Recovery

```python
# Get events up to specific timestamp
events = await event_store.get_events(
    "CUST001",
    end_timestamp=datetime(2025, 1, 1)
)

# Rebuild state at that point in time
state = {}
for event in events:
    # Apply event to state
    pass
```

---

## Snapshots

### Creating Snapshots

Snapshots optimize event replay by storing aggregate state periodically:

```python
from ultracore.event_sourcing.store.snapshot_store import SnapshotStore
from ultracore.event_sourcing.base import Snapshot

snapshot_store = SnapshotStore()

# Create snapshot
snapshot = Snapshot(
    aggregate_id="CUST001",
    aggregate_type="Customer",
    version=100,  # After 100 events
    state={
        "name": "John Doe",
        "email": "john@example.com",
        # ... full aggregate state
    },
    timestamp=datetime.utcnow()
)

# Save snapshot
await snapshot_store.save_snapshot(snapshot)
```

### Using Snapshots

```python
# Get latest snapshot
snapshot = await snapshot_store.get_snapshot("CUST001")

if snapshot:
    # Start from snapshot
    state = snapshot.state
    version = snapshot.version
    
    # Replay only events after snapshot
    events = await event_store.get_events(
        "CUST001",
        from_version=version + 1
    )
    
    for event in events:
        # Apply event to state
        pass
else:
    # No snapshot, replay all events
    events = await event_store.get_events("CUST001")
```

### Automatic Snapshots

Configure automatic snapshot creation:

```python
# Snapshot every 100 events
SNAPSHOT_FREQUENCY = 100

async def append_with_snapshot(event: Event):
    await event_store.append_event(event)
    
    if event.metadata.version % SNAPSHOT_FREQUENCY == 0:
        # Create snapshot
        state = await rebuild_aggregate_state(event.metadata.aggregate_id)
        snapshot = Snapshot(
            aggregate_id=event.metadata.aggregate_id,
            aggregate_type=event.metadata.aggregate_type,
            version=event.metadata.version,
            state=state,
            timestamp=datetime.utcnow()
        )
        await snapshot_store.save_snapshot(snapshot)
```

---

## Best Practices

### Event Design

1. **Events are facts:** Name events in past tense (e.g., `CustomerCreated`, not `CreateCustomer`)
2. **Events are immutable:** Never modify published events
3. **Include all data:** Event should contain all data needed by consumers
4. **Keep events small:** Large payloads should reference external storage
5. **Version events:** Use event versioning for schema evolution

### Versioning

```python
# Event version 1
{
    "name": "John Doe",
    "email": "john@example.com"
}

# Event version 2 (add field)
{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+61400000000"  # New field
}

# Handler supports both versions
async def handle_customer_created(event: Event):
    data = event.data
    name = data["name"]
    email = data["email"]
    phone = data.get("phone")  # Optional for v1 events
```

### Error Handling

```python
async def handle_event_with_retry(event: Event):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            await handler.handle(event)
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                # Send to DLQ
                await send_to_dlq(event, error=str(e))
            else:
                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)
```

### Idempotency

```python
# Track processed events
processed_events = set()

async def handle_event_idempotent(event: Event):
    event_id = event.metadata.event_id
    
    if event_id in processed_events:
        # Already processed, skip
        return
    
    # Process event
    await handler.handle(event)
    
    # Mark as processed
    processed_events.add(event_id)
```

### Testing

```python
import pytest

@pytest.mark.asyncio
async def test_customer_created_event():
    # Arrange
    event_store = KafkaEventStore()
    handler = CustomerEventHandler()
    
    event = Event(
        metadata=EventMetadata(
            event_id="test_001",
            event_type=EventType.CUSTOMER_CREATED,
            aggregate_id="CUST_TEST",
            aggregate_type="Customer",
            version=1,
            timestamp=datetime.utcnow(),
        ),
        data={"name": "Test User"}
    )
    
    # Act
    await event_store.append_event(event)
    await handler.handle(event)
    
    # Assert
    events = await event_store.get_events("CUST_TEST")
    assert len(events) == 1
    assert events[0].data["name"] == "Test User"
```

---

## Monitoring

### Event Metrics

Track key metrics:
- Events published per second
- Event processing latency
- Failed events (DLQ count)
- Consumer lag
- Projection rebuild time

### Logging

```python
import logging

logger = logging.getLogger(__name__)

async def handle_event(event: Event):
    logger.info(
        f"Processing event {event.metadata.event_id} "
        f"type={event.metadata.event_type} "
        f"aggregate={event.metadata.aggregate_id}"
    )
    
    try:
        await handler.handle(event)
        logger.info(f"Successfully processed {event.metadata.event_id}")
    except Exception as e:
        logger.error(
            f"Failed to process {event.metadata.event_id}: {str(e)}",
            exc_info=True
        )
```

---

## Troubleshooting

### Event Not Appearing

1. Check Kafka topic exists
2. Verify event was published (check logs)
3. Check consumer is running
4. Verify consumer group ID

### Projection Out of Sync

1. Check for failed events in DLQ
2. Rebuild projection from events
3. Verify event ordering

### Performance Issues

1. Use snapshots for large aggregates
2. Optimize read model queries
3. Scale Kafka partitions
4. Use batch processing

---

## Resources

- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Kafka Documentation](https://kafka.apache.org/documentation/)

---

**For support, contact:** event-sourcing-team@ultracore.com

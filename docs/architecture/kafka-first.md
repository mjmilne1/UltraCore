# Kafka-First Event Sourcing Architecture

## Overview

UltraCore implements a **Kafka-first event sourcing architecture** where Kafka is the single source of truth for all state changes. The database (PostgreSQL) serves as an optimized read model (projection) that is materialized from the event stream.

This architecture provides:
- **Complete audit trail** - Every state change is captured as an immutable event
- **Event replay** - Rebuild system state from events at any point in time
- **CQRS** - Command Query Responsibility Segregation for scalability
- **Reliability** - Events are never lost, always recoverable
- **Time travel** - Query historical state at any timestamp

---

## Architecture Diagram

```
┌─────────────┐
│   API/UI    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    WRITE SIDE                            │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Command    │────────▶│    Kafka     │             │
│  │   Handler    │         │   Producer   │             │
│  └──────────────┘         └──────┬───────┘             │
│                                   │                      │
│                                   ▼                      │
│                          ┌────────────────┐             │
│                          │  Kafka Topics  │             │
│                          │ (Event Store)  │             │
│                          └────────┬───────┘             │
└───────────────────────────────────┼──────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────┐
│                    READ SIDE                             │
│  ┌──────────────┐         ┌──────────────┐             │
│  │    Kafka     │────────▶│  Projection  │             │
│  │   Consumer   │         │   Handler    │             │
│  └──────────────┘         └──────┬───────┘             │
│                                   │                      │
│                                   ▼                      │
│                          ┌────────────────┐             │
│                          │   PostgreSQL   │             │
│                          │  (Read Model)  │             │
│                          └────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## Event Flow

### 1. Write Path (Command → Event)

```python
# Step 1: User action triggers command
POST /api/v1/savings/accounts
{
  "client_id": "...",
  "product_id": "...",
  "account_name": "My Savings"
}

# Step 2: Command handler publishes event to Kafka
event_id = await kafka_producer.publish_event(
    topic=EventTopic.ACCOUNT_EVENTS,
    event_type="SavingsAccountOpened",
    aggregate_id=account_id,
    event_data={...},
    tenant_id=tenant_id,
    user_id=user_id,
)

# Step 3: Event is persisted in Kafka (SOURCE OF TRUTH)
# - Immutable
# - Ordered by partition key (aggregate_id)
# - Replicated for durability
```

### 2. Read Path (Event → Projection)

```python
# Step 1: Consumer reads event from Kafka
consumer = SavingsProjectionConsumer(db_session_factory)
consumer.start()

# Step 2: Consumer processes event
async def process_event(event):
    if event['event_type'] == 'SavingsAccountOpened':
        # Create projection in PostgreSQL
        account = SavingsAccountModel(
            account_id=event['aggregate_id'],
            **event['event_data']
        )
        session.add(account)
        await session.commit()

# Step 3: Data is now queryable from PostgreSQL
account = await session.get(SavingsAccountModel, account_id)
```

### 3. Event Replay (Kafka → Rebuild State)

```python
# Rebuild aggregate from events
event_store = get_event_store()
events = event_store.get_events_by_aggregate(
    topic="ultracore.savings.accounts.lifecycle",
    aggregate_id=account_id
)

# Apply events to rebuild state
account = SavingsAccount()
for event in events:
    account.apply_event(event)

# Account state is now reconstructed from events
```

---

## Event Structure

Every event follows a standard envelope structure:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "SavingsAccountOpened",
  "event_version": 1,
  
  "aggregate_type": "SavingsAccount",
  "aggregate_id": "123e4567-e89b-12d3-a456-426614174000",
  
  "tenant_id": "tenant-123",
  "user_id": "user-456",
  
  "event_data": {
    "client_id": "...",
    "product_id": "...",
    "account_number": "SA1234567890",
    "account_name": "My Savings"
  },
  
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "causation_id": null,
  
  "event_timestamp": "2025-11-13T10:30:00Z",
  
  "metadata": {
    "source": "ultracore-api",
    "version": "1.0.0"
  }
}
```

---

## Kafka Topics

### Savings Domain

| Topic | Purpose | Retention |
|-------|---------|-----------|
| `ultracore.savings.accounts.lifecycle` | Account creation, approval, closure | Forever |
| `ultracore.savings.accounts.transactions` | Deposits, withdrawals, transfers | Forever |
| `ultracore.savings.interest` | Interest accrual, posting, tax | Forever |
| `ultracore.savings.fees` | Fee charges, waivers | Forever |
| `ultracore.savings.compliance` | TFN updates, regulatory events | Forever |

### Other Domains

| Topic | Purpose |
|-------|---------|
| `ultracore.customers.events` | Customer lifecycle |
| `ultracore.loans.events` | Loan lifecycle |
| `ultracore.transactions.events` | Payment transactions |
| `ultracore.audit.events` | Audit and compliance |

---

## Event Store

The Event Store provides query capabilities over the Kafka event log:

```python
from ultracore.event_sourcing.store.event_store import get_event_store

event_store = get_event_store()

# Get all events for an aggregate
events = event_store.get_events_by_aggregate(
    topic="ultracore.savings.accounts.lifecycle",
    aggregate_id=account_id
)

# Get events by type
events = event_store.get_events_by_type(
    topic="ultracore.savings.accounts.lifecycle",
    event_type="SavingsAccountOpened",
    limit=100
)

# Get all events from a topic
events = event_store.get_all_events(
    topic="ultracore.savings.accounts.lifecycle",
    from_offset=0,
    limit=1000
)

# Stream events in real-time
async for event in event_store.stream_events(
    topic="ultracore.savings.accounts.lifecycle"
):
    print(f"New event: {event.event_type}")
```

---

## Event Consumers

### Base Consumer

All consumers extend `BaseEventConsumer`:

```python
from ultracore.event_sourcing.consumers.base_consumer import BaseEventConsumer

class MyConsumer(BaseEventConsumer):
    def __init__(self):
        super().__init__(
            topics=["ultracore.savings.accounts.lifecycle"],
            group_id="my-consumer-group"
        )
    
    async def process_event(self, event):
        # Process event
        print(f"Processing: {event['event_type']}")
        return True  # Success

# Start consumer
consumer = MyConsumer()
consumer.start()
```

### Projection Consumer

Materializes events into PostgreSQL:

```python
from ultracore.event_sourcing.consumers.savings_projection_consumer import (
    SavingsProjectionConsumer
)

# Create consumer
consumer = SavingsProjectionConsumer(
    database_session_factory=db_config.get_session
)

# Start consuming and projecting
consumer.start()
```

---

## Event Replay

### Replay All Events

```python
from ultracore.event_sourcing.replay.event_replay import EventReplay

replay = EventReplay(event_store)

# Replay all events from a topic
stats = replay.replay_all_events(
    topic="ultracore.savings.accounts.lifecycle",
    projection_handler=my_projection_handler
)

print(f"Replayed {stats['events_processed']} events")
```

### Replay Aggregate

```python
# Rebuild aggregate from events
account = replay.replay_aggregate(
    topic="ultracore.savings.accounts.lifecycle",
    aggregate_id=account_id,
    aggregate_class=SavingsAccount
)

print(f"Account balance: {account.balance}")
```

### Verify Consistency

```python
# Verify event consistency
consistency = replay.verify_event_consistency(
    topic="ultracore.savings.accounts.lifecycle",
    aggregate_id=account_id
)

if consistency['consistent']:
    print("✓ Events are consistent")
else:
    print(f"✗ Found {len(consistency['issues'])} issues")
```

### Generate Audit Report

```python
# Generate audit report
audit_report = replay.generate_audit_report(
    topic="ultracore.savings.accounts.lifecycle",
    aggregate_id=account_id
)

print(f"Total events: {audit_report['total_events']}")
print(f"First event: {audit_report['first_event']}")
print(f"Last event: {audit_report['last_event']}")
print(f"Events by type: {audit_report['events_by_type']}")
```

---

## Database Models (Projections)

PostgreSQL stores materialized views (projections) of the event stream:

```python
from ultracore.database.models import SavingsAccountModel

# Query projection
async with db_session() as session:
    account = await session.get(SavingsAccountModel, account_id)
    print(f"Balance: {account.balance}")
```

**Important:** The database is NOT the source of truth. It's a denormalized read model optimized for queries. The source of truth is always Kafka.

---

## Reliability Guarantees

### Kafka Producer

```python
KafkaProducer(
    acks='all',  # Wait for all replicas
    retries=3,  # Retry on failure
    enable_idempotence=True,  # Prevent duplicates
    max_in_flight_requests_per_connection=1,  # Strict ordering
)
```

### Kafka Consumer

```python
KafkaConsumer(
    enable_auto_commit=False,  # Manual commit for reliability
    auto_offset_reset='earliest',  # Start from beginning
)

# Process event
success = await process_event(event)

if success:
    consumer.commit()  # Commit offset
```

---

## Benefits

### 1. Complete Audit Trail

Every state change is captured as an immutable event. Perfect for:
- Regulatory compliance
- Fraud investigation
- Dispute resolution
- Financial audits

### 2. Event Replay

Rebuild system state at any point in time:
- Disaster recovery
- Bug fixes (replay with corrected logic)
- Data migration
- Historical analysis

### 3. CQRS (Command Query Responsibility Segregation)

Separate write and read models:
- Optimize writes (Kafka)
- Optimize reads (PostgreSQL)
- Scale independently

### 4. Time Travel

Query historical state:
- "What was the account balance on 2024-01-01?"
- "Show all transactions for Q4 2024"
- "Replay events from last week"

### 5. Scalability

- Kafka handles millions of events/second
- Consumers can be scaled horizontally
- Database is only for reads (can use replicas)

---

## Best Practices

### 1. Event Naming

Use past tense (events are facts):
- ✅ `SavingsAccountOpened`
- ✅ `DepositMade`
- ❌ `OpenSavingsAccount`
- ❌ `MakeDeposit`

### 2. Event Granularity

One event per business action:
- ✅ `SavingsAccountOpened` + `InitialDepositMade`
- ❌ `SavingsAccountOpenedAndDeposited`

### 3. Event Immutability

Never modify published events:
- ✅ Publish compensating event
- ❌ Update event in Kafka

### 4. Partition Keys

Use aggregate ID as partition key for ordering:
```python
producer.send(
    topic="ultracore.savings.accounts.lifecycle",
    key=aggregate_id,  # Ensures ordering per account
    value=event
)
```

### 5. Schema Evolution

Version your events:
```json
{
  "event_type": "SavingsAccountOpened",
  "event_version": 2,  // Increment on breaking changes
  "event_data": {...}
}
```

---

## Monitoring

### Kafka Metrics

- Consumer lag (events behind)
- Throughput (events/second)
- Error rate
- Partition distribution

### Event Store Metrics

- Total events
- Events by type
- Events by aggregate
- Storage size

### Consumer Metrics

- Events processed
- Events failed
- Processing rate
- Projection lag

---

## Conclusion

The Kafka-first architecture provides UltraCore with:
- **Bank-grade reliability** - Events are never lost
- **Complete audit trail** - Every change is tracked
- **Event replay** - Rebuild state at any time
- **Scalability** - Handle millions of events
- **CQRS** - Optimize reads and writes separately

This is the foundation for a truly event-driven, scalable, and auditable core banking platform.

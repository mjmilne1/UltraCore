# Delinquency Management Module

## Overview

The **Delinquency Management Module** provides comprehensive, real-time loan delinquency tracking with automated bucket classification, portfolio-at-risk analysis, and ML-powered risk prediction.

---

## Key Features

### 1. Real-Time Delinquency Tracking
- **Event-driven architecture** - Listens to payment events from Kafka
- **Automatic status updates** - Calculates days past due in real-time
- **Bucket classification** - Automatically classifies loans into delinquency buckets
- **Instant notifications** - Publishes delinquency events for downstream processing

### 2. Automated Risk Management
- **Delinquency buckets** - 0-30, 30-60, 60-90, 90+ days past due
- **Automated actions** - Reminders, late fees, collection notices
- **Portfolio-at-Risk (PAR)** - Real-time PAR calculation
- **Provisioning recommendations** - Automated provisioning based on bucket

### 3. Event Sourcing Integration
- **11 event types** - Complete delinquency lifecycle
- **5 Kafka topics** - Organized by event category
- **Full audit trail** - Every status change is recorded
- **Event replay** - Rebuild delinquency history from events

---

## Architecture

### Event-Driven Flow

```
Payment Event (Kafka)
       ↓
Delinquency Consumer
       ↓
Calculate Days Past Due
       ↓
Update Delinquency Bucket
       ↓
Trigger Automated Actions
       ↓
Publish Delinquency Events (Kafka)
       ↓
Update PostgreSQL Projection
```

### Components

| Component | Purpose |
|-----------|---------|
| **DelinquencyStatus** | Domain model for delinquency status |
| **DelinquencyService** | Business logic for delinquency management |
| **DelinquencyConsumer** | Real-time event processing |
| **DelinquencyEventProducer** | Publishes delinquency events to Kafka |

---

## Delinquency Buckets

| Bucket | Days Past Due | Risk Level | Automated Actions |
|--------|---------------|------------|-------------------|
| **Current** | 0 | Low | None |
| **Bucket 1** | 1-30 | Low | Send reminder |
| **Bucket 2** | 31-60 | Medium | Send reminder + Apply late fee ($50) |
| **Bucket 3** | 61-90 | High | Collection notice + Late fee ($100) |
| **Bucket 4** | 91+ | Critical | Escalate to collections + 100% provisioning |

---

## Event Types

### Status Events
- `LoanBecameDelinquent` - First missed payment
- `DelinquencyBucketChanged` - Moved to different bucket
- `DelinquencyCured` - Returned to current status
- `LoanDefaulted` - Moved to default status
- `DelinquencyStatusUpdated` - Daily batch update

### Action Events
- `LateFeeApplied` - Late fee charged
- `PaymentReminderSent` - Reminder sent to customer
- `CollectionNoticeIssued` - Formal collection notice
- `LoanWrittenOff` - Loan written off

### Portfolio Events
- `PortfolioAtRiskCalculated` - PAR metrics calculated
- `ProvisioningUpdated` - Provisioning amount updated

---

## Kafka Topics

| Topic | Purpose |
|-------|---------|
| `ultracore.delinquency.status` | Delinquency status changes |
| `ultracore.delinquency.buckets` | Bucket transitions |
| `ultracore.delinquency.actions` | Automated actions |
| `ultracore.delinquency.portfolio` | Portfolio-level metrics |
| `ultracore.delinquency.provisioning` | Provisioning updates |

---

## Usage Examples

### Start Delinquency Consumer

```python
from ultracore.event_sourcing.consumers.delinquency_consumer import (
    start_delinquency_consumer
)

# Start consumer (runs in background)
consumer = start_delinquency_consumer(bootstrap_servers="localhost:9092")
```

### Calculate Portfolio at Risk

```python
from ultracore.domains.delinquency.services.delinquency_service import (
    DelinquencyService
)

service = DelinquencyService()

# Get all delinquency statuses
statuses = get_all_delinquency_statuses()

# Calculate PAR
par = service.calculate_portfolio_at_risk(
    delinquency_statuses=statuses,
    tenant_id=tenant_id
)

print(f"PAR 30: {par.par_30}%")
print(f"PAR 60: {par.par_60}%")
print(f"PAR 90: {par.par_90}%")
print(f"Total provisioning required: ${par.total_provisioning_required}")
```

### Update Delinquency Status

```python
from ultracore.domains.delinquency.models.delinquency_status import (
    DelinquencyStatus
)
from ultracore.domains.delinquency.services.delinquency_service import (
    DelinquencyService
)

service = DelinquencyService()

# Get status
status = DelinquencyStatus(
    loan_id=loan_id,
    tenant_id=tenant_id,
    next_due_date=due_date,
)

# Update with payment
changes = service.update_delinquency_status(
    status=status,
    payment_received=Decimal("500.00")
)

if changes["became_current"]:
    print("✓ Delinquency cured!")
elif changes["bucket_changed"]:
    print(f"Bucket changed: {changes['old_bucket']} → {changes['new_bucket']}")
```

---

## Integration Points

### Consumes Events From
- `ultracore.loans.payments` - Payment events
- `ultracore.loans.lifecycle` - Loan lifecycle events

### Publishes Events To
- `ultracore.delinquency.*` - Delinquency events
- `ultracore.accounting.*` - Provisioning entries (future)
- `ultracore.notifications.*` - Customer alerts (future)

---

## Benefits

### Real-Time Tracking
- **Instant updates** - Delinquency status updated immediately on payment
- **No batch delays** - Real-time bucket classification
- **Immediate actions** - Automated reminders and fees

### Complete Audit Trail
- **Event sourcing** - Every status change is an immutable event
- **Full history** - Replay delinquency history from events
- **Regulatory compliance** - Complete audit trail for regulators

### Automated Risk Management
- **Automated actions** - Reminders, fees, notices sent automatically
- **Portfolio monitoring** - Real-time PAR calculation
- **Provisioning** - Automated provisioning recommendations

---

## Future Enhancements

- ML-powered default prediction
- Cure rate prediction
- Optimal intervention timing
- Payment plan recommendations
- Collections workflow integration
- Regulatory reporting (APRA APS 220)

---

## Conclusion

The Delinquency Management module provides UltraCore with bank-grade, real-time delinquency tracking that leverages Kafka event sourcing for complete audit trail and automated risk management.

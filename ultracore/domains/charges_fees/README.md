# Charges & Fees Management Module

## Overview

The **Charges & Fees Management Module** provides comprehensive, real-time fee management across all products with automated charging rules, revenue tracking, and fee waivers via Kafka event sourcing.

---

## Key Features

### 1. Real-Time Fee Application
- **Event-driven charging** - Fees applied automatically based on triggers
- **Instant revenue recognition** - Fees recorded immediately
- **Automated fee calculation** - Based on configurable rules
- **Zero manual intervention** - Fully automated fee processing

### 2. Comprehensive Fee Types
- **Account fees** - Monthly maintenance, minimum balance, dormancy
- **Transaction fees** - ATM withdrawal, transfer, foreign transaction
- **Loan fees** - Origination, late payment, early repayment
- **Service fees** - Statement, card replacement, stop payment
- **Penalty fees** - Overdraft, NSF, returned payment

### 3. Automated Charging Rules
- **Trigger-based** - Charge on specific events (payment missed, ATM withdrawal)
- **Scheduled** - Monthly, quarterly, annually
- **Conditional** - Based on account balance, transaction count
- **Tiered** - Different rates based on volume or balance

### 4. Revenue Tracking
- **Fee revenue by product** - Loans, savings, accounts
- **Fee revenue by type** - Service, penalty, transaction
- **Fee revenue by period** - Daily, monthly, quarterly
- **Fee waivers tracking** - Waived amount and reasons

---

## Architecture

### Event-Driven Flow

```
Trigger Event (Kafka)
       ↓
Fee Consumer
       ↓
Evaluate Charging Rules
       ↓
Calculate Fee Amount
       ↓
Apply Fee (if applicable)
       ↓
Publish FeeApplied Event (Kafka)
       ↓
Update Accounting (GL Entry)
       ↓
Update Revenue Projection (PostgreSQL)
```

### Components

| Component | Purpose |
|-----------|---------|
| **Fee** | Domain model for fees |
| **ChargingRule** | Automated charging rule configuration |
| **FeeService** | Business logic for fee management |
| **FeeConsumer** | Real-time event processing |
| **FeeEventProducer** | Publishes fee events to Kafka |

---

## Fee Types

### Account Fees
- **Monthly Maintenance** - $10/month (waived if balance ≥ $1,000)
- **Minimum Balance** - Charged if balance below threshold
- **Dormancy** - Charged for inactive accounts
- **Account Closure** - One-time fee on closure

### Transaction Fees
- **ATM Withdrawal (Own Bank)** - Free (first 4/month)
- **ATM Withdrawal (Other Bank)** - $3 (after 4 free)
- **Over-the-Counter Withdrawal** - $5
- **Transfer** - $2-10 depending on type
- **Foreign Transaction** - 3% of transaction amount

### Loan Fees
- **Origination** - 1-2% of principal
- **Late Payment** - $50 (max $100)
- **Early Repayment** - 1% of remaining balance
- **Restructuring** - $200

### Service Fees
- **Paper Statement** - $5/month
- **Card Replacement** - $15
- **Stop Payment** - $25
- **Returned Payment** - $35

### Penalty Fees
- **Overdraft** - $35 per occurrence
- **NSF (Non-Sufficient Funds)** - $35

---

## Charging Rules

### Example: Late Payment Fee

```python
ChargingRule(
    rule_name="Late Payment Fee",
    rule_code="LATE_PAYMENT",
    fee_type=FeeType.LATE_PAYMENT,
    fee_name="Late Payment Fee",
    trigger_type=TriggerType.EVENT,
    trigger_event="PaymentMissed",
    amount_type=AmountType.FIXED,
    fixed_amount=Decimal("50.00"),
    conditions={
        "days_past_due": ">= 1"
    },
    max_fee_amount=Decimal("100.00"),
)
```

### Example: Monthly Maintenance Fee with Waiver

```python
ChargingRule(
    rule_name="Monthly Maintenance Fee",
    rule_code="MONTHLY_MAINT",
    fee_type=FeeType.MONTHLY_MAINTENANCE,
    fee_name="Monthly Maintenance Fee",
    trigger_type=TriggerType.SCHEDULE,
    schedule="0 0 1 * *",  # First day of month
    amount_type=AmountType.FIXED,
    fixed_amount=Decimal("10.00"),
    waiver_conditions={
        "minimum_balance": ">= 1000.00"
    },
)
```

---

## Event Types

### Fee Events
- `FeeApplied` - Fee charged to account/loan
- `FeeWaived` - Fee waived (conditional or manual)
- `FeeRefunded` - Fee refunded to customer
- `FeeRevenueRecognized` - Revenue recorded in GL

### Rule Events
- `ChargingRuleCreated` - New charging rule defined
- `ChargingRuleActivated` - Rule enabled
- `ChargingRuleDeactivated` - Rule disabled

### Revenue Events
- `FeeRevenueCalculated` - Revenue metrics for period

---

## Kafka Topics

| Topic | Purpose |
|-------|---------|
| `ultracore.fees.applied` | Fee application events |
| `ultracore.fees.waived` | Fee waiver events |
| `ultracore.fees.refunded` | Fee refund events |
| `ultracore.fees.revenue` | Revenue recognition events |
| `ultracore.fees.rules` | Charging rule events |

---

## Usage Examples

### Start Fee Consumer

```python
from ultracore.event_sourcing.consumers.fee_consumer import start_fee_consumer

# Start consumer (runs in background)
consumer = start_fee_consumer(bootstrap_servers="localhost:9092")
```

### Apply Fee Manually

```python
from ultracore.domains.charges_fees.models.fee import Fee, FeeType
from ultracore.domains.charges_fees.services.fee_service import FeeService

service = FeeService()

# Create fee
fee = Fee(
    tenant_id=tenant_id,
    account_id=account_id,
    fee_type=FeeType.MONTHLY_MAINTENANCE,
    fee_name="Monthly Maintenance Fee",
    amount=Decimal("10.00"),
    created_by="system",
)

# Apply fee
result = service.apply_fee(fee)

if result["success"]:
    print(f"✓ Fee applied: ${fee.amount}")
```

### Waive Fee

```python
# Waive fee
result = service.waive_fee(
    fee=fee,
    reason="Customer hardship",
    waived_by="manager@bank.com"
)

if result["success"]:
    print(f"✓ Fee waived: ${fee.amount}")
```

### Calculate Fee Revenue

```python
from datetime import date

# Get all fees
fees = get_all_fees()  # From database

# Calculate revenue for period
revenue = service.calculate_fee_revenue(
    fees=fees,
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
    tenant_id=tenant_id
)

print(f"Total fees applied: ${revenue.total_fees_applied}")
print(f"Total fees waived: ${revenue.total_fees_waived}")
print(f"Net fee revenue: ${revenue.net_fee_revenue}")
```

---

## Integration Points

### Consumes Events From
- `ultracore.loans.payments` - Payment events
- `ultracore.accounts.transactions` - Transaction events
- `ultracore.accounts.lifecycle` - Account lifecycle
- `ultracore.loans.lifecycle` - Loan lifecycle
- `ultracore.delinquency.buckets` - Delinquency changes

### Publishes Events To
- `ultracore.fees.*` - Fee events
- `ultracore.accounting.*` - GL entries (future)
- `ultracore.notifications.*` - Customer alerts (future)

---

## Benefits

### Real-Time Charging
- **Instant fee application** - Fees applied immediately on trigger
- **No batch delays** - Real-time processing via Kafka
- **Automated** - Zero manual intervention

### Complete Audit Trail
- **Event sourcing** - Every fee is an immutable event
- **Full history** - Replay fee history from events
- **Regulatory compliance** - Complete audit trail

### Revenue Optimization
- **Automated charging** - Never miss a fee opportunity
- **Conditional waivers** - Retain customers while maximizing revenue
- **Revenue tracking** - Real-time revenue metrics

---

## Australian Compliance

### ASIC Requirements
- **Fee disclosure** - Clear fee schedules in PDS
- **Fee caps** - Maximum fees per regulation
- **Fee waivers** - Hardship provisions
- **Fee refunds** - Dispute resolution

### Consumer Protection
- **Excessive fees** - Monitoring and caps
- **Fee transparency** - Clear communication
- **Fee disputes** - Resolution process

---

## Conclusion

The Charges & Fees Management Module provides real-time, event-driven fee management with automated charging rules, revenue tracking, and full compliance with Australian regulations.

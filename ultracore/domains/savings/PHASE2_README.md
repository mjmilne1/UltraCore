## Savings Phase 2 Features

### Overview

**Phase 2 Savings Features** provide advanced banking products with full Kafka event sourcing integration:

1. **Recurring Deposits** - Automated periodic deposits with interest benefits
2. **Standing Orders** - Scheduled automatic transfers between accounts
3. **Savings Buckets (Goals)** - Goal-based savings with progress tracking

---

## Features

### 1. Recurring Deposits

**Automated periodic deposits with higher interest rates**

- **Flexible frequency**: Daily, weekly, fortnightly, monthly, quarterly, yearly
- **Interest benefits**: Higher rates than regular savings (e.g., 5.5% vs 3%)
- **Bonus interest**: Extra 0.5% for uninterrupted deposits
- **Maturity options**: Auto-renew, transfer to savings, or payout
- **Early withdrawal**: Penalty of 1% of principal
- **Event-driven execution**: Kafka-scheduled automated deposits

**Use Cases:**
- Regular savings commitment
- Goal-based accumulation
- Higher interest earnings
- Disciplined saving habits

### 2. Standing Orders

**Automated scheduled transfers with smart execution**

- **Transfer types**: Internal, external (BPAY, EFT), loan repayment, bill payment
- **Flexible scheduling**: One-time or recurring (daily, weekly, monthly)
- **Smart execution**: Balance checks, retry logic, weekend/holiday skipping
- **Management**: Pause, resume, modify, cancel anytime
- **Notifications**: Success/failure alerts
- **Event-driven processing**: Real-time execution via Kafka

**Use Cases:**
- Automated bill payments
- Regular loan repayments
- Savings transfers
- Rent payments

### 3. Savings Buckets (Goals)

**Goal-based savings with progress tracking and auto-allocation**

- **Goal types**: Emergency fund, vacation, home deposit, car, education, custom
- **Progress tracking**: Visual progress indicators, milestones, achievement badges
- **Auto-allocation**: Distribute deposits across buckets based on priority or percentage
- **Target dates**: Time-bound goals with estimated completion
- **Achievement rewards**: Bonus interest on goal completion (0.5%)
- **Event-driven updates**: Real-time progress tracking via Kafka

**Use Cases:**
- Emergency fund building
- Vacation savings
- Home deposit accumulation
- Car purchase planning
- Education funding

---

## Event-Driven Architecture

### Recurring Deposits Flow

```
1. RecurringDepositScheduled
   ↓
2. RecurringDepositDue (scheduled event)
   ↓
3. Consumer processes event
   ↓
4. Execute deposit (debit source, credit RD account)
   ↓
5. RecurringDepositExecuted or RecurringDepositFailed
   ↓
6. Update account balance
   ↓
7. Calculate interest accrual
   ↓
8. Send notification
```

### Standing Orders Flow

```
1. StandingOrderScheduled
   ↓
2. StandingOrderDue (scheduled event)
   ↓
3. Consumer processes event
   ↓
4. Check account balance
   ↓
5. Execute transfer (if sufficient funds)
   ↓
6. StandingOrderExecuted or StandingOrderFailed
   ↓
7. Update account balances
   ↓
8. Send notification
   ↓
9. Schedule retry (if failed and retry enabled)
```

### Savings Buckets Flow

```
1. DepositReceived (to parent account)
   ↓
2. Consumer processes event
   ↓
3. Get active buckets
   ↓
4. Calculate allocation (based on strategy)
   ↓
5. Allocate to each bucket
   ↓
6. BucketAllocated events published
   ↓
7. Update bucket balances
   ↓
8. Check milestones
   ↓
9. BucketMilestoneReached (if applicable)
   ↓
10. BucketGoalAchieved (if target reached)
   ↓
11. Apply bonus interest
   ↓
12. Send celebration notification
```

---

## Usage Examples

### Create Recurring Deposit

```python
from ultracore.domains.savings.models.phase2.recurring_deposit import (
    RecurringDeposit,
    DepositFrequency,
    MaturityAction
)
from datetime import date
from decimal import Decimal

# Create monthly recurring deposit
rd = RecurringDeposit(
    tenant_id=tenant_id,
    account_id=account_id,
    customer_id=customer_id,
    deposit_amount=Decimal("500.00"),  # $500/month
    frequency=DepositFrequency.MONTHLY,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),  # 12 months
    interest_rate=Decimal("5.5"),  # 5.5% p.a.
    bonus_interest_rate=Decimal("0.5"),  # +0.5% for uninterrupted
    maturity_action=MaturityAction.AUTO_RENEW,
    created_by="customer@example.com"
)

# Activate
rd.activate()

# Calculate expected deposits
rd.calculate_expected_deposits()  # 12 deposits

# Calculate maturity amount
rd.calculate_maturity_amount()  # $6,000 + interest
```

### Create Standing Order

```python
from ultracore.domains.savings.models.phase2.standing_order import (
    StandingOrder,
    TransferType,
    StandingOrderFrequency
)

# Create monthly rent payment
so = StandingOrder(
    tenant_id=tenant_id,
    from_account_id=savings_account_id,
    customer_id=customer_id,
    transfer_type=TransferType.EXTERNAL,
    amount=Decimal("2000.00"),  # $2,000/month rent
    frequency=StandingOrderFrequency.MONTHLY,
    start_date=date(2025, 1, 1),
    bsb="123-456",
    account_number="12345678",
    account_name="Landlord Name",
    reference="Rent payment",
    check_balance_before_execution=True,
    retry_on_failure=True,
    max_retry_attempts=3,
    skip_weekends=True,
    created_by="customer@example.com"
)

# Activate
so.activate()

# Calculate next execution
so.calculate_next_execution_date()
```

### Create Savings Bucket

```python
from ultracore.domains.savings.models.phase2.savings_bucket import (
    SavingsBucket,
    GoalType,
    GoalPriority
)

# Create vacation savings goal
bucket = SavingsBucket(
    tenant_id=tenant_id,
    account_id=account_id,
    customer_id=customer_id,
    goal_type=GoalType.VACATION,
    goal_name="Hawaii Vacation 2025",
    goal_description="Family trip to Hawaii",
    goal_icon="🏝️",
    target_amount=Decimal("5000.00"),
    target_date=date(2025, 12, 1),
    auto_allocation_enabled=True,
    allocation_percentage=Decimal("20.00"),  # 20% of deposits
    priority=GoalPriority.HIGH,
    milestones=[Decimal("25.00"), Decimal("50.00"), Decimal("75.00")],
    bonus_interest_on_achievement=Decimal("0.50"),  # 0.5% bonus
    created_by="customer@example.com"
)

# Allocate funds
bucket.allocate(Decimal("100.00"))

# Calculate progress
bucket.calculate_progress()  # 2% (100/5000)

# Check milestones
new_milestones = bucket.check_milestones()
```

---

## Kafka Topics

| Topic | Purpose |
|-------|---------|
| `ultracore.savings.recurring_deposits` | Recurring deposit events |
| `ultracore.savings.standing_orders` | Standing order events |
| `ultracore.savings.buckets` | Savings bucket events |
| `ultracore.savings.scheduled_tasks` | Scheduled task execution |
| `ultracore.savings.allocations` | Bucket allocation events |

---

## Event Types

### Recurring Deposit Events
- `RecurringDepositCreated`
- `RecurringDepositActivated`
- `RecurringDepositDue`
- `RecurringDepositExecuted`
- `RecurringDepositFailed`
- `RecurringDepositMissed`
- `RecurringDepositMatured`
- `RecurringDepositRenewed`
- `RecurringDepositClosed`

### Standing Order Events
- `StandingOrderCreated`
- `StandingOrderActivated`
- `StandingOrderDue`
- `StandingOrderExecuted`
- `StandingOrderFailed`
- `StandingOrderRetried`
- `StandingOrderCompleted`
- `StandingOrderCancelled`

### Savings Bucket Events
- `SavingsBucketCreated`
- `SavingsBucketActivated`
- `BucketAllocated`
- `BucketProgressUpdated`
- `BucketMilestoneReached`
- `BucketGoalAchieved`
- `BucketWithdrawal`
- `BucketCancelled`

---

## Benefits

### Customer Benefits
✅ **Automated savings** - Set and forget  
✅ **Higher interest rates** - Recurring deposit benefits  
✅ **Goal achievement** - Visual progress tracking  
✅ **Flexibility** - Pause, modify, cancel anytime  
✅ **Convenience** - Automated bill payments and transfers

### Bank Benefits
✅ **Stable funding** - Predictable deposit flows  
✅ **Customer retention** - Long-term commitment  
✅ **Cross-sell opportunities** - Goal-based products  
✅ **Reduced churn** - Automated engagement  
✅ **Operational efficiency** - Automated processing

### Technical Benefits
✅ **Event-driven** - Real-time processing via Kafka  
✅ **Scalable** - Horizontal scaling with consumer groups  
✅ **Auditable** - Complete event history  
✅ **Extensible** - Easy to add new features  
✅ **Resilient** - Retry logic and error handling

---

## Australian Compliance

### Recurring Deposits
- **TFN withholding**: 47% if no TFN provided
- **Interest reporting**: Annual interest statement
- **Early withdrawal**: Penalty disclosure in PDS
- **FCS protection**: $250,000 coverage

### Standing Orders
- **BPAY compliance**: BPAY code validation
- **EFT compliance**: BSB and account number validation
- **Transaction limits**: Daily/monthly limits
- **Fraud prevention**: Velocity checks

### Savings Buckets
- **Virtual accounts**: Not separate bank accounts
- **Interest allocation**: Pro-rata based on bucket balance
- **Reporting**: Consolidated statement
- **Tax treatment**: Interest taxed at parent account level

---

## Conclusion

Phase 2 Savings features provide advanced, event-driven banking products that enable automated, intelligent, and customer-centric savings experiences. These features leverage UltraCore's Kafka-first architecture for real-time processing, scalability, and complete auditability.

# Savings Phase 2 Features - Architecture

## Overview

**Phase 2 Savings Features** provide advanced banking products with full Kafka event sourcing integration:

1. **Recurring Deposits** - Automated periodic deposits with interest benefits
2. **Standing Orders** - Scheduled automatic transfers between accounts
3. **Savings Buckets (Goals)** - Goal-based savings with progress tracking

---

## Key Features

### 1. Recurring Deposits
- **Automated deposits** - Scheduled periodic contributions
- **Interest benefits** - Higher rates for committed savings
- **Flexible frequency** - Daily, weekly, fortnightly, monthly
- **Maturity handling** - Auto-renewal or payout options
- **Penalty-free withdrawals** - After maturity
- **Event-driven execution** - Kafka-scheduled processing

### 2. Standing Orders
- **Automated transfers** - Scheduled payments between accounts
- **Flexible scheduling** - One-time or recurring
- **Smart execution** - Balance checks before transfer
- **Retry logic** - Failed transfer handling
- **Notification** - Success/failure alerts
- **Event-driven processing** - Real-time execution

### 3. Savings Buckets (Goals)
- **Goal-based savings** - Save for specific purposes
- **Progress tracking** - Visual progress indicators
- **Auto-allocation** - Distribute deposits across buckets
- **Target dates** - Time-bound goals
- **Achievement rewards** - Bonus interest on goal completion
- **Event-driven updates** - Real-time progress tracking

---

## Architecture

### Event-Driven Flow

```
Scheduled Event (Kafka)
       ↓
Event Consumer
       ↓
Execute Action (Deposit/Transfer/Allocation)
       ↓
Publish Execution Event
       ↓
Update Account Balance
       ↓
Publish Balance Update Event
       ↓
Trigger Notifications
```

### Components

| Component | Purpose |
|-----------|---------|
| **RecurringDeposit** | Recurring deposit product model |
| **StandingOrder** | Standing order model |
| **SavingsBucket** | Savings goal/bucket model |
| **ScheduledTaskService** | Automated scheduling engine |
| **RecurringDepositConsumer** | Processes recurring deposit events |
| **StandingOrderConsumer** | Processes standing order events |
| **SavingsBucketConsumer** | Processes bucket allocation events |

---

## Recurring Deposits

### Product Features

**Deposit Schedule:**
- Daily, Weekly, Fortnightly, Monthly, Quarterly, Yearly
- Fixed deposit amount
- Flexible start and end dates
- Auto-renewal option

**Interest Benefits:**
- Higher interest rates than regular savings
- Compounding frequency (daily, monthly, quarterly)
- Bonus interest for uninterrupted deposits
- Interest credited at maturity

**Maturity Options:**
- Auto-renew for another term
- Transfer to savings account
- Payout to external account
- Partial withdrawal allowed

**Penalties:**
- Early withdrawal penalty (e.g., 1% of principal)
- Missed deposit handling (grace period, auto-pause)

### Event Flow

```
1. RecurringDepositScheduled
   ↓
2. RecurringDepositDue (scheduled event)
   ↓
3. RecurringDepositExecuted (deposit made)
   ↓
4. InterestAccrued (daily)
   ↓
5. RecurringDepositMatured (at end date)
   ↓
6. RecurringDepositRenewed or RecurringDepositClosed
```

---

## Standing Orders

### Product Features

**Transfer Types:**
- Account-to-account (internal)
- Account-to-external (BPAY, EFT)
- Loan repayment
- Bill payment

**Scheduling:**
- One-time (future-dated)
- Recurring (daily, weekly, monthly)
- End date or indefinite
- Skip weekends/holidays option

**Smart Execution:**
- Balance check before transfer
- Retry on insufficient funds
- Partial transfer option
- Notification on success/failure

**Management:**
- Pause/resume
- Modify amount or schedule
- Cancel anytime
- Execution history

### Event Flow

```
1. StandingOrderCreated
   ↓
2. StandingOrderScheduled
   ↓
3. StandingOrderDue (scheduled event)
   ↓
4. StandingOrderExecuted or StandingOrderFailed
   ↓
5. StandingOrderRetried (if failed)
   ↓
6. StandingOrderCompleted or StandingOrderCancelled
```

---

## Savings Buckets (Goals)

### Product Features

**Goal Types:**
- Emergency fund
- Vacation
- Home deposit
- Car purchase
- Education
- Custom goals

**Goal Configuration:**
- Target amount
- Target date
- Priority (high, medium, low)
- Auto-allocation percentage
- Visual progress tracking

**Auto-Allocation:**
- Distribute deposits across buckets
- Priority-based allocation
- Round-up spare change
- Percentage-based split

**Achievement Rewards:**
- Bonus interest on goal completion
- Badges and milestones
- Progress notifications
- Celebration events

### Event Flow

```
1. SavingsBucketCreated
   ↓
2. DepositReceived (to parent account)
   ↓
3. SavingsBucketAllocationCalculated
   ↓
4. SavingsBucketAllocated (funds moved to bucket)
   ↓
5. SavingsBucketProgressUpdated
   ↓
6. SavingsBucketMilestoneReached
   ↓
7. SavingsBucketGoalAchieved
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

## Scheduling Engine

### Cron-Based Scheduling

**Recurring Deposits:**
```
Daily:       0 0 9 * * *        (9am daily)
Weekly:      0 0 9 * * 1        (9am Monday)
Fortnightly: 0 0 9 */14 * *     (9am every 14 days)
Monthly:     0 0 9 1 * *        (9am 1st of month)
```

**Standing Orders:**
```
Custom schedule based on user preference
Supports complex patterns (e.g., last Friday of month)
```

### Event-Driven Execution

```python
# Scheduled task publishes event
scheduled_event = RecurringDepositDue(
    recurring_deposit_id=rd_id,
    account_id=account_id,
    amount=amount,
    due_date=date.today()
)

# Consumer processes event
consumer.process_recurring_deposit_due(scheduled_event)

# Execute deposit
result = execute_deposit(account_id, amount)

# Publish execution event
execution_event = RecurringDepositExecuted(
    recurring_deposit_id=rd_id,
    account_id=account_id,
    amount=amount,
    executed_at=datetime.utcnow()
)
```

---

## Australian Compliance

### Recurring Deposits
- **TFN withholding** - 47% if no TFN provided
- **Interest reporting** - Annual interest statement
- **Early withdrawal** - Penalty disclosure in PDS
- **FCS protection** - $250,000 coverage

### Standing Orders
- **BPAY compliance** - BPAY code validation
- **EFT compliance** - BSB and account number validation
- **Transaction limits** - Daily/monthly limits
- **Fraud prevention** - Velocity checks

### Savings Buckets
- **Virtual accounts** - Not separate bank accounts
- **Interest allocation** - Pro-rata based on bucket balance
- **Reporting** - Consolidated statement
- **Tax treatment** - Interest taxed at parent account level

---

## Benefits

### Customer Benefits
✅ **Automated savings** - Set and forget  
✅ **Higher interest rates** - Recurring deposit benefits  
✅ **Goal achievement** - Visual progress tracking  
✅ **Flexibility** - Pause, modify, cancel anytime

### Bank Benefits
✅ **Stable funding** - Predictable deposit flows  
✅ **Customer retention** - Long-term commitment  
✅ **Cross-sell opportunities** - Goal-based products  
✅ **Reduced churn** - Automated engagement

### Technical Benefits
✅ **Event-driven** - Real-time processing  
✅ **Scalable** - Kafka-based scheduling  
✅ **Auditable** - Complete event history  
✅ **Extensible** - Easy to add new features

---

## Conclusion

Phase 2 Savings features provide advanced banking products with full event sourcing integration, enabling automated, intelligent, and customer-centric savings experiences.

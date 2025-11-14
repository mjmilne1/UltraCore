# Delinquency Management Module - Architecture

## Overview

The **Delinquency Management Module** provides comprehensive loan delinquency tracking, automated bucket classification, and portfolio-at-risk analysis with full Kafka event sourcing integration for real-time updates.

---

## Key Features

### 1. Real-Time Delinquency Tracking
- **Event-driven updates** - Delinquency status changes published to Kafka
- **Automated bucket classification** - 0-30, 30-60, 60-90, 90+ days past due
- **Payment monitoring** - Real-time payment event processing
- **Status transitions** - Track movement between delinquency buckets

### 2. Automated Risk Management
- **Portfolio-at-Risk (PAR)** calculation
- **Aging analysis** and trend detection
- **ML-powered default prediction**
- **Automated provisioning** recommendations

### 3. Compliance & Reporting
- **APRA reporting** - Prudential Standard APS 220
- **ASIC compliance** - Responsible lending obligations
- **Audit trail** - Complete event history
- **Regulatory reports** - Delinquency aging, PAR, write-offs

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
Classify into Bucket
       ↓
Publish Delinquency Event (Kafka)
       ↓
Update PostgreSQL Projection
       ↓
Trigger Alerts & Actions
```

### Kafka Topics

| Topic | Purpose |
|-------|---------|
| `ultracore.loans.payments` | Payment events (received, missed) |
| `ultracore.delinquency.status` | Delinquency status changes |
| `ultracore.delinquency.buckets` | Bucket transitions |
| `ultracore.delinquency.actions` | Automated actions (fees, notices) |

---

## Delinquency Buckets

| Bucket | Days Past Due | Risk Level | Actions |
|--------|---------------|------------|---------|
| **Current** | 0 | Low | None |
| **Bucket 1** | 1-30 | Low | Courtesy reminder |
| **Bucket 2** | 31-60 | Medium | Payment plan offer |
| **Bucket 3** | 61-90 | High | Collection notice |
| **Bucket 4** | 91+ | Critical | Legal action, write-off |

---

## Domain Models

### DelinquencyStatus
- loan_id
- days_past_due
- current_bucket
- previous_bucket
- amount_overdue
- last_payment_date
- next_due_date

### DelinquencyBucket
- bucket_name
- min_days
- max_days
- risk_level
- automated_actions

### PortfolioAtRisk
- calculation_date
- total_loans
- par_30 (% of portfolio 30+ days overdue)
- par_60
- par_90
- total_amount_at_risk

---

## Event Types

### Delinquency Events
- `LoanBecameDelinquent` - First missed payment
- `DelinquencyBucketChanged` - Moved to different bucket
- `DelinquencyCured` - Returned to current status
- `LoanDefaulted` - Moved to default status
- `ProvisioningRequired` - Automated provisioning trigger

### Action Events
- `LateFeeApplied` - Automated late fee
- `ReminderSent` - Payment reminder
- `CollectionNoticeIssued` - Formal notice
- `LoanWrittenOff` - Write-off event

---

## ML Models

### 1. Default Prediction Model
- Predicts probability of default (0-100%)
- Features: payment history, loan characteristics, customer demographics
- Output: Default risk score, recommended actions

### 2. Cure Rate Prediction
- Predicts likelihood of delinquency cure
- Features: delinquency duration, payment patterns, customer engagement
- Output: Cure probability, optimal intervention timing

---

## Integration Points

### Consumes Events From:
- Loan origination (new loans)
- Payment processing (payments received/missed)
- Customer service (payment plans, hardship)

### Publishes Events To:
- Accounting (provisioning entries)
- Collections (automated workflows)
- Reporting (regulatory reports)
- Notifications (customer alerts)

---

## Conclusion

The Delinquency Management module provides real-time, event-driven delinquency tracking with automated risk management and ML-powered predictions.

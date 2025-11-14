# Charges & Fees Management Module - Architecture

## Overview

The **Charges & Fees Management Module** provides comprehensive fee management across all products with real-time fee application, automated charging rules, revenue tracking, and fee waivers via Kafka event sourcing.

---

## Key Features

### 1. Real-Time Fee Application
- **Event-driven charging** - Fees applied automatically based on triggers
- **Instant revenue recognition** - Fees recorded immediately
- **Automated fee calculation** - Based on configurable rules
- **Fee waivers** - Conditional and manual waivers

### 2. Comprehensive Fee Types
- **Account fees** - Monthly maintenance, minimum balance
- **Transaction fees** - Withdrawal, transfer, ATM
- **Loan fees** - Origination, late payment, early repayment
- **Service fees** - Statement, card replacement, stop payment
- **Penalty fees** - Overdraft, NSF, returned payment

### 3. Automated Charging Rules
- **Trigger-based** - Charge on specific events
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
Publish Fee Event (Kafka)
       ↓
Update Accounting (GL Entry)
       ↓
Update Revenue Projection (PostgreSQL)
```

### Kafka Topics

| Topic | Purpose |
|-------|---------|
| `ultracore.fees.applied` | Fee application events |
| `ultracore.fees.waived` | Fee waiver events |
| `ultracore.fees.refunded` | Fee refund events |
| `ultracore.fees.revenue` | Revenue recognition events |

---

## Fee Types

### Account Fees
- **Monthly maintenance fee** - Fixed monthly charge
- **Minimum balance fee** - Charged if balance below threshold
- **Dormancy fee** - Charged for inactive accounts
- **Account closure fee** - One-time fee on closure

### Transaction Fees
- **ATM withdrawal fee** - Per withdrawal (own/other bank)
- **Over-the-counter withdrawal fee** - Branch withdrawal
- **Transfer fee** - Internal/external transfers
- **Foreign transaction fee** - International transactions

### Loan Fees
- **Origination fee** - One-time fee at disbursement
- **Late payment fee** - Charged on missed payments
- **Early repayment fee** - Penalty for early payoff
- **Restructuring fee** - Loan modification fee

### Service Fees
- **Statement fee** - Paper statement delivery
- **Card replacement fee** - Lost/stolen card
- **Stop payment fee** - Check stop payment
- **Returned payment fee** - NSF, bounced check

---

## Charging Rules

### Trigger-Based Rules
```json
{
  "rule_id": "late_payment_fee",
  "trigger_event": "PaymentMissed",
  "fee_type": "late_payment",
  "amount": 50.00,
  "conditions": {
    "days_past_due": ">= 1"
  }
}
```

### Scheduled Rules
```json
{
  "rule_id": "monthly_maintenance_fee",
  "schedule": "monthly",
  "fee_type": "maintenance",
  "amount": 10.00,
  "waiver_conditions": {
    "minimum_balance": ">= 1000.00"
  }
}
```

### Conditional Rules
```json
{
  "rule_id": "atm_withdrawal_fee",
  "trigger_event": "ATMWithdrawal",
  "fee_type": "atm_withdrawal",
  "amount": 3.00,
  "conditions": {
    "atm_network": "other_bank",
    "free_withdrawals_used": ">= 4"
  }
}
```

---

## Event Types

### Fee Events
- `FeeApplied` - Fee charged to account
- `FeeWaived` - Fee waived (conditional or manual)
- `FeeRefunded` - Fee refunded to customer
- `FeeRevenueRecognized` - Revenue recorded in GL

### Rule Events
- `ChargingRuleCreated` - New charging rule defined
- `ChargingRuleUpdated` - Rule modified
- `ChargingRuleActivated` - Rule enabled
- `ChargingRuleDeactivated` - Rule disabled

---

## Domain Models

### Fee
- fee_id
- fee_type
- amount
- currency
- account_id / loan_id
- applied_date
- waived (boolean)
- waiver_reason
- revenue_recognized (boolean)

### ChargingRule
- rule_id
- rule_name
- fee_type
- trigger_type (event, schedule, conditional)
- trigger_event
- schedule
- amount_type (fixed, percentage, tiered)
- amount
- conditions
- waiver_conditions
- is_active

### FeeRevenue
- revenue_id
- period_start
- period_end
- total_fees_applied
- total_fees_waived
- net_fee_revenue
- breakdown_by_type
- breakdown_by_product

---

## Integration Points

### Consumes Events From
- Account lifecycle (opened, closed, dormant)
- Transaction processing (withdrawals, transfers)
- Loan lifecycle (disbursed, payment missed)
- Delinquency (bucket changes)

### Publishes Events To
- Accounting (GL entries for fee revenue)
- Customer notifications (fee applied, waived)
- Reporting (revenue recognition)

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

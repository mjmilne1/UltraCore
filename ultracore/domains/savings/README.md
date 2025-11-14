# Savings & Deposit Management Module

## Overview

The **Savings & Deposit Management Module** is a comprehensive, Australian-compliant savings account system built on UltraCore's advanced architectural framework. It provides full event sourcing, AI-powered insights, ML predictions, and seamless accounting integration.

## Features

### ✅ Australian Regulatory Compliance

- **ASIC Compliance**: Product Disclosure Statement (PDS), Key Facts Sheet (KFS)
- **APRA Prudential Standards**: Risk management, capital adequacy
- **Tax Compliance**: TFN collection, 47% withholding tax for non-TFN accounts
- **Financial Claims Scheme (FCS)**: $250,000 deposit protection eligibility
- **Consumer Data Right (CDR)**: Data portability and open banking readiness

### ✅ Product Types

1. **High Interest Savings** - Competitive rates with bonus interest conditions
2. **Youth Saver** - Age-restricted products for under-25s with higher rates
3. **Pensioner Saver** - Products for retirees with fee waivers
4. **Business Savings** - Business account savings products
5. **Term Deposits** - Fixed-term deposits with guaranteed rates

### ✅ Interest Calculation

- **Daily Balance Method** - Most accurate, calculates interest on daily closing balance
- **Minimum Monthly Balance Method** - Interest on minimum balance during month
- **Average Daily Balance Method** - Interest on average balance
- **Bonus Interest** - Conditional bonus rates for meeting deposit/withdrawal criteria
- **Compound Interest** - Monthly, quarterly, or annual compounding

### ✅ Account Lifecycle

- Account opening with PDS acceptance
- Maker-checker approval workflow
- Deposits and withdrawals
- Interest accrual and posting
- Fee charging and waivers
- TFN collection and updates
- Dormancy tracking and prevention
- Account closure

### ✅ Event Sourcing

All account activities are captured as immutable events and published to Kafka:

**Account Events:**
- `savings.account.opened`
- `savings.account.approved`
- `savings.account.activated`
- `savings.account.closed`
- `savings.account.frozen`
- `savings.account.dormant`
- `savings.account.tfn_provided`

**Transaction Events:**
- `savings.transaction.deposit`
- `savings.transaction.withdrawal`
- `savings.transaction.transfer_in`
- `savings.transaction.transfer_out`

**Interest Events:**
- `savings.interest.accrued`
- `savings.interest.posted`
- `savings.interest.bonus_earned`
- `savings.interest.bonus_forfeited`
- `savings.tax.withholding_deducted`

**Fee Events:**
- `savings.fee.monthly_charged`
- `savings.fee.waived`
- `savings.fee.withdrawal_charged`

### ✅ AI Agent: Anya Savings Specialist

**Capabilities:**
- Product recommendations based on customer profile
- Savings goal planning and tracking
- Bonus interest condition monitoring
- Dormancy prevention and customer engagement
- TFN withholding tax advisory
- Financial wellness insights

**Example Usage:**
```python
from ultracore.agentic_ai.agents.savings.anya_savings_agent import AnyaSavingsAgent

agent = AnyaSavingsAgent()

# Get product recommendation
recommendation = agent.recommend_savings_product(
    customer_age=30,
    monthly_income=Decimal("5000.00"),
    current_savings=Decimal("10000.00"),
    savings_goal=Decimal("50000.00"),
    available_products=products,
)

# Create savings plan
plan = agent.create_savings_plan(
    current_balance=Decimal("10000.00"),
    target_amount=Decimal("50000.00"),
    target_date=date(2026, 12, 31),
    annual_interest_rate=Decimal("4.50"),
)
```

### ✅ ML Models

**1. Savings Behavior Predictor**
- Predicts savings propensity score (0-100)
- Recommends optimal monthly deposit amount
- Analyzes deposit consistency patterns
- Provides personalized insights

**2. Dormancy Predictor**
- Predicts dormancy risk score (0-100)
- Estimates days until likely dormancy
- Recommends proactive interventions
- Batch processing for portfolio-wide analysis

**Example Usage:**
```python
from ultracore.ml.savings.savings_behavior_predictor import SavingsBehaviorPredictor

predictor = SavingsBehaviorPredictor()

prediction = predictor.predict_savings_propensity(
    age=30,
    monthly_income=Decimal("5000.00"),
    employment_status="employed",
    current_balance=Decimal("10000.00"),
    transaction_history=transactions,
    account_age_months=12,
    has_tfn=True,
    product_type="high_interest_savings",
)
# Returns: propensity_score, recommended_monthly_deposit, insights
```

### ✅ Accounting Integration

Automatic double-entry journal entries for all transactions:

**Chart of Accounts:**
- `1110` - Cash at Bank (ASSET)
- `1100` - Savings Accounts / Customer Deposits (LIABILITY)
- `2100` - Interest Payable (LIABILITY)
- `4100` - Account Fees Revenue (REVENUE)
- `5100` - Interest Expense (EXPENSE)
- `5200` - Withholding Tax Payable (LIABILITY)

**Example Journal Entry (Deposit):**
```
DR: 1110 Cash at Bank          $1,000.00
CR: 1100 Savings Deposits                  $1,000.00
```

## API Endpoints

### Accounts

- `POST /api/v1/savings/accounts` - Create savings account
- `GET /api/v1/savings/accounts/{account_id}` - Get account details
- `GET /api/v1/savings/accounts` - List accounts
- `DELETE /api/v1/savings/accounts/{account_id}` - Close account
- `PUT /api/v1/savings/accounts/{account_id}/tfn` - Update TFN

### Transactions

- `POST /api/v1/savings/accounts/{account_id}/deposit` - Make deposit
- `POST /api/v1/savings/accounts/{account_id}/withdraw` - Make withdrawal
- `GET /api/v1/savings/accounts/{account_id}/transactions` - Get transaction history

### Interest

- `GET /api/v1/savings/accounts/{account_id}/interest/projection` - Project future interest

### Products

- `GET /api/v1/savings/products` - List savings products
- `GET /api/v1/savings/products/{product_id}` - Get product details

## Architecture

```
ultracore/domains/savings/
├── models/                      # Domain models
│   ├── savings_account.py      # Account entity
│   ├── savings_product.py      # Product catalog
│   ├── term_deposit.py         # Term deposit entity
│   └── transaction.py          # Transaction entity
├── services/                    # Business logic
│   ├── account_service.py      # Account lifecycle
│   ├── interest_calculator.py  # Interest calculations
│   └── accounting_integration.py # GL integration
├── events/                      # Event sourcing
│   ├── account_events.py       # Account lifecycle events
│   ├── transaction_events.py   # Transaction events
│   ├── interest_events.py      # Interest events
│   ├── fee_events.py           # Fee events
│   └── event_producer.py       # Kafka producer
└── README.md                    # This file

ultracore/api/v1/savings/
├── routes.py                    # API endpoints
└── schemas.py                   # Request/response schemas

ultracore/agentic_ai/agents/savings/
└── anya_savings_agent.py        # AI agent

ultracore/ml/savings/
├── savings_behavior_predictor.py # ML model
└── dormancy_predictor.py         # ML model

tests/savings/
└── test_savings_module.py       # Comprehensive tests
```

## Testing

Run the comprehensive test suite:

```bash
python3 -m pytest tests/savings/test_savings_module.py -v
```

**Test Coverage:**
- ✅ 18/18 tests passing (100%)
- Domain models
- Business logic services
- Interest calculations
- Accounting integration
- AI agent recommendations
- ML predictions

## Usage Examples

### 1. Create Savings Account

```python
from ultracore.domains.savings.services.account_service import AccountService

account = AccountService.create_account(
    client_id=client_id,
    product=product,
    account_name="Emergency Fund",
    bsb="062000",
    account_number="SA1234567890",
    tenant_id=tenant_id,
    initial_deposit=Decimal("1000.00"),
    tfn="123456789",  # Avoid 47% withholding tax
)
```

### 2. Make Deposit

```python
updated_account, transaction = AccountService.make_deposit(
    account=account,
    amount=Decimal("500.00"),
    source="Salary",
    reference="DEP001",
    description="Monthly savings",
    tenant_id=tenant_id,
)
```

### 3. Calculate Interest

```python
from ultracore.domains.savings.services.interest_calculator import InterestCalculator

# Project 12-month returns
gross, tax, net = InterestCalculator.project_interest(
    principal=Decimal("10000.00"),
    annual_rate=Decimal("4.50"),
    months=12,
    posting_frequency="monthly",
    withholding_tax_rate=Decimal("0.00"),
)
```

### 4. Check Bonus Eligibility

```python
from ultracore.agentic_ai.agents.savings.anya_savings_agent import AnyaSavingsAgent

agent = AnyaSavingsAgent()
eligibility = agent.check_bonus_eligibility(
    account=account,
    product=product,
    monthly_transactions=transactions,
)
```

## Compliance Notes

### TFN Withholding Tax

- **Without TFN**: 47% withholding tax on interest
- **With TFN**: 0% withholding tax (interest still taxable via tax return)
- **TFN Exemption**: Available for certain categories (pensioners, minors)

### Financial Claims Scheme (FCS)

- Protects deposits up to **$250,000** per account holder per ADI
- All savings accounts are FCS-eligible
- Displayed on account statements and PDS

### Product Disclosure Statement (PDS)

- Required for all savings products
- Must be accepted by customer before account opening
- Includes fees, interest rates, terms and conditions

## Future Enhancements

- [ ] Recurring deposit automation
- [ ] Savings goals dashboard
- [ ] Round-up savings (transaction rounding)
- [ ] Linked savings buckets
- [ ] Automated rebalancing
- [ ] Integration with external payment rails

## Support

For questions or issues, please contact the UltraCore development team.

---

**Version:** 1.0.0  
**Last Updated:** November 13, 2025  
**License:** Proprietary

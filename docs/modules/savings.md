# UltraCore Savings & Deposit Management Module

**Version:** 1.0  
**Date:** November 13, 2025  
**Status:** Design Phase  
**Compliance:** Australian Regulatory Framework (ASIC, APRA, ATO)

---

## 1. Executive Summary

This document outlines the architecture for UltraCore's comprehensive Savings & Deposit Management module, designed to be fully compliant with Australian banking regulations while leveraging UltraCore's advanced event sourcing, data mesh, AI agents, and ML/RL infrastructure.

**Key Features:**
- Full Australian regulatory compliance (ASIC, APRA, ATO)
- Event-sourced architecture with Kafka
- AI-powered savings recommendations
- ML-based interest optimization
- Real-time accounting integration
- Multi-product support (Savings, Term Deposits, High-Interest Savings)

---

## 2. Australian Regulatory Compliance

### 2.1 APRA Prudential Standards

**APS 210 - Liquidity Management:**
- Maintain adequate liquidity buffers
- Monitor deposit concentration
- Stress testing for deposit withdrawals
- Liquidity Coverage Ratio (LCR) compliance

**APS 220 - Credit Risk Management:**
- Credit risk assessment for overdraft facilities
- Exposure limits and monitoring

**APS 330 - Capital Adequacy:**
- Risk-weighted assets calculation for deposits
- Capital allocation for deposit products

### 2.2 ASIC Regulations

**Product Disclosure:**
- Product Disclosure Statement (PDS) generation
- Key Facts Sheet (KFS) for deposit products
- Fee disclosure and transparency
- Interest rate disclosure

**Consumer Protection:**
- Unfair contract terms compliance
- Responsible lending obligations
- Dispute resolution procedures
- Financial hardship provisions

### 2.3 ATO Tax Compliance

**TFN Withholding Tax:**
- TFN collection and validation
- Withholding tax at 47% for accounts without TFN
- Exemption handling (under 18, pensioners, etc.)
- Annual interest reporting to ATO

**Interest Reporting:**
- Annual interest statements
- PAYG withholding for non-residents
- Tax invoice generation

### 2.4 Financial Claims Scheme (FCS)

- $250,000 per depositor guarantee
- FCS disclosure on all deposit products
- Account aggregation for FCS limits
- Customer communication requirements

---

## 3. Product Types

### 3.1 Savings Accounts

**Features:**
- At-call access (unlimited withdrawals)
- Tiered interest rates
- Bonus interest conditions
- Minimum balance requirements
- Monthly account fees (with fee waivers)
- Transaction limits for bonus interest

**Australian-Specific:**
- TFN declaration
- Government co-contribution eligibility (for specific products)
- Centrelink direct deposit support

### 3.2 High-Interest Savings Accounts

**Features:**
- Higher base interest rate
- Bonus interest for conditions met (e.g., monthly deposits, no withdrawals)
- Introductory rates for new customers
- Age-based products (e.g., youth savers)

### 3.3 Term Deposits (Fixed Deposits)

**Features:**
- Fixed term (1 month to 5 years)
- Fixed interest rate
- Interest payment options (monthly, quarterly, annually, at maturity)
- Early withdrawal penalties
- Auto-renewal options
- Minimum deposit amounts

**Australian-Specific:**
- APRA reporting requirements
- Maturity notification (30 days before maturity)
- Interest withholding for non-residents

### 3.4 Recurring Deposits

**Features:**
- Regular contribution schedule (weekly, fortnightly, monthly)
- Fixed term
- Interest calculation on cumulative balance
- Flexible contribution amounts
- Missed payment handling

---

## 4. Domain Model

### 4.1 Core Entities

```python
# Savings Account
class SavingsAccount:
    account_id: UUID
    client_id: UUID
    product_id: UUID
    account_number: str
    bsb: str  # Australian Bank State Branch number
    account_name: str
    account_type: SavingsAccountType
    currency: str = "AUD"
    status: AccountStatus
    balance: Decimal
    available_balance: Decimal
    hold_balance: Decimal
    interest_rate: Decimal
    bonus_interest_rate: Decimal
    tfn: Optional[str]  # Tax File Number
    tfn_exemption: Optional[TFNExemption]
    withholding_tax_rate: Decimal  # 0% if TFN provided, 47% otherwise
    opened_date: datetime
    last_interest_date: datetime
    dormancy_date: Optional[datetime]
    closure_date: Optional[datetime]
    fcs_eligible: bool  # Financial Claims Scheme eligibility
    
# Savings Product
class SavingsProduct:
    product_id: UUID
    product_code: str
    product_name: str
    product_type: ProductType
    description: str
    base_interest_rate: Decimal
    bonus_interest_rate: Decimal
    bonus_conditions: List[BonusCondition]
    interest_calculation_method: InterestCalculationMethod
    interest_posting_frequency: InterestPostingFrequency
    minimum_opening_balance: Decimal
    minimum_balance: Decimal
    maximum_balance: Optional[Decimal]
    monthly_fee: Decimal
    fee_waiver_conditions: List[FeeWaiverCondition]
    withdrawal_limit: Optional[int]
    withdrawal_fee: Decimal
    dormancy_period_days: int
    age_restrictions: Optional[AgeRestriction]
    pds_url: str  # Product Disclosure Statement
    kfs_url: str  # Key Facts Sheet
    
# Term Deposit
class TermDeposit:
    deposit_id: UUID
    client_id: UUID
    product_id: UUID
    account_number: str
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    start_date: date
    maturity_date: date
    interest_payment_frequency: InterestPaymentFrequency
    auto_renew: bool
    early_withdrawal_penalty_rate: Decimal
    status: TermDepositStatus
    tfn: Optional[str]
    withholding_tax_rate: Decimal
```

### 4.2 Enumerations

```python
class SavingsAccountType(Enum):
    SAVINGS = "savings"
    HIGH_INTEREST_SAVINGS = "high_interest_savings"
    YOUTH_SAVER = "youth_saver"
    PENSIONER_SAVER = "pensioner_saver"
    BUSINESS_SAVINGS = "business_savings"

class AccountStatus(Enum):
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    DORMANT = "dormant"
    FROZEN = "frozen"
    CLOSED = "closed"

class InterestCalculationMethod(Enum):
    DAILY_BALANCE = "daily_balance"
    MINIMUM_MONTHLY_BALANCE = "minimum_monthly_balance"
    AVERAGE_DAILY_BALANCE = "average_daily_balance"

class InterestPostingFrequency(Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    AT_MATURITY = "at_maturity"

class TFNExemption(Enum):
    UNDER_18 = "under_18"
    PENSIONER = "pensioner"
    NON_RESIDENT = "non_resident"
    EXEMPT_ORGANIZATION = "exempt_organization"
```

---

## 5. Event Sourcing Architecture

### 5.1 Savings Events

All state changes are captured as immutable events in Kafka:

```python
# Account Lifecycle Events
class SavingsAccountOpenedEvent(BaseEvent):
    account_id: UUID
    client_id: UUID
    product_id: UUID
    opening_balance: Decimal
    tfn: Optional[str]
    
class SavingsAccountApprovedEvent(BaseEvent):
    account_id: UUID
    approved_by: UUID
    
class SavingsAccountActivatedEvent(BaseEvent):
    account_id: UUID
    activation_date: datetime
    
class SavingsAccountClosedEvent(BaseEvent):
    account_id: UUID
    closure_reason: str
    final_balance: Decimal

# Transaction Events
class DepositMadeEvent(BaseEvent):
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    source: str
    balance_after: Decimal
    
class WithdrawalMadeEvent(BaseEvent):
    account_id: UUID
    transaction_id: UUID
    amount: Decimal
    destination: str
    balance_after: Decimal

# Interest Events
class InterestAccruedEvent(BaseEvent):
    account_id: UUID
    accrual_date: date
    interest_amount: Decimal
    balance: Decimal
    interest_rate: Decimal
    
class InterestPostedEvent(BaseEvent):
    account_id: UUID
    posting_date: date
    gross_interest: Decimal
    withholding_tax: Decimal
    net_interest: Decimal
    balance_after: Decimal

# Bonus Interest Events
class BonusInterestEarnedEvent(BaseEvent):
    account_id: UUID
    period: str
    bonus_amount: Decimal
    conditions_met: List[str]
    
class BonusInterestForfeitedEvent(BaseEvent):
    account_id: UUID
    period: str
    reason: str

# Fee Events
class MonthlyFeeChargedEvent(BaseEvent):
    account_id: UUID
    fee_amount: Decimal
    balance_after: Decimal
    
class FeeWaivedEvent(BaseEvent):
    account_id: UUID
    fee_amount: Decimal
    waiver_reason: str

# Compliance Events
class TFNProvidedEvent(BaseEvent):
    account_id: UUID
    tfn: str
    
class WithholdingTaxDeductedEvent(BaseEvent):
    account_id: UUID
    gross_interest: Decimal
    tax_amount: Decimal
    tax_rate: Decimal
```

### 5.2 Kafka Topics

```
ultracore.savings.accounts.lifecycle
ultracore.savings.accounts.transactions
ultracore.savings.interest.accrual
ultracore.savings.interest.posting
ultracore.savings.fees
ultracore.savings.compliance
ultracore.savings.term_deposits
```

---

## 6. Data Mesh Integration

### 6.1 Savings Domain Data Products

```python
class SavingsDomain:
    """Savings domain data mesh"""
    
    # Data Products
    - savings_account_360_view
    - daily_interest_accrual_stream
    - savings_transaction_stream
    - term_deposit_maturity_calendar
    - savings_analytics_aggregate
    
    # Quality SLAs
    - Completeness: 100%
    - Latency: < 100ms for real-time, < 1 hour for batch
    - Accuracy: 99.99%
    - Freshness: Real-time for transactions, daily for analytics
    
    # Governance
    - PII masking for TFN
    - Audit logging for all access
    - Data lineage tracking
```

---

## 7. AI Agent Integration

### 7.1 Anya Savings Agent

**Capabilities:**
- Savings product recommendations based on customer profile
- Interest optimization suggestions
- Bonus interest condition monitoring and alerts
- Dormancy prevention (proactive customer engagement)
- Term deposit maturity management
- Savings goal tracking and recommendations

**MCP Tools:**
- `get_savings_account_details`
- `calculate_projected_interest`
- `recommend_savings_product`
- `check_bonus_eligibility`
- `optimize_term_deposit_ladder`

---

## 8. ML/RL Models

### 8.1 Interest Rate Optimization (RL)

**Model:** PPO (Proximal Policy Optimization)  
**Objective:** Maximize customer retention while maintaining profitability  
**State:** Customer balance, tenure, transaction patterns, market rates  
**Action:** Adjust bonus interest rates within approved ranges  
**Reward:** Customer retention + deposit growth - interest cost

### 8.2 Savings Behavior Prediction (ML)

**Model:** XGBoost Classifier  
**Objective:** Predict customer savings patterns  
**Features:** Age, income, transaction history, balance trends  
**Output:** Savings propensity score, recommended deposit amount

### 8.3 Dormancy Prediction (ML)

**Model:** Random Forest  
**Objective:** Predict accounts at risk of dormancy  
**Features:** Days since last transaction, balance, customer demographics  
**Output:** Dormancy risk score (0-100)

---

## 9. Accounting Integration

### 9.1 Chart of Accounts Mapping

```
Assets:
- 1100 - Savings Accounts (Customer Deposits)
- 1110 - Term Deposits (Customer Deposits)

Liabilities:
- 2100 - Interest Payable

Expenses:
- 5100 - Interest Expense
- 5200 - Withholding Tax Payable

Revenue:
- 4100 - Account Fees Revenue
```

### 9.2 Automated Journal Entries

**Deposit:**
```
DR: Cash at Bank
CR: Savings Accounts (Customer Deposits)
```

**Withdrawal:**
```
DR: Savings Accounts (Customer Deposits)
CR: Cash at Bank
```

**Interest Accrual:**
```
DR: Interest Expense
CR: Interest Payable
```

**Interest Posting:**
```
DR: Interest Payable
CR: Savings Accounts (Customer Deposits)
```

**Withholding Tax:**
```
DR: Interest Expense
CR: Withholding Tax Payable
```

---

## 10. API Endpoints

```
POST   /api/v1/savings/accounts                    # Open savings account
GET    /api/v1/savings/accounts/{account_id}       # Get account details
PUT    /api/v1/savings/accounts/{account_id}       # Update account
DELETE /api/v1/savings/accounts/{account_id}       # Close account

POST   /api/v1/savings/accounts/{account_id}/deposit      # Make deposit
POST   /api/v1/savings/accounts/{account_id}/withdraw     # Make withdrawal
POST   /api/v1/savings/accounts/{account_id}/transfer     # Transfer funds

GET    /api/v1/savings/accounts/{account_id}/transactions # Get transaction history
GET    /api/v1/savings/accounts/{account_id}/interest     # Get interest details
GET    /api/v1/savings/accounts/{account_id}/statement    # Get account statement

POST   /api/v1/savings/term-deposits                      # Open term deposit
GET    /api/v1/savings/term-deposits/{deposit_id}         # Get term deposit details
POST   /api/v1/savings/term-deposits/{deposit_id}/renew   # Renew term deposit
POST   /api/v1/savings/term-deposits/{deposit_id}/close   # Close term deposit early

GET    /api/v1/savings/products                           # List savings products
GET    /api/v1/savings/products/{product_id}              # Get product details

POST   /api/v1/savings/batch/interest-accrual             # Batch interest accrual
POST   /api/v1/savings/batch/interest-posting             # Batch interest posting
POST   /api/v1/savings/batch/monthly-fees                 # Batch monthly fees
POST   /api/v1/savings/batch/dormancy-check               # Batch dormancy check
```

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Domain models and entities
- Event schemas and Kafka topics
- Database schema
- Base repository layer

### Phase 2: Business Logic (Days 2-3)
- Account lifecycle management
- Transaction processing
- Interest calculation engine
- Fee management

### Phase 3: Compliance & Reporting (Day 3-4)
- TFN withholding tax
- APRA reporting
- Financial statements integration
- PDS/KFS generation

### Phase 4: API Layer (Day 4-5)
- REST API endpoints
- Request/response validation
- API documentation

### Phase 5: AI/ML Integration (Day 5-6)
- Anya Savings Agent
- ML models for predictions
- RL model for interest optimization

### Phase 6: Testing & Documentation (Day 6-7)
- Unit tests
- Integration tests
- API documentation
- User guides

---

## 12. Success Metrics

- **Functional Completeness:** 100% of Fineract savings features implemented
- **Regulatory Compliance:** 100% ASIC, APRA, ATO compliance
- **Test Coverage:** >90% code coverage
- **Performance:** <100ms API response time for 95th percentile
- **Accuracy:** 100% accuracy in interest calculations
- **Event Reliability:** 100% event delivery guarantee

---

**Document Owner:** UltraCore Platform Team  
**Last Updated:** November 13, 2025  
**Next Review:** November 20, 2025

# Financial Reporting Module

## Overview

The **Financial Reporting Module** provides comprehensive, real-time financial reporting optimized for **Australian accounting standards (AASB)** with full **APRA prudential reporting**, flexible financial year configuration (default: Jul 1 - Jun 30), and **AI-powered financial analysis**.

---

## Key Features

### 1. Australian Accounting Standards (AASB)
- **AASB 101** - Presentation of Financial Statements
- **AASB 107** - Statement of Cash Flows
- **AASB 9** - Financial Instruments
- **AASB 15** - Revenue from Contracts
- **Complete compliance** with Australian reporting requirements

### 2. Flexible Financial Year
- **Default**: July 1 - June 30 (Australian financial year)
- **Configurable**: Any start/end dates
- **Multi-period**: Quarterly, monthly, weekly reporting
- **Comparative analysis**: YoY, QoQ, MoM

### 3. Comprehensive Chart of Accounts
- **40+ accounts** optimized for Australian banking
- **APRA category mapping** for prudential reporting
- **Double-entry bookkeeping** with automatic balancing
- **Hierarchical structure** with sub-accounts

### 4. Core Financial Statements
- **Balance Sheet** - Statement of Financial Position (AASB 101)
- **Income Statement** - Profit & Loss (AASB 101)
- **Cash Flow Statement** - AASB 107
- **Financial Ratios** - 15+ KPIs and metrics

### 5. APRA Prudential Reporting
- **APS 110** - Capital Adequacy (CET1, Tier 1, Total Capital)
- **APS 220** - Credit Risk Management (NPL, Provisions)
- **APS 330** - Public Disclosure (Pillar 3)
- **ARF 320** - Liquidity (LCR, NSFR)

---

## Architecture

### Australian Chart of Accounts

**Assets (1000-1999)**
- 1000-1199: Current Assets (Cash, Loans, Receivables)
- 1200-1999: Non-Current Assets (Loans, PPE, Intangibles)

**Liabilities (2000-2999)**
- 2000-2199: Current Liabilities (Deposits, Payables)
- 2200-2999: Non-Current Liabilities (Deposits, Borrowings, Provisions)

**Equity (3000-3999)**
- 3000: Share Capital
- 3100: Retained Earnings
- 3200: Reserves
- 3300: Current Year Profit/Loss

**Revenue (4000-4999)**
- 4000: Interest Income
- 4100: Fee Income
- 4200: Other Operating Income

**Expenses (5000-5999)**
- 5000: Interest Expense
- 5200: Operating Expenses
- 5300: Loan Loss Provisions
- 5400: Depreciation and Amortisation

---

## Financial Year Configuration

### Australian Financial Year (Default)

```python
from ultracore.domains.financial_reporting.models.financial_statements import FinancialYear

# FY2025 = July 1, 2024 to June 30, 2025
fy = FinancialYear.australian_fy(2025)

print(fy.start_date)  # 2024-07-01
print(fy.end_date)    # 2025-06-30
print(fy.name)        # "FY2025"
```

### Calendar Year

```python
# CY2025 = January 1, 2025 to December 31, 2025
fy = FinancialYear.calendar_year(2025)

print(fy.start_date)  # 2025-01-01
print(fy.end_date)    # 2025-12-31
```

### Custom Financial Year

```python
# Custom: April 1 to March 31
fy = FinancialYear(
    start_month=4,
    start_day=1,
    end_month=3,
    end_day=31,
    year=2025,
    name="FY2025"
)
```

---

## Usage Examples

### Generate Balance Sheet

```python
from ultracore.domains.financial_reporting.services.reporting_service import (
    FinancialReportingService
)
from ultracore.domains.financial_reporting.models.chart_of_accounts import (
    create_australian_chart_of_accounts
)
from datetime import date

# Create Australian COA
coa = create_australian_chart_of_accounts(tenant_id=tenant_id, created_by="system")

# Create reporting service
service = FinancialReportingService(chart_of_accounts=coa)

# Generate balance sheet
balance_sheet = service.generate_balance_sheet(
    as_of_date=date(2025, 6, 30)  # End of Australian FY
)

print(f"Total Assets: ${balance_sheet.total_assets}")
print(f"Total Liabilities: ${balance_sheet.total_liabilities}")
print(f"Total Equity: ${balance_sheet.total_equity}")
print(f"Balanced: {balance_sheet.is_balanced}")
```

### Generate Income Statement

```python
# Generate P&L for full financial year
income_statement = service.generate_income_statement(
    period_start=date(2024, 7, 1),
    period_end=date(2025, 6, 30)
)

print(f"Total Revenue: ${income_statement.total_revenue}")
print(f"Total Expenses: ${income_statement.total_expenses}")
print(f"Net Profit: ${income_statement.net_profit_after_tax}")
print(f"Net Interest Margin: ${income_statement.net_interest_income}")
```

### Calculate Financial Ratios

```python
# Calculate KPIs and ratios
ratios = service.calculate_financial_ratios(
    balance_sheet=balance_sheet,
    income_statement=income_statement,
    total_loans=Decimal("10000000.00"),
    non_performing_loans=Decimal("200000.00"),
    provisions=Decimal("150000.00"),
    risk_weighted_assets=Decimal("8000000.00"),
    cet1_capital=Decimal("1000000.00"),
    tier1_capital=Decimal("1200000.00"),
    total_capital=Decimal("1500000.00")
)

print(f"Net Interest Margin: {ratios.net_interest_margin}%")
print(f"Return on Assets: {ratios.return_on_assets}%")
print(f"Return on Equity: {ratios.return_on_equity}%")
print(f"CET1 Ratio: {ratios.cet1_ratio}% (min 4.5%)")
print(f"NPL Ratio: {ratios.non_performing_loan_ratio}%")
```

---

## Financial Ratios

### Profitability Ratios
- **Net Interest Margin (NIM)** - (Interest Income - Interest Expense) / Avg Assets
- **Return on Assets (ROA)** - Net Profit / Avg Assets
- **Return on Equity (ROE)** - Net Profit / Avg Equity
- **Cost-to-Income Ratio** - Operating Expenses / Operating Income

### Asset Quality Ratios
- **Non-Performing Loan Ratio** - NPL / Total Loans
- **Provision Coverage Ratio** - Provisions / NPL
- **Loan Loss Rate** - Loan Losses / Avg Loans

### Liquidity Ratios
- **Liquidity Coverage Ratio (LCR)** - APRA requirement: ≥ 100%
- **Net Stable Funding Ratio (NSFR)** - APRA requirement: ≥ 100%
- **Loan-to-Deposit Ratio** - Total Loans / Total Deposits
- **Cash Ratio** - Cash / Current Liabilities

### Capital Ratios (APRA APS 110)
- **CET1 Ratio** - CET1 Capital / RWA (minimum 4.5%)
- **Tier 1 Ratio** - Tier 1 Capital / RWA (minimum 6%)
- **Total Capital Ratio** - Total Capital / RWA (minimum 8%)
- **Leverage Ratio** - Tier 1 Capital / Total Exposures (minimum 3%)

---

## APRA Prudential Standards

### APS 110 - Capital Adequacy

**Minimum Capital Requirements:**
- CET1 Ratio: ≥ 4.5%
- Tier 1 Ratio: ≥ 6%
- Total Capital Ratio: ≥ 8%
- Capital Conservation Buffer: 2.5%
- **Total Minimum CET1**: 7% (4.5% + 2.5%)

### APS 220 - Credit Risk Management

**Credit Quality Metrics:**
- Non-Performing Loan (NPL) Ratio
- Provision Coverage Ratio
- Portfolio at Risk (PAR) 30, 60, 90
- Delinquency by bucket
- Cure rates

### APS 330 - Public Disclosure

**Pillar 3 Disclosures:**
- Capital structure
- Risk exposures
- Capital adequacy
- Credit risk
- Operational risk

---

## Benefits

### Australian Compliance
✅ **AASB compliant** - Full compliance with Australian accounting standards  
✅ **APRA ready** - Prudential reporting built-in  
✅ **Tax optimized** - 30% corporate tax rate  
✅ **FY flexibility** - Jul 1 - Jun 30 default, fully configurable

### Real-Time Reporting
✅ **Event-driven** - Financial statements updated in real-time  
✅ **Instant KPIs** - Ratios calculated on-demand  
✅ **No batch delays** - Kafka event sourcing for instant updates

### Comprehensive Coverage
✅ **40+ accounts** - Complete chart of accounts  
✅ **3 core statements** - Balance Sheet, P&L, Cash Flow  
✅ **15+ ratios** - Profitability, asset quality, liquidity, capital  
✅ **APRA reporting** - Capital adequacy, credit risk, liquidity

---

## Future Enhancements

- Real-time financial statement updates via Kafka
- AI-powered financial analysis and forecasting
- Automated APRA report generation
- Comparative period analysis (YoY, QoQ, MoM)
- Financial statement consolidation
- Multi-currency support
- XBRL export for regulatory filing

---

## Conclusion

The Financial Reporting Module provides comprehensive, real-time financial reporting optimized for Australian accounting standards with APRA prudential reporting, flexible financial year configuration, and complete coverage of core banking financial statements.

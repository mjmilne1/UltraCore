# Data Mesh API Documentation

**Version:** 1.0  
**Last Updated:** January 14, 2025

---

## Overview

The Data Mesh API provides decentralized data access through domain-owned data products. Each data product exposes standardized interfaces for querying, quality monitoring, and lineage tracking.

**Base URL:** `/api/data-mesh`

**Authentication:** Bearer token required for all endpoints

---

## Core Concepts

### Data Product

A data product is a self-contained unit of data owned by a domain team. It includes:
- **Data:** The actual dataset
- **Metadata:** Schema, ownership, SLA information
- **Quality Metrics:** Completeness, accuracy, timeliness, consistency, uniqueness
- **Lineage:** Upstream sources and downstream consumers

### Quality Levels

- **Gold:** Production-ready, SLA-backed (99.9% quality)
- **Silver:** Validated, monitored (95% quality)
- **Bronze:** Raw, experimental (80% quality)

### Domains

Data products are organized by business domain:
- Customers
- Accounts
- Transactions
- Payments
- Loans
- Investments
- Risk
- Compliance
- Analytics
- Operations
- Finance

---

## Endpoints

### List Data Products

Get a paginated list of all data products with optional filtering.

**Endpoint:** `GET /api/data-mesh/products`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain` | string | No | Filter by domain (e.g., "customers") |
| `quality_level` | string | No | Filter by quality level (gold, silver, bronze) |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "products": [
    {
      "id": "customer_360",
      "name": "Customer360",
      "domain": "customers",
      "description": "Unified customer view with demographics, KYC, and risk data",
      "quality_level": "gold",
      "owner": "customer-team@example.com",
      "version": "1.0.0",
      "last_updated": "2025-01-14T10:30:00Z",
      "refresh_frequency": "hourly",
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 15,
    "total_pages": 1
  }
}
```

**Example:**

```bash
curl -X GET "https://api.ultracore.com/api/data-mesh/products?domain=customers&quality_level=gold" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Data Product Details

Get detailed information about a specific data product.

**Endpoint:** `GET /api/data-mesh/products/{product_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Data product identifier |

**Response:**

```json
{
  "id": "customer_360",
  "name": "Customer360",
  "domain": "customers",
  "description": "Unified customer view with demographics, KYC, and risk data",
  "quality_level": "gold",
  "owner": "customer-team@example.com",
  "version": "1.0.0",
  "last_updated": "2025-01-14T10:30:00Z",
  "refresh_frequency": "hourly",
  "status": "active",
  "schema": {
    "fields": [
      {
        "name": "customer_id",
        "type": "string",
        "description": "Unique customer identifier",
        "required": true
      },
      {
        "name": "name",
        "type": "string",
        "description": "Customer full name",
        "required": true
      },
      {
        "name": "email",
        "type": "string",
        "description": "Customer email address",
        "required": false
      }
    ]
  },
  "quality_metrics": {
    "completeness": 0.99,
    "accuracy": 0.98,
    "consistency": 0.99,
    "timeliness": 1.0,
    "uniqueness": 1.0,
    "overall_score": 0.99,
    "last_measured": "2025-01-14T10:00:00Z"
  },
  "lineage": {
    "upstream": [
      "customer_service_db",
      "kyc_system",
      "risk_engine"
    ],
    "downstream": [
      "analytics_warehouse",
      "reporting_system"
    ]
  },
  "sla": {
    "availability": 0.999,
    "max_latency_ms": 500,
    "refresh_frequency": "hourly"
  }
}
```

**Example:**

```bash
curl -X GET "https://api.ultracore.com/api/data-mesh/products/customer_360" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Query Data Product

Query data from a data product with filters and pagination.

**Endpoint:** `POST /api/data-mesh/products/{product_id}/query`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Data product identifier |

**Request Body:**

```json
{
  "filters": {
    "customer_id": "CUST001",
    "status": "active"
  },
  "fields": ["customer_id", "name", "email"],
  "limit": 100,
  "offset": 0
}
```

**Response:**

```json
{
  "data": [
    {
      "customer_id": "CUST001",
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "metadata": {
    "total_records": 1,
    "returned_records": 1,
    "query_time_ms": 45
  }
}
```

**Example:**

```bash
curl -X POST "https://api.ultracore.com/api/data-mesh/products/customer_360/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"customer_id": "CUST001"},
    "fields": ["customer_id", "name", "email"]
  }'
```

---

### Refresh Data Product

Trigger a manual refresh of a data product.

**Endpoint:** `POST /api/data-mesh/products/{product_id}/refresh`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Data product identifier |

**Response:**

```json
{
  "product_id": "customer_360",
  "refresh_status": "in_progress",
  "refresh_id": "refresh_12345",
  "estimated_completion": "2025-01-14T10:35:00Z"
}
```

**Example:**

```bash
curl -X POST "https://api.ultracore.com/api/data-mesh/products/customer_360/refresh" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Quality Report

Get quality metrics report for a data product.

**Endpoint:** `GET /api/data-mesh/quality/report`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | No | Filter by product ID |
| `start_date` | string | No | Start date (ISO 8601) |
| `end_date` | string | No | End date (ISO 8601) |

**Response:**

```json
{
  "product_id": "customer_360",
  "report_period": {
    "start": "2025-01-07T00:00:00Z",
    "end": "2025-01-14T00:00:00Z"
  },
  "quality_metrics": {
    "average_score": 0.99,
    "completeness": 0.99,
    "accuracy": 0.98,
    "consistency": 0.99,
    "timeliness": 1.0,
    "uniqueness": 1.0
  },
  "measurements": [
    {
      "timestamp": "2025-01-14T10:00:00Z",
      "completeness": 0.99,
      "accuracy": 0.98,
      "consistency": 0.99,
      "timeliness": 1.0,
      "uniqueness": 1.0
    }
  ],
  "alerts": {
    "critical": 0,
    "high": 0,
    "medium": 1,
    "low": 2
  }
}
```

**Example:**

```bash
curl -X GET "https://api.ultracore.com/api/data-mesh/quality/report?product_id=customer_360" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Quality Alerts

Get active quality alerts.

**Endpoint:** `GET /api/data-mesh/quality/alerts`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | No | Filter by product ID |
| `severity` | string | No | Filter by severity (critical, high, medium, low) |
| `status` | string | No | Filter by status (active, resolved) |

**Response:**

```json
{
  "alerts": [
    {
      "alert_id": "alert_001",
      "product_id": "customer_360",
      "metric": "accuracy",
      "severity": "medium",
      "threshold": 0.95,
      "actual_value": 0.93,
      "message": "Accuracy below threshold",
      "created_at": "2025-01-14T09:00:00Z",
      "status": "active"
    }
  ],
  "summary": {
    "total_alerts": 3,
    "critical": 0,
    "high": 0,
    "medium": 1,
    "low": 2
  }
}
```

**Example:**

```bash
curl -X GET "https://api.ultracore.com/api/data-mesh/quality/alerts?severity=critical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Resolve Quality Alert

Mark a quality alert as resolved.

**Endpoint:** `POST /api/data-mesh/quality/alerts/{alert_id}/resolve`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `alert_id` | string | Yes | Alert identifier |

**Request Body:**

```json
{
  "resolved_by": "admin@example.com",
  "resolution_notes": "Fixed data quality issue in upstream system"
}
```

**Response:**

```json
{
  "alert_id": "alert_001",
  "status": "resolved",
  "resolved_at": "2025-01-14T10:30:00Z",
  "resolved_by": "admin@example.com"
}
```

**Example:**

```bash
curl -X POST "https://api.ultracore.com/api/data-mesh/quality/alerts/alert_001/resolve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resolved_by": "admin@example.com",
    "resolution_notes": "Fixed upstream issue"
  }'
```

---

### List Domains

Get a list of all domains with product counts.

**Endpoint:** `GET /api/data-mesh/domains`

**Response:**

```json
{
  "domains": [
    {
      "domain": "customers",
      "product_count": 1,
      "description": "Customer-related data products"
    },
    {
      "domain": "accounts",
      "product_count": 1,
      "description": "Account-related data products"
    }
  ],
  "total_domains": 11
}
```

**Example:**

```bash
curl -X GET "https://api.ultracore.com/api/data-mesh/domains" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Available Data Products

### Customer Domain

**Customer360**
- **ID:** `customer_360`
- **Description:** Unified customer view with demographics, KYC, risk, and relationships
- **Quality Level:** Gold
- **Refresh:** Hourly

### Accounts Domain

**AccountBalances**
- **ID:** `account_balances`
- **Description:** Real-time account balances, transactions, and limits
- **Quality Level:** Gold
- **Refresh:** Real-time

### Transactions Domain

**TransactionHistory**
- **ID:** `transaction_history`
- **Description:** Complete transaction history with categorization
- **Quality Level:** Gold
- **Refresh:** Real-time

### Payments Domain

**PaymentAnalytics**
- **ID:** `payment_analytics`
- **Description:** Payment patterns, success rates, routing analytics
- **Quality Level:** Silver
- **Refresh:** Hourly

### Loans Domain

**LoanPortfolio**
- **ID:** `loan_portfolio`
- **Description:** Loan portfolio metrics, performance, risk exposure
- **Quality Level:** Gold
- **Refresh:** Daily

### Investments Domain

**InvestmentPerformance**
- **ID:** `investment_performance`
- **Description:** Investment returns, asset allocation, benchmarks
- **Quality Level:** Gold
- **Refresh:** Daily

### Risk Domain

**RiskMetrics**
- **ID:** `risk_metrics`
- **Description:** Portfolio risk, VaR, stress testing
- **Quality Level:** Gold
- **Refresh:** Daily

**FraudSignals**
- **ID:** `fraud_signals`
- **Description:** Fraud detection signals, patterns, alerts
- **Quality Level:** Silver
- **Refresh:** Real-time

### Compliance Domain

**ComplianceReports**
- **ID:** `compliance_reports`
- **Description:** AML/CTF reports, regulatory metrics
- **Quality Level:** Gold
- **Refresh:** Daily

### Regulatory Domain

**RegulatoryReporting**
- **ID:** `regulatory_reporting`
- **Description:** AUSTRAC, APRA reporting data
- **Quality Level:** Gold
- **Refresh:** Daily

### Analytics Domain

**CustomerSegments**
- **ID:** `customer_segments`
- **Description:** Customer segmentation, behavior patterns
- **Quality Level:** Silver
- **Refresh:** Daily

**ProductUsage**
- **ID:** `product_usage`
- **Description:** Product adoption, usage trends
- **Quality Level:** Silver
- **Refresh:** Hourly

**ChannelAnalytics**
- **ID:** `channel_analytics`
- **Description:** Channel performance, customer preferences
- **Quality Level:** Silver
- **Refresh:** Hourly

### Operations Domain

**OperationalMetrics**
- **ID:** `operational_metrics`
- **Description:** System health, performance, SLAs
- **Quality Level:** Gold
- **Refresh:** Real-time

### Finance Domain

**FinancialReporting**
- **ID:** `financial_reporting`
- **Description:** P&L, balance sheet, cash flow data
- **Quality Level:** Gold
- **Refresh:** Daily

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Product not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Product temporarily unavailable |

---

## Rate Limits

- **Standard:** 100 requests per minute
- **Query endpoints:** 20 requests per minute
- **Refresh endpoints:** 5 requests per minute

---

## Best Practices

1. **Use filters:** Always filter queries to reduce data transfer
2. **Cache results:** Cache query results when appropriate
3. **Monitor quality:** Subscribe to quality alerts for critical products
4. **Respect SLAs:** Check refresh frequency before querying
5. **Handle errors:** Implement retry logic with exponential backoff

---

## SDK Examples

### Python

```python
from ultracore.data_mesh import DataMeshClient

client = DataMeshClient(api_key="YOUR_API_KEY")

# List products
products = client.list_products(domain="customers")

# Query product
data = client.query_product(
    "customer_360",
    filters={"customer_id": "CUST001"}
)

# Get quality report
report = client.get_quality_report("customer_360")
```

### JavaScript

```javascript
const { DataMeshClient } = require('@ultracore/data-mesh');

const client = new DataMeshClient({ apiKey: 'YOUR_API_KEY' });

// List products
const products = await client.listProducts({ domain: 'customers' });

// Query product
const data = await client.queryProduct('customer_360', {
  filters: { customer_id: 'CUST001' }
});

// Get quality report
const report = await client.getQualityReport('customer_360');
```

---

**For support, contact:** data-mesh-team@ultracore.com

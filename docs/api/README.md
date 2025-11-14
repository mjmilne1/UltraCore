# 🌐 API Documentation

Comprehensive API documentation for UltraCore Banking Platform.

---

## 📚 Documentation Index

| Document | Description | Time to Read |
|----------|-------------|--------------|
| **[REST API](rest-api.md)** | Complete REST API reference with endpoints, authentication, error handling | 30 min |
| **[Swagger UI](swagger-ui.md)** | Interactive API documentation and testing guide | 15 min |
| **[MCP Tools](mcp-tools.md)** | Agentic AI integration with Model Context Protocol | 25 min |
| **[Code Examples](examples.md)** | Integration examples in Python, JavaScript, cURL | 20 min |

---

## 🚀 Quick Start

### 1. Access Interactive Documentation

**Swagger UI (Recommended):**
```
http://localhost:8000/api/v1/docs
```

**ReDoc (Alternative):**
```
http://localhost:8000/api/v1/redoc
```

### 2. Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

### 3. Make Your First API Call

```bash
# Get account balance
curl -X GET "http://localhost:8000/api/v1/accounts/acc-123/balance" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🎯 API Overview

### REST API

Traditional REST API with JSON request/response.

**Base URL:** `http://localhost:8000/api/v1`

**Features:**
- ✅ RESTful endpoints
- ✅ JWT authentication
- ✅ OpenAPI 3.0 specification
- ✅ Automatic Swagger UI
- ✅ Rate limiting
- ✅ Pagination
- ✅ Filtering

**Endpoints:**
- `/customers` - Customer management
- `/accounts` - Account management
- `/transactions` - Transaction processing
- `/payments` - Payment processing
- `/loans` - Loan management

**[Read Full Documentation →](rest-api.md)**

---

### MCP Tools

Agentic AI integration using Model Context Protocol.

**MCP Server:** `http://localhost:8000/mcp`

**Features:**
- ✅ Dynamic tool discovery
- ✅ AI-native interface
- ✅ Context-aware operations
- ✅ Self-describing tools
- ✅ Claude integration
- ✅ GPT integration

**Tools:**
- `get_customer_360` - Complete customer profile
- `check_loan_eligibility` - Loan eligibility check
- `get_account_balance` - Account balance
- `analyze_credit_risk` - ML-powered credit risk
- `create_investment_pod` - AI-managed investments
- `optimize_portfolio` - Portfolio optimization

**[Read Full Documentation →](mcp-tools.md)**

---

## 📖 Documentation by Use Case

### For Developers

**Getting Started:**
1. **[REST API Documentation](rest-api.md)** - Learn the basics
2. **[Swagger UI Guide](swagger-ui.md)** - Try APIs interactively
3. **[Code Examples](examples.md)** - Copy-paste integration code

**Common Tasks:**
- [Create a customer](examples.md#create-customer)
- [Create an account](examples.md#create-account)
- [Make a transaction](examples.md#make-transaction)
- [Check account balance](examples.md#get-account-balance)

---

### For AI Engineers

**Getting Started:**
1. **[MCP Tools Documentation](mcp-tools.md)** - Learn MCP integration
2. **[Code Examples](examples.md#python-claude-api)** - Claude integration
3. **[Available Tools](mcp-tools.md#available-tools)** - Tool reference

**Common Tasks:**
- [Get customer 360 view](mcp-tools.md#get_customer_360)
- [Check loan eligibility](mcp-tools.md#check_loan_eligibility)
- [Analyze credit risk](mcp-tools.md#analyze_credit_risk)
- [Create investment pod](mcp-tools.md#create_investment_pod)

---

### For API Consumers

**Getting Started:**
1. **[Swagger UI](http://localhost:8000/api/v1/docs)** - Interactive API explorer
2. **[OpenAPI Spec](http://localhost:8000/api/v1/openapi.json)** - Download specification
3. **[Code Examples](examples.md)** - Integration examples

**Common Tasks:**
- [Authentication](rest-api.md#authentication)
- [Error handling](rest-api.md#error-handling)
- [Rate limiting](rest-api.md#rate-limiting)
- [Pagination](rest-api.md#pagination)

---

## 🔐 Authentication

UltraCore uses **JWT (JSON Web Tokens)** for authentication.

### Get Access Token

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]
```

### Use Token in Requests

```python
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/v1/accounts",
    headers=headers
)
```

**[Full Authentication Guide →](rest-api.md#authentication)**

---

## 📋 API Endpoints

### Core Banking

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Customers** | `/customers` | Customer management (CRUD) |
| **Accounts** | `/accounts` | Account management (CRUD) |
| **Transactions** | `/transactions` | Transaction processing |
| **Payments** | `/payments` | Payment processing |
| **Loans** | `/loans` | Loan management |

### Wealth Management

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Investment Pods** | `/investment-pods` | AI-managed investment pods |
| **Portfolio** | `/portfolio` | Portfolio management |
| **Trading** | `/trading` | Stock/ETF trading |

### Multi-Currency

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Forex** | `/forex` | Foreign exchange rates |
| **Multi-Currency** | `/multi-currency` | Multi-currency accounts |

**[Full Endpoint Reference →](rest-api.md#endpoints)**

---

## 💻 Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Create customer
customer = requests.post(
    "http://localhost:8000/api/v1/customers",
    json={
        "tenant_id": "tenant-123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com"
    },
    headers={"Authorization": f"Bearer {token}"}
).json()

print(f"Customer created: {customer['id']}")
```

### JavaScript

```javascript
const axios = require('axios');

// Login
const loginResponse = await axios.post(
  'http://localhost:8000/api/v1/auth/login',
  { email: 'user@example.com', password: 'password' }
);
const token = loginResponse.data.access_token;

// Create customer
const customer = await axios.post(
  'http://localhost:8000/api/v1/customers',
  {
    tenant_id: 'tenant-123',
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@example.com'
  },
  { headers: { Authorization: `Bearer ${token}` } }
);

console.log(`Customer created: ${customer.data.id}`);
```

**[More Examples →](examples.md)**

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Account has insufficient funds for this transaction",
    "details": {
      "account_id": "acc-123",
      "available_balance": 100.00,
      "requested_amount": 150.00
    },
    "timestamp": "2024-11-14T10:30:00Z",
    "request_id": "req-abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

**[Full Error Reference →](rest-api.md#error-handling)**

---

## 🚦 Rate Limiting

| Tier | Requests/Min | Requests/Hour |
|------|--------------|---------------|
| **Free** | 60 | 1,000 |
| **Pro** | 600 | 10,000 |
| **Enterprise** | Unlimited | Unlimited |

**[Rate Limiting Guide →](rest-api.md#rate-limiting)**

---

## 📚 Additional Resources

### Documentation
- **[Getting Started Guide](../getting-started/quick-start.md)** - New to UltraCore?
- **[Architecture Documentation](../architecture/README.md)** - System design
- **[Module Documentation](../modules/README.md)** - Module reference

### Tools
- **[Swagger UI](http://localhost:8000/api/v1/docs)** - Interactive API explorer
- **[ReDoc](http://localhost:8000/api/v1/redoc)** - Alternative documentation
- **[OpenAPI Spec](http://localhost:8000/api/v1/openapi.json)** - Download specification

### Support
- **[Troubleshooting Guide](../getting-started/troubleshooting.md)** - Common issues
- **[GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)** - Ask questions
- **Email:** michael@turingdynamics.ai

---

## 🎯 Next Steps

1. **[Try Swagger UI](http://localhost:8000/api/v1/docs)** - Explore APIs interactively
2. **[Read REST API Docs](rest-api.md)** - Learn the API
3. **[Copy Code Examples](examples.md)** - Start integrating
4. **[Explore MCP Tools](mcp-tools.md)** - Build AI agents

---

**Happy building!** 🚀

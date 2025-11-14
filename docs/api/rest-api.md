# 🌐 REST API Documentation

UltraCore provides a comprehensive REST API built with FastAPI, offering automatic OpenAPI 3.0 specification, interactive documentation, and type-safe endpoints.

---

## 📚 Quick Links

- **[Swagger UI](#swagger-ui)** - Interactive API explorer
- **[Authentication](#authentication)** - API authentication guide
- **[Endpoints](#endpoints)** - Complete endpoint reference
- **[Code Examples](#code-examples)** - Integration examples
- **[Error Handling](#error-handling)** - Error codes and responses
- **[Rate Limiting](#rate-limiting)** - API limits and quotas

---

## 🚀 Getting Started

### Base URL

```
http://localhost:8000/api/v1
```

**Production:** `https://ultracore.turingdynamics.ai/api/v1`

### Quick Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-11-14T10:30:00Z"
}
```

---

## 📖 Swagger UI

UltraCore provides interactive API documentation via Swagger UI.

### Access Swagger UI

```
http://localhost:8000/api/v1/docs
```

**Features:**
- ✅ Interactive API explorer
- ✅ Try endpoints directly in browser
- ✅ Auto-generated from code
- ✅ Request/response examples
- ✅ Schema validation

### ReDoc Alternative

For a cleaner, read-only documentation experience:

```
http://localhost:8000/api/v1/redoc
```

### Download OpenAPI Spec

```bash
# JSON format
curl http://localhost:8000/api/v1/openapi.json > openapi.json

# Or visit in browser
http://localhost:8000/api/v1/openapi.json
```

---

## 🔐 Authentication

UltraCore uses **JWT (JSON Web Tokens)** for API authentication.

### Get Access Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Use Token in Requests

```bash
curl -X GET http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Token Expiration

- **Access tokens** expire after 1 hour
- **Refresh tokens** expire after 30 days
- Use `/api/v1/auth/refresh` to get a new access token

---

## 📋 Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/` | API root information |

### Customers

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/customers` | Create new customer | ✅ |
| GET | `/customers` | List all customers | ✅ |
| GET | `/customers/{id}` | Get customer by ID | ✅ |
| PUT | `/customers/{id}` | Update customer | ✅ |
| DELETE | `/customers/{id}` | Delete customer | ✅ |
| GET | `/customers/{id}/accounts` | Get customer accounts | ✅ |

### Accounts

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/accounts` | Create new account | ✅ |
| GET | `/accounts` | List all accounts | ✅ |
| GET | `/accounts/{id}` | Get account by ID | ✅ |
| PUT | `/accounts/{id}` | Update account | ✅ |
| DELETE | `/accounts/{id}` | Close account | ✅ |
| GET | `/accounts/{id}/balance` | Get account balance | ✅ |
| GET | `/accounts/{id}/transactions` | Get account transactions | ✅ |

### Transactions

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/transactions` | Create transaction | ✅ |
| GET | `/transactions` | List transactions | ✅ |
| GET | `/transactions/{id}` | Get transaction by ID | ✅ |
| POST | `/transactions/{id}/reverse` | Reverse transaction | ✅ |

### Payments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/payments` | Initiate payment | ✅ |
| GET | `/payments` | List payments | ✅ |
| GET | `/payments/{id}` | Get payment by ID | ✅ |
| POST | `/payments/{id}/cancel` | Cancel payment | ✅ |
| GET | `/payments/{id}/status` | Get payment status | ✅ |

### Loans

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/loans` | Create loan application | ✅ |
| GET | `/loans` | List loans | ✅ |
| GET | `/loans/{id}` | Get loan by ID | ✅ |
| POST | `/loans/{id}/approve` | Approve loan | ✅ Admin |
| POST | `/loans/{id}/disburse` | Disburse loan | ✅ Admin |
| POST | `/loans/{id}/repay` | Make loan repayment | ✅ |

---

## 💻 Code Examples

### Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# 2. Create headers
headers = {"Authorization": f"Bearer {token}"}

# 3. Create customer
customer_data = {
    "tenant_id": "tenant-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+61412345678",
    "date_of_birth": "1990-01-15"
}
response = requests.post(
    f"{BASE_URL}/customers",
    json=customer_data,
    headers=headers
)
customer = response.json()
print(f"Customer created: {customer['id']}")

# 4. Create account
account_data = {
    "customer_id": customer["id"],
    "account_type": "savings",
    "currency": "AUD",
    "initial_balance": 1000.00
}
response = requests.post(
    f"{BASE_URL}/accounts",
    json=account_data,
    headers=headers
)
account = response.json()
print(f"Account created: {account['account_number']}")

# 5. Get account balance
response = requests.get(
    f"{BASE_URL}/accounts/{account['id']}/balance",
    headers=headers
)
balance = response.json()
print(f"Balance: ${balance['available_balance']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';

async function main() {
  // 1. Login
  const loginResponse = await axios.post(`${BASE_URL}/auth/login`, {
    email: 'user@example.com',
    password: 'password'
  });
  const token = loginResponse.data.access_token;

  // 2. Create headers
  const headers = { Authorization: `Bearer ${token}` };

  // 3. Create customer
  const customerData = {
    tenant_id: 'tenant-123',
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@example.com',
    phone: '+61412345678',
    date_of_birth: '1990-01-15'
  };
  const customerResponse = await axios.post(
    `${BASE_URL}/customers`,
    customerData,
    { headers }
  );
  const customer = customerResponse.data;
  console.log(`Customer created: ${customer.id}`);

  // 4. Create account
  const accountData = {
    customer_id: customer.id,
    account_type: 'savings',
    currency: 'AUD',
    initial_balance: 1000.00
  };
  const accountResponse = await axios.post(
    `${BASE_URL}/accounts`,
    accountData,
    { headers }
  );
  const account = accountResponse.data;
  console.log(`Account created: ${account.account_number}`);

  // 5. Get account balance
  const balanceResponse = await axios.get(
    `${BASE_URL}/accounts/${account.id}/balance`,
    { headers }
  );
  const balance = balanceResponse.data;
  console.log(`Balance: $${balance.available_balance}`);
}

main().catch(console.error);
```

### cURL

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# 2. Create customer
CUSTOMER_ID=$(curl -s -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+61412345678",
    "date_of_birth": "1990-01-15"
  }' \
  | jq -r '.id')

echo "Customer created: $CUSTOMER_ID"

# 3. Create account
ACCOUNT_ID=$(curl -s -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"$CUSTOMER_ID\",
    \"account_type\": \"savings\",
    \"currency\": \"AUD\",
    \"initial_balance\": 1000.00
  }" \
  | jq -r '.id')

echo "Account created: $ACCOUNT_ID"

# 4. Get account balance
curl -X GET "http://localhost:8000/api/v1/accounts/$ACCOUNT_ID/balance" \
  -H "Authorization: Bearer $TOKEN"
```

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
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `INVALID_CREDENTIALS` | Invalid email or password | Check credentials |
| `TOKEN_EXPIRED` | Access token expired | Refresh token |
| `INSUFFICIENT_FUNDS` | Account has insufficient funds | Add funds or reduce amount |
| `ACCOUNT_CLOSED` | Account is closed | Use active account |
| `DUPLICATE_ACCOUNT` | Account already exists | Use existing account |
| `INVALID_CURRENCY` | Unsupported currency | Use supported currency (AUD, USD, EUR, GBP) |
| `TRANSACTION_FAILED` | Transaction processing failed | Retry or contact support |

---

## 🚦 Rate Limiting

### Limits

| Tier | Requests per Minute | Requests per Hour |
|------|---------------------|-------------------|
| **Free** | 60 | 1,000 |
| **Pro** | 600 | 10,000 |
| **Enterprise** | Unlimited | Unlimited |

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699964400
```

### Handling Rate Limits

```python
import requests
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limit exceeded
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = reset_time - int(time.time())
            print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
            time.sleep(wait_time + 1)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## 🔍 Pagination

### Query Parameters

```
GET /api/v1/accounts?page=1&page_size=20&sort=created_at&order=desc
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `sort` | string | `created_at` | Sort field |
| `order` | string | `desc` | Sort order (`asc` or `desc`) |

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🔍 Filtering

### Query Parameters

```
GET /api/v1/accounts?account_type=savings&currency=AUD&status=active
```

### Supported Filters

| Endpoint | Filters |
|----------|---------|
| `/accounts` | `account_type`, `currency`, `status`, `customer_id` |
| `/transactions` | `account_id`, `transaction_type`, `status`, `date_from`, `date_to` |
| `/payments` | `account_id`, `payment_method`, `status`, `date_from`, `date_to` |
| `/loans` | `customer_id`, `loan_type`, `status` |

---

## 📚 Additional Resources

- **[OpenAPI Specification](openapi.json)** - Download full API spec
- **[Swagger UI](http://localhost:8000/api/v1/docs)** - Interactive API explorer
- **[ReDoc](http://localhost:8000/api/v1/redoc)** - Alternative documentation
- **[Code Examples](examples.md)** - More integration examples
- **[MCP Tools](mcp-tools.md)** - Agentic AI integration
- **[WebSocket API](websocket-api.md)** - Real-time updates

---

## 🆘 Need Help?

- **[Troubleshooting Guide](../getting-started/troubleshooting.md)** - Common API issues
- **[GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)** - Ask questions
- **Email:** michael@turingdynamics.ai

---

**Happy coding!** 🚀

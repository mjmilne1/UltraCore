# 💻 API Code Examples

Comprehensive code examples for integrating with UltraCore API.

---

## 📚 Quick Links

- **[Python Examples](#python-examples)** - Python SDK examples
- **[JavaScript Examples](#javascript-examples)** - Node.js examples
- **[cURL Examples](#curl-examples)** - Command-line examples
- **[Common Workflows](#common-workflows)** - End-to-end scenarios

---

## 🐍 Python Examples

### Installation

```bash
pip install requests
```

### Basic Setup

```python
import requests
from typing import Dict, Any

class UltraCoreClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
    
    def login(self, email: str, password: str) -> str:
        """Authenticate and get access token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token
    
    def _headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def get(self, endpoint: str) -> Any:
        """GET request"""
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict) -> Any:
        """POST request"""
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
```

### Create Customer

```python
# Initialize client
client = UltraCoreClient()
client.login("user@example.com", "password")

# Create customer
customer = client.post("/customers", {
    "tenant_id": "tenant-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+61412345678",
    "date_of_birth": "1990-01-15",
    "address": {
        "street": "123 Main St",
        "city": "Sydney",
        "state": "NSW",
        "postcode": "2000",
        "country": "AU"
    }
})

print(f"Customer created: {customer['id']}")
```

### Create Account

```python
# Create savings account
account = client.post("/accounts", {
    "customer_id": customer["id"],
    "account_type": "savings",
    "currency": "AUD",
    "initial_balance": 1000.00
})

print(f"Account created: {account['account_number']}")
print(f"Balance: ${account['balance']}")
```

### Make Transaction

```python
# Transfer money
transaction = client.post("/transactions", {
    "from_account_id": account["id"],
    "to_account_id": "acc-789",
    "amount": 100.00,
    "currency": "AUD",
    "description": "Payment for services"
})

print(f"Transaction ID: {transaction['id']}")
print(f"Status: {transaction['status']}")
```

### Get Account Balance

```python
# Get balance
balance = client.get(f"/accounts/{account['id']}/balance")

print(f"Available: ${balance['available_balance']}")
print(f"Current: ${balance['current_balance']}")
print(f"Pending: ${balance['pending_balance']}")
```

### List Transactions

```python
# Get transactions
transactions = client.get(
    f"/accounts/{account['id']}/transactions?page=1&page_size=10"
)

for txn in transactions["data"]:
    print(f"{txn['date']}: ${txn['amount']} - {txn['description']}")
```

---

## 🟨 JavaScript Examples

### Installation

```bash
npm install axios
```

### Basic Setup

```javascript
const axios = require('axios');

class UltraCoreClient {
  constructor(baseURL = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
    this.token = null;
  }

  async login(email, password) {
    const response = await axios.post(`${this.baseURL}/auth/login`, {
      email,
      password
    });
    this.token = response.data.access_token;
    return this.token;
  }

  _headers() {
    return {
      Authorization: `Bearer ${this.token}`
    };
  }

  async get(endpoint) {
    const response = await axios.get(`${this.baseURL}${endpoint}`, {
      headers: this._headers()
    });
    return response.data;
  }

  async post(endpoint, data) {
    const response = await axios.post(`${this.baseURL}${endpoint}`, data, {
      headers: this._headers()
    });
    return response.data;
  }
}

module.exports = UltraCoreClient;
```

### Create Customer

```javascript
const UltraCoreClient = require('./UltraCoreClient');

async function main() {
  // Initialize client
  const client = new UltraCoreClient();
  await client.login('user@example.com', 'password');

  // Create customer
  const customer = await client.post('/customers', {
    tenant_id: 'tenant-123',
    first_name: 'John',
    last_name: 'Doe',
    email: 'john.doe@example.com',
    phone: '+61412345678',
    date_of_birth: '1990-01-15',
    address: {
      street: '123 Main St',
      city: 'Sydney',
      state: 'NSW',
      postcode: '2000',
      country: 'AU'
    }
  });

  console.log(`Customer created: ${customer.id}`);
}

main().catch(console.error);
```

### Create Account

```javascript
// Create savings account
const account = await client.post('/accounts', {
  customer_id: customer.id,
  account_type: 'savings',
  currency: 'AUD',
  initial_balance: 1000.00
});

console.log(`Account created: ${account.account_number}`);
console.log(`Balance: $${account.balance}`);
```

### Make Transaction

```javascript
// Transfer money
const transaction = await client.post('/transactions', {
  from_account_id: account.id,
  to_account_id: 'acc-789',
  amount: 100.00,
  currency: 'AUD',
  description: 'Payment for services'
});

console.log(`Transaction ID: ${transaction.id}`);
console.log(`Status: ${transaction.status}`);
```

---

## 🔧 cURL Examples

### Login

```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Create Customer

```bash
# Create customer
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

echo "Customer ID: $CUSTOMER_ID"
```

### Create Account

```bash
# Create account
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

echo "Account ID: $ACCOUNT_ID"
```

### Get Balance

```bash
# Get balance
curl -X GET "http://localhost:8000/api/v1/accounts/$ACCOUNT_ID/balance" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

## 🔄 Common Workflows

### Workflow 1: Customer Onboarding

Complete customer onboarding flow.

```python
def onboard_customer(client, customer_data):
    """Complete customer onboarding"""
    
    # 1. Create customer
    customer = client.post("/customers", customer_data)
    print(f"✓ Customer created: {customer['id']}")
    
    # 2. Create savings account
    savings = client.post("/accounts", {
        "customer_id": customer["id"],
        "account_type": "savings",
        "currency": "AUD",
        "initial_balance": 1000.00
    })
    print(f"✓ Savings account: {savings['account_number']}")
    
    # 3. Create checking account
    checking = client.post("/accounts", {
        "customer_id": customer["id"],
        "account_type": "checking",
        "currency": "AUD",
        "initial_balance": 500.00
    })
    print(f"✓ Checking account: {checking['account_number']}")
    
    # 4. Get customer 360 view
    customer_360 = client.get(f"/customers/{customer['id']}")
    print(f"✓ Customer has {len(customer_360['accounts'])} accounts")
    
    return customer_360

# Usage
client = UltraCoreClient()
client.login("user@example.com", "password")

customer_360 = onboard_customer(client, {
    "tenant_id": "tenant-123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+61412345678",
    "date_of_birth": "1990-01-15"
})
```

### Workflow 2: Loan Application

Complete loan application process.

```python
def apply_for_loan(client, customer_id, loan_amount):
    """Apply for a loan"""
    
    # 1. Check eligibility
    eligibility = client.post("/loans/check-eligibility", {
        "customer_id": customer_id,
        "loan_amount": loan_amount
    })
    
    if not eligibility["eligible"]:
        print("✗ Not eligible for loan")
        print(f"Reasons: {', '.join(eligibility['reasons'])}")
        return None
    
    print(f"✓ Eligible for ${eligibility['max_loan_amount']}")
    print(f"Interest rate: {eligibility['interest_rate']}%")
    
    # 2. Create loan application
    loan = client.post("/loans", {
        "customer_id": customer_id,
        "loan_amount": loan_amount,
        "loan_type": "personal",
        "term_months": 60,
        "purpose": "Home renovation"
    })
    
    print(f"✓ Loan application created: {loan['id']}")
    print(f"Status: {loan['status']}")
    
    return loan

# Usage
loan = apply_for_loan(client, customer["id"], 30000.00)
```

### Workflow 3: Investment Pod Creation

Create and optimize an investment pod.

```python
def create_investment_pod(client, customer_id, goal_amount, target_date):
    """Create and optimize investment pod"""
    
    # 1. Create investment pod
    pod = client.post("/investment-pods", {
        "customer_id": customer_id,
        "goal_amount": goal_amount,
        "target_date": target_date,
        "risk_tolerance": "moderate"
    })
    
    print(f"✓ Investment pod created: {pod['id']}")
    print(f"Goal: ${pod['goal_amount']} by {pod['target_date']}")
    
    # 2. Optimize portfolio
    optimization = client.post(f"/investment-pods/{pod['id']}/optimize", {})
    
    print(f"✓ Portfolio optimized")
    print(f"Expected return: {optimization['expected_return']*100:.2f}%")
    print(f"Sharpe ratio: {optimization['sharpe_ratio']:.2f}")
    
    # 3. Fund the pod
    funding = client.post(f"/investment-pods/{pod['id']}/fund", {
        "account_id": "acc-123",
        "amount": 10000.00
    })
    
    print(f"✓ Pod funded with ${funding['amount']}")
    
    return pod

# Usage
pod = create_investment_pod(
    client,
    customer["id"],
    100000.00,
    "2034-11-14"
)
```

### Workflow 4: Multi-Currency Payment

Make a multi-currency payment.

```python
def make_international_payment(client, from_account_id, to_account_id, amount, from_currency, to_currency):
    """Make international payment with currency conversion"""
    
    # 1. Get exchange rate
    rate = client.get(f"/forex/rate?from={from_currency}&to={to_currency}")
    
    print(f"Exchange rate: 1 {from_currency} = {rate['rate']} {to_currency}")
    converted_amount = amount * rate["rate"]
    print(f"${amount} {from_currency} = ${converted_amount:.2f} {to_currency}")
    
    # 2. Create payment
    payment = client.post("/payments", {
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "payment_method": "wire_transfer"
    })
    
    print(f"✓ Payment created: {payment['id']}")
    print(f"Status: {payment['status']}")
    
    # 3. Track payment status
    import time
    while payment["status"] == "pending":
        time.sleep(2)
        payment = client.get(f"/payments/{payment['id']}")
        print(f"Status: {payment['status']}")
    
    print(f"✓ Payment {payment['status']}")
    
    return payment

# Usage
payment = make_international_payment(
    client,
    "acc-123",
    "acc-456",
    1000.00,
    "AUD",
    "USD"
)
```

---

## 🔐 Authentication Examples

### JWT Token Authentication

```python
import requests
import time

class UltraCoreAuthClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
    
    def login(self, email: str, password: str):
        """Login and store tokens"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.token_expires_at = time.time() + data.get("expires_in", 3600)
    
    def refresh(self):
        """Refresh access token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        response = requests.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 3600)
    
    def _ensure_valid_token(self):
        """Ensure token is valid, refresh if needed"""
        if time.time() >= self.token_expires_at - 60:  # Refresh 1 min before expiry
            self.refresh()
    
    def get(self, endpoint: str):
        """GET request with automatic token refresh"""
        self._ensure_valid_token()
        
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()
```

---

## ⚠️ Error Handling Examples

### Comprehensive Error Handling

```python
import requests
from typing import Optional

class UltraCoreError(Exception):
    """Base exception for UltraCore API errors"""
    pass

class AuthenticationError(UltraCoreError):
    """Authentication failed"""
    pass

class InsufficientFundsError(UltraCoreError):
    """Insufficient funds for transaction"""
    pass

class RateLimitError(UltraCoreError):
    """Rate limit exceeded"""
    pass

def make_request_with_retry(client, method, endpoint, data=None, max_retries=3):
    """Make API request with error handling and retry logic"""
    
    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_data = e.response.json().get("error", {})
            error_code = error_data.get("code")
            
            # Handle specific errors
            if status_code == 401:
                raise AuthenticationError("Authentication failed")
            
            elif status_code == 400 and error_code == "INSUFFICIENT_FUNDS":
                raise InsufficientFundsError(error_data.get("message"))
            
            elif status_code == 429:
                # Rate limit - wait and retry
                wait_time = int(e.response.headers.get("Retry-After", 60))
                print(f"Rate limit exceeded. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            elif status_code >= 500:
                # Server error - retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Server error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise UltraCoreError(f"Server error after {max_retries} attempts")
            
            else:
                # Other errors - don't retry
                raise UltraCoreError(error_data.get("message", "Unknown error"))
        
        except requests.exceptions.RequestException as e:
            # Network error - retry
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Network error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                raise UltraCoreError(f"Network error after {max_retries} attempts")
    
    raise UltraCoreError(f"Max retries ({max_retries}) exceeded")

# Usage
try:
    transaction = make_request_with_retry(
        client,
        "POST",
        "/transactions",
        {
            "from_account_id": "acc-123",
            "to_account_id": "acc-456",
            "amount": 100.00
        }
    )
    print(f"Transaction successful: {transaction['id']}")

except InsufficientFundsError as e:
    print(f"Error: {e}")
    # Handle insufficient funds

except AuthenticationError as e:
    print(f"Error: {e}")
    # Re-authenticate

except UltraCoreError as e:
    print(f"Error: {e}")
    # General error handling
```

---

## 📚 Additional Resources

- **[REST API Documentation](rest-api.md)** - Complete API reference
- **[Swagger UI](swagger-ui.md)** - Interactive API explorer
- **[MCP Tools](mcp-tools.md)** - Agentic AI integration
- **[Troubleshooting](../getting-started/troubleshooting.md)** - Common issues

---

## 🆘 Need Help?

- **[GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)** - Ask questions
- **Email:** michael@turingdynamics.ai

---

**Happy coding!** 🚀

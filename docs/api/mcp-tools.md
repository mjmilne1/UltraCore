# 🤖 MCP Tools Documentation

Model Context Protocol (MCP) integration for agentic AI in UltraCore.

---

## 📚 Quick Links

- **[What is MCP?](#what-is-mcp)** - Protocol overview
- **[Available Tools](#available-tools)** - Complete tool reference
- **[Authentication](#authentication)** - Security and permissions
- **[Code Examples](#code-examples)** - Integration examples
- **[Best Practices](#best-practices)** - Usage guidelines

---

## 🎯 What is MCP?

**Model Context Protocol (MCP)** is Anthropic's standard for AI agent communication with external systems. It enables AI agents to:

- ✅ **Access** banking data through standardized interface
- ✅ **Execute** operations with proper permissions
- ✅ **Maintain** context across conversations
- ✅ **Discover** available tools dynamically

### Why MCP?

| Traditional API | MCP |
|-----------------|-----|
| Fixed endpoints | Dynamic tool discovery |
| Manual integration | AI-native interface |
| No context | Context-aware |
| Documentation required | Self-describing |

---

## 🚀 Getting Started

### 1. Install MCP Client

```bash
pip install mcp
```

### 2. Connect to UltraCore MCP Server

```python
from mcp import Client

# Connect to UltraCore MCP server
client = Client("http://localhost:8000/mcp")

# List available tools
tools = client.list_tools()
print(f"Available tools: {len(tools)}")

# List available resources
resources = client.list_resources()
print(f"Available resources: {len(resources)}")
```

### 3. Call a Tool

```python
# Get customer 360 view
result = client.call_tool(
    "get_customer_360",
    {"client_id": "cust-123"}
)
print(result)
```

---

## 🛠️ Available Tools

### Customer Tools

#### `get_customer_360`

Get complete 360-degree customer profile.

**Parameters:**
- `client_id` (string, required) - Customer ID

**Returns:**
```json
{
  "customer": {
    "id": "cust-123",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+61412345678"
  },
  "accounts": [
    {
      "id": "acc-456",
      "type": "savings",
      "balance": 10000.00,
      "currency": "AUD"
    }
  ],
  "loans": [...],
  "transactions": [...],
  "credit_score": 750,
  "risk_profile": "low"
}
```

**Example:**
```python
profile = client.call_tool(
    "get_customer_360",
    {"client_id": "cust-123"}
)
```

---

#### `check_loan_eligibility`

Check if customer is eligible for a loan.

**Parameters:**
- `client_id` (string, required) - Customer ID
- `loan_amount` (number, required) - Requested loan amount

**Returns:**
```json
{
  "eligible": true,
  "max_loan_amount": 50000.00,
  "interest_rate": 5.5,
  "term_months": 60,
  "monthly_payment": 943.56,
  "reasons": [
    "Good credit score (750)",
    "Stable income",
    "Low debt-to-income ratio"
  ]
}
```

**Example:**
```python
eligibility = client.call_tool(
    "check_loan_eligibility",
    {
        "client_id": "cust-123",
        "loan_amount": 30000.00
    }
)
```

---

### Account Tools

#### `get_account_balance`

Get account balance and details.

**Parameters:**
- `account_id` (string, required) - Account ID

**Returns:**
```json
{
  "account_id": "acc-456",
  "account_number": "1234567890",
  "account_type": "savings",
  "currency": "AUD",
  "balance": {
    "available": 10000.00,
    "current": 10000.00,
    "pending": 0.00
  },
  "status": "active",
  "last_transaction": "2024-11-14T10:30:00Z"
}
```

**Example:**
```python
balance = client.call_tool(
    "get_account_balance",
    {"account_id": "acc-456"}
)
```

---

#### `create_account`

Create a new account for a customer.

**Parameters:**
- `customer_id` (string, required) - Customer ID
- `account_type` (string, required) - Account type (`savings`, `checking`, `investment`)
- `currency` (string, required) - Currency code (AUD, USD, EUR, GBP)
- `initial_balance` (number, optional) - Initial deposit amount

**Returns:**
```json
{
  "account_id": "acc-789",
  "account_number": "9876543210",
  "account_type": "savings",
  "currency": "AUD",
  "balance": 1000.00,
  "status": "active",
  "created_at": "2024-11-14T10:30:00Z"
}
```

**Example:**
```python
account = client.call_tool(
    "create_account",
    {
        "customer_id": "cust-123",
        "account_type": "savings",
        "currency": "AUD",
        "initial_balance": 1000.00
    }
)
```

---

### Financial Tools

#### `get_trial_balance`

Get general ledger trial balance.

**Parameters:** None

**Returns:**
```json
{
  "trial_balance": [
    {
      "account_code": "1000",
      "account_name": "Cash",
      "debit": 100000.00,
      "credit": 0.00
    },
    {
      "account_code": "2000",
      "account_name": "Customer Deposits",
      "debit": 0.00,
      "credit": 100000.00
    }
  ],
  "total_debits": 500000.00,
  "total_credits": 500000.00,
  "balanced": true,
  "as_of": "2024-11-14T10:30:00Z"
}
```

**Example:**
```python
trial_balance = client.call_tool("get_trial_balance", {})
```

---

### ML/AI Tools

#### `analyze_credit_risk`

ML-powered credit risk analysis.

**Parameters:**
- `client_id` (string, required) - Customer ID

**Returns:**
```json
{
  "client_id": "cust-123",
  "credit_score": 750,
  "risk_category": "low",
  "probability_of_default": 0.02,
  "factors": {
    "positive": [
      "Stable income",
      "Low debt-to-income ratio",
      "Good payment history"
    ],
    "negative": [
      "Short credit history"
    ]
  },
  "recommendations": [
    "Eligible for prime rates",
    "Consider increasing credit limit"
  ]
}
```

**Example:**
```python
risk = client.call_tool(
    "analyze_credit_risk",
    {"client_id": "cust-123"}
)
```

---

#### `detect_fraud`

ML-powered fraud detection for transactions.

**Parameters:**
- `transaction_id` (string, required) - Transaction ID

**Returns:**
```json
{
  "transaction_id": "txn-789",
  "fraud_score": 0.15,
  "is_fraud": false,
  "risk_level": "low",
  "factors": {
    "suspicious": [
      "Unusual transaction time"
    ],
    "normal": [
      "Typical transaction amount",
      "Known merchant",
      "Expected location"
    ]
  },
  "recommended_action": "approve"
}
```

**Example:**
```python
fraud_check = client.call_tool(
    "detect_fraud",
    {"transaction_id": "txn-789"}
)
```

---

### Investment Tools

#### `create_investment_pod`

Create an AI-managed investment pod.

**Parameters:**
- `customer_id` (string, required) - Customer ID
- `goal_amount` (number, required) - Target amount
- `target_date` (string, required) - Target date (ISO 8601)
- `risk_tolerance` (string, required) - Risk tolerance (`conservative`, `moderate`, `aggressive`)

**Returns:**
```json
{
  "pod_id": "pod-123",
  "customer_id": "cust-123",
  "goal_amount": 100000.00,
  "target_date": "2034-11-14",
  "risk_tolerance": "moderate",
  "status": "created",
  "allocation": {
    "stocks": 0.60,
    "bonds": 0.30,
    "cash": 0.10
  },
  "created_at": "2024-11-14T10:30:00Z"
}
```

**Example:**
```python
pod = client.call_tool(
    "create_investment_pod",
    {
        "customer_id": "cust-123",
        "goal_amount": 100000.00,
        "target_date": "2034-11-14",
        "risk_tolerance": "moderate"
    }
)
```

---

#### `optimize_portfolio`

Optimize investment portfolio using UltraOptimiser.

**Parameters:**
- `pod_id` (string, required) - Investment Pod ID

**Returns:**
```json
{
  "pod_id": "pod-123",
  "current_allocation": {
    "VAS.AX": 0.30,
    "VGS.AX": 0.40,
    "VAF.AX": 0.30
  },
  "optimized_allocation": {
    "VAS.AX": 0.35,
    "VGS.AX": 0.45,
    "VAF.AX": 0.20
  },
  "expected_return": 0.0889,
  "expected_risk": 0.1234,
  "sharpe_ratio": 0.66,
  "rebalance_required": true
}
```

**Example:**
```python
optimization = client.call_tool(
    "optimize_portfolio",
    {"pod_id": "pod-123"}
)
```

---

## 📦 Available Resources

Resources are read-only data sources that AI agents can access.

### `ultracore://chart_of_accounts`

Banking chart of accounts.

**Type:** `financial_data`  
**Permissions:** Public

**Example:**
```python
chart = client.read_resource("ultracore://chart_of_accounts")
```

---

### `ultracore://compliance_rules`

Australian banking compliance rules.

**Type:** `regulatory_data`  
**Permissions:** Public

**Example:**
```python
rules = client.read_resource("ultracore://compliance_rules")
```

---

### `ultracore://customer_data`

Customer profiles and history.

**Type:** `customer_data`  
**Permissions:** Requires authentication

**Example:**
```python
customers = client.read_resource(
    "ultracore://customer_data",
    {"customer_id": "cust-123"}
)
```

---

## 🔐 Authentication

### API Key Authentication

```python
from mcp import Client

client = Client(
    "http://localhost:8000/mcp",
    api_key="your_api_key_here"
)
```

### JWT Token Authentication

```python
from mcp import Client

client = Client(
    "http://localhost:8000/mcp",
    token="your_jwt_token_here"
)
```

### Permissions

| Tool | Permission Required |
|------|---------------------|
| `get_customer_360` | `customer:read` |
| `check_loan_eligibility` | `loan:read` |
| `get_account_balance` | `account:read` |
| `create_account` | `account:write` |
| `get_trial_balance` | `financial:read` |
| `analyze_credit_risk` | `ml:read` |
| `detect_fraud` | `ml:read` |
| `create_investment_pod` | `investment:write` |
| `optimize_portfolio` | `investment:write` |

---

## 💻 Code Examples

### Python (Claude API)

```python
import anthropic
from mcp import Client

# Initialize MCP client
mcp_client = Client("http://localhost:8000/mcp", api_key="your_api_key")

# Initialize Claude
claude = anthropic.Anthropic(api_key="your_claude_api_key")

# Get available tools
tools = mcp_client.list_tools()

# Create message with tools
message = claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "What is the balance of account acc-456?"
        }
    ]
)

# Handle tool use
if message.stop_reason == "tool_use":
    tool_use = message.content[-1]
    
    # Call MCP tool
    result = mcp_client.call_tool(
        tool_use.name,
        tool_use.input
    )
    
    # Continue conversation with tool result
    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What is the balance of account acc-456?"},
            {"role": "assistant", "content": message.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(result)
                    }
                ]
            }
        ]
    )
    
    print(response.content[0].text)
```

### JavaScript (Node.js)

```javascript
const { Client } = require('@modelcontextprotocol/sdk');
const Anthropic = require('@anthropic-ai/sdk');

// Initialize MCP client
const mcpClient = new Client({
  url: 'http://localhost:8000/mcp',
  apiKey: 'your_api_key'
});

// Initialize Claude
const claude = new Anthropic({
  apiKey: 'your_claude_api_key'
});

async function main() {
  // Get available tools
  const tools = await mcpClient.listTools();

  // Create message with tools
  const message = await claude.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    tools: tools,
    messages: [
      {
        role: 'user',
        content: 'What is the balance of account acc-456?'
      }
    ]
  });

  // Handle tool use
  if (message.stop_reason === 'tool_use') {
    const toolUse = message.content[message.content.length - 1];
    
    // Call MCP tool
    const result = await mcpClient.callTool(
      toolUse.name,
      toolUse.input
    );
    
    // Continue conversation with tool result
    const response = await claude.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 1024,
      tools: tools,
      messages: [
        { role: 'user', content: 'What is the balance of account acc-456?' },
        { role: 'assistant', content: message.content },
        {
          role: 'user',
          content: [
            {
              type: 'tool_result',
              tool_use_id: toolUse.id,
              content: JSON.stringify(result)
            }
          ]
        }
      ]
    });
    
    console.log(response.content[0].text);
  }
}

main();
```

---

## 🎯 Best Practices

### 1. Tool Discovery

Always discover tools dynamically instead of hardcoding:

```python
# ✅ Good: Dynamic discovery
tools = client.list_tools()

# ❌ Bad: Hardcoded tools
tools = [
    {"name": "get_customer_360", ...},
    {"name": "check_loan_eligibility", ...}
]
```

### 2. Error Handling

Handle tool errors gracefully:

```python
try:
    result = client.call_tool("get_account_balance", {"account_id": "acc-456"})
except MCPError as e:
    print(f"Tool error: {e.message}")
    # Fallback logic
```

### 3. Context Management

Maintain context across tool calls:

```python
# Store customer context
context = {
    "customer_id": "cust-123",
    "session_id": "sess-789"
}

# Use context in subsequent calls
balance = client.call_tool(
    "get_account_balance",
    {
        "account_id": "acc-456",
        **context
    }
)
```

### 4. Rate Limiting

Respect rate limits:

```python
import time

for account_id in account_ids:
    balance = client.call_tool(
        "get_account_balance",
        {"account_id": account_id}
    )
    time.sleep(0.1)  # 10 requests per second
```

### 5. Security

Never expose sensitive data in tool responses:

```python
# ✅ Good: Masked data
{
    "account_number": "****7890",
    "balance": 10000.00
}

# ❌ Bad: Full account number
{
    "account_number": "1234567890",
    "balance": 10000.00
}
```

---

## 📚 Additional Resources

- **[REST API Documentation](rest-api.md)** - Traditional API reference
- **[Swagger UI](swagger-ui.md)** - Interactive API explorer
- **[Code Examples](examples.md)** - More integration examples
- **[MCP Specification](https://modelcontextprotocol.io/)** - Official MCP docs

---

## 🆘 Need Help?

- **[Troubleshooting Guide](../getting-started/troubleshooting.md)** - Common issues
- **[GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)** - Ask questions
- **Email:** michael@turingdynamics.ai

---

**Happy building!** 🤖

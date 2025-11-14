# 💻 Code Examples

Practical code examples for working with UltraCore modules.

---

## 📚 Quick Links

- **[Account Management](#account-management)** - Create and manage accounts
- **[Transaction Processing](#transaction-processing)** - Process transactions
- **[Investment Pods](#investment-pods)** - Create and manage investment pods
- **[Event Sourcing](#event-sourcing)** - Work with events
- **[Data Mesh](#data-mesh)** - Access data products
- **[AI Agents](#ai-agents)** - Build AI agents
- **[MCP Tools](#mcp-tools)** - Use MCP tools

---

## 🏦 Account Management

### Create Account

```python
from ultracore.domains.accounts.models.account import Account
from ultracore.domains.accounts.events.account_events import AccountCreatedEvent
from ultracore.infrastructure.event_store.event_store import EventStore

# Create account aggregate
account = Account.create(
    tenant_id="tenant-123",
    customer_id="customer-456",
    account_type="savings",
    currency="AUD",
    initial_balance=1000.00
)

# Publish event
event_store = EventStore()
for event in account.uncommitted_events:
    await event_store.publish(event)

# Clear uncommitted events
account.clear_uncommitted_events()

print(f"Account created: {account.account_id}")
print(f"Balance: ${account.balance}")
```

### Get Account Balance

```python
from ultracore.domains.accounts.services.account_service import AccountService

# Initialize service
account_service = AccountService()

# Get balance
balance = await account_service.get_balance(
    account_id="acc-123"
)

print(f"Available: ${balance.available_balance}")
print(f"Current: ${balance.current_balance}")
print(f"Pending: ${balance.pending_balance}")
```

### List Account Transactions

```python
from ultracore.domains.accounts.services.account_service import AccountService

# Initialize service
account_service = AccountService()

# Get transactions
transactions = await account_service.get_transactions(
    account_id="acc-123",
    start_date="2024-01-01",
    end_date="2024-12-31",
    page=1,
    page_size=10
)

for txn in transactions.data:
    print(f"{txn.date}: ${txn.amount} - {txn.description}")
```

---

## 💸 Transaction Processing

### Create Transaction

```python
from ultracore.domains.accounts.models.account import Account
from ultracore.domains.accounts.events.account_events import TransactionCreatedEvent

# Load account
account = await Account.load_from_events(
    account_id="acc-123",
    event_store=event_store
)

# Create transaction
transaction = account.create_transaction(
    transaction_type="debit",
    amount=100.00,
    description="Payment for services",
    reference="REF-123"
)

# Publish events
for event in account.uncommitted_events:
    await event_store.publish(event)

account.clear_uncommitted_events()

print(f"Transaction created: {transaction.transaction_id}")
print(f"New balance: ${account.balance}")
```

### Transfer Between Accounts

```python
from ultracore.domains.accounts.services.account_service import AccountService

# Initialize service
account_service = AccountService()

# Transfer money
transfer = await account_service.transfer(
    from_account_id="acc-123",
    to_account_id="acc-456",
    amount=100.00,
    description="Transfer to savings"
)

print(f"Transfer ID: {transfer.transfer_id}")
print(f"Status: {transfer.status}")
```

---

## 📊 Investment Pods

### Create Investment Pod

```python
from ultracore.domains.wealth.models.investment_pod import InvestmentPod
from ultracore.domains.wealth.events.wealth_events import InvestmentPodCreatedEvent
from datetime import datetime, timedelta

# Create investment pod
pod = InvestmentPod.create(
    tenant_id="tenant-123",
    customer_id="customer-456",
    goal_amount=100000.00,
    target_date=datetime.now() + timedelta(days=3650),  # 10 years
    risk_tolerance="moderate"
)

# Publish event
for event in pod.uncommitted_events:
    await event_store.publish(event)

pod.clear_uncommitted_events()

print(f"Investment pod created: {pod.pod_id}")
print(f"Goal: ${pod.goal_amount} by {pod.target_date}")
```

### Optimize Portfolio

```python
from ultracore.domains.wealth.services.portfolio_optimizer import PortfolioOptimizer

# Initialize optimizer
optimizer = PortfolioOptimizer()

# Optimize portfolio
optimization = await optimizer.optimize(
    pod_id="pod-123",
    risk_tolerance="moderate",
    constraints={
        "max_single_asset": 0.20,  # Max 20% in single asset
        "min_diversification": 10,  # Min 10 assets
        "rebalance_threshold": 0.05  # Rebalance if drift > 5%
    }
)

print(f"Expected return: {optimization.expected_return*100:.2f}%")
print(f"Sharpe ratio: {optimization.sharpe_ratio:.2f}")
print(f"Volatility: {optimization.volatility*100:.2f}%")

# Print allocation
for asset, weight in optimization.allocation.items():
    print(f"  {asset}: {weight*100:.2f}%")
```

### Fund Investment Pod

```python
from ultracore.domains.wealth.models.investment_pod import InvestmentPod

# Load pod
pod = await InvestmentPod.load_from_events(
    pod_id="pod-123",
    event_store=event_store
)

# Fund pod
pod.fund(
    account_id="acc-123",
    amount=10000.00
)

# Publish events
for event in pod.uncommitted_events:
    await event_store.publish(event)

pod.clear_uncommitted_events()

print(f"Pod funded with ${10000.00}")
print(f"Current value: ${pod.current_value}")
print(f"Progress: {pod.progress_percentage:.1f}%")
```

---

## 📡 Event Sourcing

### Publish Event

```python
from ultracore.infrastructure.event_store.event_store import EventStore
from ultracore.domains.accounts.events.account_events import AccountCreatedEvent
from datetime import datetime

# Create event
event = AccountCreatedEvent(
    aggregate_id="acc-123",
    tenant_id="tenant-123",
    customer_id="customer-456",
    account_type="savings",
    currency="AUD",
    initial_balance=1000.00,
    timestamp=datetime.utcnow()
)

# Publish to Kafka
event_store = EventStore()
await event_store.publish(event)

print(f"Event published: {event.event_type}")
```

### Subscribe to Events

```python
from ultracore.infrastructure.event_store.event_store import EventStore
from ultracore.domains.accounts.events.account_events import AccountCreatedEvent

# Create event handler
async def handle_account_created(event: AccountCreatedEvent):
    print(f"New account created: {event.aggregate_id}")
    print(f"Customer: {event.customer_id}")
    print(f"Balance: ${event.initial_balance}")
    
    # Do something with the event
    # e.g., send welcome email, update analytics, etc.

# Subscribe to events
event_store = EventStore()
await event_store.subscribe(
    topic="accounts.created",
    handler=handle_account_created,
    consumer_group="account-notifications"
)
```

### Replay Events

```python
from ultracore.infrastructure.event_store.event_store import EventStore
from ultracore.domains.accounts.models.account import Account

# Load aggregate from events
event_store = EventStore()
events = await event_store.get_events(
    aggregate_id="acc-123",
    aggregate_type="Account"
)

# Replay events to rebuild state
account = Account()
for event in events:
    account.apply_event(event)

print(f"Account state rebuilt from {len(events)} events")
print(f"Balance: ${account.balance}")
```

---

## 🗄️ Data Mesh

### Access Data Product

```python
from ultracore.data_mesh.platform.data_product_registry import DataProductRegistry

# Initialize registry
registry = DataProductRegistry()

# Get data product
customer_360 = await registry.get_data_product(
    product_id="client.customer_360"
)

# Query data product
customer_data = await customer_360.query(
    customer_id="customer-456"
)

print(f"Customer: {customer_data.name}")
print(f"Accounts: {len(customer_data.accounts)}")
print(f"Total balance: ${customer_data.total_balance}")
print(f"Credit score: {customer_data.credit_score}")
```

### Create Data Product

```python
from ultracore.data_mesh.platform.data_product import DataProduct
from ultracore.data_mesh.catalog.data_catalog import DataCatalog

# Define data product
class AccountBalanceDataProduct(DataProduct):
    product_id = "accounts.balances"
    domain = "accounts"
    owner = "accounts-team"
    
    async def query(self, account_id: str):
        # Query logic
        balance = await self.get_balance(account_id)
        return balance
    
    async def get_balance(self, account_id: str):
        # Implementation
        pass

# Register data product
catalog = DataCatalog()
await catalog.register(AccountBalanceDataProduct())

print("Data product registered: accounts.balances")
```

---

## 🤖 AI Agents

### Create AI Agent

```python
from ultracore.agentic_ai.agents.base_agent import BaseAgent
from ultracore.ai.assistants.llm_client import LLMClient

class LoanOfficerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="loan-officer",
            name="AI Loan Officer",
            description="Autonomous loan application processor"
        )
        self.llm = LLMClient()
    
    async def process_application(self, application_id: str):
        # Get application
        application = await self.get_application(application_id)
        
        # Analyze with LLM
        analysis = await self.llm.analyze(
            prompt=f"Analyze loan application: {application}",
            context={"credit_score": application.credit_score}
        )
        
        # Make decision
        decision = await self.make_decision(analysis)
        
        return decision
    
    async def make_decision(self, analysis):
        # Decision logic
        if analysis.risk_score < 0.3:
            return "approved"
        elif analysis.risk_score < 0.7:
            return "manual_review"
        else:
            return "rejected"

# Use agent
agent = LoanOfficerAgent()
decision = await agent.process_application("app-123")

print(f"Decision: {decision}")
```

### Use Investment Agent

```python
from ultracore.agents.investment_agents import InvestmentAdvisorAgent

# Initialize agent
advisor = InvestmentAdvisorAgent()

# Get investment advice
advice = await advisor.get_advice(
    customer_id="customer-456",
    risk_tolerance="moderate",
    time_horizon=10,  # years
    goal_amount=100000.00
)

print(f"Recommended allocation:")
for asset_class, allocation in advice.allocation.items():
    print(f"  {asset_class}: {allocation*100:.1f}%")

print(f"\nExpected return: {advice.expected_return*100:.2f}%")
print(f"Risk level: {advice.risk_level}")
```

---

## 🔧 MCP Tools

### Use MCP Tool

```python
from ultracore.mcp.tool_registry import ToolRegistry

# Initialize registry
registry = ToolRegistry()

# Get tool
customer_360_tool = registry.get_tool("get_customer_360")

# Execute tool
result = await customer_360_tool.execute(
    customer_id="customer-456"
)

print(f"Customer: {result['name']}")
print(f"Accounts: {len(result['accounts'])}")
print(f"Total balance: ${result['total_balance']}")
```

### Create Custom MCP Tool

```python
from ultracore.mcp.base_tool import BaseTool
from ultracore.mcp.tool_registry import ToolRegistry

class CheckLoanEligibilityTool(BaseTool):
    name = "check_loan_eligibility"
    description = "Check if customer is eligible for a loan"
    
    input_schema = {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Customer ID"
            },
            "loan_amount": {
                "type": "number",
                "description": "Requested loan amount"
            }
        },
        "required": ["customer_id", "loan_amount"]
    }
    
    async def execute(self, customer_id: str, loan_amount: float):
        # Get customer data
        customer = await self.get_customer(customer_id)
        
        # Check eligibility
        eligible = (
            customer.credit_score > 600 and
            customer.debt_to_income < 0.4 and
            loan_amount < customer.annual_income * 3
        )
        
        return {
            "eligible": eligible,
            "max_loan_amount": customer.annual_income * 3,
            "interest_rate": self.calculate_rate(customer.credit_score)
        }

# Register tool
registry = ToolRegistry()
registry.register(CheckLoanEligibilityTool())

print("MCP tool registered: check_loan_eligibility")
```

---

## 🔐 Authentication & Authorization

### Check Permissions

```python
from ultracore.security.rbac.permission_checker import PermissionChecker

# Initialize checker
checker = PermissionChecker()

# Check permission
has_permission = await checker.check(
    user_id="user-123",
    resource="accounts",
    action="read",
    tenant_id="tenant-123"
)

if has_permission:
    # Allow access
    accounts = await get_accounts(tenant_id="tenant-123")
else:
    # Deny access
    raise PermissionError("Access denied")
```

### Assign Role

```python
from ultracore.security.rbac.role_manager import RoleManager

# Initialize manager
role_manager = RoleManager()

# Assign role
await role_manager.assign_role(
    user_id="user-123",
    role="account_manager",
    tenant_id="tenant-123"
)

print("Role assigned: account_manager")
```

---

## 📊 Reporting

### Generate Financial Statement

```python
from ultracore.reporting.financial.statement_generator import StatementGenerator
from datetime import datetime

# Initialize generator
generator = StatementGenerator()

# Generate balance sheet
balance_sheet = await generator.generate_balance_sheet(
    tenant_id="tenant-123",
    as_of_date=datetime.now()
)

print("Assets:")
for account, balance in balance_sheet.assets.items():
    print(f"  {account}: ${balance:,.2f}")

print("\nLiabilities:")
for account, balance in balance_sheet.liabilities.items():
    print(f"  {account}: ${balance:,.2f}")

print(f"\nEquity: ${balance_sheet.equity:,.2f}")
```

---

## 🔔 Notifications

### Send Notification

```python
from ultracore.notifications.notification_service import NotificationService

# Initialize service
notification_service = NotificationService()

# Send notification
await notification_service.send(
    customer_id="customer-456",
    channel="email",
    template="account_created",
    data={
        "account_number": "1234567890",
        "account_type": "savings",
        "initial_balance": 1000.00
    }
)

print("Notification sent")
```

---

## 🧪 Testing

### Test Event Sourcing

```python
import pytest
from ultracore.domains.accounts.models.account import Account
from ultracore.domains.accounts.events.account_events import AccountCreatedEvent

@pytest.mark.asyncio
async def test_account_creation():
    # Create account
    account = Account.create(
        tenant_id="tenant-123",
        customer_id="customer-456",
        account_type="savings",
        currency="AUD",
        initial_balance=1000.00
    )
    
    # Check state
    assert account.balance == 1000.00
    assert account.account_type == "savings"
    
    # Check events
    assert len(account.uncommitted_events) == 1
    event = account.uncommitted_events[0]
    assert isinstance(event, AccountCreatedEvent)
    assert event.initial_balance == 1000.00
```

### Test Data Product

```python
import pytest
from ultracore.data_mesh.platform.data_product_registry import DataProductRegistry

@pytest.mark.asyncio
async def test_customer_360_data_product():
    # Get data product
    registry = DataProductRegistry()
    customer_360 = await registry.get_data_product("client.customer_360")
    
    # Query data
    customer_data = await customer_360.query(customer_id="customer-456")
    
    # Check data
    assert customer_data.customer_id == "customer-456"
    assert len(customer_data.accounts) > 0
    assert customer_data.total_balance >= 0
```

---

## 📚 Additional Resources

- **[Module Index](module-index.md)** - Find modules by category
- **[Code Navigation Guide](code-navigation-guide.md)** - Navigate the codebase
- **[API Documentation](../api/README.md)** - REST API and MCP tools
- **[Architecture Documentation](../architecture/README.md)** - System design

---

**Last Updated:** November 14, 2024

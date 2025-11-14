# 🧭 Code Navigation

Navigate the UltraCore codebase with ease.

---

## 📚 Documentation Index

| Document | Description | Time to Read |
|----------|-------------|--------------|
| **[Code Navigation Guide](code-navigation-guide.md)** | Complete guide to navigating the codebase | 20 min |
| **[Module Index](module-index.md)** | Comprehensive index of all modules by category | 15 min |
| **[Source Code Reference](source-code-reference.md)** | Quick reference to key source files | 10 min |
| **[Code Examples](code-examples.md)** | Practical code examples for common tasks | 25 min |

---

## 🚀 Quick Start

### New to UltraCore?

**Start here:**

1. **[Code Navigation Guide](code-navigation-guide.md)** - Learn how to navigate the codebase
2. **[Module Index](module-index.md)** - Explore modules by category
3. **[Code Examples](code-examples.md)** - See practical examples

### Looking for Specific Code?

**Use the right tool:**

- **By Category:** [Module Index](module-index.md) - Browse by functionality
- **By File:** [Source Code Reference](source-code-reference.md) - Direct links to files
- **By Example:** [Code Examples](code-examples.md) - See it in action

---

## 🗺️ Repository Structure

```
src/ultracore/
├── domains/              # Domain-driven design bounded contexts
│   ├── accounts/        # Account domain
│   ├── wealth/          # Wealth management domain
│   ├── lending/         # Lending domain
│   ├── payments/        # Payment domain
│   └── ...              # Other domains
├── api/                 # REST API endpoints
├── agentic_ai/          # AI agent system
├── infrastructure/      # Infrastructure services
├── data_mesh/           # Data mesh platform
└── mcp/                 # MCP tool registry
```

**[Full Structure Guide →](code-navigation-guide.md#repository-structure)**

---

## 🔍 Finding Code

### By Functionality

| Need to work on... | Start here | Documentation |
|--------------------|------------|---------------|
| **Accounts** | [`domains/accounts/`](../../src/ultracore/domains/accounts/) | [Module Index](module-index.md#account-domain) |
| **Investments** | [`domains/wealth/`](../../src/ultracore/domains/wealth/) | [Module Index](module-index.md#wealth-domain) |
| **Loans** | [`domains/lending/`](../../src/ultracore/domains/lending/) | [Module Index](module-index.md#lending-domain) |
| **Payments** | [`domains/payments/`](../../src/ultracore/domains/payments/) | [Module Index](module-index.md#payment-domain) |
| **Customers** | [`domains/client/`](../../src/ultracore/domains/client/) | [Module Index](module-index.md#client-domain) |

**[Full Finding Guide →](code-navigation-guide.md#finding-code)**

---

### By Feature

| Feature | Location | Documentation |
|---------|----------|---------------|
| **Event Sourcing** | [`infrastructure/event_store/`](../../src/ultracore/infrastructure/event_store/) | [Event Sourcing Guide](code-navigation-guide.md#event-sourcing) |
| **Data Mesh** | [`data_mesh/`](../../src/ultracore/data_mesh/) | [Data Mesh Guide](code-navigation-guide.md#data-mesh) |
| **AI Agents** | [`agentic_ai/`](../../src/ultracore/agentic_ai/) | [AI Guide](code-navigation-guide.md#ai--ml) |
| **MCP Tools** | [`mcp/`](../../src/ultracore/mcp/) | [MCP Guide](../api/mcp-tools.md) |
| **REST API** | [`api/`](../../src/ultracore/api/) | [API Docs](../api/rest-api.md) |

---

## 💻 Code Examples

### Quick Examples

**Create Account:**
```python
from ultracore.domains.accounts.models.account import Account

account = Account.create(
    tenant_id="tenant-123",
    customer_id="customer-456",
    account_type="savings",
    currency="AUD",
    initial_balance=1000.00
)
```

**Create Investment Pod:**
```python
from ultracore.domains.wealth.models.investment_pod import InvestmentPod

pod = InvestmentPod.create(
    tenant_id="tenant-123",
    customer_id="customer-456",
    goal_amount=100000.00,
    target_date=datetime.now() + timedelta(days=3650),
    risk_tolerance="moderate"
)
```

**[More Examples →](code-examples.md)**

---

## 🏛️ Domain-Driven Design

UltraCore uses **Domain-Driven Design (DDD)** with bounded contexts.

### Key Domains

| Domain | Purpose | Path |
|--------|---------|------|
| **Accounts** | Account management | [`domains/accounts/`](../../src/ultracore/domains/accounts/) |
| **Wealth** | Investment management | [`domains/wealth/`](../../src/ultracore/domains/wealth/) |
| **Lending** | Loan management | [`domains/lending/`](../../src/ultracore/domains/lending/) |
| **Payments** | Payment processing | [`domains/payments/`](../../src/ultracore/domains/payments/) |
| **Client** | Customer management | [`domains/client/`](../../src/ultracore/domains/client/) |

**[All Domains →](module-index.md#by-domain)**

### Domain Structure

Each domain follows a consistent structure:

```
domains/<domain_name>/
├── models/              # Aggregates and entities
├── events/              # Domain events
├── services/            # Domain services
├── agents/              # AI agents
├── ml/                  # Machine learning models
├── mcp/                 # MCP tools
└── datamesh/            # Data products
```

**[DDD Guide →](code-navigation-guide.md#domain-driven-design)**

---

## 📡 Event Sourcing

All domains use **event sourcing** with Kafka.

### Event Flow

```
Command → Aggregate → Event → Kafka → Subscribers → Read Models
```

### Key Files

- **Event Store:** [`infrastructure/event_store/event_store.py`](../../src/ultracore/infrastructure/event_store/event_store.py)
- **Kafka Implementation:** [`infrastructure/kafka_event_store/`](../../src/ultracore/infrastructure/kafka_event_store/)
- **Base Event:** [`events/base_event.py`](../../src/ultracore/events/base_event.py)

**[Event Sourcing Guide →](code-navigation-guide.md#event-sourcing)**

---

## 🗄️ Data Mesh

**Data Mesh** architecture with domain-oriented data products.

### Data Products

| Domain | Data Products | Path |
|--------|---------------|------|
| **Account** | Account balances, transaction history | [`domains/account/data_products/`](../../src/ultracore/domains/account/data_products/) |
| **Loan** | Loan portfolio, delinquency report | [`domains/loan/data_products/`](../../src/ultracore/domains/loan/data_products/) |
| **Client** | Customer 360 view | [`domains/client/data_products/`](../../src/ultracore/domains/client/data_products/) |

**[Data Mesh Guide →](code-navigation-guide.md#data-mesh)**

---

## 🤖 AI & Machine Learning

### AI Agents

Autonomous AI systems for decision-making.

**Examples:**
- [`domains/wealth/agents/investment_advisor.py`](../../src/ultracore/domains/wealth/agents/investment_advisor.py) - AI investment advisor
- [`domains/lending/agents/loan_officer.py`](../../src/ultracore/domains/lending/agents/loan_officer.py) - AI loan officer

**[AI Guide →](code-navigation-guide.md#ai--ml)**

### ML Models

Machine learning models for predictions.

**Examples:**
- [`domains/lending/ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py) - Credit scoring
- [`domains/wealth/ml/price_predictor.py`](../../src/ultracore/domains/wealth/ml/price_predictor.py) - Price prediction

### MCP Tools

Model Context Protocol tools for AI integration.

**Examples:**
- [`domains/accounts/mcp/account_tools.py`](../../src/ultracore/domains/accounts/mcp/account_tools.py) - Account tools
- [`domains/wealth/mcp/wealth_tools.py`](../../src/ultracore/domains/wealth/mcp/wealth_tools.py) - Wealth tools

**[MCP Documentation →](../api/mcp-tools.md)**

---

## 🎯 Navigation Patterns

### Common Workflows

**Feature Development:**
1. Identify domain
2. Update aggregate
3. Define events
4. Update services
5. Add API endpoints
6. Write tests

**Bug Investigation:**
1. Find domain
2. Check aggregate
3. Review events
4. Check services
5. Review tests
6. Check logs

**[Navigation Patterns →](code-navigation-guide.md#navigation-patterns)**

---

## 🔧 Tools & Commands

### Finding Files

```bash
# Find all aggregates
find src/ultracore/domains -name "*.py" -path "*/models/*"

# Find all events
find src/ultracore/domains -name "*_events.py"

# Find all agents
find src/ultracore/domains -name "*.py" -path "*/agents/*"
```

### Searching Code

```bash
# Search for a function
grep -r "def create_investment_pod" src/

# Search for a class
grep -r "class InvestmentPod" src/
```

**[More Commands →](code-navigation-guide.md#tools--commands)**

---

## 📚 Additional Resources

### Documentation
- **[Architecture Documentation](../architecture/README.md)** - System design
- **[API Documentation](../api/README.md)** - REST API and MCP tools
- **[Module Documentation](../modules/README.md)** - Module guides
- **[Getting Started](../getting-started/quick-start.md)** - Quick start guide

### Learning Path
- **[Quick Start Guide](../getting-started/quick-start.md)** - Get started in 30 minutes
- **[Architecture Overview](../architecture/README.md)** - Understand the system
- **[First Contribution](../getting-started/first-contribution.md)** - Make your first contribution

---

## 🎓 Learning Path

### For New Developers

1. **[Code Navigation Guide](code-navigation-guide.md)** - Learn to navigate
2. **[Module Index](module-index.md)** - Explore modules
3. **[Code Examples](code-examples.md)** - See examples
4. **[First Contribution](../getting-started/first-contribution.md)** - Contribute

### For Experienced Developers

1. **[Module Index](module-index.md)** - Quick overview
2. **[Source Code Reference](source-code-reference.md)** - Direct links
3. **[Architecture Docs](../architecture/README.md)** - Deep dive

---

**Happy navigating!** 🧭

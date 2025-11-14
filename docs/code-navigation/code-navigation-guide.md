# 🧭 Code Navigation Guide

Complete guide to navigating the UltraCore codebase efficiently.

---

## 📚 Quick Links

- **[Repository Structure](#repository-structure)** - High-level organization
- **[Finding Code](#finding-code)** - How to locate specific functionality
- **[Domain-Driven Design](#domain-driven-design)** - Understanding DDD structure
- **[Event Sourcing](#event-sourcing)** - Working with events
- **[Data Mesh](#data-mesh)** - Accessing data products
- **[AI & ML](#ai--ml)** - AI agents and ML models
- **[Navigation Patterns](#navigation-patterns)** - Common navigation workflows

---

## 🗂️ Repository Structure

UltraCore follows a **Domain-Driven Design (DDD)** architecture with clear separation of concerns.

### High-Level Structure

```
src/ultracore/
├── domains/              # Domain-driven design bounded contexts
│   ├── accounts/        # Account domain
│   ├── wealth/          # Wealth management domain
│   ├── lending/         # Lending domain
│   ├── payments/        # Payment domain
│   ├── client/          # Client domain
│   └── ...              # Other domains
├── api/                 # REST API endpoints
├── agentic_ai/          # AI agent system
├── infrastructure/      # Infrastructure services
├── data_mesh/           # Data mesh platform
├── events/              # Base event classes
├── ml_models/           # ML model registry
└── mcp/                 # MCP tool registry
```

### Domain Structure

Each domain follows a consistent structure:

```
domains/<domain_name>/
├── models/              # Aggregates and entities
├── events/              # Domain events
├── services/            # Domain services
├── agents/              # AI agents
├── ml/                  # Machine learning models
├── rl/                  # Reinforcement learning models
├── mcp/                 # MCP tools
├── api/                 # Domain-specific API
└── datamesh/            # Data products
```

---

## 🔍 Finding Code

### By Functionality

**"I need to work on accounts"**

1. **Start with the domain:** [`src/ultracore/domains/accounts/`](../../src/ultracore/domains/accounts/)
2. **Check the aggregate:** [`models/account.py`](../../src/ultracore/domains/accounts/models/account.py)
3. **Review events:** [`events/account_events.py`](../../src/ultracore/domains/accounts/events/account_events.py)
4. **Find services:** [`services/account_service.py`](../../src/ultracore/domains/accounts/services/account_service.py)
5. **Check API:** [`api/routers/accounts.py`](../../src/ultracore/api/routers/accounts.py)

**"I need to work on loans"**

1. **Start with the domain:** [`src/ultracore/domains/lending/`](../../src/ultracore/domains/lending/)
2. **Check the aggregate:** [`models/loan.py`](../../src/ultracore/domains/lending/models/loan.py)
3. **Review origination:** [`origination/loan_application.py`](../../src/ultracore/domains/lending/origination/loan_application.py)
4. **Find ML models:** [`ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py)

**"I need to work on investments"**

1. **Start with the domain:** [`src/ultracore/domains/wealth/`](../../src/ultracore/domains/wealth/)
2. **Check investment pods:** [`models/investment_pod.py`](../../src/ultracore/domains/wealth/models/investment_pod.py)
3. **Review optimization:** [`services/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/services/portfolio_optimizer.py)
4. **Check trading:** [`trading/trading_engine.py`](../../src/ultracore/domains/wealth/trading/trading_engine.py)

**"I need to work on payments"**

1. **Start with the domain:** [`src/ultracore/domains/payments/`](../../src/ultracore/domains/payments/)
2. **Check payment rails:** [`src/ultracore/payments/`](../../src/ultracore/payments/)
3. **Review NPP:** [`payments/npp/`](../../src/ultracore/payments/npp/)
4. **Check BPAY:** [`payments/bpay/`](../../src/ultracore/payments/bpay/)

---

### By Feature

**Event Sourcing**

All event-sourced code follows this pattern:

1. **Aggregate:** `domains/<domain>/models/<aggregate>.py`
2. **Events:** `domains/<domain>/events/<domain>_events.py`
3. **Event Store:** [`infrastructure/event_store/`](../../src/ultracore/infrastructure/event_store/)

**Data Mesh**

Data products are organized by domain:

1. **Data Products:** `domains/<domain>/data_products/`
2. **Data Catalog:** [`data_mesh/catalog/`](../../src/ultracore/data_mesh/catalog/)
3. **Platform:** [`data_mesh/platform/`](../../src/ultracore/data_mesh/platform/)

**AI Agents**

AI agents are organized by domain:

1. **Domain Agents:** `domains/<domain>/agents/`
2. **Agent System:** [`agentic_ai/agent_system.py`](../../src/ultracore/agentic_ai/agent_system.py)
3. **Base Agent:** [`agentic_ai/agents/base_agent.py`](../../src/ultracore/agentic_ai/agents/base_agent.py)

**ML Models**

ML models are organized by domain:

1. **Domain Models:** `domains/<domain>/ml/`
2. **Model Registry:** [`ml_models/registry/`](../../src/ultracore/ml_models/registry/)

**MCP Tools**

MCP tools are organized by domain:

1. **Domain Tools:** `domains/<domain>/mcp/`
2. **Tool Registry:** [`mcp/tool_registry.py`](../../src/ultracore/mcp/tool_registry.py)
3. **MCP Server:** [`agentic_ai/mcp_server.py`](../../src/ultracore/agentic_ai/mcp_server.py)

---

## 🏛️ Domain-Driven Design

UltraCore uses **Domain-Driven Design (DDD)** with bounded contexts.

### Understanding Domains

**What is a Domain?**

A domain is a bounded context representing a specific area of business functionality. Each domain is self-contained with its own:

- **Models** - Aggregates and entities
- **Events** - Domain events
- **Services** - Business logic
- **Agents** - AI agents
- **ML Models** - Machine learning models
- **MCP Tools** - Integration tools

**Key Domains:**

| Domain | Purpose | Path |
|--------|---------|------|
| **Accounts** | Account management | [`domains/accounts/`](../../src/ultracore/domains/accounts/) |
| **Wealth** | Investment management | [`domains/wealth/`](../../src/ultracore/domains/wealth/) |
| **Lending** | Loan management | [`domains/lending/`](../../src/ultracore/domains/lending/) |
| **Payments** | Payment processing | [`domains/payments/`](../../src/ultracore/domains/payments/) |
| **Client** | Customer management | [`domains/client/`](../../src/ultracore/domains/client/) |
| **Onboarding** | Customer onboarding | [`domains/onboarding/`](../../src/ultracore/domains/onboarding/) |
| **Collateral** | Collateral management | [`domains/collateral/`](../../src/ultracore/domains/collateral/) |

### Navigating a Domain

**1. Start with the README (if available)**

Some domains have README files explaining their purpose and structure.

**2. Check the models/**

The `models/` directory contains aggregates (domain entities). Start here to understand the core domain objects.

**Example:** [`domains/wealth/models/investment_pod.py`](../../src/ultracore/domains/wealth/models/investment_pod.py)

**3. Review the events/**

The `events/` directory contains domain events. These show what state changes can occur.

**Example:** [`domains/wealth/events/wealth_events.py`](../../src/ultracore/domains/wealth/events/wealth_events.py)

**4. Explore the services/**

The `services/` directory contains domain services (business logic).

**Example:** [`domains/wealth/services/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/services/portfolio_optimizer.py)

**5. Check specialized directories**

- `agents/` - AI agents
- `ml/` - ML models
- `rl/` - RL models
- `mcp/` - MCP tools
- `api/` - Domain API
- `datamesh/` - Data products

---

## 📡 Event Sourcing

UltraCore uses **event sourcing** with Kafka as the event store.

### Understanding Event Sourcing

**What is Event Sourcing?**

Instead of storing current state, we store a sequence of events that led to the current state. The current state is derived by replaying events.

**Benefits:**
- Complete audit trail
- Time travel (replay to any point)
- Event-driven architecture
- Scalability

### Navigating Event-Sourced Code

**1. Find the Aggregate**

Aggregates are the core domain entities that emit events.

**Location:** `domains/<domain>/models/<aggregate>.py`

**Example:** [`domains/accounts/models/account.py`](../../src/ultracore/domains/accounts/models/account.py)

**2. Find the Events**

Events represent state changes in the aggregate.

**Location:** `domains/<domain>/events/<domain>_events.py`

**Example:** [`domains/accounts/events/account_events.py`](../../src/ultracore/domains/accounts/events/account_events.py)

**3. Find the Event Store**

The event store publishes and retrieves events.

**Location:** [`infrastructure/event_store/event_store.py`](../../src/ultracore/infrastructure/event_store/event_store.py)

**4. Find Kafka Implementation**

Kafka-specific event store implementation.

**Location:** [`infrastructure/kafka_event_store/`](../../src/ultracore/infrastructure/kafka_event_store/)

### Event Flow

```
1. Command → Aggregate
2. Aggregate → Create Event
3. Event → Event Store (Kafka)
4. Event Store → Publish to Topic
5. Subscribers → Consume Event
6. Subscribers → Update Read Models
```

---

## 🗄️ Data Mesh

UltraCore implements **Data Mesh** architecture with domain-oriented data products.

### Understanding Data Mesh

**What is Data Mesh?**

Data Mesh is a decentralized approach to data architecture where each domain owns and publishes its own data products.

**Benefits:**
- Domain ownership
- Scalability
- Data as a product
- Self-service

### Navigating Data Mesh

**1. Find Data Products**

Data products are organized by domain.

**Location:** `domains/<domain>/data_products/`

**Examples:**
- [`domains/account/data_products/account_balances.py`](../../src/ultracore/domains/account/data_products/account_balances.py)
- [`domains/client/data_products/client_360.py`](../../src/ultracore/domains/client/data_products/client_360.py)
- [`domains/loan/data_products/loan_portfolio.py`](../../src/ultracore/domains/loan/data_products/loan_portfolio.py)

**2. Find Data Catalog**

The data catalog registers and discovers data products.

**Location:** [`data_mesh/catalog/data_catalog.py`](../../src/ultracore/data_mesh/catalog/data_catalog.py)

**3. Find Data Mesh Platform**

The platform provides infrastructure for data products.

**Location:** [`data_mesh/platform/data_mesh_platform.py`](../../src/ultracore/data_mesh/platform/data_mesh_platform.py)

**4. Find Data Governance**

Data governance policies and enforcement.

**Location:** [`data_mesh/governance/data_governance.py`](../../src/ultracore/data_mesh/governance/data_governance.py)

---

## 🤖 AI & ML

UltraCore has extensive AI and ML capabilities.

### AI Agents

**What are AI Agents?**

Autonomous AI systems that can make decisions and take actions.

**Finding Agents:**

1. **Domain Agents:** `domains/<domain>/agents/`
2. **Agent System:** [`agentic_ai/agent_system.py`](../../src/ultracore/agentic_ai/agent_system.py)
3. **Base Agent:** [`agentic_ai/agents/base_agent.py`](../../src/ultracore/agentic_ai/agents/base_agent.py)

**Examples:**
- [`domains/wealth/agents/investment_advisor.py`](../../src/ultracore/domains/wealth/agents/investment_advisor.py) - AI investment advisor
- [`domains/lending/agents/loan_officer.py`](../../src/ultracore/domains/lending/agents/loan_officer.py) - AI loan officer
- [`domains/payments/agents/payment_router.py`](../../src/ultracore/domains/payments/agents/payment_router.py) - AI payment router

### ML Models

**What are ML Models?**

Machine learning models for predictions and analysis.

**Finding ML Models:**

1. **Domain Models:** `domains/<domain>/ml/`
2. **Model Registry:** [`ml_models/registry/`](../../src/ultracore/ml_models/registry/)

**Examples:**
- [`domains/lending/ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py) - Credit scoring
- [`domains/wealth/ml/price_predictor.py`](../../src/ultracore/domains/wealth/ml/price_predictor.py) - Price prediction
- [`domains/accounts/ml/account_ml_models.py`](../../src/ultracore/domains/accounts/ml/account_ml_models.py) - Fraud detection

### RL Models

**What are RL Models?**

Reinforcement learning models for optimization.

**Finding RL Models:**

1. **Domain Models:** `domains/<domain>/rl/`

**Examples:**
- [`domains/wealth/rl/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/rl/portfolio_optimizer.py) - Portfolio optimization
- [`domains/lending/rl/loan_pricing.py`](../../src/ultracore/domains/lending/rl/loan_pricing.py) - Loan pricing
- [`domains/capsules/rl/savings_optimizer.py`](../../src/ultracore/domains/capsules/rl/savings_optimizer.py) - Savings optimization

### MCP Tools

**What are MCP Tools?**

Model Context Protocol tools for AI integration.

**Finding MCP Tools:**

1. **Domain Tools:** `domains/<domain>/mcp/`
2. **Tool Registry:** [`mcp/tool_registry.py`](../../src/ultracore/mcp/tool_registry.py)
3. **MCP Server:** [`agentic_ai/mcp_server.py`](../../src/ultracore/agentic_ai/mcp_server.py)

**Examples:**
- [`domains/accounts/mcp/account_tools.py`](../../src/ultracore/domains/accounts/mcp/account_tools.py) - Account tools
- [`domains/wealth/mcp/wealth_tools.py`](../../src/ultracore/domains/wealth/mcp/wealth_tools.py) - Wealth tools
- [`domains/onboarding/mcp/onboarding_tools.py`](../../src/ultracore/domains/onboarding/mcp/onboarding_tools.py) - Onboarding tools

---

## 🎯 Navigation Patterns

### Pattern 1: Feature Development

**Scenario:** You need to add a new feature to an existing domain.

**Steps:**

1. **Identify the domain** - Which domain does this feature belong to?
2. **Check the aggregate** - Does the aggregate need to change?
3. **Define events** - What events will be emitted?
4. **Update services** - What business logic is needed?
5. **Add API endpoints** - What REST endpoints are needed?
6. **Add tests** - Write tests for the new feature

**Example:** Adding "scheduled transfers" to accounts

1. Domain: `domains/accounts/`
2. Aggregate: `models/account.py` - Add `schedule_transfer()` method
3. Events: `events/account_events.py` - Add `TransferScheduledEvent`
4. Service: `services/account_service.py` - Add scheduling logic
5. API: `api/routers/accounts.py` - Add `/accounts/{id}/scheduled-transfers` endpoint
6. Tests: `tests/domains/accounts/test_scheduled_transfers.py`

---

### Pattern 2: Bug Investigation

**Scenario:** There's a bug in loan approval logic.

**Steps:**

1. **Find the domain** - `domains/lending/`
2. **Check the aggregate** - `models/loan.py` - Look for `approve()` method
3. **Review events** - `events/lending_events.py` - Check `LoanApprovedEvent`
4. **Check services** - `origination/loan_application.py` - Review approval logic
5. **Check ML models** - `ml/credit_scoring.py` - Verify scoring logic
6. **Review tests** - `tests/domains/lending/` - Check test coverage
7. **Check logs** - Look for event logs in Kafka

---

### Pattern 3: API Integration

**Scenario:** You need to integrate with the REST API.

**Steps:**

1. **Check API docs** - [`docs/api/rest-api.md`](../api/rest-api.md)
2. **Find the router** - `api/routers/<domain>.py`
3. **Review schemas** - `api/schemas/<domain>_schemas.py`
4. **Check examples** - [`docs/api/examples.md`](../api/examples.md)
5. **Test with Swagger** - `http://localhost:8000/api/v1/docs`

---

### Pattern 4: AI Agent Development

**Scenario:** You need to create a new AI agent.

**Steps:**

1. **Choose the domain** - Which domain does this agent belong to?
2. **Check base agent** - [`agentic_ai/agents/base_agent.py`](../../src/ultracore/agentic_ai/agents/base_agent.py)
3. **Create agent class** - `domains/<domain>/agents/<agent_name>.py`
4. **Implement logic** - Add decision-making logic
5. **Register agent** - Register with agent system
6. **Add tests** - Test agent behavior

---

### Pattern 5: Data Product Creation

**Scenario:** You need to create a new data product.

**Steps:**

1. **Choose the domain** - Which domain owns this data?
2. **Check base class** - [`data_mesh/platform/data_product.py`](../../src/ultracore/data_mesh/platform/data_product.py)
3. **Create data product** - `domains/<domain>/data_products/<product_name>.py`
4. **Implement query** - Add query logic
5. **Register product** - Register with data catalog
6. **Add tests** - Test data product

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

# Find all ML models
find src/ultracore/domains -name "*.py" -path "*/ml/*"

# Find all MCP tools
find src/ultracore/domains -name "*.py" -path "*/mcp/*"
```

### Searching Code

```bash
# Search for a specific function
grep -r "def create_investment_pod" src/

# Search for a specific class
grep -r "class InvestmentPod" src/

# Search for a specific event
grep -r "InvestmentPodCreatedEvent" src/

# Search for TODO comments
grep -r "TODO" src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run domain tests
pytest tests/domains/accounts/

# Run specific test
pytest tests/domains/accounts/test_account.py

# Run with coverage
pytest --cov=src/ultracore
```

---

## 📚 Additional Resources

- **[Module Index](module-index.md)** - Find modules by category
- **[Code Examples](code-examples.md)** - Practical code examples
- **[Source Code Reference](source-code-reference.md)** - Quick reference to key files
- **[API Documentation](../api/README.md)** - REST API and MCP tools
- **[Architecture Documentation](../architecture/README.md)** - System design

---

## 🎓 Learning Path

### For New Developers

1. **Start here:** [Quick Start Guide](../getting-started/quick-start.md)
2. **Understand architecture:** [Architecture Overview](../architecture/README.md)
3. **Learn event sourcing:** [Event Sourcing](../architecture/event-sourcing.md)
4. **Explore a domain:** Pick one domain and read all its code
5. **Try examples:** [Code Examples](code-examples.md)
6. **Make a contribution:** [First Contribution Guide](../getting-started/first-contribution.md)

### For Experienced Developers

1. **Review architecture:** [Architecture Documentation](../architecture/README.md)
2. **Understand domains:** [Module Index](module-index.md)
3. **Check API:** [REST API Documentation](../api/rest-api.md)
4. **Explore AI:** [Agentic AI](../architecture/agentic-ai.md)
5. **Review code:** [Source Code Reference](source-code-reference.md)

---

**Happy navigating!** 🧭

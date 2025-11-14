# 📦 Module Index

Comprehensive index of all UltraCore modules with navigation to source code and documentation.

---

## 🗺️ Navigation

- **[By Category](#by-category)** - Modules grouped by functionality
- **[By Domain](#by-domain)** - Domain-driven design modules
- **[By Feature](#by-feature)** - Feature-based organization
- **[Alphabetical](#alphabetical-index)** - Complete alphabetical list

---

## 📊 By Category

### Core Banking

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Accounts** | Account management and operations | [`src/ultracore/accounts/`](../../src/ultracore/accounts/) | [📖](../modules/savings.md) |
| **Transactions** | Transaction processing and ledger | [`src/ultracore/business_logic/transactions/`](../../src/ultracore/business_logic/transactions/) | - |
| **Payments** | Payment rails (NPP, BPAY, Direct Entry) | [`src/ultracore/payments/`](../../src/ultracore/payments/) | - |
| **Cards** | Card management and processing | [`src/ultracore/cards/`](../../src/ultracore/cards/) | - |
| **General Ledger** | Double-entry accounting ledger | [`src/ultracore/general_ledger/`](../../src/ultracore/general_ledger/) | - |

### Lending & Credit

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Lending** | Loan origination and servicing | [`src/ultracore/lending/`](../../src/ultracore/lending/) | - |
| **Loan Domain** | Event-sourced loan aggregates | [`src/ultracore/domains/lending/`](../../src/ultracore/domains/lending/) | - |
| **Loan Restructuring** | Loan modification and restructuring | [`src/ultracore/domains/loan_restructuring/`](../../src/ultracore/domains/loan_restructuring/) | - |
| **Collections** | Delinquency and collections | [`src/ultracore/lending/collections/`](../../src/ultracore/lending/collections/) | [📖](../modules/delinquency.md) |
| **Collateral** | Collateral management | [`src/ultracore/domains/collateral/`](../../src/ultracore/domains/collateral/) | - |

### Wealth Management

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Wealth Domain** | Investment pods and portfolio management | [`src/ultracore/domains/wealth/`](../../src/ultracore/domains/wealth/) | - |
| **Investment Agents** | AI investment agents | [`src/ultracore/agents/investment_agents.py`](../../src/ultracore/agents/investment_agents.py) | - |
| **Holdings** | Investment holdings tracking | [`src/ultracore/domains/wealth/models/`](../../src/ultracore/domains/wealth/models/) | [📖](../modules/holdings.md) |
| **Trading** | Stock/ETF trading | [`src/ultracore/domains/wealth/trading/`](../../src/ultracore/domains/wealth/trading/) | - |
| **Margin** | Margin trading and lending | [`src/ultracore/domains/wealth/margin/`](../../src/ultracore/domains/wealth/margin/) | - |

### Savings & Deposits

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Fixed Deposits** | Term deposit management | [`src/ultracore/domains/fixed_deposits/`](../../src/ultracore/domains/fixed_deposits/) | - |
| **Recurring Deposits** | Recurring deposit accounts | [`src/ultracore/domains/recurring_deposits/`](../../src/ultracore/domains/recurring_deposits/) | - |
| **Superannuation** | Australian superannuation | [`src/ultracore/domains/superannuation/`](../../src/ultracore/domains/superannuation/) | - |
| **Investment Capsules** | Goal-based savings capsules | [`src/ultracore/domains/capsules/`](../../src/ultracore/domains/capsules/) | - |

### Customer Management

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Customers** | Customer profiles and management | [`src/ultracore/customers/`](../../src/ultracore/customers/) | [📖](../modules/client-management.md) |
| **Client Domain** | Event-sourced client aggregates | [`src/ultracore/domains/client/`](../../src/ultracore/domains/client/) | [📖](../modules/client-management.md) |
| **Onboarding** | Customer onboarding workflows | [`src/ultracore/domains/onboarding/`](../../src/ultracore/domains/onboarding/) | - |
| **KYC** | Know Your Customer verification | [`src/ultracore/kyc/`](../../src/ultracore/kyc/) | - |
| **Document Management** | Document storage and verification | [`src/ultracore/document_management/`](../../src/ultracore/document_management/) | [📖](../modules/document-management.md) |

### Financial Operations

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Accounting** | Chart of accounts and accounting | [`src/ultracore/accounting/`](../../src/ultracore/accounting/) | [📖](../modules/accounting.md) |
| **Forex** | Foreign exchange and multi-currency | [`src/ultracore/accounting/forex/`](../../src/ultracore/accounting/forex/) | [📖](../modules/multi-currency.md) |
| **Fee Management** | Fee calculation and charging | [`src/ultracore/business_logic/fees/`](../../src/ultracore/business_logic/fees/) | [📖](../modules/fee-management.md) |
| **Interest** | Interest calculation engine | [`src/ultracore/business_logic/interest/`](../../src/ultracore/business_logic/interest/) | - |
| **Financial Reporting** | Financial statements and reports | [`src/ultracore/reporting/financial/`](../../src/ultracore/reporting/financial/) | [📖](../modules/financial-reporting.md) |

### Compliance & Security

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Compliance** | Regulatory compliance | [`src/ultracore/compliance/`](../../src/ultracore/compliance/) | - |
| **Security** | Authentication and authorization | [`src/ultracore/security/`](../../src/ultracore/security/) | [📖](../modules/permissions.md) |
| **Audit** | Audit logging and trails | [`src/ultracore/audit/`](../../src/ultracore/audit/) | - |
| **Open Banking** | Open banking APIs | [`src/ultracore/openbanking/`](../../src/ultracore/openbanking/) | - |

### AI & Machine Learning

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Agentic AI** | AI agent system and MCP server | [`src/ultracore/agentic_ai/`](../../src/ultracore/agentic_ai/) | [📖](../api/mcp-tools.md) |
| **ML Models** | Machine learning model registry | [`src/ultracore/ml_models/`](../../src/ultracore/ml_models/) | - |
| **AI Assistants** | AI assistant implementations | [`src/ultracore/ai/assistants/`](../../src/ultracore/ai/assistants/) | - |
| **Vision AI** | Computer vision for documents | [`src/ultracore/ai/vision/`](../../src/ultracore/ai/vision/) | - |
| **Voice AI** | Voice recognition and synthesis | [`src/ultracore/ai/voice/`](../../src/ultracore/ai/voice/) | - |
| **Embeddings** | Vector embeddings for AI | [`src/ultracore/ai/embeddings/`](../../src/ultracore/ai/embeddings/) | - |

### Infrastructure

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Event Store** | Kafka event sourcing infrastructure | [`src/ultracore/infrastructure/event_store/`](../../src/ultracore/infrastructure/event_store/) | [📖](../architecture/event-sourcing.md) |
| **Data Mesh** | Data mesh platform | [`src/ultracore/data_mesh/`](../../src/ultracore/data_mesh/) | [📖](../architecture/data-mesh.md) |
| **Caching** | Redis caching layer | [`src/ultracore/infrastructure/caching/`](../../src/ultracore/infrastructure/caching/) | - |
| **Sharding** | Database sharding | [`src/ultracore/infrastructure/sharding/`](../../src/ultracore/infrastructure/sharding/) | - |
| **Batch Analytics** | Batch processing | [`src/ultracore/infrastructure/batch_analytics/`](../../src/ultracore/infrastructure/batch_analytics/) | - |

### Integration & Extensibility

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **OpenMarkets** | OpenMarkets trading integration | [`src/ultracore/integrations/openmarkets/`](../../src/ultracore/integrations/openmarkets/) | - |
| **MCP** | Model Context Protocol tools | [`src/ultracore/mcp/`](../../src/ultracore/mcp/) | [📖](../api/mcp-tools.md) |
| **API** | REST API endpoints | [`src/ultracore/api/`](../../src/ultracore/api/) | [📖](../api/rest-api.md) |
| **Extensibility** | Plugin and extension system | [`src/ultracore/extensibility/`](../../src/ultracore/extensibility/) | - |

### Multi-Tenancy

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Multitenancy** | Tenant isolation and management | [`src/ultracore/`](../../src/ultracore/) | [📖](../modules/multitenancy.md) |
| **Database Models** | Multi-tenant data models | [`src/ultracore/database/models/`](../../src/ultracore/database/models/) | - |

### Notifications & Communication

| Module | Description | Source | Docs |
|--------|-------------|--------|------|
| **Notifications** | Multi-channel notifications | [`src/ultracore/notifications/`](../../src/ultracore/notifications/) | [📖](../modules/notifications.md) |
| **Customer Service** | Customer service channels | [`src/ultracore/customer_service/`](../../src/ultracore/customer_service/) | - |

---

## 🏛️ By Domain

UltraCore follows Domain-Driven Design (DDD) with bounded contexts.

### Account Domain

**Path:** [`src/ultracore/domains/accounts/`](../../src/ultracore/domains/accounts/)

**Components:**
- **Models** - Account aggregates and entities
- **Events** - Account domain events
- **Services** - Account domain services
- **Ledger** - Account ledger
- **Agents** - AI agents for accounts
- **ML** - Machine learning models
- **MCP** - MCP tools

**Key Files:**
- [`models/account.py`](../../src/ultracore/domains/accounts/models/account.py) - Account aggregate
- [`events/account_events.py`](../../src/ultracore/domains/accounts/events/account_events.py) - Domain events
- [`services/account_service.py`](../../src/ultracore/domains/accounts/services/account_service.py) - Business logic

---

### Wealth Domain

**Path:** [`src/ultracore/domains/wealth/`](../../src/ultracore/domains/wealth/)

**Components:**
- **Models** - Investment pod aggregates
- **Events** - Wealth domain events
- **Services** - Portfolio services
- **Trading** - Trading engine
- **Margin** - Margin trading
- **Planning** - Financial planning
- **Agents** - AI wealth advisors
- **ML** - Predictive models
- **RL** - Reinforcement learning
- **MCP** - MCP tools

**Key Files:**
- [`models/investment_pod.py`](../../src/ultracore/domains/wealth/models/investment_pod.py) - Investment pod aggregate
- [`services/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/services/portfolio_optimizer.py) - Portfolio optimization
- [`trading/trading_engine.py`](../../src/ultracore/domains/wealth/trading/trading_engine.py) - Trading execution

---

### Lending Domain

**Path:** [`src/ultracore/domains/lending/`](../../src/ultracore/domains/lending/)

**Components:**
- **Models** - Loan aggregates
- **Events** - Lending events
- **Origination** - Loan origination
- **Products** - Loan products
- **Agents** - AI loan officers
- **ML** - Credit scoring models
- **RL** - Loan pricing optimization

**Key Files:**
- [`models/loan.py`](../../src/ultracore/domains/lending/models/loan.py) - Loan aggregate
- [`origination/loan_application.py`](../../src/ultracore/domains/lending/origination/loan_application.py) - Application process
- [`ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py) - Credit risk models

---

### Client Domain

**Path:** [`src/ultracore/domains/client/`](../../src/ultracore/domains/client/)

**Components:**
- **Services** - Client services
- **Data Products** - Client data mesh products

**Key Files:**
- [`services/client_service.py`](../../src/ultracore/domains/client/services/client_service.py) - Client management
- [`data_products/client_360.py`](../../src/ultracore/domains/client/data_products/client_360.py) - Customer 360 view

**Documentation:** [Client Management](../modules/client-management.md)

---

### Payment Domain

**Path:** [`src/ultracore/domains/payments/`](../../src/ultracore/domains/payments/)

**Components:**
- **Models** - Payment aggregates
- **Events** - Payment events
- **Agents** - AI payment routing
- **Integrations** - Payment rails

**Key Files:**
- [`models/payment.py`](../../src/ultracore/domains/payments/models/payment.py) - Payment aggregate
- [`integrations/npp.py`](../../src/ultracore/domains/payments/integrations/npp.py) - NPP integration

---

### Onboarding Domain

**Path:** [`src/ultracore/domains/onboarding/`](../../src/ultracore/domains/onboarding/)

**Components:**
- **Models** - Onboarding aggregates
- **Events** - Onboarding events
- **Services** - Onboarding workflows
- **Agents** - AI onboarding assistants
- **ML** - Risk assessment models
- **MCP** - MCP tools

**Key Files:**
- [`models/onboarding_application.py`](../../src/ultracore/domains/onboarding/models/onboarding_application.py) - Application aggregate
- [`services/kyc_verification.py`](../../src/ultracore/domains/onboarding/services/kyc_verification.py) - KYC verification

---

### Collateral Domain

**Path:** [`src/ultracore/domains/collateral/`](../../src/ultracore/domains/collateral/)

**Components:**
- **Models** - Collateral aggregates
- **Events** - Collateral events
- **Services** - Valuation services
- **Agents** - AI valuation agents
- **ML** - Valuation models
- **Integrations** - External valuations

**Key Files:**
- [`models/collateral.py`](../../src/ultracore/domains/collateral/models/collateral.py) - Collateral aggregate
- [`services/valuation_service.py`](../../src/ultracore/domains/collateral/services/valuation_service.py) - Valuation engine

---

### Insurance Domain

**Path:** [`src/ultracore/domains/insurance/`](../../src/ultracore/domains/insurance/)

**Components:**
- **Models** - Insurance policy aggregates
- **Events** - Insurance events
- **Agents** - AI insurance advisors
- **ML** - Risk assessment models

**Key Files:**
- [`models/insurance_policy.py`](../../src/ultracore/domains/insurance/models/insurance_policy.py) - Policy aggregate

---

### Fixed Deposits Domain

**Path:** [`src/ultracore/domains/fixed_deposits/`](../../src/ultracore/domains/fixed_deposits/)

**Components:**
- **Models** - Fixed deposit aggregates
- **Events** - Deposit events
- **Services** - Interest calculation
- **Agents** - AI deposit advisors
- **ML** - Rate optimization models

---

### Recurring Deposits Domain

**Path:** [`src/ultracore/domains/recurring_deposits/`](../../src/ultracore/domains/recurring_deposits/)

**Components:**
- **Models** - Recurring deposit aggregates
- **Events** - Deposit events
- **Services** - Recurring payment processing

---

### Superannuation Domain

**Path:** [`src/ultracore/domains/superannuation/`](../../src/ultracore/domains/superannuation/)

**Components:**
- **Models** - Superannuation aggregates
- **Events** - Super events
- **Services** - Contribution processing
- **ML** - Retirement planning models

---

### Capsules Domain

**Path:** [`src/ultracore/domains/capsules/`](../../src/ultracore/domains/capsules/)

**Components:**
- **Models** - Investment capsule aggregates
- **Events** - Capsule events
- **Services** - Goal tracking
- **Agents** - AI goal advisors
- **ML** - Goal prediction models
- **RL** - Savings optimization

---

## 🎯 By Feature

### Event Sourcing

All domains use event sourcing with Kafka.

**Core Infrastructure:**
- [`infrastructure/event_store/`](../../src/ultracore/infrastructure/event_store/) - Event store implementation
- [`infrastructure/kafka_event_store/`](../../src/ultracore/infrastructure/kafka_event_store/) - Kafka-specific implementation
- [`events/`](../../src/ultracore/events/) - Base event classes

**Documentation:** [Event Sourcing Architecture](../architecture/event-sourcing.md)

---

### Data Mesh

Data mesh architecture with domain-oriented data products.

**Core Infrastructure:**
- [`data_mesh/platform/`](../../src/ultracore/data_mesh/platform/) - Data mesh platform
- [`data_mesh/catalog/`](../../src/ultracore/data_mesh/catalog/) - Data catalog
- [`data_mesh/governance/`](../../src/ultracore/data_mesh/governance/) - Data governance

**Domain Data Products:**
- [`domains/account/data_products/`](../../src/ultracore/domains/account/data_products/) - Account data products
- [`domains/loan/data_products/`](../../src/ultracore/domains/loan/data_products/) - Loan data products
- [`domains/payment/data_products/`](../../src/ultracore/domains/payment/data_products/) - Payment data products
- [`domains/risk/data_products/`](../../src/ultracore/domains/risk/data_products/) - Risk data products
- [`domains/client/data_products/`](../../src/ultracore/domains/client/data_products/) - Client data products

**Documentation:** [Data Mesh Architecture](../architecture/data-mesh.md)

---

### Agentic AI

AI agents with autonomous decision-making.

**Core Infrastructure:**
- [`agentic_ai/`](../../src/ultracore/agentic_ai/) - Agent system
- [`agents/`](../../src/ultracore/agents/) - Agent implementations

**Domain Agents:**
- [`domains/accounts/agents/`](../../src/ultracore/domains/accounts/agents/) - Account agents
- [`domains/wealth/agents/`](../../src/ultracore/domains/wealth/agents/) - Wealth agents
- [`domains/lending/agents/`](../../src/ultracore/domains/lending/agents/) - Lending agents
- [`domains/onboarding/agents/`](../../src/ultracore/domains/onboarding/agents/) - Onboarding agents
- [`domains/collateral/agents/`](../../src/ultracore/domains/collateral/agents/) - Collateral agents

**Documentation:** [Agentic AI Architecture](../architecture/agentic-ai.md)

---

### Machine Learning

ML models for predictions and optimization.

**Core Infrastructure:**
- [`ml_models/registry/`](../../src/ultracore/ml_models/registry/) - Model registry
- [`ml/`](../../src/ultracore/ml/) - ML utilities

**Domain ML Models:**
- [`domains/accounts/ml/`](../../src/ultracore/domains/accounts/ml/) - Account ML models
- [`domains/wealth/ml/`](../../src/ultracore/domains/wealth/ml/) - Wealth ML models
- [`domains/lending/ml/`](../../src/ultracore/domains/lending/ml/) - Lending ML models
- [`domains/onboarding/ml/`](../../src/ultracore/domains/onboarding/ml/) - Onboarding ML models

---

### Reinforcement Learning

RL models for optimization and decision-making.

**Domain RL Models:**
- [`domains/wealth/rl/`](../../src/ultracore/domains/wealth/rl/) - Portfolio optimization
- [`domains/lending/rl/`](../../src/ultracore/domains/lending/rl/) - Loan pricing
- [`domains/capsules/rl/`](../../src/ultracore/domains/capsules/rl/) - Savings optimization
- [`domains/collateral/rl/`](../../src/ultracore/domains/collateral/rl/) - Valuation optimization

---

### MCP Tools

Model Context Protocol tools for AI integration.

**Core Infrastructure:**
- [`mcp/`](../../src/ultracore/mcp/) - MCP tool registry
- [`agentic_ai/mcp_server.py`](../../src/ultracore/agentic_ai/mcp_server.py) - MCP server

**Domain MCP Tools:**
- [`domains/accounts/mcp/`](../../src/ultracore/domains/accounts/mcp/) - Account MCP tools
- [`domains/wealth/mcp/`](../../src/ultracore/domains/wealth/mcp/) - Wealth MCP tools
- [`domains/onboarding/mcp/`](../../src/ultracore/domains/onboarding/mcp/) - Onboarding MCP tools

**Documentation:** [MCP Tools](../api/mcp-tools.md)

---

## 📖 Alphabetical Index

| Module | Path | Documentation |
|--------|------|---------------|
| **Accounting** | [`src/ultracore/accounting/`](../../src/ultracore/accounting/) | [📖](../modules/accounting.md) |
| **Accounts** | [`src/ultracore/accounts/`](../../src/ultracore/accounts/) | [📖](../modules/savings.md) |
| **Agentic AI** | [`src/ultracore/agentic_ai/`](../../src/ultracore/agentic_ai/) | [📖](../api/mcp-tools.md) |
| **Agents** | [`src/ultracore/agents/`](../../src/ultracore/agents/) | - |
| **AI** | [`src/ultracore/ai/`](../../src/ultracore/ai/) | - |
| **API** | [`src/ultracore/api/`](../../src/ultracore/api/) | [📖](../api/rest-api.md) |
| **Audit** | [`src/ultracore/audit/`](../../src/ultracore/audit/) | - |
| **Business Logic** | [`src/ultracore/business_logic/`](../../src/ultracore/business_logic/) | - |
| **Cards** | [`src/ultracore/cards/`](../../src/ultracore/cards/) | - |
| **Compliance** | [`src/ultracore/compliance/`](../../src/ultracore/compliance/) | - |
| **Customer Service** | [`src/ultracore/customer_service/`](../../src/ultracore/customer_service/) | - |
| **Customers** | [`src/ultracore/customers/`](../../src/ultracore/customers/) | [📖](../modules/client-management.md) |
| **Data Mesh** | [`src/ultracore/data_mesh/`](../../src/ultracore/data_mesh/) | [📖](../architecture/data-mesh.md) |
| **Database** | [`src/ultracore/database/`](../../src/ultracore/database/) | - |
| **Document Management** | [`src/ultracore/document_management/`](../../src/ultracore/document_management/) | [📖](../modules/document-management.md) |
| **Documents** | [`src/ultracore/documents/`](../../src/ultracore/documents/) | - |
| **Domains** | [`src/ultracore/domains/`](../../src/ultracore/domains/) | - |
| **Events** | [`src/ultracore/events/`](../../src/ultracore/events/) | [📖](../architecture/event-sourcing.md) |
| **Extensibility** | [`src/ultracore/extensibility/`](../../src/ultracore/extensibility/) | - |
| **General Ledger** | [`src/ultracore/general_ledger/`](../../src/ultracore/general_ledger/) | - |
| **Infrastructure** | [`src/ultracore/infrastructure/`](../../src/ultracore/infrastructure/) | - |
| **Integrations** | [`src/ultracore/integrations/`](../../src/ultracore/integrations/) | - |
| **KYC** | [`src/ultracore/kyc/`](../../src/ultracore/kyc/) | - |
| **Ledger** | [`src/ultracore/ledger/`](../../src/ultracore/ledger/) | - |
| **Lending** | [`src/ultracore/lending/`](../../src/ultracore/lending/) | - |
| **MCP** | [`src/ultracore/mcp/`](../../src/ultracore/mcp/) | [📖](../api/mcp-tools.md) |
| **Mesh** | [`src/ultracore/mesh/`](../../src/ultracore/mesh/) | - |
| **ML** | [`src/ultracore/ml/`](../../src/ultracore/ml/) | - |
| **ML Models** | [`src/ultracore/ml_models/`](../../src/ultracore/ml_models/) | - |
| **Notifications** | [`src/ultracore/notifications/`](../../src/ultracore/notifications/) | [📖](../modules/notifications.md) |
| **Open Banking** | [`src/ultracore/openbanking/`](../../src/ultracore/openbanking/) | - |
| **Payments** | [`src/ultracore/payments/`](../../src/ultracore/payments/) | - |
| **Reporting** | [`src/ultracore/reporting/`](../../src/ultracore/reporting/) | [📖](../modules/financial-reporting.md) |
| **Rules** | [`src/ultracore/rules/`](../../src/ultracore/rules/) | - |
| **Security** | [`src/ultracore/security/`](../../src/ultracore/security/) | [📖](../modules/permissions.md) |
| **Temporal** | [`src/ultracore/temporal/`](../../src/ultracore/temporal/) | - |

---

## 🔍 Finding Code

### By Functionality

**Need to work on accounts?**
- Start with [`domains/accounts/`](../../src/ultracore/domains/accounts/) for domain logic
- Check [`accounts/`](../../src/ultracore/accounts/) for legacy code
- See [`api/routers/accounts.py`](../../src/ultracore/api/routers/) for REST API

**Need to work on loans?**
- Start with [`domains/lending/`](../../src/ultracore/domains/lending/) for domain logic
- Check [`lending/`](../../src/ultracore/lending/) for legacy code
- See [`business_logic/loans/`](../../src/ultracore/business_logic/loans/) for business rules

**Need to work on investments?**
- Start with [`domains/wealth/`](../../src/ultracore/domains/wealth/) for domain logic
- Check [`agents/investment_agents.py`](../../src/ultracore/agents/investment_agents.py) for AI agents
- See [`integrations/openmarkets/`](../../src/ultracore/integrations/openmarkets/) for trading

**Need to work on payments?**
- Start with [`domains/payments/`](../../src/ultracore/domains/payments/) for domain logic
- Check [`payments/`](../../src/ultracore/payments/) for payment rails
- See [`payments/npp/`](../../src/ultracore/payments/npp/) for NPP integration

---

## 📚 Additional Resources

- **[Architecture Documentation](../architecture/README.md)** - System architecture
- **[API Documentation](../api/README.md)** - REST API and MCP tools
- **[Module Documentation](../modules/README.md)** - Module guides
- **[Code Navigation Guide](code-navigation-guide.md)** - How to navigate the codebase

---

**Last Updated:** November 14, 2024

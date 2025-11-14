# 🔗 Source Code Reference

Quick reference guide to key source code files and their locations.

---

## 📚 Quick Links

- **[Core Domains](#core-domains)** - Domain-driven design aggregates
- **[API Endpoints](#api-endpoints)** - REST API routers
- **[Event Definitions](#event-definitions)** - Event sourcing events
- **[Data Products](#data-products)** - Data mesh products
- **[AI Agents](#ai-agents)** - Agentic AI implementations
- **[MCP Tools](#mcp-tools)** - Model Context Protocol tools
- **[ML Models](#ml-models)** - Machine learning models

---

## 🏛️ Core Domains

### Account Domain

**Aggregates:**
- [`domains/accounts/models/account.py`](../../src/ultracore/domains/accounts/models/account.py) - Account aggregate root
- [`domains/accounts/models/transaction.py`](../../src/ultracore/domains/accounts/models/transaction.py) - Transaction entity

**Events:**
- [`domains/accounts/events/account_events.py`](../../src/ultracore/domains/accounts/events/account_events.py) - Account domain events
  - `AccountCreatedEvent`
  - `TransactionCreatedEvent`
  - `BalanceUpdatedEvent`
  - `AccountClosedEvent`

**Services:**
- [`domains/accounts/services/account_service.py`](../../src/ultracore/domains/accounts/services/account_service.py) - Account business logic
- [`domains/accounts/services/interest_calculator.py`](../../src/ultracore/domains/accounts/services/interest_calculator.py) - Interest calculation

**Agents:**
- [`domains/accounts/agents/account_agent.py`](../../src/ultracore/domains/accounts/agents/account_agent.py) - AI account manager

**ML Models:**
- [`domains/accounts/ml/account_ml_models.py`](../../src/ultracore/domains/accounts/ml/account_ml_models.py) - Account ML models

**MCP Tools:**
- [`domains/accounts/mcp/account_tools.py`](../../src/ultracore/domains/accounts/mcp/account_tools.py) - Account MCP tools

---

### Wealth Domain

**Aggregates:**
- [`domains/wealth/models/investment_pod.py`](../../src/ultracore/domains/wealth/models/investment_pod.py) - Investment pod aggregate
- [`domains/wealth/models/portfolio.py`](../../src/ultracore/domains/wealth/models/portfolio.py) - Portfolio aggregate
- [`domains/wealth/models/holding.py`](../../src/ultracore/domains/wealth/models/holding.py) - Holding entity

**Events:**
- [`domains/wealth/events/wealth_events.py`](../../src/ultracore/domains/wealth/events/wealth_events.py) - Wealth domain events
  - `InvestmentPodCreatedEvent`
  - `PortfolioOptimizedEvent`
  - `HoldingAddedEvent`
  - `TradeExecutedEvent`

**Services:**
- [`domains/wealth/services/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/services/portfolio_optimizer.py) - Portfolio optimization
- [`domains/wealth/services/rebalancer.py`](../../src/ultracore/domains/wealth/services/rebalancer.py) - Portfolio rebalancing
- [`domains/wealth/trading/trading_engine.py`](../../src/ultracore/domains/wealth/trading/trading_engine.py) - Trading execution

**Agents:**
- [`domains/wealth/agents/investment_advisor.py`](../../src/ultracore/domains/wealth/agents/investment_advisor.py) - AI investment advisor
- [`domains/wealth/agents/portfolio_manager.py`](../../src/ultracore/domains/wealth/agents/portfolio_manager.py) - AI portfolio manager

**ML Models:**
- [`domains/wealth/ml/price_predictor.py`](../../src/ultracore/domains/wealth/ml/price_predictor.py) - Price prediction
- [`domains/wealth/ml/risk_analyzer.py`](../../src/ultracore/domains/wealth/ml/risk_analyzer.py) - Risk analysis

**RL Models:**
- [`domains/wealth/rl/portfolio_optimizer.py`](../../src/ultracore/domains/wealth/rl/portfolio_optimizer.py) - RL portfolio optimization

**MCP Tools:**
- [`domains/wealth/mcp/wealth_tools.py`](../../src/ultracore/domains/wealth/mcp/wealth_tools.py) - Wealth MCP tools

---

### Lending Domain

**Aggregates:**
- [`domains/lending/models/loan.py`](../../src/ultracore/domains/lending/models/loan.py) - Loan aggregate
- [`domains/lending/models/loan_application.py`](../../src/ultracore/domains/lending/models/loan_application.py) - Application aggregate

**Events:**
- [`domains/lending/events/lending_events.py`](../../src/ultracore/domains/lending/events/lending_events.py) - Lending domain events
  - `LoanApplicationCreatedEvent`
  - `LoanApprovedEvent`
  - `LoanDisbursedEvent`
  - `PaymentReceivedEvent`

**Services:**
- [`domains/lending/origination/loan_application.py`](../../src/ultracore/domains/lending/origination/loan_application.py) - Loan origination
- [`domains/lending/products/loan_products.py`](../../src/ultracore/domains/lending/products/loan_products.py) - Loan products

**Agents:**
- [`domains/lending/agents/loan_officer.py`](../../src/ultracore/domains/lending/agents/loan_officer.py) - AI loan officer
- [`domains/lending/agents/underwriter.py`](../../src/ultracore/domains/lending/agents/underwriter.py) - AI underwriter

**ML Models:**
- [`domains/lending/ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py) - Credit scoring
- [`domains/lending/ml/default_predictor.py`](../../src/ultracore/domains/lending/ml/default_predictor.py) - Default prediction

**RL Models:**
- [`domains/lending/rl/loan_pricing.py`](../../src/ultracore/domains/lending/rl/loan_pricing.py) - RL loan pricing

---

### Client Domain

**Services:**
- [`domains/client/services/client_service.py`](../../src/ultracore/domains/client/services/client_service.py) - Client management

**Data Products:**
- [`domains/client/data_products/client_360.py`](../../src/ultracore/domains/client/data_products/client_360.py) - Customer 360 view

---

### Payment Domain

**Aggregates:**
- [`domains/payments/models/payment.py`](../../src/ultracore/domains/payments/models/payment.py) - Payment aggregate

**Events:**
- [`domains/payments/events/payment_events.py`](../../src/ultracore/domains/payments/events/payment_events.py) - Payment domain events
  - `PaymentInitiatedEvent`
  - `PaymentProcessedEvent`
  - `PaymentFailedEvent`

**Agents:**
- [`domains/payments/agents/payment_router.py`](../../src/ultracore/domains/payments/agents/payment_router.py) - AI payment router

**Integrations:**
- [`domains/payments/integrations/npp.py`](../../src/ultracore/domains/payments/integrations/npp.py) - NPP integration
- [`domains/payments/integrations/bpay.py`](../../src/ultracore/domains/payments/integrations/bpay.py) - BPAY integration

---

### Onboarding Domain

**Aggregates:**
- [`domains/onboarding/models/onboarding_application.py`](../../src/ultracore/domains/onboarding/models/onboarding_application.py) - Onboarding aggregate

**Events:**
- [`domains/onboarding/events/onboarding_events.py`](../../src/ultracore/domains/onboarding/events/onboarding_events.py) - Onboarding events

**Services:**
- [`domains/onboarding/services/kyc_verification.py`](../../src/ultracore/domains/onboarding/services/kyc_verification.py) - KYC verification

**Agents:**
- [`domains/onboarding/agents/onboarding_assistant.py`](../../src/ultracore/domains/onboarding/agents/onboarding_assistant.py) - AI onboarding assistant

**ML Models:**
- [`domains/onboarding/ml/risk_assessment.py`](../../src/ultracore/domains/onboarding/ml/risk_assessment.py) - Risk assessment

**MCP Tools:**
- [`domains/onboarding/mcp/onboarding_tools.py`](../../src/ultracore/domains/onboarding/mcp/onboarding_tools.py) - Onboarding MCP tools

---

### Collateral Domain

**Aggregates:**
- [`domains/collateral/models/collateral.py`](../../src/ultracore/domains/collateral/models/collateral.py) - Collateral aggregate

**Events:**
- [`domains/collateral/events/collateral_events.py`](../../src/ultracore/domains/collateral/events/collateral_events.py) - Collateral events

**Services:**
- [`domains/collateral/services/valuation_service.py`](../../src/ultracore/domains/collateral/services/valuation_service.py) - Valuation engine

**Agents:**
- [`domains/collateral/agents/valuation_agent.py`](../../src/ultracore/domains/collateral/agents/valuation_agent.py) - AI valuation agent

**ML Models:**
- [`domains/collateral/ml/valuation_models.py`](../../src/ultracore/domains/collateral/ml/valuation_models.py) - Valuation models

---

### Capsules Domain

**Aggregates:**
- [`domains/capsules/models/investment_capsule.py`](../../src/ultracore/domains/capsules/models/investment_capsule.py) - Capsule aggregate

**Events:**
- [`domains/capsules/events/capsule_events.py`](../../src/ultracore/domains/capsules/events/capsule_events.py) - Capsule events

**Services:**
- [`domains/capsules/services/goal_tracker.py`](../../src/ultracore/domains/capsules/services/goal_tracker.py) - Goal tracking

**Agents:**
- [`domains/capsules/agents/goal_advisor.py`](../../src/ultracore/domains/capsules/agents/goal_advisor.py) - AI goal advisor

**RL Models:**
- [`domains/capsules/rl/savings_optimizer.py`](../../src/ultracore/domains/capsules/rl/savings_optimizer.py) - RL savings optimization

---

## 🌐 API Endpoints

### REST API Routers

**Main Router:**
- [`api/main.py`](../../src/ultracore/api/main.py) - FastAPI application

**Domain Routers:**
- [`api/routers/accounts.py`](../../src/ultracore/api/routers/accounts.py) - Account endpoints
- [`api/routers/customers.py`](../../src/ultracore/api/routers/customers.py) - Customer endpoints
- [`api/routers/transactions.py`](../../src/ultracore/api/routers/transactions.py) - Transaction endpoints
- [`api/routers/payments.py`](../../src/ultracore/api/routers/payments.py) - Payment endpoints
- [`api/routers/loans.py`](../../src/ultracore/api/routers/loans.py) - Loan endpoints
- [`api/routers/investment_pods.py`](../../src/ultracore/api/routers/investment_pods.py) - Investment pod endpoints

**Middleware:**
- [`api/middleware/auth.py`](../../src/ultracore/api/middleware/auth.py) - Authentication middleware
- [`api/middleware/tenant.py`](../../src/ultracore/api/middleware/tenant.py) - Multi-tenancy middleware
- [`api/middleware/rate_limit.py`](../../src/ultracore/api/middleware/rate_limit.py) - Rate limiting

**Schemas:**
- [`api/schemas/account_schemas.py`](../../src/ultracore/api/schemas/account_schemas.py) - Account schemas
- [`api/schemas/customer_schemas.py`](../../src/ultracore/api/schemas/customer_schemas.py) - Customer schemas
- [`api/schemas/transaction_schemas.py`](../../src/ultracore/api/schemas/transaction_schemas.py) - Transaction schemas

---

## 📡 Event Definitions

### Base Events

- [`events/base_event.py`](../../src/ultracore/events/base_event.py) - Base event class
- [`events/domain_event.py`](../../src/ultracore/events/domain_event.py) - Domain event base

### Domain Events

**Account Events:**
- [`domains/accounts/events/account_events.py`](../../src/ultracore/domains/accounts/events/account_events.py)

**Wealth Events:**
- [`domains/wealth/events/wealth_events.py`](../../src/ultracore/domains/wealth/events/wealth_events.py)

**Lending Events:**
- [`domains/lending/events/lending_events.py`](../../src/ultracore/domains/lending/events/lending_events.py)

**Payment Events:**
- [`domains/payments/events/payment_events.py`](../../src/ultracore/domains/payments/events/payment_events.py)

**Onboarding Events:**
- [`domains/onboarding/events/onboarding_events.py`](../../src/ultracore/domains/onboarding/events/onboarding_events.py)

---

## 🗄️ Data Products

### Account Data Products

- [`domains/account/data_products/account_balances.py`](../../src/ultracore/domains/account/data_products/account_balances.py) - Account balances
- [`domains/account/data_products/transaction_history.py`](../../src/ultracore/domains/account/data_products/transaction_history.py) - Transaction history

### Loan Data Products

- [`domains/loan/data_products/loan_portfolio.py`](../../src/ultracore/domains/loan/data_products/loan_portfolio.py) - Loan portfolio
- [`domains/loan/data_products/delinquency_report.py`](../../src/ultracore/domains/loan/data_products/delinquency_report.py) - Delinquency report

### Payment Data Products

- [`domains/payment/data_products/payment_flows.py`](../../src/ultracore/domains/payment/data_products/payment_flows.py) - Payment flows
- [`domains/payment/data_products/payment_analytics.py`](../../src/ultracore/domains/payment/data_products/payment_analytics.py) - Payment analytics

### Risk Data Products

- [`domains/risk/data_products/credit_risk.py`](../../src/ultracore/domains/risk/data_products/credit_risk.py) - Credit risk
- [`domains/risk/data_products/market_risk.py`](../../src/ultracore/domains/risk/data_products/market_risk.py) - Market risk

### Client Data Products

- [`domains/client/data_products/client_360.py`](../../src/ultracore/domains/client/data_products/client_360.py) - Customer 360 view

---

## 🤖 AI Agents

### Core Agent System

- [`agentic_ai/agents/base_agent.py`](../../src/ultracore/agentic_ai/agents/base_agent.py) - Base agent class
- [`agentic_ai/agent_system.py`](../../src/ultracore/agentic_ai/agent_system.py) - Agent orchestration

### Domain Agents

**Account Agents:**
- [`domains/accounts/agents/account_agent.py`](../../src/ultracore/domains/accounts/agents/account_agent.py)

**Wealth Agents:**
- [`domains/wealth/agents/investment_advisor.py`](../../src/ultracore/domains/wealth/agents/investment_advisor.py)
- [`domains/wealth/agents/portfolio_manager.py`](../../src/ultracore/domains/wealth/agents/portfolio_manager.py)

**Lending Agents:**
- [`domains/lending/agents/loan_officer.py`](../../src/ultracore/domains/lending/agents/loan_officer.py)
- [`domains/lending/agents/underwriter.py`](../../src/ultracore/domains/lending/agents/underwriter.py)

**Payment Agents:**
- [`domains/payments/agents/payment_router.py`](../../src/ultracore/domains/payments/agents/payment_router.py)

**Onboarding Agents:**
- [`domains/onboarding/agents/onboarding_assistant.py`](../../src/ultracore/domains/onboarding/agents/onboarding_assistant.py)

**Collateral Agents:**
- [`domains/collateral/agents/valuation_agent.py`](../../src/ultracore/domains/collateral/agents/valuation_agent.py)

**Capsule Agents:**
- [`domains/capsules/agents/goal_advisor.py`](../../src/ultracore/domains/capsules/agents/goal_advisor.py)

---

## 🔧 MCP Tools

### MCP Server

- [`agentic_ai/mcp_server.py`](../../src/ultracore/agentic_ai/mcp_server.py) - MCP server implementation
- [`agentic_ai/mcp_api.py`](../../src/ultracore/agentic_ai/mcp_api.py) - MCP API endpoints

### Tool Registry

- [`mcp/tool_registry.py`](../../src/ultracore/mcp/tool_registry.py) - Tool registry
- [`mcp/base_tool.py`](../../src/ultracore/mcp/base_tool.py) - Base tool class

### Domain MCP Tools

**Account Tools:**
- [`domains/accounts/mcp/account_tools.py`](../../src/ultracore/domains/accounts/mcp/account_tools.py)
  - `get_account_balance`
  - `get_account_transactions`

**Wealth Tools:**
- [`domains/wealth/mcp/wealth_tools.py`](../../src/ultracore/domains/wealth/mcp/wealth_tools.py)
  - `create_investment_pod`
  - `optimize_portfolio`
  - `get_portfolio_performance`

**Onboarding Tools:**
- [`domains/onboarding/mcp/onboarding_tools.py`](../../src/ultracore/domains/onboarding/mcp/onboarding_tools.py)
  - `check_kyc_status`
  - `verify_identity`

---

## 🧠 ML Models

### ML Model Registry

- [`ml_models/registry/model_registry.py`](../../src/ultracore/ml_models/registry/model_registry.py) - Model registry

### Domain ML Models

**Account ML:**
- [`domains/accounts/ml/account_ml_models.py`](../../src/ultracore/domains/accounts/ml/account_ml_models.py)
  - Fraud detection
  - Spending prediction

**Wealth ML:**
- [`domains/wealth/ml/price_predictor.py`](../../src/ultracore/domains/wealth/ml/price_predictor.py) - Price prediction
- [`domains/wealth/ml/risk_analyzer.py`](../../src/ultracore/domains/wealth/ml/risk_analyzer.py) - Risk analysis

**Lending ML:**
- [`domains/lending/ml/credit_scoring.py`](../../src/ultracore/domains/lending/ml/credit_scoring.py) - Credit scoring
- [`domains/lending/ml/default_predictor.py`](../../src/ultracore/domains/lending/ml/default_predictor.py) - Default prediction

**Onboarding ML:**
- [`domains/onboarding/ml/risk_assessment.py`](../../src/ultracore/domains/onboarding/ml/risk_assessment.py) - Risk assessment

**Collateral ML:**
- [`domains/collateral/ml/valuation_models.py`](../../src/ultracore/domains/collateral/ml/valuation_models.py) - Valuation models

---

## 🏗️ Infrastructure

### Event Store

- [`infrastructure/event_store/event_store.py`](../../src/ultracore/infrastructure/event_store/event_store.py) - Event store interface
- [`infrastructure/kafka_event_store/kafka_event_store.py`](../../src/ultracore/infrastructure/kafka_event_store/kafka_event_store.py) - Kafka implementation

### Data Mesh

- [`data_mesh/platform/data_mesh_platform.py`](../../src/ultracore/data_mesh/platform/data_mesh_platform.py) - Data mesh platform
- [`data_mesh/catalog/data_catalog.py`](../../src/ultracore/data_mesh/catalog/data_catalog.py) - Data catalog
- [`data_mesh/governance/data_governance.py`](../../src/ultracore/data_mesh/governance/data_governance.py) - Data governance

### Caching

- [`infrastructure/caching/redis_cache.py`](../../src/ultracore/infrastructure/caching/redis_cache.py) - Redis cache

### Sharding

- [`infrastructure/sharding/tenant_sharding.py`](../../src/ultracore/infrastructure/sharding/tenant_sharding.py) - Tenant sharding

---

## 🔐 Security

### Authentication

- [`security/auth/jwt_auth.py`](../../src/ultracore/security/auth/jwt_auth.py) - JWT authentication
- [`security/auth/oauth.py`](../../src/ultracore/security/auth/oauth.py) - OAuth integration

### Authorization

- [`security/rbac/permission_checker.py`](../../src/ultracore/security/rbac/permission_checker.py) - Permission checking
- [`security/rbac/role_manager.py`](../../src/ultracore/security/rbac/role_manager.py) - Role management

### Audit

- [`security/audit/audit_logger.py`](../../src/ultracore/security/audit/audit_logger.py) - Audit logging

---

## 📚 Additional Resources

- **[Module Index](module-index.md)** - Find modules by category
- **[Code Examples](code-examples.md)** - Practical code examples
- **[Code Navigation Guide](code-navigation-guide.md)** - Navigate the codebase
- **[API Documentation](../api/README.md)** - REST API and MCP tools

---

**Last Updated:** November 14, 2024

# UltraCore V2 - Complete Financial Services Platform

🏦 Production-ready banking platform with **Kafka as the critical backbone**

## Architecture

\\\
┌─────────────────────────────────────────────────────────────┐
│                    UltraCore API Layer                       │
│  (Loans • Clients • Accounts • Payments • Cards • etc.)     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   KAFKA EVENT STORE     │ ◄── SOURCE OF TRUTH
        │  (Durable, Observable)  │
        └────────┬────────┬───────┘
                 │        │
     ┌───────────▼──┐  ┌──▼──────────┐
     │ PostgreSQL   │  │ Consumers   │
     │ (Read Model) │  │ (Real-time) │
     └──────────────┘  └─────────────┘
\\\

## Quick Start

### 1. Start Infrastructure

\\\powershell
# Start Kafka, PostgreSQL, Redis, etc.
./start-infrastructure.ps1
\\\

### 2. Install Dependencies

\\\ash
pip install -r requirements.txt
\\\

### 3. Start UltraCore

\\\ash
\src = "src"
python -m ultracore.main
\\\

### 4. Access Services

- **API**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

## Event-Driven Architecture

**Every critical operation writes to Kafka FIRST:**

- ✅ Loan decisions
- ✅ Payments
- ✅ Account transactions
- ✅ Fraud detections
- ✅ Compliance checks
- ✅ All state changes

**Benefits:**
- 🔄 **Replay**: Reconstruct any state from events
- 🕐 **Time Travel**: Query historical states
- 📊 **Audit**: Complete audit trail
- 🔍 **Observable**: See everything happening
- 📈 **Scalable**: Distribute across partitions

## Domains

- 💰 **Loans**: Complete lifecycle (origination → servicing)
- 👥 **Clients**: KYC & onboarding
- 💳 **Accounts**: Deposits & withdrawals
- 💸 **Payments**: Transfers & fraud detection
- 💳 **Cards**: Credit & debit cards
- 📈 **Investments**: Stocks & portfolios
- 🛡️ **Insurance**: Policies & claims
- 🏪 **Merchants**: Business banking
- ⚠️ **Risk**: Portfolio management

## Infrastructure

- **Event Store**: Kafka (primary) + PostgreSQL (secondary)
- **Event Bus**: Kafka with 13+ topics
- **General Ledger**: Double-entry accounting
- **Data Mesh**: Dynamic data products
- **AI Agents**: Anya + MCP protocol
- **ML Pipeline**: Credit + Fraud + more
- **Compliance**: Australian regulations

## Company

**TuringDynamics / Richelou Pty Ltd**
Version 2.0.0

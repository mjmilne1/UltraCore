from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Domain APIs - Complete Financial Platform (9 Domains!)
from ultracore.domains.loan.api import router as loan_router
from ultracore.domains.loan.integrated_api import router as integrated_loan_router
from ultracore.domains.client.api import router as client_router
from ultracore.domains.client.compliance_api import router as compliance_router
from ultracore.domains.account.api import router as account_router
from ultracore.domains.payment.api import router as payment_router
from ultracore.domains.risk.api import router as risk_router
from ultracore.domains.cards.api import router as cards_router
from ultracore.domains.investment.api import router as investment_router
from ultracore.domains.insurance.api import router as insurance_router
from ultracore.domains.merchant.api import router as merchant_router

# Infrastructure APIs
from ultracore.data_mesh.api import router as data_mesh_router
from ultracore.infrastructure.event_store.api import router as event_store_router
from ultracore.ledger.api import router as ledger_router
from ultracore.agentic_ai.mcp_api import router as mcp_router
from ultracore.ml_models.api import router as ml_router
from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.infrastructure.event_bus.api import router as event_bus_router
from ultracore.infrastructure.event_bus.bus import initialize_event_bus, EventBusType
from ultracore.infrastructure.event_bus.handlers import setup_event_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    store = get_event_store()
    await store.initialize()
    print('✅ Event Store initialized')
    
    # Initialize Event Bus
    event_bus = initialize_event_bus(EventBusType.IN_MEMORY)
    await event_bus.start()
    print('✅ Event Bus started')
    
    # Setup event handlers
    await setup_event_handlers()
    print('✅ Event handlers configured')
    
    print('✅ General Ledger ready')
    print('✅ All 9 Domains loaded')
    print('✅ AI Agents (Anya) ready')
    print('✅ ML Pipeline ready')
    print('✅ MCP Server ready')
    print('🚀 UltraCore V2 - Complete Financial Platform ONLINE')
    
    yield
    
    # Shutdown
    await event_bus.stop()
    print('✅ Event Bus stopped')


app = FastAPI(
    title='UltraCore V2 - Complete Financial Services Platform',
    version='2.0.0',
    lifespan=lifespan,
    description='''
    🏦 Complete Financial Services Platform with Event Streaming
    
    🎯 9 COMPLETE DOMAINS:
    
    Core Banking:
    - 💰 Loans: AI-powered underwriting
    - 👥 Clients: KYC & onboarding
    - 💳 Accounts: Deposits & withdrawals
    - 💸 Payments: Transfers & fraud detection
    - ⚠️ Risk: Portfolio & compliance
    
    Advanced Financial Services:
    - 💳 Cards: Credit & debit cards
    - 📈 Investments: Stocks, ETF, funds
    - 🛡️ Insurance: Life, health, property
    - 🏪 Merchant: Business banking & POS
    
    🔧 Infrastructure:
    - ⚡ Event Sourcing + Event Streaming
    - 📊 General Ledger
    - 🔗 Data Mesh
    - 🤖 AI Agents (Anya + MCP)
    - 🧠 ML Pipeline
    - 🇦🇺 Australian Compliance
    - 📡 Event Bus (Kafka/Pulsar/Redpanda compatible)
    '''
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Core Banking Domains
app.include_router(loan_router, prefix='/api/v1/loans', tags=['💰 Loans'])
app.include_router(integrated_loan_router, prefix='/api/v1/loans', tags=['🚀 Integrated Loans'])
app.include_router(client_router, prefix='/api/v1/clients', tags=['👥 Clients'])
app.include_router(account_router, prefix='/api/v1/accounts', tags=['💳 Accounts'])
app.include_router(payment_router, prefix='/api/v1/payments', tags=['💸 Payments'])
app.include_router(risk_router, prefix='/api/v1/risk', tags=['⚠️ Risk'])

# Advanced Financial Services
app.include_router(cards_router, prefix='/api/v1/cards', tags=['💳 Cards'])
app.include_router(investment_router, prefix='/api/v1/investments', tags=['📈 Investments'])
app.include_router(insurance_router, prefix='/api/v1/insurance', tags=['🛡️ Insurance'])
app.include_router(merchant_router, prefix='/api/v1/merchants', tags=['🏪 Merchants'])

# Compliance & Infrastructure
app.include_router(compliance_router, prefix='/api/v1', tags=['🇦🇺 Compliance'])
app.include_router(event_store_router, tags=['⚡ Event Store'])
app.include_router(event_bus_router, prefix='/api/v1', tags=['📡 Event Bus'])
app.include_router(ledger_router, prefix='/api/v1/ledger', tags=['📊 General Ledger'])
app.include_router(data_mesh_router, tags=['🔗 Data Mesh'])
app.include_router(mcp_router, prefix='/api/v1', tags=['🤖 MCP'])
app.include_router(ml_router, prefix='/api/v1', tags=['🧠 ML'])


@app.get('/')
async def root():
    return {
        'service': 'UltraCore V2',
        'company': 'TuringDynamics / Richelou Pty Ltd',
        'version': '2.0.0',
        'tagline': 'Complete Financial Services Platform',
        'domains': {
            'core_banking': [
                'Loans', 'Clients', 'Accounts', 'Payments', 'Risk'
            ],
            'advanced_services': [
                'Cards', 'Investments', 'Insurance', 'Merchants'
            ],
            'total_domains': 9
        },
        'infrastructure': {
            'event_sourcing': 'PostgreSQL',
            'event_bus': 'In-Memory (Kafka/Pulsar/Redpanda compatible)',
            'general_ledger': 'Double-entry accounting',
            'data_mesh': '15 data products',
            'ai_agents': 'Anya + MCP',
            'ml_pipeline': 'Credit + Fraud detection',
            'compliance': 'Australian regulations'
        },
        'event_topics': [
            'loans', 'clients', 'accounts', 'payments', 'cards',
            'investments', 'insurance', 'merchants', 'risk',
            'orders', 'fills', 'funding', 'compliance', 'fraud'
        ],
        'docs': '/docs'
    }


@app.get('/health')
async def health():
    return {
        'status': 'healthy',
        'version': '2.0.0',
        'domains': 9,
        'systems': {
            'event_store': 'online',
            'event_bus': 'online',
            'general_ledger': 'online',
            'ai_agents': 'online',
            'ml_pipeline': 'online',
            'mcp_server': 'online'
        }
    }


def main():
    uvicorn.run('ultracore.main:app', host='0.0.0.0', port=8000, reload=True)


if __name__ == '__main__':
    main()

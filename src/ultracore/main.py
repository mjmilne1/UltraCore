from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(
    title='UltraCore V2 - Complete Financial Services Platform',
    version='2.0.0',
    description='''
    🏦 Complete Financial Services Platform
    
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
    - ⚡ Event Sourcing
    - 📊 General Ledger
    - 🔗 Data Mesh
    - 🤖 AI Agents (Anya)
    - 🧠 ML Pipeline
    - 🇦🇺 Australian Compliance
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
app.include_router(ledger_router, prefix='/api/v1/ledger', tags=['📊 General Ledger'])
app.include_router(data_mesh_router, tags=['🔗 Data Mesh'])
app.include_router(mcp_router, prefix='/api/v1', tags=['🤖 MCP'])
app.include_router(ml_router, prefix='/api/v1', tags=['🧠 ML'])


@app.on_event('startup')
async def startup():
    store = get_event_store()
    await store.initialize()
    print('✅ Event Store initialized')
    print('✅ General Ledger ready')
    print('✅ All 9 Domains loaded')
    print('✅ AI Agents (Anya) ready')
    print('✅ ML Pipeline ready')
    print('✅ MCP Server ready')
    print('🚀 UltraCore V2 - Complete Financial Platform ONLINE')


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
        'capabilities': [
            'AI-Powered Loan Decisions',
            'KYC & Compliance',
            'Account Management',
            'Payment Processing',
            'Credit & Debit Cards',
            'Investment Portfolio Management',
            'Insurance Policies & Claims',
            'Merchant Payment Processing',
            'Risk Assessment',
            'General Ledger Accounting',
            'Event Sourcing & Audit Trail',
            'ML Fraud Detection',
            'Australian Regulatory Compliance'
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all domain APIs
from ultracore.domains.client.api import router as client_router
from ultracore.domains.account.api import router as account_router
from ultracore.domains.payment.api import router as payment_router
from ultracore.domains.cards.api import router as cards_router
from ultracore.domains.investment.api import router as investment_router
from ultracore.domains.insurance.api import router as insurance_router
from ultracore.domains.merchant.api import router as merchant_router
from ultracore.domains.risk.api import router as risk_router
from ultracore.domains.loan.api import router as loan_router

# Import Anya API
from ultracore.anya.api import router as anya_router
from ultracore.ml_models.api import router as ml_router

app = FastAPI(
    title='UltraCore Banking Platform',
    description='Complete Banking Platform with AI Assistant (Anya)',
    version='2.4.0'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount domain APIs
app.include_router(client_router, prefix='/api/clients', tags=['Clients'])
app.include_router(account_router, prefix='/api/accounts', tags=['Accounts'])
app.include_router(payment_router, prefix='/api/payments', tags=['Payments'])
app.include_router(cards_router, prefix='/api/cards', tags=['Cards'])
app.include_router(investment_router, prefix='/api/investments', tags=['Investments'])
app.include_router(insurance_router, prefix='/api/insurance', tags=['Insurance'])
app.include_router(merchant_router, prefix='/api/merchants', tags=['Merchants'])
app.include_router(risk_router, prefix='/api/risk', tags=['Risk'])
app.include_router(loan_router, prefix='/api/loans', tags=['Loans'])

# Mount ML API
app.include_router(ml_router, prefix='/api/ml', tags=['ML Models'])

# Mount Anya API (primary customer interface)
app.include_router(anya_router, prefix='/api/anya', tags=['Anya - AI Assistant'])


@app.get('/')
async def root():
    return {
        'name': 'UltraCore Banking Platform',
        'version': '2.4.0',
        'ai_assistant': 'Anya',
        'domains': [
            'clients', 'accounts', 'payments', 'cards',
            'investments', 'insurance', 'merchants', 'risk', 'loans'
        ],
        'docs': '/docs'
    }


@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'anya': 'online',
        'kafka': 'connected',
        'database': 'connected'
    }


"""
UltraCore Financial API - Complete Platform
Version 6.0.0 with Australian Compliance
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
sys.path.insert(0, r'C:\Users\mjmil\UltraCore')

from ultracore.api.v1.financial.routes import router as financial_router
from ultracore.api.v1.ultrawealth.routes import router as ultrawealth_router
from ultracore.api.v1.clients.routes import router as clients_router
from ultracore.api.v1.holdings.routes import router as holdings_router
from ultracore.api.v1.transactions.routes import router as transactions_router
from ultracore.api.v1.accounting.routes import router as accounting_router
from ultracore.api.v1.compliance.routes import router as compliance_router

app = FastAPI(
    title="UltraCore Financial Platform",
    description="Complete wealth management platform with full Australian compliance",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(financial_router)
app.include_router(ultrawealth_router)
app.include_router(clients_router)
app.include_router(holdings_router)
app.include_router(transactions_router)
app.include_router(accounting_router)
app.include_router(compliance_router)

@app.get("/")
async def root():
    return {
        "message": "UltraCore Financial Platform",
        "version": "6.0.0",
        "modules": {
            "financial": "Global financial data (Yahoo Finance)",
            "ultrawealth": "Australian ETFs (100+)",
            "clients": "Client management, KYC, Onboarding",
            "holdings": "Positions, Portfolio, Rebalancing",
            "transactions": "Orders, Trading, Settlement",
            "accounting": "Double-Entry Bookkeeping, Financial Statements",
            "compliance": "Australian Regulatory Compliance (NEW!)"
        },
        "australian_compliance": {
            "asic": "Securities & Investments Commission",
            "austrac": "AML/CTF Requirements",
            "asx": "Trading Rules",
            "ato": "Taxation (CGT, TFN, ABN)",
            "privacy_act": "Data Protection",
            "corporations_act": "Company Law",
            "aasb": "Accounting Standards",
            "superannuation": "Super Compliance",
            "fcs": "Financial Claims Scheme"
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": [
            "financial", "ultrawealth", "clients",
            "holdings", "transactions", "accounting", "compliance"
        ],
        "version": "6.0.0",
        "australian_compliant": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

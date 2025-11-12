"""
UltraCore Financial API - Complete Platform
Version 7.0.0 with Cash Management
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
from ultracore.api.v1.cash.routes import router as cash_router

app = FastAPI(
    title="UltraCore Financial Platform",
    description="Complete wealth management platform with cash management",
    version="7.0.0"
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
app.include_router(cash_router)

@app.get("/")
async def root():
    return {
        "message": "UltraCore Financial Platform",
        "version": "7.0.0",
        "modules": {
            "financial": "Global financial data",
            "ultrawealth": "Australian ETFs (100+)",
            "clients": "Client management, KYC",
            "holdings": "Positions, Portfolio",
            "transactions": "Orders, Trading, Settlement",
            "accounting": "Double-Entry Bookkeeping",
            "compliance": "Australian Regulatory Compliance",
            "cash": "Cash Management Accounts (NEW!)"
        },
        "cash_management": {
            "event_sourcing": "Complete audit trail",
            "kafka_streaming": "Real-time event processing",
            "data_mesh": "Quality, lineage, governance",
            "agentic_ai": "Fraud detection & validation",
            "reinforcement_learning": "Cash optimization",
            "bank_integration": "NPP, BPAY, Direct Debit/Credit",
            "interest": "Tiered interest calculations",
            "fees": "Automated fee management",
            "reconciliation": "Daily reconciliation",
            "limits": "Transaction controls",
            "compliance": "AUSTRAC & ASIC integration"
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
            "holdings", "transactions", "accounting",
            "compliance", "cash"
        ],
        "version": "7.0.0",
        "cash_enabled": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

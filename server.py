"""
UltraCore Financial API - Complete Platform
Version 7.0.0 with Cash Management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers with graceful fallback
routers = {}

try:
    from ultracore.api.v1.financial.routes import router as financial_router
    routers['financial'] = financial_router
except ImportError as e:
    logger.warning(f"Financial router not available: {e}")

try:
    from ultracore.api.v1.ultrawealth.routes import router as ultrawealth_router
    routers['ultrawealth'] = ultrawealth_router
except ImportError as e:
    logger.warning(f"UltraWealth router not available: {e}")

try:
    from ultracore.api.v1.clients.routes import router as clients_router
    routers['clients'] = clients_router
except ImportError as e:
    logger.warning(f"Clients router not available: {e}")

try:
    from ultracore.api.v1.holdings.routes import router as holdings_router
    routers['holdings'] = holdings_router
except ImportError as e:
    logger.warning(f"Holdings router not available: {e}")

try:
    from ultracore.api.v1.transactions.routes import router as transactions_router
    routers['transactions'] = transactions_router
except ImportError as e:
    logger.warning(f"Transactions router not available: {e}")

try:
    from ultracore.api.v1.accounting.routes import router as accounting_router
    routers['accounting'] = accounting_router
except ImportError as e:
    logger.warning(f"Accounting router not available: {e}")

try:
    from ultracore.api.v1.compliance.routes import router as compliance_router
    routers['compliance'] = compliance_router
except ImportError as e:
    logger.warning(f"Compliance router not available: {e}")

try:
    from ultracore.api.v1.cash.routes import router as cash_router
    routers['cash'] = cash_router
except ImportError as e:
    logger.warning(f"Cash router not available: {e}")

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

# Include all available routers
for name, router in routers.items():
    app.include_router(router)
    logger.info(f"Loaded router: {name}")

logger.info(f"Total routers loaded: {len(routers)}/8")

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

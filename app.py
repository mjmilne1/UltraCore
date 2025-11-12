"""FastAPI Application - Complete with UltraWealth"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ultracore.api.v1.financial.routes import router as financial_router
from ultracore.api.v1.ultrawealth.routes import router as ultrawealth_router

app = FastAPI(
    title="UltraCore Financial API with UltraWealth",
    description="Financial data integration with Australian ETF support",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financial_router)
app.include_router(ultrawealth_router)

@app.get("/")
async def root():
    return {
        "message": "UltraCore Financial API with UltraWealth",
        "version": "2.0.0",
        "services": {
            "financial": "Global financial data",
            "ultrawealth": "Australian ETFs (30+ ASX listed)"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # PORT 8001

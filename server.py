"""
UltraWealth Complete API Server
Integrated: DataMesh + ML + RL + Agentic AI + MCP + Auto-Update
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import sys
sys.path.insert(0, r'C:\Users\mjmil\UltraCore')

from ultracore.services.yahoo_finance import yahoo_service
from ultracore.services.ultrawealth import (
    ultrawealth_service,
    australian_etf_universe,
    ultrawealth_datamesh,
    ml_engine,
    rl_optimizer,
    agentic_ai,
    mcp_tools,
    auto_updater
)

app = FastAPI(
    title="UltraWealth Platform",
    description="Complete AI-powered wealth management platform with DataMesh, ML, RL, and Agentic AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TickerList(BaseModel):
    tickers: List[str]

class PortfolioOptimizeRequest(BaseModel):
    tickers: List[str]
    initial_balance: float = 100000
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive

class AIDecisionRequest(BaseModel):
    tickers: List[str]
    current_allocation: dict
    portfolio_value: float = 100000

class DataIngestRequest(BaseModel):
    tickers: List[str]
    period: str = "2y"
    force_refresh: bool = False

# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "UltraWealth Platform - AI-Powered Wealth Management",
        "version": "2.0.0",
        "components": {
            "datamesh": "Data governance & auto-update",
            "ml_engine": "Random Forest + Gradient Boosting predictions",
            "rl_optimizer": "Portfolio optimization with PPO",
            "agentic_ai": "Autonomous decision making",
            "mcp_tools": "AI agent access layer"
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    update_status = ultrawealth_datamesh.get_update_status()
    return {
        "status": "healthy",
        "components": {
            "datamesh": "operational",
            "ml_engine": "operational",
            "rl_optimizer": "operational",
            "agentic_ai": "operational",
            "mcp_tools": "operational"
        },
        "cached_etfs": len(update_status),
        "last_updates": update_status
    }

# ============================================================================
# ETF UNIVERSE ENDPOINTS
# ============================================================================

@app.get("/api/v1/universe")
async def get_universe():
    """Get complete Australian ETF universe"""
    return australian_etf_universe.get_summary()

@app.get("/api/v1/universe/category/{category}")
async def get_by_category(category: str):
    """Get ETFs by category"""
    tickers = australian_etf_universe.get_by_category(category)
    etfs = []
    for ticker in tickers:
        info = australian_etf_universe.get_etf_info(ticker)
        etfs.append({"ticker": ticker, **info})
    return {"category": category, "count": len(etfs), "etfs": etfs}

@app.get("/api/v1/universe/provider/{provider}")
async def get_by_provider(provider: str):
    """Get ETFs by provider"""
    tickers = australian_etf_universe.get_by_provider(provider)
    etfs = []
    for ticker in tickers:
        info = australian_etf_universe.get_etf_info(ticker)
        etfs.append({"ticker": ticker, **info})
    return {"provider": provider, "count": len(etfs), "etfs": etfs}

# ============================================================================
# DATAMESH ENDPOINTS
# ============================================================================

@app.post("/api/v1/datamesh/ingest")
async def ingest_data(request: DataIngestRequest, background_tasks: BackgroundTasks):
    """Ingest ETF data into DataMesh"""
    try:
        result = await ultrawealth_datamesh.batch_ingest(
            request.tickers, 
            request.period
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/datamesh/lineage/{ticker}")
async def get_lineage(ticker: str, period: str = "2y"):
    """Get data lineage for a ticker"""
    lineage = ultrawealth_datamesh.get_data_lineage(ticker, period)
    if not lineage:
        raise HTTPException(status_code=404, detail="No lineage found")
    return lineage

@app.get("/api/v1/datamesh/status")
async def get_datamesh_status():
    """Get DataMesh update status"""
    return ultrawealth_datamesh.get_update_status()

@app.post("/api/v1/datamesh/update-all")
async def update_all_etfs(background_tasks: BackgroundTasks):
    """Trigger update of all ETFs"""
    background_tasks.add_task(auto_updater.update_all_etfs)
    return {"status": "update_started", "message": "Updating all ETFs in background"}

# ============================================================================
# ML PREDICTION ENDPOINTS
# ============================================================================

@app.get("/api/v1/ml/predict/{ticker}")
async def predict_etf(ticker: str):
    """Get ML prediction for an ETF"""
    try:
        # Validate ticker
        if not australian_etf_universe.is_valid_etf(ticker):
            raise ValueError(f"{ticker} not in approved universe")
        
        # Get data
        df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
        if df is None or len(df) == 0:
            raise ValueError("No data available")
        
        # Make prediction
        prediction = await ml_engine.predict(ticker, df)
        return prediction
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/train/{ticker}")
async def train_model(ticker: str):
    """Train ML model for an ETF"""
    try:
        if not australian_etf_universe.is_valid_etf(ticker):
            raise ValueError(f"{ticker} not in approved universe")
        
        df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
        if df is None:
            raise ValueError("No data available")
        
        result = await ml_engine.train_model(ticker, df)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/batch-predict")
async def batch_predict(request: TickerList):
    """Get predictions for multiple ETFs"""
    try:
        predictions = []
        for ticker in request.tickers:
            if not australian_etf_universe.is_valid_etf(ticker):
                continue
            
            df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
            if df is not None:
                pred = await ml_engine.predict(ticker, df)
                predictions.append(pred)
        
        return {"predictions": predictions, "count": len(predictions)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RL PORTFOLIO OPTIMIZATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/portfolio/optimize")
async def optimize_portfolio(request: PortfolioOptimizeRequest):
    """Optimize portfolio allocation using RL"""
    try:
        # Validate tickers
        for ticker in request.tickers:
            if not australian_etf_universe.is_valid_etf(ticker):
                raise ValueError(f"{ticker} not in approved universe")
        
        # Get data for all ETFs
        etf_data = {}
        for ticker in request.tickers:
            df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
            if df is not None:
                etf_data[ticker] = df
        
        if not etf_data:
            raise ValueError("No data available for any ticker")
        
        # Optimize
        result = await rl_optimizer.optimize_portfolio(
            etf_data,
            request.initial_balance,
            request.risk_tolerance
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AGENTIC AI ENDPOINTS
# ============================================================================

@app.post("/api/v1/ai/analyze")
async def ai_analyze_market(request: TickerList):
    """Get AI analysis of market conditions"""
    try:
        predictions = []
        for ticker in request.tickers:
            if australian_etf_universe.is_valid_etf(ticker):
                df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
                if df is not None:
                    pred = await ml_engine.predict(ticker, df)
                    predictions.append(pred)
        
        analysis = await agentic_ai.analyze_market_conditions(predictions)
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/recommend")
async def ai_recommend(request: AIDecisionRequest):
    """Get AI recommendations for portfolio"""
    try:
        predictions = []
        for ticker in request.tickers:
            if australian_etf_universe.is_valid_etf(ticker):
                df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
                if df is not None:
                    pred = await ml_engine.predict(ticker, df)
                    predictions.append(pred)
        
        decision = await agentic_ai.make_decision(
            request.current_allocation,
            predictions,
            request.portfolio_value
        )
        
        return decision
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/history")
async def ai_history(limit: int = 10):
    """Get AI decision history"""
    return {"decisions": agentic_ai.get_decision_history(limit)}

# ============================================================================
# MCP TOOLS ENDPOINTS
# ============================================================================

@app.get("/api/v1/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {"tools": mcp_tools.get_available_tools()}

@app.get("/api/v1/mcp/price/{ticker}")
async def mcp_get_price(ticker: str):
    """MCP: Get ETF price"""
    try:
        return await mcp_tools.get_etf_price(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/predict/{ticker}")
async def mcp_predict(ticker: str):
    """MCP: Predict ETF price"""
    try:
        return await mcp_tools.predict_etf_price(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/optimize")
async def mcp_optimize(request: PortfolioOptimizeRequest):
    """MCP: Optimize portfolio"""
    try:
        return await mcp_tools.optimize_portfolio(
            request.tickers,
            request.initial_balance,
            request.risk_tolerance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BASIC ETF ENDPOINTS
# ============================================================================

@app.get("/api/v1/etf/{ticker}/price")
async def get_etf_price(ticker: str):
    """Get current ETF price"""
    try:
        return await ultrawealth_service.get_etf_price(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/etf/batch/prices")
async def batch_prices(request: TickerList):
    """Get prices for multiple ETFs"""
    try:
        prices = await ultrawealth_service.get_portfolio_prices(request.tickers)
        return {"prices": prices}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting UltraWealth Platform...")
    print("📊 Components: DataMesh + ML + RL + Agentic AI + MCP")
    print("🌐 Server: http://localhost:9000")
    print("📚 Docs: http://localhost:9000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=9000)


"""
UltraWealth API Endpoints - Australian ETFs Only
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from ultracore.services.ultrawealth import ultrawealth_service, australian_etf_universe

router = APIRouter(prefix="/api/v1/ultrawealth", tags=["ultrawealth"])

class PortfolioRequest(BaseModel):
    tickers: List[str]
    
class RiskProfileRequest(BaseModel):
    risk_profile: str  # conservative, moderate, aggressive

@router.get("/universe")
async def get_etf_universe():
    """Get complete Australian ETF universe"""
    return ultrawealth_service.get_universe_summary()

@router.get("/universe/category/{category}")
async def get_etfs_by_category(category: str):
    """Get ETFs by category"""
    etfs = australian_etf_universe.get_by_category(category)
    result = []
    for ticker in etfs:
        info = australian_etf_universe.get_etf_info(ticker)
        result.append({"ticker": ticker, **info})
    return {"category": category, "etfs": result}

@router.get("/universe/provider/{provider}")
async def get_etfs_by_provider(provider: str):
    """Get ETFs by provider"""
    etfs = australian_etf_universe.get_by_provider(provider)
    result = []
    for ticker in etfs:
        info = australian_etf_universe.get_etf_info(ticker)
        result.append({"ticker": ticker, **info})
    return {"provider": provider, "etfs": result}

@router.get("/etf/{ticker}/price")
async def get_etf_price(ticker: str):
    """Get current price for Australian ETF"""
    try:
        return await ultrawealth_service.get_etf_price(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/etf/{ticker}/predict")
async def predict_etf_price(ticker: str):
    """Get ML prediction for Australian ETF"""
    try:
        return await ultrawealth_service.get_etf_prediction(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/prices")
async def get_portfolio_prices(request: PortfolioRequest):
    """Get prices for portfolio of Australian ETFs"""
    try:
        prices = await ultrawealth_service.get_portfolio_prices(request.tickers)
        return {"tickers": request.tickers, "prices": prices}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/recommend")
async def recommend_portfolio(request: RiskProfileRequest):
    """Get recommended ETF portfolio based on risk profile"""
    try:
        portfolio = ultrawealth_service.get_recommended_portfolio(request.risk_profile)
        return {
            "risk_profile": request.risk_profile,
            "portfolio": portfolio,
            "total_weight": sum(p["weight"] for p in portfolio)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for UltraWealth service"""
    universe_summary = ultrawealth_service.get_universe_summary()
    return {
        "status": "healthy",
        "service": "ultrawealth_australian_etfs",
        "total_etfs": universe_summary["total_etfs"],
        "categories": universe_summary["categories"]
    }

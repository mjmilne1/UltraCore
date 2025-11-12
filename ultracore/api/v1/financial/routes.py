"""FastAPI Routes for Financial Data"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ultracore.services.yahoo_finance import yahoo_service, ml_pipeline

router = APIRouter(prefix="/api/v1/financial", tags=["financial"])

class StockRequest(BaseModel):
    tickers: List[str]

@router.get("/stock/{ticker}/price")
async def get_stock_price(ticker: str):
    try:
        data = await yahoo_service.get_company_data(ticker)
        return {"ticker": ticker, "price": data["market_data"]["current_price"], "market_cap": data["market_data"]["market_cap"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/data")
async def get_company_data(ticker: str):
    try:
        return await yahoo_service.get_company_data(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml/train/{ticker}")
async def train_ml_model(ticker: str):
    try:
        return await ml_pipeline.train_price_predictor(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml/predict/{ticker}")
async def predict_price(ticker: str):
    try:
        predicted = await ml_pipeline.predict_next_price(ticker)
        current_data = await yahoo_service.get_company_data(ticker)
        current = current_data["market_data"]["current_price"]
        return {
            "ticker": ticker,
            "current_price": current,
            "predicted_price": predicted,
            "change_percent": ((predicted - current) / current * 100) if current else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/prices")
async def batch_prices(request: StockRequest):
    try:
        prices = await yahoo_service.batch_get_prices(request.tickers)
        return {"tickers": request.tickers, "prices": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ultracore_financial",
        "integrations": {
            "yahoo_finance": "active",
            "ml_pipeline": "active"
        }
    }

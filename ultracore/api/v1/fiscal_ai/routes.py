"""
Fiscal.ai API Routes for UltraCore
Exposes financial data endpoints for wealth management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from ultracore.services.fiscal_ai import FiscalAIService, PortfolioAnalyzer


router = APIRouter(prefix="/fiscal-ai", tags=["Fiscal.ai Financial Data"])


class Holding(BaseModel):
    ticker: str
    quantity: float
    cost_basis: float


class PortfolioRequest(BaseModel):
    holdings: List[Holding]


@router.get("/company/{ticker}/profile")
async def get_company_profile(ticker: str):
    """Get company profile and key information"""
    try:
        service = FiscalAIService()
        async with service.client as client:
            profile = await client.get_company_profile(ticker)
            return profile
    except Exception as e:
        logger.error(f"Error fetching company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{ticker}/financials")
async def get_company_financials(
    ticker: str,
    period: str = Query("annual", regex="^(annual|quarterly)$")
):
    """Get comprehensive financial statements"""
    try:
        service = FiscalAIService()
        async with service.client as client:
            income = await client.get_income_statement(ticker, period, 3)
            balance = await client.get_balance_sheet(ticker, period, 3)
            cash_flow = await client.get_cash_flow_statement(ticker, period, 3)
            ratios = await client.get_company_ratios(ticker, period, 3)
            
            return {
                "ticker": ticker,
                "period": period,
                "income_statement": income,
                "balance_sheet": balance,
                "cash_flow": cash_flow,
                "ratios": ratios
            }
    except Exception as e:
        logger.error(f"Error fetching financials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{ticker}/price")
async def get_stock_price(
    ticker: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Get stock price data"""
    try:
        service = FiscalAIService()
        async with service.client as client:
            prices = await client.get_stock_prices(ticker, from_date, to_date)
            return {"ticker": ticker, "prices": prices}
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/analyze")
async def analyze_portfolio(request: PortfolioRequest):
    """Analyze portfolio holdings and calculate metrics"""
    try:
        service = FiscalAIService()
        holdings = [h.dict() for h in request.holdings]
        
        # Get basic metrics
        metrics = await service.calculate_portfolio_metrics(holdings)
        
        # Get health analysis
        analyzer = PortfolioAnalyzer(service)
        health = await analyzer.analyze_portfolio_health(holdings)
        
        # Get diversification
        diversification = await analyzer.get_diversification_analysis(holdings)
        
        return {
            "metrics": metrics,
            "health_analysis": health,
            "diversification": diversification
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/holdings/enrich")
async def enrich_holdings(request: PortfolioRequest):
    """Enrich holdings with Fiscal.ai financial data"""
    try:
        service = FiscalAIService()
        holdings = [h.dict() for h in request.holdings]
        enriched = await service.get_portfolio_holdings_data(holdings)
        return {"holdings": enriched}
    except Exception as e:
        logger.error(f"Error enriching holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_companies(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search for companies by name or ticker"""
    try:
        service = FiscalAIService()
        async with service.client as client:
            results = await client.search_companies(query, limit)
            return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

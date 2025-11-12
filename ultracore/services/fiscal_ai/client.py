"""
Fiscal.ai API Client - CORRECTED VERSION
Based on actual OpenAPI specification
"""
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger


class FiscalAIClient:
    """Client for Fiscal.ai API - Correct Implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FISCAL_AI_API_KEY")
        if not self.api_key:
            raise ValueError("FISCAL_AI_API_KEY must be provided")
        
        self.base_url = "https://api.fiscal.ai"
        self.headers = {
            "X-API-KEY": self.api_key,  # CORRECT: X-API-KEY header
            "Content-Type": "application/json",
        }
        self._client = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Fiscal.ai API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            logger.debug(f"Fiscal.ai API request: {endpoint} with params: {params}")
            
            response = await self._client.get(
                url,
                headers=self.headers,
                params=params or {}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Fiscal.ai API error: {e}")
            raise
    
    # Company Data
    async def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """Get company profile with sector, industry, description"""
        return await self._request("v2/company/profile", {"ticker": ticker})
    
    async def search_companies(self, query: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of all companies"""
        params = {"limit": limit}
        if query:
            params["search"] = query
        return await self._request("v2/companies-list", params)
    
    # Financial Statements - Standardized
    async def get_income_statement(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get standardized income statements"""
        params = {
            "ticker": ticker,
            "period": period,
            "limit": limit
        }
        return await self._request(
            "v1/company/financials/income-statement/standardized",
            params
        )
    
    async def get_balance_sheet(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get standardized balance sheets"""
        params = {
            "ticker": ticker,
            "period": period,
            "limit": limit
        }
        return await self._request(
            "v1/company/financials/balance-sheet/standardized",
            params
        )
    
    async def get_cash_flow_statement(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get standardized cash flow statements"""
        params = {
            "ticker": ticker,
            "period": period,
            "limit": limit
        }
        return await self._request(
            "v1/company/financials/cash-flow/standardized",
            params
        )
    
    # Ratios & Metrics
    async def get_company_ratios(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get all financial ratios time series"""
        params = {
            "ticker": ticker,
            "period": period,
            "limit": limit
        }
        return await self._request("v1/company/ratios", params)
    
    async def get_adjusted_metrics(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get adjusted financial metrics"""
        params = {
            "ticker": ticker,
            "period": period,
            "limit": limit
        }
        return await self._request("v1/company/adjusted-metrics", params)
    
    # Market Data
    async def get_stock_prices(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical stock prices"""
        params = {"ticker": ticker}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._request("v1/company/stock-prices", params)
    
    async def get_latest_price(self, ticker: str) -> Dict[str, Any]:
        """Get latest stock price"""
        prices = await self.get_stock_prices(ticker)
        if isinstance(prices, list) and len(prices) > 0:
            return prices[0]
        elif isinstance(prices, dict):
            # If it returns a dict with a data field
            if 'data' in prices and len(prices['data']) > 0:
                return prices['data'][0]
        return {}
    
    # Segments & Filings
    async def get_segments_kpis(
        self,
        ticker: str,
        period: str = "annual"
    ) -> Dict[str, Any]:
        """Get business segment data and KPIs"""
        params = {"ticker": ticker, "period": period}
        return await self._request("v1/company/segments-and-kpis", params)
    
    async def get_company_filings(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get SEC filings"""
        params = {"ticker": ticker, "limit": limit}
        return await self._request("v2/company/filings", params)
    
    async def get_shares_outstanding(self, ticker: str) -> Dict[str, Any]:
        """Get latest shares outstanding"""
        return await self._request("v1/company/shares-outstanding", {"ticker": ticker})
    
    async def get_earnings_summary(self, ticker: str) -> Dict[str, Any]:
        """Get latest earnings summary"""
        return await self._request("v1/company/earnings-summary", {"ticker": ticker})

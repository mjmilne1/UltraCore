"""
Fiscal.ai Service Layer
Business logic for financial data integration with UltraCore
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from .client import FiscalAIClient


class FiscalAIService:
    """Service for managing Fiscal.ai financial data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = FiscalAIClient(api_key)
    
    async def get_holding_data(
        self,
        ticker: str,
        include_fundamentals: bool = True,
        include_price: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive data for a portfolio holding
        
        Args:
            ticker: Stock ticker symbol
            include_fundamentals: Include financial statements and ratios
            include_price: Include current price data
            
        Returns:
            Comprehensive holding data
        """
        async with self.client as client:
            data = {"ticker": ticker}
            
            # Get company profile
            try:
                profile = await client.get_company_profile(ticker)
                data["profile"] = profile
            except Exception as e:
                logger.error(f"Error fetching profile for {ticker}: {e}")
                data["profile"] = None
            
            # Get current price
            if include_price:
                try:
                    price_data = await client.get_latest_price(ticker)
                    data["current_price"] = price_data.get("close")
                    data["price_date"] = price_data.get("date")
                except Exception as e:
                    logger.error(f"Error fetching price for {ticker}: {e}")
                    data["current_price"] = None
            
            # Get fundamentals
            if include_fundamentals:
                try:
                    # Latest income statement
                    income_stmt = await client.get_income_statement(ticker, "annual", 1)
                    data["income_statement"] = income_stmt[0] if income_stmt else None
                    
                    # Latest balance sheet
                    balance_sheet = await client.get_balance_sheet(ticker, "annual", 1)
                    data["balance_sheet"] = balance_sheet[0] if balance_sheet else None
                    
                    # Latest ratios
                    ratios = await client.get_company_ratios(ticker, "annual", 1)
                    data["ratios"] = ratios[0] if ratios else None
                    
                except Exception as e:
                    logger.error(f"Error fetching fundamentals for {ticker}: {e}")
                    data["fundamentals_error"] = str(e)
            
            return data
    
    async def get_portfolio_holdings_data(
        self,
        holdings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get financial data for multiple portfolio holdings
        
        Args:
            holdings: List of holdings with 'ticker' and 'quantity' fields
            
        Returns:
            List of holdings enriched with financial data
        """
        enriched_holdings = []
        
        async with self.client as client:
            for holding in holdings:
                ticker = holding.get("ticker")
                if not ticker:
                    continue
                
                try:
                    data = await self.get_holding_data(ticker)
                    enriched_holdings.append({
                        **holding,
                        "fiscal_data": data
                    })
                except Exception as e:
                    logger.error(f"Error enriching holding {ticker}: {e}")
                    enriched_holdings.append({
                        **holding,
                        "fiscal_data": {"error": str(e)}
                    })
        
        return enriched_holdings
    
    async def calculate_portfolio_metrics(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio-level metrics
        
        Args:
            holdings: Portfolio holdings with ticker, quantity, cost_basis
            
        Returns:
            Portfolio metrics including market value, gains, allocation
        """
        enriched = await self.get_portfolio_holdings_data(holdings)
        
        total_market_value = 0
        total_cost_basis = 0
        sector_allocation = {}
        
        for holding in enriched:
            quantity = holding.get("quantity", 0)
            cost_basis = holding.get("cost_basis", 0)
            
            fiscal_data = holding.get("fiscal_data", {})
            current_price = fiscal_data.get("current_price", 0)
            profile = fiscal_data.get("profile", {})
            sector = profile.get("sector", "Unknown")
            
            market_value = quantity * current_price
            total_market_value += market_value
            total_cost_basis += cost_basis * quantity
            
            # Sector allocation
            sector_allocation[sector] = sector_allocation.get(sector, 0) + market_value
        
        # Calculate percentages
        for sector in sector_allocation:
            sector_allocation[sector] = {
                "value": sector_allocation[sector],
                "percentage": (sector_allocation[sector] / total_market_value * 100) 
                    if total_market_value > 0 else 0
            }
        
        return {
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_gain_loss": total_market_value - total_cost_basis,
            "total_gain_loss_pct": (
                (total_market_value - total_cost_basis) / total_cost_basis * 100
            ) if total_cost_basis > 0 else 0,
            "sector_allocation": sector_allocation,
            "holdings_count": len(enriched),
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    async def get_stock_performance(
        self,
        ticker: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get stock price performance over specified period
        
        Args:
            ticker: Stock ticker
            days: Number of days to analyze
            
        Returns:
            Performance metrics
        """
        async with self.client as client:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            prices = await client.get_stock_prices(
                ticker,
                str(start_date),
                str(end_date)
            )
            
            if not prices:
                return {"error": "No price data available"}
            
            first_price = prices[-1].get("close", 0)
            last_price = prices[0].get("close", 0)
            
            return {
                "ticker": ticker,
                "period_days": days,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "start_price": first_price,
                "end_price": last_price,
                "change": last_price - first_price,
                "change_pct": ((last_price - first_price) / first_price * 100) 
                    if first_price > 0 else 0,
                "high": max(p.get("high", 0) for p in prices),
                "low": min(p.get("low", float('inf')) for p in prices),
            }

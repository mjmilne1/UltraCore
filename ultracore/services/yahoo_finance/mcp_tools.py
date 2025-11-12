"""MCP Tools for Financial Data"""
from typing import Dict, List, Any
from ultracore.services.yahoo_finance.service import yahoo_service
from ultracore.services.yahoo_finance.datamesh import financial_datamesh
from ultracore.services.yahoo_finance.ml_pipeline import ml_pipeline

class FinancialDataMCPTools:
    @staticmethod
    async def get_stock_price(ticker: str) -> Dict[str, Any]:
        data = await yahoo_service.get_company_data(ticker)
        return {
            "tool": "get_stock_price",
            "ticker": ticker,
            "price": data["market_data"]["current_price"],
            "market_cap": data["market_data"]["market_cap"]
        }
    
    @staticmethod
    async def get_company_info(ticker: str) -> Dict[str, Any]:
        data = await yahoo_service.get_company_data(ticker)
        return {
            "tool": "get_company_info",
            "ticker": ticker,
            "company": data["company_info"]
        }
    
    @staticmethod
    async def predict_price(ticker: str) -> Dict[str, Any]:
        # Ensure data is ingested before prediction
        await financial_datamesh.ingest_time_series_data(ticker, "2y")
        prediction = await ml_pipeline.predict_next_price(ticker)
        
        # Get current price for comparison
        data = await yahoo_service.get_company_data(ticker)
        current = data["market_data"]["current_price"]
        
        return {
            "tool": "predict_price",
            "ticker": ticker,
            "current_price": current,
            "predicted_price": prediction,
            "change": ((prediction - current) / current * 100) if current else 0
        }
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        return [
            {"name": "get_stock_price", "description": "Get current stock price"},
            {"name": "get_company_info", "description": "Get company information"},
            {"name": "predict_price", "description": "Predict next price using ML"}
        ]

mcp_tools = FinancialDataMCPTools()

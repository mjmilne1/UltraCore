"""
MCP Tools for AI Agent Access to UltraWealth
"""

from typing import Dict, List
from ultracore.services.ultrawealth.datamesh import ultrawealth_datamesh
from ultracore.services.ultrawealth.ml_engine import ml_engine
from ultracore.services.ultrawealth.rl_optimizer import rl_optimizer
from ultracore.services.ultrawealth.agentic_ai import agentic_ai

class UltraWealthMCPTools:
    """MCP-compatible tools for AI agents"""
    
    @staticmethod
    async def get_etf_price(ticker: str) -> Dict:
        """Get current ETF price"""
        df = await ultrawealth_datamesh.get_etf_data(ticker, "1mo")
        if df is None or len(df) == 0:
            return {"error": "No data available"}
        
        return {
            "ticker": ticker,
            "price": float(df['Close'].iloc[-1]),
            "change_1d": float(df['Close'].pct_change().iloc[-1] * 100),
            "volume": int(df['Volume'].iloc[-1])
        }
    
    @staticmethod
    async def predict_etf_price(ticker: str) -> Dict:
        """Predict future ETF price using ML"""
        df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
        if df is None:
            return {"error": "No data available"}
        
        prediction = await ml_engine.predict(ticker, df)
        return prediction
    
    @staticmethod
    async def optimize_portfolio(tickers: List[str], balance: float = 100000, risk: str = "moderate") -> Dict:
        """Optimize portfolio allocation"""
        etf_data = {}
        for ticker in tickers:
            df = await ultrawealth_datamesh.get_etf_data(ticker, "2y")
            if df is not None:
                etf_data[ticker] = df
        
        if not etf_data:
            return {"error": "No data available"}
        
        result = await rl_optimizer.optimize_portfolio(etf_data, balance, risk)
        return result
    
    @staticmethod
    async def get_ai_recommendation(tickers: List[str], current_allocation: Dict) -> Dict:
        """Get AI agent recommendations"""
        predictions = []
        for ticker in tickers:
            pred = await UltraWealthMCPTools.predict_etf_price(ticker)
            if 'error' not in pred:
                predictions.append(pred)
        
        decision = await agentic_ai.make_decision(current_allocation, predictions, 100000)
        return decision
    
    @staticmethod
    def get_available_tools() -> List[Dict]:
        """List all available MCP tools"""
        return [
            {
                "name": "get_etf_price",
                "description": "Get current price and basic info for an ETF",
                "parameters": ["ticker"]
            },
            {
                "name": "predict_etf_price",
                "description": "Get ML prediction for future ETF price",
                "parameters": ["ticker"]
            },
            {
                "name": "optimize_portfolio",
                "description": "Optimize portfolio allocation using RL",
                "parameters": ["tickers", "balance", "risk"]
            },
            {
                "name": "get_ai_recommendation",
                "description": "Get autonomous AI recommendations",
                "parameters": ["tickers", "current_allocation"]
            }
        ]

mcp_tools = UltraWealthMCPTools()

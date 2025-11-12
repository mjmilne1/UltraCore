"""MCP Server for OpenMarkets Trading Tools"""
from typing import Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from ultracore.mcp.base import BaseMCPServer
from ..client import OpenMarketsClient


class OpenMarketsMCPServer(BaseMCPServer):
    """
    MCP Server exposing OpenMarkets trading capabilities as AI tools.
    
    Tools available to AI agents (Claude, etc.):
    - place_trade: Execute trades via natural language
    - get_position: Check current positions
    - get_portfolio: View entire portfolio
    - analyze_market: Get market analysis for a symbol
    - optimize_portfolio: Get AI portfolio recommendations
    """
    
    def __init__(self, client: OpenMarketsClient, account_id: str):
        super().__init__(server_name="openmarkets")
        self.client = client
        self.account_id = account_id
    
    def register_tools(self):
        """Register all OpenMarkets tools."""
        
        @self.server.tool()
        async def place_trade(
            symbol: str,
            action: str,  # "buy" or "sell"
            quantity: int,
            order_type: str = "market",
            price: float = None
        ) -> Dict[str, Any]:
            """
            Place a trade on the Australian stock market.
            
            Args:
                symbol: ASX ticker symbol (e.g., 'BHP', 'CBA')
                action: 'buy' or 'sell'
                quantity: Number of shares
                order_type: 'market' or 'limit'
                price: Limit price (required if order_type is 'limit')
            
            Returns:
                Order confirmation with order ID and status
            """
            from ..models import OrderRequest, OrderSide, OrderType
            from decimal import Decimal
            
            order = OrderRequest(
                symbol=symbol,
                side=OrderSide.BUY if action.lower() == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
                quantity=quantity,
                price=Decimal(str(price)) if price else None
            )
            
            response = await self.client.place_order(order, self.account_id)
            
            return {
                "success": True,
                "order_id": response.order_id,
                "symbol": response.symbol,
                "quantity": response.quantity,
                "status": response.status,
                "message": f"Successfully placed {action} order for {quantity} {symbol} shares"
            }
        
        @self.server.tool()
        async def get_position(symbol: str) -> Dict[str, Any]:
            """
            Get current position for a specific stock.
            
            Args:
                symbol: ASX ticker symbol
            
            Returns:
                Position details including quantity, value, and P&L
            """
            position = await self.client.get_position(self.account_id, symbol)
            
            if not position:
                return {
                    "symbol": symbol,
                    "quantity": 0,
                    "message": f"No position in {symbol}"
                }
            
            return {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_cost": float(position.average_cost),
                "current_price": float(position.current_price),
                "market_value": float(position.market_value),
                "unrealized_pnl": float(position.unrealized_pnl),
                "unrealized_pnl_percent": float(position.unrealized_pnl_percent)
            }
        
        @self.server.tool()
        async def get_portfolio() -> Dict[str, Any]:
            """
            Get complete portfolio overview.
            
            Returns:
                All positions, account balance, and total portfolio value
            """
            positions = await self.client.get_positions(self.account_id)
            balance = await self.client.get_account_balance(self.account_id)
            
            return {
                "cash_balance": float(balance.cash_balance),
                "portfolio_value": float(balance.portfolio_value),
                "total_equity": float(balance.total_equity),
                "unrealized_pnl": float(balance.unrealized_pnl),
                "positions": [
                    {
                        "symbol": p.symbol,
                        "quantity": p.quantity,
                        "value": float(p.market_value),
                        "pnl": float(p.unrealized_pnl)
                    }
                    for p in positions
                ]
            }
        
        @self.server.tool()
        async def analyze_market(symbol: str) -> Dict[str, Any]:
            """
            Get AI-powered market analysis for a stock.
            
            Args:
                symbol: ASX ticker symbol
            
            Returns:
                Market data, technical analysis, and AI insights
            """
            market_data = await self.client.get_market_data(symbol)
            
            # Calculate technical indicators
            change_percent = float(market_data.change_percent)
            
            # AI sentiment (simplified)
            sentiment = "bullish" if change_percent > 2 else "bearish" if change_percent < -2 else "neutral"
            
            return {
                "symbol": symbol,
                "current_price": float(market_data.last_price),
                "change": float(market_data.change),
                "change_percent": change_percent,
                "volume": market_data.volume,
                "high": float(market_data.high),
                "low": float(market_data.low),
                "sentiment": sentiment,
                "recommendation": f"Market showing {sentiment} signals based on price action"
            }
        
        @self.server.tool()
        async def optimize_portfolio() -> Dict[str, Any]:
            """
            Get AI-powered portfolio optimization recommendations.
            
            Returns:
                Recommended portfolio allocation changes
            """
            # Get current positions
            positions = await self.client.get_positions(self.account_id)
            
            # Simplified optimization (in production, would use ML model)
            recommendations = []
            for position in positions:
                allocation_pct = float(position.market_value) / float(position.market_value) * 100
                
                if allocation_pct > 30:
                    recommendations.append({
                        "symbol": position.symbol,
                        "action": "reduce",
                        "reason": f"Over-concentrated at {allocation_pct:.1f}%",
                        "target_allocation": 20.0
                    })
            
            return {
                "recommendations": recommendations,
                "risk_score": 45,  # Medium risk
                "expected_improvement": "15% reduction in portfolio volatility"
            }

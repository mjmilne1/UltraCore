"""Agentic AI Trading Agent - Natural Language Trading with Anya"""
import re
from typing import Optional, Dict, Any
from decimal import Decimal

from anthropic import Anthropic
from ..client import OpenMarketsClient
from ..models import OrderRequest, OrderSide, OrderType
from ultracore.anya.agent import AnyaAgent


class TradingAgent(AnyaAgent):
    """
    Natural language trading agent powered by Claude (Anya).
    
    Examples:
        "Buy 1000 BHP shares at market price"
        "Sell 500 CBA at "
        "Place a stop loss on my WES position at "
        "What's my current position in TLS?"
        "Show me my portfolio performance today"
    """
    
    def __init__(
        self,
        client: OpenMarketsClient,
        anthropic_client: Anthropic,
        account_id: str
    ):
        super().__init__(
            name="AnyaTradingAgent",
            description="AI-powered trading agent for natural language trading",
            capabilities=[
                "Place market/limit/stop orders",
                "Check positions and portfolio",
                "Analyze market conditions",
                "Provide trading recommendations",
                "Execute complex trading strategies"
            ]
        )
        self.client = client
        self.anthropic = anthropic_client
        self.account_id = account_id
    
    async def execute(self, natural_language_request: str) -> Dict[str, Any]:
        """
        Execute a natural language trading request.
        
        Args:
            natural_language_request: User's trading instruction in natural language
        
        Returns:
            Dictionary with execution results and confidence score
        """
        # Use Claude to interpret the request
        prompt = f"""
You are Anya, an AI trading assistant for OpenMarkets. Parse this trading request:

Request: "{natural_language_request}"

Extract:
1. Action (buy, sell, check_position, analyze, etc.)
2. Symbol (ASX ticker)
3. Quantity (if applicable)
4. Price (if applicable, null for market orders)
5. Order type (market, limit, stop)
6. Confidence score (0-1)

Respond in JSON format:
{{
    "action": "buy|sell|check_position|analyze",
    "symbol": "BHP",
    "quantity": 1000,
    "price": null,
    "order_type": "market",
    "confidence": 0.95,
    "reasoning": "User wants to buy 1000 BHP shares at market price"
}}
"""
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse Claude's response
        parsed = eval(response.content[0].text)  # In production, use json.loads with error handling
        
        # Execute the parsed action
        if parsed["action"] == "buy":
            order_response = await self._execute_buy_order(
                symbol=parsed["symbol"],
                quantity=parsed["quantity"],
                price=parsed.get("price"),
                order_type=parsed["order_type"]
            )
            
            return {
                "success": True,
                "action": "order_placed",
                "order_id": order_response.order_id,
                "symbol": parsed["symbol"],
                "quantity": parsed["quantity"],
                "confidence": parsed["confidence"],
                "natural_language_request": natural_language_request,
                "reasoning": parsed["reasoning"]
            }
        
        elif parsed["action"] == "sell":
            order_response = await self._execute_sell_order(
                symbol=parsed["symbol"],
                quantity=parsed["quantity"],
                price=parsed.get("price"),
                order_type=parsed["order_type"]
            )
            
            return {
                "success": True,
                "action": "order_placed",
                "order_id": order_response.order_id,
                "symbol": parsed["symbol"],
                "quantity": parsed["quantity"],
                "confidence": parsed["confidence"]
            }
        
        elif parsed["action"] == "check_position":
            position = await self.client.get_position(
                account_id=self.account_id,
                symbol=parsed["symbol"]
            )
            
            return {
                "success": True,
                "action": "position_retrieved",
                "symbol": parsed["symbol"],
                "position": position.dict() if position else None,
                "confidence": parsed["confidence"]
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {parsed['action']}",
                "confidence": 0.0
            }
    
    async def _execute_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[Decimal],
        order_type: str
    ):
        """Execute a buy order."""
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
        
        return await self.client.place_order(
            order=order,
            account_id=self.account_id,
            agent_context={
                "agent_id": self.name,
                "confidence": 0.95
            }
        )
    
    async def _execute_sell_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[Decimal],
        order_type: str
    ):
        """Execute a sell order."""
        order = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
        
        return await self.client.place_order(
            order=order,
            account_id=self.account_id,
            agent_context={
                "agent_id": self.name,
                "confidence": 0.95
            }
        )


# Alias for clarity
AnyaTradingAgent = TradingAgent

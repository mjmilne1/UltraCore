"""MCP Tool registration and schemas"""
from mcp.types import Tool

def register_trading_tools() -> list[Tool]:
    """Register all OpenMarkets MCP tools."""
    return [
        Tool(
            name="place_trade",
            description="Place a trade on the Australian stock market (ASX, Chi-X, NSX)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "ASX ticker symbol"},
                    "action": {"type": "string", "enum": ["buy", "sell"]},
                    "quantity": {"type": "integer", "minimum": 1},
                    "order_type": {"type": "string", "enum": ["market", "limit"], "default": "market"},
                    "price": {"type": "number", "description": "Limit price (required for limit orders)"}
                },
                "required": ["symbol", "action", "quantity"]
            }
        ),
        Tool(
            name="get_position",
            description="Get current position for a specific stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "ASX ticker symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_portfolio",
            description="Get complete portfolio overview with all positions and balances",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="analyze_market",
            description="Get AI-powered market analysis for a stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "ASX ticker symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="optimize_portfolio",
            description="Get AI-powered portfolio optimization recommendations",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

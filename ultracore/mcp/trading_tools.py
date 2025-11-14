"""MCP Tools for Trading Operations"""
from typing import Dict, Any
from decimal import Decimal

def place_order_tool(symbol: str, side: str, quantity: Decimal,
                    order_type: str = "market") -> Dict[str, Any]:
    """Place trading order via MCP"""
    return {
        "tool": "place_order",
        "order_id": "order_123",
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "status": "submitted"
    }

def cancel_order_tool(order_id: str) -> Dict[str, Any]:
    """Cancel order via MCP"""
    return {
        "tool": "cancel_order",
        "order_id": order_id,
        "status": "cancelled"
    }

def get_quote_tool(symbol: str) -> Dict[str, Any]:
    """Get real-time quote via MCP"""
    return {
        "tool": "get_quote",
        "symbol": symbol,
        "bid": Decimal("100.45"),
        "ask": Decimal("100.50"),
        "last": Decimal("100.48")
    }

def get_positions_tool() -> Dict[str, Any]:
    """Get current positions via MCP"""
    return {
        "tool": "get_positions",
        "positions": [
            {
                "symbol": "CBA.AX",
                "quantity": Decimal("100"),
                "average_cost": Decimal("95.50")
            }
        ]
    }

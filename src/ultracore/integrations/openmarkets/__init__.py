"""
OpenMarkets Integration for UltraCore
=====================================

Enterprise-grade integration with OpenMarkets Australian trading infrastructure.

Features:
- Event-sourced trading with complete audit trail
- Data Mesh for trading data products
- Agentic AI for natural language trading
- ML for price prediction, portfolio optimization, risk scoring
- RL for adaptive trading strategies
- MCP framework for AI tool integration
- Australian compliance (ASIC, AML/CTF)

Usage:
    from ultracore.integrations.openmarkets import OpenMarketsClient
    from ultracore.integrations.openmarkets.agents import TradingAgent
    
    # Initialize client
    client = OpenMarketsClient(api_key="...", environment="production")
    
    # Use Anya for natural language trading
    agent = TradingAgent()
    response = await agent.execute("Buy 1000 BHP shares at market price")
"""

from .client import OpenMarketsClient
from .config import OpenMarketsConfig
from .events import (
    OrderPlacedEvent,
    OrderExecutedEvent,
    TradeSettledEvent,
    PositionUpdatedEvent
)

__version__ = "1.0.0"
__all__ = [
    "OpenMarketsClient",
    "OpenMarketsConfig",
    "OrderPlacedEvent",
    "OrderExecutedEvent",
    "TradeSettledEvent",
    "PositionUpdatedEvent",
]

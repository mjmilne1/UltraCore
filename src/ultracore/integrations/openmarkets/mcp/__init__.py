"""Model Context Protocol integration for AI-powered trading tools"""
from .server import OpenMarketsMCPServer
from .tools import register_trading_tools

__all__ = ["OpenMarketsMCPServer", "register_trading_tools"]

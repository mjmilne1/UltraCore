"""
UltraCore Account Management Module

Deposits, Transactions, Interest, ML, AI Agents, Payment Rails
"""

__version__ = "1.0.0"
__all__ = []

# Core
try:
    from ultracore.accounts.core import account_models
    __all__.append('account_models')
except ImportError:
    pass

try:
    from ultracore.accounts.core import account_manager
    __all__.append('account_manager')
except ImportError:
    pass

try:
    from ultracore.accounts.core import interest_engine
    __all__.append('interest_engine')
except ImportError:
    pass

# ML
try:
    from ultracore.accounts.ml import account_ml_models
    __all__.append('account_ml_models')
except ImportError:
    pass

# Agents
try:
    from ultracore.accounts.agents import account_agents
    __all__.append('account_agents')
except ImportError:
    pass

# MCP
try:
    from ultracore.accounts.mcp import mcp_payment_rails
    __all__.append('mcp_payment_rails')
except ImportError:
    pass

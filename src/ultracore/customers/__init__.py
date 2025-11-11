"""
UltraCore Customer Management Module

Customer lifecycle, KYC/AML, Graph, AI Agents
"""

__version__ = "1.0.0"
__all__ = []

# Core - import what exists
try:
    from ultracore.customers.core import customer_models
    __all__.append('customer_models')
except ImportError:
    pass

try:
    from ultracore.customers.core import customer_manager
    __all__.append('customer_manager')
except ImportError:
    pass

try:
    from ultracore.customers.core import customer_graph
    __all__.append('customer_graph')
except ImportError:
    pass

# Agents - import what exists
try:
    from ultracore.customers.agents import agent_base
    __all__.append('agent_base')
except ImportError:
    pass

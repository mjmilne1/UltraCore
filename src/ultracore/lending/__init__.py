"""
UltraCore Lending Module

Complete loan lifecycle management
"""

__version__ = "1.0.0"
__all__ = []

# Import what actually exists - using try/except to be safe
try:
    from ultracore.lending import loan_models
    __all__.append('loan_models')
except ImportError:
    pass

try:
    from ultracore.lending import loan_manager
    __all__.append('loan_manager')
except ImportError:
    pass

try:
    from ultracore.lending import underwriting
    __all__.append('underwriting')
except ImportError:
    pass

try:
    from ultracore.lending import servicing
    __all__.append('servicing')
except ImportError:
    pass

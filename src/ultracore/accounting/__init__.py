"""
UltraCore Accounting Module

General Ledger, Chart of Accounts, Journal Entries
"""

__version__ = "1.0.0"
__all__ = []

# Import what actually exists
try:
    from ultracore.accounting import general_ledger
    __all__.extend(['general_ledger'])
except ImportError:
    pass

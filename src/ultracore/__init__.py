"""
UltraCore Banking Platform

A complete, AI-native core banking platform with:
- Customer Management (KYC/AML, Graph, AI Agents)
- Account Management (Deposits, Transactions, Payment Rails)
- Loan Management (Lending, Servicing, Collections)
- General Ledger (Accounting)
- Audit & Compliance (Regulatory)

Version: 1.0.0
License: Proprietary
"""

__version__ = "1.0.0"
__author__ = "UltraCore Team"
__license__ = "Proprietary"

# Package metadata
__all__ = [
    'accounting',
    'audit',
    'lending',
    'customers',
    'accounts',
]

# Version info
def get_version():
    """Get UltraCore version"""
    return __version__

# System info
def get_info():
    """Get system information"""
    return {
        'version': __version__,
        'modules': __all__,
        'author': __author__,
        'license': __license__
    }

# Lazy imports - only import when needed to avoid circular dependencies
def get_general_ledger():
    """Get general ledger instance"""
    from ultracore.accounting import general_ledger
    return general_ledger.get_general_ledger()

def get_audit_store():
    """Get audit store instance"""
    from ultracore.audit import audit_core
    return audit_core.get_audit_store()

def get_customer_manager():
    """Get customer manager instance"""
    from ultracore.customers.core import customer_manager
    return customer_manager.get_customer_manager()

def get_account_manager():
    """Get account manager instance"""
    from ultracore.accounts.core import account_manager
    return account_manager.get_account_manager()

def get_loan_manager():
    """Get loan manager instance"""
    from ultracore.lending import loan_manager
    return loan_manager.get_loan_manager()

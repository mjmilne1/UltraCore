"""
UltraCore Repositories

Data access layer with repository pattern
"""

from ultracore.database.repositories.base import BaseRepository
from ultracore.database.repositories.customer_repository import (
    CustomerRepository,
    CustomerRelationshipRepository
)
from ultracore.database.repositories.account_repository import (
    AccountRepository,
    TransactionRepository
)
from ultracore.database.repositories.loan_repository import (
    LoanRepository,
    LoanPaymentRepository
)

__all__ = [
    'BaseRepository',
    'CustomerRepository',
    'CustomerRelationshipRepository',
    'AccountRepository',
    'TransactionRepository',
    'LoanRepository',
    'LoanPaymentRepository',
]

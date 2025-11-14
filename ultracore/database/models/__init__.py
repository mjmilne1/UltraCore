"""
Database Models
"""

from ultracore.database.models.savings import (
    SavingsAccountModel,
    SavingsTransactionModel,
    SavingsProductModel,
    TermDepositModel,
)

__all__ = [
    "SavingsAccountModel",
    "SavingsTransactionModel",
    "SavingsProductModel",
    "TermDepositModel",
]

"""
Savings Domain Models
Australian-compliant savings and deposit account models
"""

from ultracore.domains.savings.models.savings_account import (
    SavingsAccount,
    SavingsAccountType,
    AccountStatus,
    TFNExemption,
)
from ultracore.domains.savings.models.savings_product import (
    SavingsProduct,
    ProductType,
    InterestCalculationMethod,
    InterestPostingFrequency,
    BonusCondition,
    FeeWaiverCondition,
)
from ultracore.domains.savings.models.term_deposit import (
    TermDeposit,
    TermDepositStatus,
    InterestPaymentFrequency,
)
from ultracore.domains.savings.models.transaction import (
    SavingsTransaction,
    TransactionType,
    TransactionStatus,
)

__all__ = [
    "SavingsAccount",
    "SavingsAccountType",
    "AccountStatus",
    "TFNExemption",
    "SavingsProduct",
    "ProductType",
    "InterestCalculationMethod",
    "InterestPostingFrequency",
    "BonusCondition",
    "FeeWaiverCondition",
    "TermDeposit",
    "TermDepositStatus",
    "InterestPaymentFrequency",
    "SavingsTransaction",
    "TransactionType",
    "TransactionStatus",
]

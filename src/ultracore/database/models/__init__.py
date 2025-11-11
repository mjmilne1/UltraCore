"""
UltraCore Database Models

All SQLAlchemy models for the platform
"""

from ultracore.database.models.base import Base, BaseModel
from ultracore.database.models.events import EventStore
from ultracore.database.models.customers import (
    Customer,
    CustomerRelationship,
    CustomerTypeEnum,
    CustomerStatusEnum,
    RiskRatingEnum,
    KYCStatusEnum
)
from ultracore.database.models.accounts import (
    Account,
    AccountBalance,
    Transaction,
    AccountTypeEnum,
    AccountStatusEnum,
    TransactionTypeEnum,
    TransactionStatusEnum
)
from ultracore.database.models.loans import (
    Loan,
    LoanPaymentSchedule,
    LoanPayment,
    LoanCollateral,
    LoanTypeEnum,
    LoanStatusEnum,
    PaymentStatusEnum,
    RepaymentFrequencyEnum
)

__all__ = [
    # Base
    'Base',
    'BaseModel',
    
    # Events
    'EventStore',
    
    # Customers
    'Customer',
    'CustomerRelationship',
    'CustomerTypeEnum',
    'CustomerStatusEnum',
    'RiskRatingEnum',
    'KYCStatusEnum',
    
    # Accounts
    'Account',
    'AccountBalance',
    'Transaction',
    'AccountTypeEnum',
    'AccountStatusEnum',
    'TransactionTypeEnum',
    'TransactionStatusEnum',
    
    # Loans
    'Loan',
    'LoanPaymentSchedule',
    'LoanPayment',
    'LoanCollateral',
    'LoanTypeEnum',
    'LoanStatusEnum',
    'PaymentStatusEnum',
    'RepaymentFrequencyEnum',
]

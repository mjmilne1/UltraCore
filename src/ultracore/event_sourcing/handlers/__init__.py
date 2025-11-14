"""Domain event handlers."""

from .customer_handler import CustomerEventHandler
from .account_handler import AccountEventHandler
from .transaction_handler import TransactionEventHandler
from .payment_handler import PaymentEventHandler
from .loan_handler import LoanEventHandler
from .investment_handler import InvestmentEventHandler
from .compliance_handler import ComplianceEventHandler
from .risk_handler import RiskEventHandler
from .collateral_handler import CollateralEventHandler
from .notification_handler import NotificationEventHandler
from .audit_handler import AuditEventHandler
from .analytics_handler import AnalyticsEventHandler
from .system_handler import SystemEventHandler

__all__ = [
    "CustomerEventHandler",
    "AccountEventHandler",
    "TransactionEventHandler",
    "PaymentEventHandler",
    "LoanEventHandler",
    "InvestmentEventHandler",
    "ComplianceEventHandler",
    "RiskEventHandler",
    "CollateralEventHandler",
    "NotificationEventHandler",
    "AuditEventHandler",
    "AnalyticsEventHandler",
    "SystemEventHandler",
]

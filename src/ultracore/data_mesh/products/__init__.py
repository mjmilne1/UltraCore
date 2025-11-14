"""
Data Products.

Domain data products for the Data Mesh.
"""

from .base import (
    DataProduct,
    AggregatedDataProduct,
    StreamingDataProduct,
    DataProductMetadata,
    DataProductSchema,
    DataQualityMetrics,
    DataLineage,
    DataQualityLevel,
    RefreshFrequency,
    DataProductStatus
)
from .customer360 import Customer360
from .financial_products import (
    AccountBalances,
    TransactionHistory,
    PaymentAnalytics,
    LoanPortfolio
)

__all__ = [
    # Base classes
    "DataProduct",
    "AggregatedDataProduct",
    "StreamingDataProduct",
    "DataProductMetadata",
    "DataProductSchema",
    "DataQualityMetrics",
    "DataLineage",
    "DataQualityLevel",
    "RefreshFrequency",
    "DataProductStatus",
    
    # Data products
    "Customer360",
    "AccountBalances",
    "TransactionHistory",
    "PaymentAnalytics",
    "LoanPortfolio",
]

# TODO: Add remaining 10 data products:
# - InvestmentPerformance
# - RiskMetrics
# - ComplianceReports
# - FraudSignals
# - CustomerSegments
# - ProductUsage
# - ChannelAnalytics
# - OperationalMetrics
# - FinancialReporting
# - RegulatoryReporting

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
from .wealth_risk_products import (
    InvestmentPerformance,
    RiskMetrics,
    FraudSignals
)
from .compliance_products import (
    ComplianceReports,
    RegulatoryReporting
)
from .analytics_products import (
    CustomerSegments,
    ProductUsage,
    ChannelAnalytics
)
from .reporting_products import (
    OperationalMetrics,
    FinancialReporting
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
    "InvestmentPerformance",
    "RiskMetrics",
    "FraudSignals",
    "ComplianceReports",
    "RegulatoryReporting",
    "CustomerSegments",
    "ProductUsage",
    "ChannelAnalytics",
    "OperationalMetrics",
    "FinancialReporting",
]

"""
Client Management Module
Enhanced client management and KYC system with full UltraCore architecture
"""

from .events import (
    ClientManagementEvent,
    ClientProfileCreatedEvent,
    DocumentUploadedEvent,
    RiskQuestionnaireCompletedEvent,
    InvestmentGoalCreatedEvent,
    BeneficiaryAddedEvent,
    FamilyPortfolioCreatedEvent
)
from .event_publisher import get_event_publisher, ClientManagementTopic
from .aggregates import (
    ClientProfileAggregate,
    DocumentAggregate,
    RiskProfileAggregate,
    InvestmentGoalAggregate,
    BeneficiaryAggregate,
    FamilyPortfolioAggregate
)

__all__ = [
    # Events
    "ClientManagementEvent",
    "ClientProfileCreatedEvent",
    "DocumentUploadedEvent",
    "RiskQuestionnaireCompletedEvent",
    "InvestmentGoalCreatedEvent",
    "BeneficiaryAddedEvent",
    "FamilyPortfolioCreatedEvent",
    # Event Publisher
    "get_event_publisher",
    "ClientManagementTopic",
    # Aggregates
    "ClientProfileAggregate",
    "DocumentAggregate",
    "RiskProfileAggregate",
    "InvestmentGoalAggregate",
    "BeneficiaryAggregate",
    "FamilyPortfolioAggregate"
]

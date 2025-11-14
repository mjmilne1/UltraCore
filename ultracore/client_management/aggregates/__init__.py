"""Client Management Aggregates"""

from .client_profile import ClientProfileAggregate
from .document import DocumentAggregate
from .risk_profile import RiskProfileAggregate
from .investment_goal import InvestmentGoalAggregate
from .beneficiary import BeneficiaryAggregate, FamilyPortfolioAggregate

__all__ = [
    "ClientProfileAggregate",
    "DocumentAggregate",
    "RiskProfileAggregate",
    "InvestmentGoalAggregate",
    "BeneficiaryAggregate",
    "FamilyPortfolioAggregate"
]

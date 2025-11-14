"""
Client Management Event Schemas (Kafka-First)
All client management state changes flow through Kafka as immutable events
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


class ClientManagementTopic(str, Enum):
    """Kafka topics for client management events"""
    CLIENTS = "client_management.clients"
    DOCUMENTS = "client_management.documents"
    BENEFICIARIES = "client_management.beneficiaries"
    RISK_PROFILES = "client_management.risk_profiles"
    INVESTMENT_GOALS = "client_management.investment_goals"
    FAMILY_PORTFOLIOS = "client_management.family_portfolios"


class ClientManagementEvent(BaseModel):
    """Base event for all client management events"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    event_version: int = 1
    aggregate_type: str
    aggregate_id: str
    event_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tenant_id: str
    user_id: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    event_data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


# ============================================================================
# CLIENT PROFILE EVENTS (Topic: client_management.clients)
# ============================================================================

class ClientProfileCreatedEvent(ClientManagementEvent):
    """Client profile created"""
    event_type: str = "client_profile_created"
    aggregate_type: str = "client_profile"


class ClientProfileUpdatedEvent(ClientManagementEvent):
    """Client profile updated"""
    event_type: str = "client_profile_updated"
    aggregate_type: str = "client_profile"


class ClientInvestmentHistoryRecordedEvent(ClientManagementEvent):
    """Investment history recorded"""
    event_type: str = "client_investment_history_recorded"
    aggregate_type: str = "client_profile"


class ClientFinancialHealthScoredEvent(ClientManagementEvent):
    """Financial health score calculated"""
    event_type: str = "client_financial_health_scored"
    aggregate_type: str = "client_profile"


# ============================================================================
# DOCUMENT EVENTS (Topic: client_management.documents)
# ============================================================================

class DocumentUploadedEvent(ClientManagementEvent):
    """Document uploaded"""
    event_type: str = "document_uploaded"
    aggregate_type: str = "document"


class DocumentVerifiedEvent(ClientManagementEvent):
    """Document verified"""
    event_type: str = "document_verified"
    aggregate_type: str = "document"


class DocumentRejectedEvent(ClientManagementEvent):
    """Document rejected"""
    event_type: str = "document_rejected"
    aggregate_type: str = "document"


class DocumentExpiredEvent(ClientManagementEvent):
    """Document expired"""
    event_type: str = "document_expired"
    aggregate_type: str = "document"


# ============================================================================
# BENEFICIARY EVENTS (Topic: client_management.beneficiaries)
# ============================================================================

class BeneficiaryAddedEvent(ClientManagementEvent):
    """Beneficiary added to account"""
    event_type: str = "beneficiary_added"
    aggregate_type: str = "beneficiary"


class BeneficiaryUpdatedEvent(ClientManagementEvent):
    """Beneficiary information updated"""
    event_type: str = "beneficiary_updated"
    aggregate_type: str = "beneficiary"


class BeneficiaryRemovedEvent(ClientManagementEvent):
    """Beneficiary removed"""
    event_type: str = "beneficiary_removed"
    aggregate_type: str = "beneficiary"


# ============================================================================
# RISK PROFILE EVENTS (Topic: client_management.risk_profiles)
# ============================================================================

class RiskQuestionnaireCompletedEvent(ClientManagementEvent):
    """Risk questionnaire completed"""
    event_type: str = "risk_questionnaire_completed"
    aggregate_type: str = "risk_profile"


class RiskScoreCalculatedEvent(ClientManagementEvent):
    """Risk score calculated"""
    event_type: str = "risk_score_calculated"
    aggregate_type: str = "risk_profile"


class RiskProfileUpdatedEvent(ClientManagementEvent):
    """Risk profile updated"""
    event_type: str = "risk_profile_updated"
    aggregate_type: str = "risk_profile"


# ============================================================================
# INVESTMENT GOAL EVENTS (Topic: client_management.investment_goals)
# ============================================================================

class InvestmentGoalCreatedEvent(ClientManagementEvent):
    """Investment goal created"""
    event_type: str = "investment_goal_created"
    aggregate_type: str = "investment_goal"


class InvestmentGoalProgressUpdatedEvent(ClientManagementEvent):
    """Investment goal progress updated"""
    event_type: str = "investment_goal_progress_updated"
    aggregate_type: str = "investment_goal"


class InvestmentGoalAchievedEvent(ClientManagementEvent):
    """Investment goal achieved"""
    event_type: str = "investment_goal_achieved"
    aggregate_type: str = "investment_goal"


class InvestmentGoalModifiedEvent(ClientManagementEvent):
    """Investment goal modified"""
    event_type: str = "investment_goal_modified"
    aggregate_type: str = "investment_goal"


# ============================================================================
# FAMILY PORTFOLIO EVENTS (Topic: client_management.family_portfolios)
# ============================================================================

class FamilyPortfolioCreatedEvent(ClientManagementEvent):
    """Family portfolio created"""
    event_type: str = "family_portfolio_created"
    aggregate_type: str = "family_portfolio"


class FamilyMemberAddedEvent(ClientManagementEvent):
    """Family member added to portfolio"""
    event_type: str = "family_member_added"
    aggregate_type: str = "family_portfolio"


class FamilyMemberRemovedEvent(ClientManagementEvent):
    """Family member removed from portfolio"""
    event_type: str = "family_member_removed"
    aggregate_type: str = "family_portfolio"


class JointAccountCreatedEvent(ClientManagementEvent):
    """Joint account created"""
    event_type: str = "joint_account_created"
    aggregate_type: str = "family_portfolio"

"""
Compliance Event Schemas (Kafka-First)
All compliance state changes flow through Kafka as immutable events
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


class ComplianceTopic(str, Enum):
    """Kafka topics for compliance events"""
    AML = "compliance.aml"
    DISPUTES = "compliance.disputes"
    CLIENT_MONEY = "compliance.client_money"
    RISK = "compliance.risk"
    DISCLOSURES = "compliance.disclosures"
    AUDIT = "compliance.audit"


class ComplianceEvent(BaseModel):
    """Base event for all compliance events"""
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


# AML Events
class CustomerIdentifiedEvent(ComplianceEvent):
    event_type: str = "customer_identified"
    aggregate_type: str = "customer"

class CustomerVerifiedEvent(ComplianceEvent):
    event_type: str = "customer_verified"
    aggregate_type: str = "customer"

class TransactionMonitoredEvent(ComplianceEvent):
    event_type: str = "transaction_monitored"
    aggregate_type: str = "transaction_monitoring"

class SuspiciousActivityDetectedEvent(ComplianceEvent):
    event_type: str = "suspicious_activity_detected"
    aggregate_type: str = "transaction_monitoring"

class SMRFiledEvent(ComplianceEvent):
    event_type: str = "smr_filed"
    aggregate_type: str = "smr"


# Dispute Events
class ComplaintSubmittedEvent(ComplianceEvent):
    event_type: str = "complaint_submitted"
    aggregate_type: str = "complaint"

class ComplaintAcknowledgedEvent(ComplianceEvent):
    event_type: str = "complaint_acknowledged"
    aggregate_type: str = "complaint"

class ComplaintResolvedEvent(ComplianceEvent):
    event_type: str = "complaint_resolved"
    aggregate_type: str = "complaint"

class ComplaintEscalatedAFCAEvent(ComplianceEvent):
    event_type: str = "complaint_escalated_afca"
    aggregate_type: str = "complaint"


# Client Money Events
class ClientAccountCreatedEvent(ComplianceEvent):
    event_type: str = "client_account_created"
    aggregate_type: str = "client_account"

class ClientMoneyTransactionRecordedEvent(ComplianceEvent):
    event_type: str = "client_money_transaction_recorded"
    aggregate_type: str = "client_account"

class ReconciliationPerformedEvent(ComplianceEvent):
    event_type: str = "reconciliation_performed"
    aggregate_type: str = "reconciliation"

class VarianceDetectedEvent(ComplianceEvent):
    event_type: str = "variance_detected"
    aggregate_type: str = "reconciliation"


# Risk Events
class RiskAssessedEvent(ComplianceEvent):
    event_type: str = "risk_assessed"
    aggregate_type: str = "risk_assessment"

class ReportableSituationIdentifiedEvent(ComplianceEvent):
    event_type: str = "reportable_situation_identified"
    aggregate_type: str = "reportable_situation"

class SituationReportedASICEvent(ComplianceEvent):
    event_type: str = "situation_reported_asic"
    aggregate_type: str = "reportable_situation"


# Disclosure Events
class DocumentGeneratedEvent(ComplianceEvent):
    event_type: str = "document_generated"
    aggregate_type: str = "disclosure_document"

class DocumentDeliveredEvent(ComplianceEvent):
    event_type: str = "document_delivered"
    aggregate_type: str = "disclosure_document"


# Audit Events
class AuditLogCreatedEvent(ComplianceEvent):
    event_type: str = "audit_log_created"
    aggregate_type: str = "audit_log"

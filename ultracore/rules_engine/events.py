"""
Rules Engine Events
Kafka event schemas for business rules and workflows
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class RuleType(Enum):
    """Types of business rules"""
    REBALANCING = "rebalancing"
    ALERT = "alert"
    INVESTMENT_LIMIT = "investment_limit"
    RISK_MANAGEMENT = "risk_management"
    TAX_LOSS_HARVESTING = "tax_loss_harvesting"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class RuleStatus(Enum):
    """Rule status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WorkflowStatus(Enum):
    """Workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConditionOperator(Enum):
    """Condition operators"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    MATCHES = "matches"


class ActionType(Enum):
    """Action types"""
    SEND_ALERT = "send_alert"
    REBALANCE_PORTFOLIO = "rebalance_portfolio"
    BLOCK_TRANSACTION = "block_transaction"
    REQUIRE_APPROVAL = "require_approval"
    EXECUTE_TRADE = "execute_trade"
    UPDATE_LIMIT = "update_limit"
    TRIGGER_WORKFLOW = "trigger_workflow"
    LOG_EVENT = "log_event"


# Kafka Topics
RULES_TOPIC = "rules_engine.rules"
WORKFLOWS_TOPIC = "rules_engine.workflows"
APPROVALS_TOPIC = "rules_engine.approvals"
EXECUTIONS_TOPIC = "rules_engine.executions"


@dataclass
class RuleCreated:
    """Rule created event"""
    event_type: str = "RuleCreated"
    tenant_id: str = ""
    rule_id: str = ""
    name: str = ""
    rule_type: RuleType = RuleType.CUSTOM
    description: Optional[str] = None
    conditions: List[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = None
    priority: int = 0
    created_by: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
        if self.actions is None:
            self.actions = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class RuleActivated:
    """Rule activated event"""
    event_type: str = "RuleActivated"
    tenant_id: str = ""
    rule_id: str = ""
    activated_by: str = ""
    activated_at: datetime = None
    
    def __post_init__(self):
        if self.activated_at is None:
            self.activated_at = datetime.utcnow()


@dataclass
class RulePaused:
    """Rule paused event"""
    event_type: str = "RulePaused"
    tenant_id: str = ""
    rule_id: str = ""
    reason: Optional[str] = None
    paused_by: str = ""
    paused_at: datetime = None
    
    def __post_init__(self):
        if self.paused_at is None:
            self.paused_at = datetime.utcnow()


@dataclass
class RuleExecuted:
    """Rule executed event"""
    event_type: str = "RuleExecuted"
    tenant_id: str = ""
    rule_id: str = ""
    execution_id: str = ""
    matched_conditions: List[str] = None
    executed_actions: List[Dict[str, Any]] = None
    context: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None
    executed_at: datetime = None
    execution_time_ms: int = 0
    
    def __post_init__(self):
        if self.matched_conditions is None:
            self.matched_conditions = []
        if self.executed_actions is None:
            self.executed_actions = []
        if self.context is None:
            self.context = {}
        if self.executed_at is None:
            self.executed_at = datetime.utcnow()


@dataclass
class WorkflowCreated:
    """Workflow created event"""
    event_type: str = "WorkflowCreated"
    tenant_id: str = ""
    workflow_id: str = ""
    workflow_type: str = ""
    title: str = ""
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = None
    required_approvers: List[str] = None
    created_by: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.required_approvers is None:
            self.required_approvers = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WorkflowStepCompleted:
    """Workflow step completed event"""
    event_type: str = "WorkflowStepCompleted"
    tenant_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    completed_by: str = ""
    result: Dict[str, Any] = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.result is None:
            self.result = {}
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()


@dataclass
class ApprovalRequested:
    """Approval requested event"""
    event_type: str = "ApprovalRequested"
    tenant_id: str = ""
    approval_id: str = ""
    workflow_id: Optional[str] = None
    request_type: str = ""
    title: str = ""
    description: Optional[str] = None
    required_approvers: List[str] = None
    approval_data: Dict[str, Any] = None
    expires_at: Optional[datetime] = None
    requested_by: str = ""
    requested_at: datetime = None
    
    def __post_init__(self):
        if self.required_approvers is None:
            self.required_approvers = []
        if self.approval_data is None:
            self.approval_data = {}
        if self.requested_at is None:
            self.requested_at = datetime.utcnow()


@dataclass
class ApprovalGranted:
    """Approval granted event"""
    event_type: str = "ApprovalGranted"
    tenant_id: str = ""
    approval_id: str = ""
    approver_id: str = ""
    comments: Optional[str] = None
    approved_at: datetime = None
    
    def __post_init__(self):
        if self.approved_at is None:
            self.approved_at = datetime.utcnow()


@dataclass
class ApprovalRejected:
    """Approval rejected event"""
    event_type: str = "ApprovalRejected"
    tenant_id: str = ""
    approval_id: str = ""
    approver_id: str = ""
    reason: str = ""
    rejected_at: datetime = None
    
    def __post_init__(self):
        if self.rejected_at is None:
            self.rejected_at = datetime.utcnow()

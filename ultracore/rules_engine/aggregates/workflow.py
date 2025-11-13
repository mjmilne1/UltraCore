"""
Workflow and Approval Aggregates
Event-sourced aggregates for workflows and approvals
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from ultracore.rules_engine.events import (
    WorkflowStatus, ApprovalStatus,
    WorkflowCreated, WorkflowStepCompleted,
    ApprovalRequested, ApprovalGranted, ApprovalRejected
)
from ultracore.rules_engine.event_publisher import get_rules_event_publisher


@dataclass
class WorkflowAggregate:
    """Event-sourced aggregate for workflows"""
    
    tenant_id: str
    workflow_id: str
    workflow_type: str = ""
    title: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[Dict[str, Any]] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    _events: List[Any] = field(default_factory=list)
    
    def create(self, workflow_type: str, title: str, description: Optional[str],
               steps: List[Dict[str, Any]], required_approvers: List[str], created_by: str):
        event = WorkflowCreated(
            tenant_id=self.tenant_id, workflow_id=self.workflow_id,
            workflow_type=workflow_type, title=title, description=description,
            steps=steps, required_approvers=required_approvers,
            created_by=created_by, created_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_rules_event_publisher().publish_workflow_event(event)
    
    def complete_step(self, step_id: str, completed_by: str, result: Dict[str, Any]):
        event = WorkflowStepCompleted(
            tenant_id=self.tenant_id, workflow_id=self.workflow_id,
            step_id=step_id, completed_by=completed_by, result=result,
            completed_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_rules_event_publisher().publish_workflow_event(event)
    
    def _apply_event(self, event: Any):
        if isinstance(event, WorkflowCreated):
            self.workflow_type, self.title = event.workflow_type, event.title
            self.steps, self.status = event.steps, WorkflowStatus.IN_PROGRESS
        elif isinstance(event, WorkflowStepCompleted):
            self.completed_steps.append(event.step_id)
            if len(self.completed_steps) == len(self.steps):
                self.status = WorkflowStatus.APPROVED
        self._events.append(event)


@dataclass
class ApprovalAggregate:
    """Event-sourced aggregate for approvals (four eyes principle)"""
    
    tenant_id: str
    approval_id: str
    request_type: str = ""
    title: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    required_approvers: List[str] = field(default_factory=list)
    approvals: List[str] = field(default_factory=list)
    _events: List[Any] = field(default_factory=list)
    
    def request(self, workflow_id: Optional[str], request_type: str, title: str,
                description: Optional[str], required_approvers: List[str],
                approval_data: Dict[str, Any], expires_at: Optional[datetime],
                requested_by: str):
        event = ApprovalRequested(
            tenant_id=self.tenant_id, approval_id=self.approval_id,
            workflow_id=workflow_id, request_type=request_type, title=title,
            description=description, required_approvers=required_approvers,
            approval_data=approval_data, expires_at=expires_at,
            requested_by=requested_by, requested_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_rules_event_publisher().publish_approval_event(event)
    
    def approve(self, approver_id: str, comments: Optional[str]):
        if approver_id not in self.required_approvers:
            raise ValueError("Approver not in required approvers list")
        event = ApprovalGranted(
            tenant_id=self.tenant_id, approval_id=self.approval_id,
            approver_id=approver_id, comments=comments, approved_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_rules_event_publisher().publish_approval_event(event)
    
    def reject(self, approver_id: str, reason: str):
        event = ApprovalRejected(
            tenant_id=self.tenant_id, approval_id=self.approval_id,
            approver_id=approver_id, reason=reason, rejected_at=datetime.utcnow()
        )
        self._apply_event(event)
        get_rules_event_publisher().publish_approval_event(event)
    
    def _apply_event(self, event: Any):
        if isinstance(event, ApprovalRequested):
            self.request_type, self.title = event.request_type, event.title
            self.required_approvers = event.required_approvers
        elif isinstance(event, ApprovalGranted):
            self.approvals.append(event.approver_id)
            if len(self.approvals) >= len(self.required_approvers):
                self.status = ApprovalStatus.APPROVED
        elif isinstance(event, ApprovalRejected):
            self.status = ApprovalStatus.REJECTED
        self._events.append(event)

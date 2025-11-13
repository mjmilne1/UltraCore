"""
UltraCore Loan Management - Collections Manager

Collections workflow and actions:
- Collections strategy
- Automated reminders
- Escalation rules
- Collections actions
- Hardship programs
- Write-off process
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid

from ultracore.lending.servicing.loan_account import LoanAccount, LoanStatus
from ultracore.lending.collections.delinquency_tracker import (
    get_delinquency_tracker, DelinquencyBucket, ContactAttemptType,
    ContactOutcome
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Collections Enums
# ============================================================================

class CollectionsStage(str, Enum):
    """Collections process stage"""
    EARLY_STAGE = "EARLY_STAGE"  # 1-30 days
    MID_STAGE = "MID_STAGE"  # 31-90 days
    LATE_STAGE = "LATE_STAGE"  # 91-180 days
    LEGAL = "LEGAL"  # 180+ days
    RECOVERY = "RECOVERY"  # Post legal action


class CollectionsAction(str, Enum):
    """Types of collections actions"""
    PAYMENT_REMINDER = "PAYMENT_REMINDER"
    PHONE_CALL = "PHONE_CALL"
    DEMAND_LETTER = "DEMAND_LETTER"
    FIELD_VISIT = "FIELD_VISIT"
    LEGAL_NOTICE = "LEGAL_NOTICE"
    ASSET_SEIZURE = "ASSET_SEIZURE"
    WRITE_OFF = "WRITE_OFF"


class HardshipType(str, Enum):
    """Type of financial hardship"""
    UNEMPLOYMENT = "UNEMPLOYMENT"
    ILLNESS = "ILLNESS"
    FAMILY_CRISIS = "FAMILY_CRISIS"
    BUSINESS_FAILURE = "BUSINESS_FAILURE"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    OTHER = "OTHER"


class HardshipResolution(str, Enum):
    """Hardship resolution options"""
    PAYMENT_PLAN = "PAYMENT_PLAN"
    PAYMENT_HOLIDAY = "PAYMENT_HOLIDAY"
    RATE_REDUCTION = "RATE_REDUCTION"
    TERM_EXTENSION = "TERM_EXTENSION"
    PARTIAL_FORGIVENESS = "PARTIAL_FORGIVENESS"
    SETTLEMENT = "SETTLEMENT"


class WriteOffReason(str, Enum):
    """Reason for write-off"""
    UNCOLLECTABLE = "UNCOLLECTABLE"
    BANKRUPTCY = "BANKRUPTCY"
    DECEASED = "DECEASED"
    STATUTE_BARRED = "STATUTE_BARRED"
    SETTLEMENT = "SETTLEMENT"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CollectionsCase:
    """Collections case for delinquent account"""
    case_id: str
    loan_account_id: str
    stage: CollectionsStage
    assigned_to: Optional[str] = None
    assigned_date: Optional[datetime] = None
    active: bool = True
    closed: bool = False
    closed_date: Optional[datetime] = None
    close_reason: Optional[str] = None
    action_count: int = 0
    last_action_date: Optional[datetime] = None
    next_action_date: Optional[date] = None
    promise_count: int = 0
    broken_promise_count: int = 0
    escalated: bool = False
    escalation_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: List[str] = field(default_factory=list)


@dataclass
class CollectionsActionRecord:
    """Record of a collections action"""
    action_id: str
    case_id: str
    loan_account_id: str
    action_type: CollectionsAction
    action_date: datetime
    description: str
    outcome: Optional[str] = None
    action_cost: Decimal = Decimal('0.00')
    agent_id: str = ""
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HardshipApplication:
    """Financial hardship application"""
    application_id: str
    loan_account_id: str
    customer_id: str
    hardship_type: HardshipType
    hardship_description: str
    hardship_start_date: date
    expected_duration_months: int
    income_reduction_percent: Optional[Decimal] = None
    current_expenses: Optional[Decimal] = None
    requested_resolution: HardshipResolution
    requested_details: Optional[str] = None
    documents: List[str] = field(default_factory=list)
    assessed: bool = False
    assessed_date: Optional[datetime] = None
    assessed_by: Optional[str] = None
    approved: bool = False
    approval_date: Optional[datetime] = None
    approved_resolution: Optional[HardshipResolution] = None
    decline_reason: Optional[str] = None
    active: bool = False
    end_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WriteOff:
    """Loan write-off record"""
    writeoff_id: str
    loan_account_id: str
    writeoff_date: date
    writeoff_reason: WriteOffReason
    principal_written_off: Decimal
    interest_written_off: Decimal
    fees_written_off: Decimal
    total_written_off: Decimal
    recoverable: bool = False
    recovery_expected: Optional[Decimal] = None
    approved_by: str = ""
    approval_date: date = field(default_factory=date.today)
    gl_entry_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# ============================================================================
# Collections Manager
# ============================================================================

class CollectionsManager:
    """Collections management system"""
    
    def __init__(self):
        self.cases: Dict[str, CollectionsCase] = {}
        self.actions: Dict[str, CollectionsActionRecord] = {}
        self.hardship_applications: Dict[str, HardshipApplication] = {}
        self.writeoffs: Dict[str, WriteOff] = {}
        self.delinquency_tracker = get_delinquency_tracker()
        self.audit_store = get_audit_store()
        self.auto_escalate_days = 90
        self.max_contact_attempts = 10
    
    async def create_collections_case(self, loan_account: LoanAccount) -> CollectionsCase:
        """Create collections case for delinquent account"""
        case_id = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        dpd = loan_account.days_past_due
        
        if dpd <= 30:
            stage = CollectionsStage.EARLY_STAGE
        elif dpd <= 90:
            stage = CollectionsStage.MID_STAGE
        elif dpd <= 180:
            stage = CollectionsStage.LATE_STAGE
        else:
            stage = CollectionsStage.LEGAL
        
        case = CollectionsCase(
            case_id=case_id,
            loan_account_id=loan_account.account_id,
            stage=stage,
            next_action_date=date.today()
        )
        
        self.cases[case_id] = case
        return case
    
    async def send_payment_reminder(self, loan_account: LoanAccount, reminder_type: str = "EMAIL") -> CollectionsActionRecord:
        """Send automated payment reminder"""
        case = await self._get_or_create_case(loan_account)
        action_id = f"ACT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        action = CollectionsActionRecord(
            action_id=action_id,
            case_id=case.case_id,
            loan_account_id=loan_account.account_id,
            action_type=CollectionsAction.PAYMENT_REMINDER,
            action_date=datetime.now(timezone.utc),
            description=f"Payment reminder sent via {reminder_type}",
            outcome="SENT",
            agent_id="SYSTEM"
        )
        
        self.actions[action_id] = action
        case.action_count += 1
        case.last_action_date = datetime.now(timezone.utc)
        case.next_action_date = date.today() + timedelta(days=7)
        case.updated_at = datetime.now(timezone.utc)
        
        await self.delinquency_tracker.record_contact_attempt(
            loan_account_id=loan_account.account_id,
            contact_type=ContactAttemptType.EMAIL if reminder_type == "EMAIL" else ContactAttemptType.SMS,
            outcome=ContactOutcome.LEFT_MESSAGE,
            agent_id="SYSTEM",
            notes=f"Automated {reminder_type} reminder sent"
        )
        
        return action
    
    async def schedule_phone_call(self, loan_account: LoanAccount, agent_id: str, call_date: date) -> CollectionsActionRecord:
        """Schedule phone call with customer"""
        case = await self._get_or_create_case(loan_account)
        action_id = f"ACT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        action = CollectionsActionRecord(
            action_id=action_id,
            case_id=case.case_id,
            loan_account_id=loan_account.account_id,
            action_type=CollectionsAction.PHONE_CALL,
            action_date=datetime.now(timezone.utc),
            description="Phone call scheduled",
            agent_id=agent_id,
            follow_up_required=True,
            follow_up_date=call_date
        )
        
        self.actions[action_id] = action
        case.next_action_date = call_date
        case.updated_at = datetime.now(timezone.utc)
        
        return action
    
    async def record_phone_call_outcome(
        self,
        action_id: str,
        outcome: ContactOutcome,
        notes: Optional[str] = None,
        promise_to_pay_date: Optional[date] = None,
        promise_to_pay_amount: Optional[Decimal] = None
    ):
        """Record outcome of phone call"""
        action = self.actions.get(action_id)
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        action.outcome = outcome.value
        
        if notes:
            if 'notes' not in action.metadata:
                action.metadata['notes'] = []
            action.metadata['notes'].append(notes)
        
        await self.delinquency_tracker.record_contact_attempt(
            loan_account_id=action.loan_account_id,
            contact_type=ContactAttemptType.PHONE,
            outcome=outcome,
            agent_id=action.agent_id,
            notes=notes,
            promise_to_pay_date=promise_to_pay_date,
            promise_to_pay_amount=promise_to_pay_amount
        )
        
        case = self.cases.get(action.case_id)
        if case:
            if outcome == ContactOutcome.PROMISE_TO_PAY:
                case.promise_count += 1
                if promise_to_pay_date:
                    case.next_action_date = promise_to_pay_date
    
    async def send_demand_letter(self, loan_account: LoanAccount, agent_id: str) -> CollectionsActionRecord:
        """Send formal demand letter"""
        case = await self._get_or_create_case(loan_account)
        action_id = f"ACT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        action = CollectionsActionRecord(
            action_id=action_id,
            case_id=case.case_id,
            loan_account_id=loan_account.account_id,
            action_type=CollectionsAction.DEMAND_LETTER,
            action_date=datetime.now(timezone.utc),
            description="Formal demand letter sent",
            outcome="SENT",
            agent_id=agent_id,
            action_cost=Decimal('50.00')
        )
        
        self.actions[action_id] = action
        case.action_count += 1
        case.last_action_date = datetime.now(timezone.utc)
        case.next_action_date = date.today() + timedelta(days=14)
        case.updated_at = datetime.now(timezone.utc)
        
        return action
    
    async def escalate_to_legal(self, loan_account: LoanAccount, escalated_by: str) -> CollectionsCase:
        """Escalate account to legal stage"""
        case = await self._get_or_create_case(loan_account)
        
        case.stage = CollectionsStage.LEGAL
        case.escalated = True
        case.escalation_date = datetime.now(timezone.utc)
        case.updated_at = datetime.now(timezone.utc)
        case.notes.append(f"Escalated to legal by {escalated_by}")
        
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.WARNING,
            resource_type='collections_escalation',
            resource_id=case.case_id,
            action='escalated_to_legal',
            description=f"Account escalated to legal: {loan_account.account_id}",
            user_id=escalated_by,
            metadata={
                'loan_account_id': loan_account.account_id,
                'days_past_due': loan_account.days_past_due,
                'arrears': str(loan_account.current_balance.total_arrears)
            },
            regulatory_relevant=True
        )
        
        return case
    
    async def submit_hardship_application(
        self,
        loan_account: LoanAccount,
        customer_id: str,
        hardship_type: HardshipType,
        hardship_description: str,
        expected_duration_months: int,
        requested_resolution: HardshipResolution
    ) -> HardshipApplication:
        """Submit financial hardship application"""
        app_id = f"HARD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        application = HardshipApplication(
            application_id=app_id,
            loan_account_id=loan_account.account_id,
            customer_id=customer_id,
            hardship_type=hardship_type,
            hardship_description=hardship_description,
            hardship_start_date=date.today(),
            expected_duration_months=expected_duration_months,
            requested_resolution=requested_resolution
        )
        
        self.hardship_applications[app_id] = application
        return application
    
    async def assess_hardship_application(
        self,
        application_id: str,
        assessed_by: str,
        approved: bool,
        approved_resolution: Optional[HardshipResolution] = None,
        decline_reason: Optional[str] = None
    ) -> HardshipApplication:
        """Assess hardship application"""
        application = self.hardship_applications.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        application.assessed = True
        application.assessed_date = datetime.now(timezone.utc)
        application.assessed_by = assessed_by
        application.approved = approved
        
        if approved:
            application.approval_date = datetime.now(timezone.utc)
            application.approved_resolution = approved_resolution or application.requested_resolution
            application.active = True
            application.end_date = date.today() + timedelta(days=application.expected_duration_months * 30)
        else:
            application.decline_reason = decline_reason
        
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='hardship_assessment',
            resource_id=application_id,
            action='hardship_assessed',
            description=f"Hardship application {'approved' if approved else 'declined'}",
            user_id=assessed_by,
            metadata={
                'loan_account_id': application.loan_account_id,
                'hardship_type': application.hardship_type.value,
                'approved': approved,
                'resolution': approved_resolution.value if approved_resolution else None
            },
            regulatory_relevant=True
        )
        
        return application
    
    async def write_off_loan(
        self,
        loan_account: LoanAccount,
        writeoff_reason: WriteOffReason,
        approved_by: str,
        notes: Optional[str] = None
    ) -> WriteOff:
        """Write off uncollectable loan"""
        writeoff_id = f"WO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        balance = loan_account.current_balance
        
        writeoff = WriteOff(
            writeoff_id=writeoff_id,
            loan_account_id=loan_account.account_id,
            writeoff_date=date.today(),
            writeoff_reason=writeoff_reason,
            principal_written_off=balance.principal_outstanding,
            interest_written_off=balance.interest_accrued + balance.interest_in_arrears,
            fees_written_off=balance.fees_outstanding + balance.fees_in_arrears,
            total_written_off=balance.total_outstanding,
            approved_by=approved_by,
            notes=notes
        )
        
        self.writeoffs[writeoff_id] = writeoff
        
        loan_account.status = LoanStatus.WRITTEN_OFF
        loan_account.status_reason = f"Written off: {writeoff_reason.value}"
        loan_account.closed_date = date.today()
        
        balance.principal_outstanding = Decimal('0.00')
        balance.interest_accrued = Decimal('0.00')
        balance.interest_in_arrears = Decimal('0.00')
        balance.fees_outstanding = Decimal('0.00')
        balance.fees_in_arrears = Decimal('0.00')
        balance.penalties_outstanding = Decimal('0.00')
        balance.update_total()
        
        case = await self._get_case_by_account(loan_account.account_id)
        if case:
            case.active = False
            case.closed = True
            case.closed_date = datetime.now(timezone.utc)
            case.close_reason = f"Write-off: {writeoff_reason.value}"
        
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_DELETED,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.WARNING,
            resource_type='loan_writeoff',
            resource_id=writeoff_id,
            action='loan_written_off',
            description=f"Loan written off: ${writeoff.total_written_off}",
            user_id=approved_by,
            metadata={
                'loan_account_id': loan_account.account_id,
                'reason': writeoff_reason.value,
                'amount': str(writeoff.total_written_off)
            },
            regulatory_relevant=True
        )
        
        return writeoff
    
    async def _get_or_create_case(self, loan_account: LoanAccount) -> CollectionsCase:
        """Get existing case or create new one"""
        for case in self.cases.values():
            if (case.loan_account_id == loan_account.account_id and
                case.active and not case.closed):
                return case
        return await self.create_collections_case(loan_account)
    
    async def _get_case_by_account(self, loan_account_id: str) -> Optional[CollectionsCase]:
        """Get case by account ID"""
        for case in self.cases.values():
            if case.loan_account_id == loan_account_id and case.active:
                return case
        return None
    
    async def get_active_cases(self, stage: Optional[CollectionsStage] = None) -> List[CollectionsCase]:
        """Get active collections cases"""
        cases = [c for c in self.cases.values() if c.active and not c.closed]
        if stage:
            cases = [c for c in cases if c.stage == stage]
        return cases


_collections_manager: Optional[CollectionsManager] = None

def get_collections_manager() -> CollectionsManager:
    """Get the singleton collections manager"""
    global _collections_manager
    if _collections_manager is None:
        _collections_manager = CollectionsManager()
    return _collections_manager

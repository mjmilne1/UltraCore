"""
Compliance Domain Models.

Australian financial services compliance models including AML/CTF,
transaction monitoring, and regulatory reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class ComplianceCheckStatus(str, Enum):
    """Compliance check status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    ESCALATED = "escalated"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(str, Enum):
    """Regulatory report types."""
    AUSTRAC_TTR = "austrac_ttr"  # Threshold Transaction Report
    AUSTRAC_SMR = "austrac_smr"  # Suspicious Matter Report
    AUSTRAC_IFT = "austrac_ift"  # International Funds Transfer Instruction
    APRA_QUARTERLY = "apra_quarterly"
    APRA_ANNUAL = "apra_annual"


class ReportStatus(str, Enum):
    """Report submission status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"


class MonitoringRuleType(str, Enum):
    """Transaction monitoring rule types."""
    THRESHOLD = "threshold"
    VELOCITY = "velocity"
    PATTERN = "pattern"
    GEOGRAPHIC = "geographic"
    SANCTIONS = "sanctions"
    PEP = "pep"
    STRUCTURING = "structuring"


@dataclass
class ComplianceCheck:
    """
    Compliance Check aggregate.
    
    Represents a compliance check performed on a customer, transaction,
    or entity for AML/CTF compliance.
    """
    
    # Identity
    check_id: str = field(default_factory=lambda: f"chk_{uuid4().hex[:12]}")
    tenant_id: str = ""
    
    # Subject
    subject_type: str = ""  # customer, transaction, account
    subject_id: str = ""
    
    # Check details
    check_type: str = ""  # kyc, aml, sanctions, pep, transaction
    status: ComplianceCheckStatus = ComplianceCheckStatus.PENDING
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: Decimal = Decimal("0")
    
    # Results
    passed: bool = False
    findings: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    performed_by: str = ""  # user_id or "system"
    performed_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def start_check(self):
        """Start compliance check."""
        if self.status != ComplianceCheckStatus.PENDING:
            raise ValueError(f"Cannot start check in status: {self.status}")
        
        self.status = ComplianceCheckStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def complete_check(
        self,
        passed: bool,
        risk_level: RiskLevel,
        risk_score: Decimal,
        findings: List[Dict]
    ):
        """Complete compliance check with results."""
        if self.status != ComplianceCheckStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete check in status: {self.status}")
        
        self.passed = passed
        self.risk_level = risk_level
        self.risk_score = risk_score
        self.findings = findings
        
        if passed:
            self.status = ComplianceCheckStatus.PASSED
        elif risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.status = ComplianceCheckStatus.ESCALATED
        else:
            self.status = ComplianceCheckStatus.REQUIRES_REVIEW
        
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def escalate(self, reason: str):
        """Escalate check for manual review."""
        self.status = ComplianceCheckStatus.ESCALATED
        self.findings.append({
            "type": "escalation",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "tenant_id": self.tenant_id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "check_type": self.check_type,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "risk_score": float(self.risk_score),
            "passed": self.passed,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "performed_by": self.performed_by,
            "performed_at": self.performed_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }


@dataclass
class TransactionMonitoring:
    """
    Transaction Monitoring model.
    
    Real-time monitoring of transactions for suspicious activity.
    """
    
    # Identity
    monitoring_id: str = field(default_factory=lambda: f"mon_{uuid4().hex[:12]}")
    tenant_id: str = ""
    transaction_id: str = ""
    
    # Transaction details
    customer_id: str = ""
    account_id: str = ""
    amount: Decimal = Decimal("0")
    currency: str = "AUD"
    transaction_type: str = ""
    
    # Monitoring results
    rules_triggered: List[Dict] = field(default_factory=list)
    risk_score: Decimal = Decimal("0")
    risk_level: RiskLevel = RiskLevel.LOW
    flagged: bool = False
    
    # Alert
    alert_generated: bool = False
    alert_id: Optional[str] = None
    
    # Metadata
    monitored_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def add_rule_trigger(
        self,
        rule_type: MonitoringRuleType,
        rule_name: str,
        severity: str,
        details: Dict
    ):
        """Add triggered rule."""
        self.rules_triggered.append({
            "rule_type": rule_type.value,
            "rule_name": rule_name,
            "severity": severity,
            "details": details,
            "triggered_at": datetime.utcnow().isoformat()
        })
        self.flagged = True
        self.version += 1
    
    def calculate_risk_score(self) -> Decimal:
        """Calculate overall risk score from triggered rules."""
        if not self.rules_triggered:
            return Decimal("0")
        
        # Risk score calculation based on rule severity
        severity_weights = {
            "low": Decimal("10"),
            "medium": Decimal("25"),
            "high": Decimal("50"),
            "critical": Decimal("100")
        }
        
        total_score = sum(
            severity_weights.get(rule["severity"], Decimal("0"))
            for rule in self.rules_triggered
        )
        
        # Cap at 100
        self.risk_score = min(total_score, Decimal("100"))
        
        # Determine risk level
        if self.risk_score >= 75:
            self.risk_level = RiskLevel.CRITICAL
        elif self.risk_score >= 50:
            self.risk_level = RiskLevel.HIGH
        elif self.risk_score >= 25:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
        
        return self.risk_score
    
    def generate_alert(self, alert_id: str):
        """Generate compliance alert."""
        self.alert_generated = True
        self.alert_id = alert_id
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "monitoring_id": self.monitoring_id,
            "tenant_id": self.tenant_id,
            "transaction_id": self.transaction_id,
            "customer_id": self.customer_id,
            "account_id": self.account_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "transaction_type": self.transaction_type,
            "rules_triggered": self.rules_triggered,
            "risk_score": float(self.risk_score),
            "risk_level": self.risk_level.value,
            "flagged": self.flagged,
            "alert_generated": self.alert_generated,
            "alert_id": self.alert_id,
            "monitored_at": self.monitored_at.isoformat(),
            "version": self.version
        }


@dataclass
class SuspiciousActivity:
    """
    Suspicious Activity model.
    
    Represents a suspicious activity alert for AML/CTF compliance.
    """
    
    # Identity
    alert_id: str = field(default_factory=lambda: f"alert_{uuid4().hex[:12]}")
    tenant_id: str = ""
    
    # Subject
    customer_id: str = ""
    account_id: str = ""
    transaction_ids: List[str] = field(default_factory=list)
    
    # Alert details
    alert_type: str = ""  # structuring, layering, unusual_pattern, etc.
    priority: AlertPriority = AlertPriority.MEDIUM
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: Decimal = Decimal("0")
    
    # Description
    title: str = ""
    description: str = ""
    indicators: List[str] = field(default_factory=list)
    
    # Investigation
    status: str = "open"  # open, investigating, resolved, false_positive, reported
    assigned_to: Optional[str] = None
    investigation_notes: List[Dict] = field(default_factory=list)
    
    # Reporting
    reported_to_austrac: bool = False
    austrac_report_id: Optional[str] = None
    reported_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    version: int = 1
    
    def assign(self, user_id: str):
        """Assign alert to compliance officer."""
        self.assigned_to = user_id
        self.status = "investigating"
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_investigation_note(self, note: str, author: str):
        """Add investigation note."""
        self.investigation_notes.append({
            "note": note,
            "author": author,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def report_to_austrac(self, report_id: str):
        """Mark as reported to AUSTRAC."""
        self.reported_to_austrac = True
        self.austrac_report_id = report_id
        self.reported_at = datetime.utcnow()
        self.status = "reported"
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def resolve(self, resolution: str, is_false_positive: bool = False):
        """Resolve alert."""
        self.status = "false_positive" if is_false_positive else "resolved"
        self.resolved_at = datetime.utcnow()
        self.investigation_notes.append({
            "note": f"Resolution: {resolution}",
            "author": self.assigned_to or "system",
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "account_id": self.account_id,
            "transaction_ids": self.transaction_ids,
            "alert_type": self.alert_type,
            "priority": self.priority.value,
            "risk_level": self.risk_level.value,
            "risk_score": float(self.risk_score),
            "title": self.title,
            "description": self.description,
            "indicators": self.indicators,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "investigation_notes": self.investigation_notes,
            "reported_to_austrac": self.reported_to_austrac,
            "austrac_report_id": self.austrac_report_id,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "version": self.version
        }


@dataclass
class RegulatoryReport:
    """
    Regulatory Report model.
    
    Represents a regulatory report for AUSTRAC or APRA.
    """
    
    # Identity
    report_id: str = field(default_factory=lambda: f"rpt_{uuid4().hex[:12]}")
    tenant_id: str = ""
    
    # Report details
    report_type: ReportType = ReportType.AUSTRAC_TTR
    status: ReportStatus = ReportStatus.DRAFT
    
    # Period
    reporting_period_start: datetime = field(default_factory=datetime.utcnow)
    reporting_period_end: datetime = field(default_factory=datetime.utcnow)
    
    # Content
    report_data: Dict = field(default_factory=dict)
    summary: str = ""
    transaction_count: int = 0
    total_amount: Decimal = Decimal("0")
    
    # Submission
    prepared_by: str = ""
    approved_by: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    
    # Response
    acknowledgment_number: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def approve(self, approver_id: str):
        """Approve report for submission."""
        if self.status != ReportStatus.PENDING_REVIEW:
            raise ValueError(f"Cannot approve report in status: {self.status}")
        
        self.approved_by = approver_id
        self.status = ReportStatus.APPROVED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def submit(self, submitter_id: str):
        """Submit report to regulator."""
        if self.status != ReportStatus.APPROVED:
            raise ValueError(f"Cannot submit report in status: {self.status}")
        
        self.submitted_by = submitter_id
        self.submitted_at = datetime.utcnow()
        self.status = ReportStatus.SUBMITTED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def acknowledge(self, acknowledgment_number: str):
        """Record acknowledgment from regulator."""
        if self.status != ReportStatus.SUBMITTED:
            raise ValueError(f"Cannot acknowledge report in status: {self.status}")
        
        self.acknowledgment_number = acknowledgment_number
        self.acknowledged_at = datetime.utcnow()
        self.status = ReportStatus.ACKNOWLEDGED
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def reject(self, reason: str):
        """Reject report."""
        self.status = ReportStatus.REJECTED
        self.report_data["rejection_reason"] = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "tenant_id": self.tenant_id,
            "report_type": self.report_type.value,
            "status": self.status.value,
            "reporting_period_start": self.reporting_period_start.isoformat(),
            "reporting_period_end": self.reporting_period_end.isoformat(),
            "report_data": self.report_data,
            "summary": self.summary,
            "transaction_count": self.transaction_count,
            "total_amount": float(self.total_amount),
            "prepared_by": self.prepared_by,
            "approved_by": self.approved_by,
            "submitted_by": self.submitted_by,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "acknowledgment_number": self.acknowledgment_number,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }


@dataclass
class CustomerRiskProfile:
    """
    Customer Risk Profile model.
    
    Ongoing risk assessment for AML/CTF compliance.
    """
    
    # Identity
    profile_id: str = field(default_factory=lambda: f"prof_{uuid4().hex[:12]}")
    tenant_id: str = ""
    customer_id: str = ""
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: Decimal = Decimal("0")
    risk_factors: List[Dict] = field(default_factory=list)
    
    # Customer attributes
    is_pep: bool = False
    pep_details: Optional[Dict] = None
    is_sanctioned: bool = False
    sanctions_details: Optional[Dict] = None
    
    # Geographic risk
    country_of_residence: str = ""
    country_risk_level: str = "low"
    high_risk_jurisdictions: List[str] = field(default_factory=list)
    
    # Transaction behavior
    average_transaction_amount: Decimal = Decimal("0")
    transaction_frequency: int = 0
    unusual_patterns_detected: int = 0
    
    # Enhanced due diligence
    edd_required: bool = False
    edd_completed: bool = False
    edd_completed_at: Optional[datetime] = None
    
    # Review
    last_reviewed_at: datetime = field(default_factory=datetime.utcnow)
    next_review_due: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def update_risk_score(self, new_score: Decimal, factors: List[Dict]):
        """Update risk score and factors."""
        self.risk_score = new_score
        self.risk_factors = factors
        
        # Update risk level
        if new_score >= 75:
            self.risk_level = RiskLevel.CRITICAL
        elif new_score >= 50:
            self.risk_level = RiskLevel.HIGH
        elif new_score >= 25:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
        
        # Require EDD for high risk
        if self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.edd_required = True
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def mark_as_pep(self, details: Dict):
        """Mark customer as Politically Exposed Person."""
        self.is_pep = True
        self.pep_details = details
        self.edd_required = True
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def mark_as_sanctioned(self, details: Dict):
        """Mark customer as sanctioned."""
        self.is_sanctioned = True
        self.sanctions_details = details
        self.risk_level = RiskLevel.CRITICAL
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def complete_edd(self):
        """Mark enhanced due diligence as completed."""
        self.edd_completed = True
        self.edd_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "risk_level": self.risk_level.value,
            "risk_score": float(self.risk_score),
            "risk_factors": self.risk_factors,
            "is_pep": self.is_pep,
            "pep_details": self.pep_details,
            "is_sanctioned": self.is_sanctioned,
            "sanctions_details": self.sanctions_details,
            "country_of_residence": self.country_of_residence,
            "country_risk_level": self.country_risk_level,
            "high_risk_jurisdictions": self.high_risk_jurisdictions,
            "average_transaction_amount": float(self.average_transaction_amount),
            "transaction_frequency": self.transaction_frequency,
            "unusual_patterns_detected": self.unusual_patterns_detected,
            "edd_required": self.edd_required,
            "edd_completed": self.edd_completed,
            "edd_completed_at": self.edd_completed_at.isoformat() if self.edd_completed_at else None,
            "last_reviewed_at": self.last_reviewed_at.isoformat(),
            "next_review_due": self.next_review_due.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }

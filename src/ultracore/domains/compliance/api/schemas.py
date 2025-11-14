"""
Compliance API Schemas.

Request and response schemas for compliance endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# Request Schemas

class ComplianceCheckRequest(BaseModel):
    """Request to run compliance check."""
    subject_type: str = Field(..., description="Type of subject (customer, transaction, account)")
    subject_id: str = Field(..., description="Subject identifier")
    check_type: str = Field(..., description="Type of check (kyc, aml, sanctions, pep, transaction)")
    context: Optional[Dict] = Field(default=None, description="Additional context for check")


class TransactionMonitoringRequest(BaseModel):
    """Request to monitor transaction."""
    transaction_id: str
    customer_id: str
    account_id: str
    amount: Decimal
    currency: str = "AUD"
    transaction_type: str
    destination_country: Optional[str] = None
    origin_country: Optional[str] = None
    timestamp: Optional[str] = None


class SuspiciousActivityRequest(BaseModel):
    """Request to create suspicious activity alert."""
    customer_id: str
    account_id: str
    transaction_ids: List[str]
    alert_type: str
    title: str
    description: str
    indicators: List[str]


class AssignAlertRequest(BaseModel):
    """Request to assign alert to compliance officer."""
    user_id: str


class InvestigationNoteRequest(BaseModel):
    """Request to add investigation note."""
    note: str
    author: str


class ResolveAlertRequest(BaseModel):
    """Request to resolve alert."""
    resolution: str
    is_false_positive: bool = False


class ReportToAUSTRACRequest(BaseModel):
    """Request to report to AUSTRAC."""
    report_id: str


class GenerateReportRequest(BaseModel):
    """Request to generate regulatory report."""
    report_type: str = Field(..., description="Type of report (austrac_ttr, austrac_smr, austrac_ift, apra_quarterly, apra_annual)")
    reporting_period_start: datetime
    reporting_period_end: datetime
    data: Dict = Field(default_factory=dict, description="Report-specific data")


class ApproveReportRequest(BaseModel):
    """Request to approve report."""
    approver_id: str


class SubmitReportRequest(BaseModel):
    """Request to submit report."""
    submitter_id: str


# Response Schemas

class ComplianceCheckResponse(BaseModel):
    """Compliance check response."""
    check_id: str
    tenant_id: str
    subject_type: str
    subject_id: str
    check_type: str
    status: str
    risk_level: str
    risk_score: float
    passed: bool
    findings: List[Dict]
    recommendations: List[str]
    performed_by: str
    performed_at: str
    completed_at: Optional[str]
    created_at: str
    updated_at: str
    version: int


class TransactionMonitoringResponse(BaseModel):
    """Transaction monitoring response."""
    monitoring_id: str
    tenant_id: str
    transaction_id: str
    customer_id: str
    account_id: str
    amount: float
    currency: str
    transaction_type: str
    rules_triggered: List[Dict]
    risk_score: float
    risk_level: str
    flagged: bool
    alert_generated: bool
    alert_id: Optional[str]
    monitored_at: str
    version: int


class SuspiciousActivityResponse(BaseModel):
    """Suspicious activity response."""
    alert_id: str
    tenant_id: str
    customer_id: str
    account_id: str
    transaction_ids: List[str]
    alert_type: str
    priority: str
    risk_level: str
    risk_score: float
    title: str
    description: str
    indicators: List[str]
    status: str
    assigned_to: Optional[str]
    investigation_notes: List[Dict]
    reported_to_austrac: bool
    austrac_report_id: Optional[str]
    reported_at: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    version: int


class RegulatoryReportResponse(BaseModel):
    """Regulatory report response."""
    report_id: str
    tenant_id: str
    report_type: str
    status: str
    reporting_period_start: str
    reporting_period_end: str
    report_data: Dict
    summary: str
    transaction_count: int
    total_amount: float
    prepared_by: str
    approved_by: Optional[str]
    submitted_by: Optional[str]
    submitted_at: Optional[str]
    acknowledgment_number: Optional[str]
    acknowledged_at: Optional[str]
    created_at: str
    updated_at: str
    version: int


class CustomerRiskProfileResponse(BaseModel):
    """Customer risk profile response."""
    profile_id: str
    tenant_id: str
    customer_id: str
    risk_level: str
    risk_score: float
    risk_factors: List[Dict]
    is_pep: bool
    pep_details: Optional[Dict]
    is_sanctioned: bool
    sanctions_details: Optional[Dict]
    country_of_residence: str
    country_risk_level: str
    high_risk_jurisdictions: List[str]
    average_transaction_amount: float
    transaction_frequency: int
    unusual_patterns_detected: int
    edd_required: bool
    edd_completed: bool
    edd_completed_at: Optional[str]
    last_reviewed_at: str
    next_review_due: str
    created_at: str
    updated_at: str
    version: int


class ComplianceStatusResponse(BaseModel):
    """Compliance status response."""
    tenant_id: str
    overall_status: str
    compliance_checks_today: int
    alerts_open: int
    alerts_critical: int
    reports_pending: int
    high_risk_customers: int
    edd_pending: int
    last_updated: str


class ComplianceMetricsResponse(BaseModel):
    """Compliance metrics response."""
    period_start: str
    period_end: str
    reports_generated: int
    reports_submitted: int
    reports_pending: int
    compliance_checks_performed: int
    compliance_checks_passed: int
    compliance_checks_failed: int
    suspicious_activities_detected: int
    suspicious_activities_reported: int
    suspicious_activities_resolved: int
    average_risk_score: float
    high_risk_customers: int
    edd_required: int
    edd_completed: int


class MonitoringRuleResponse(BaseModel):
    """Monitoring rule response."""
    name: str
    type: str
    severity: str
    enabled: bool


class ReportScheduleResponse(BaseModel):
    """Report schedule response."""
    report_type: str
    due_date: str
    frequency: str
    description: str


# List Response Schemas

class ComplianceCheckListResponse(BaseModel):
    """List of compliance checks."""
    checks: List[ComplianceCheckResponse]
    total: int
    page: int
    page_size: int


class SuspiciousActivityListResponse(BaseModel):
    """List of suspicious activities."""
    alerts: List[SuspiciousActivityResponse]
    total: int
    page: int
    page_size: int


class RegulatoryReportListResponse(BaseModel):
    """List of regulatory reports."""
    reports: List[RegulatoryReportResponse]
    total: int
    page: int
    page_size: int


class MonitoringRulesListResponse(BaseModel):
    """List of monitoring rules."""
    rules: List[MonitoringRuleResponse]
    total: int

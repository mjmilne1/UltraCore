"""
Compliance API Routes.

REST API endpoints for compliance operations.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models import (
    ComplianceCheck,
    RegulatoryReport,
    SuspiciousActivity,
    TransactionMonitoring,
)
from ..services import (
    AMLCTFService,
    RegulatoryReportingService,
    TransactionMonitoringService,
)
from .schemas import (
    ApproveReportRequest,
    AssignAlertRequest,
    ComplianceCheckListResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ComplianceMetricsResponse,
    ComplianceStatusResponse,
    GenerateReportRequest,
    InvestigationNoteRequest,
    MonitoringRulesListResponse,
    RegulatoryReportListResponse,
    RegulatoryReportResponse,
    ReportScheduleResponse,
    ReportToAUSTRACRequest,
    ResolveAlertRequest,
    SubmitReportRequest,
    SuspiciousActivityListResponse,
    SuspiciousActivityRequest,
    SuspiciousActivityResponse,
    TransactionMonitoringRequest,
    TransactionMonitoringResponse,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


# In-memory storage (replace with database in production)
_compliance_checks: List[ComplianceCheck] = []
_transaction_monitoring: List[TransactionMonitoring] = []
_suspicious_activities: List[SuspiciousActivity] = []
_regulatory_reports: List[RegulatoryReport] = []


def get_tenant_id() -> str:
    """Get tenant ID from context (mock implementation)."""
    return "tenant_001"


def get_user_id() -> str:
    """Get user ID from context (mock implementation)."""
    return "user_001"


# Compliance Checks

@router.post(
    "/checks",
    response_model=ComplianceCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run compliance check",
    description="Perform compliance check on customer, transaction, or account"
)
async def run_compliance_check(
    request: ComplianceCheckRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
) -> ComplianceCheckResponse:
    """Run compliance check."""
    # Initialize service
    aml_service = AMLCTFService(tenant_id=tenant_id)
    
    # Perform check based on type
    if request.check_type in ["kyc", "aml", "aml_ctf_screening"]:
        # Get customer data from context
        customer_data = request.context or {}
        transaction_history = customer_data.get("transaction_history", [])
        
        check = aml_service.perform_customer_screening(
            customer_id=request.subject_id,
            customer_data=customer_data,
            transaction_history=transaction_history
        )
    else:
        # Generic compliance check
        check = ComplianceCheck(
            tenant_id=tenant_id,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            check_type=request.check_type,
            performed_by=user_id
        )
        check.start_check()
        # Perform check logic here
        check.complete_check(
            passed=True,
            risk_level="low",
            risk_score=10.0,
            findings=[]
        )
    
    # Store check
    _compliance_checks.append(check)
    
    return ComplianceCheckResponse(**check.to_dict())


@router.get(
    "/checks",
    response_model=ComplianceCheckListResponse,
    summary="List compliance checks",
    description="Get list of compliance checks with optional filtering"
)
async def list_compliance_checks(
    tenant_id: str = Depends(get_tenant_id),
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    check_type: Optional[str] = Query(None, description="Filter by check type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
) -> ComplianceCheckListResponse:
    """List compliance checks."""
    # Filter checks
    checks = [c for c in _compliance_checks if c.tenant_id == tenant_id]
    
    if subject_type:
        checks = [c for c in checks if c.subject_type == subject_type]
    if subject_id:
        checks = [c for c in checks if c.subject_id == subject_id]
    if check_type:
        checks = [c for c in checks if c.check_type == check_type]
    if status:
        checks = [c for c in checks if c.status.value == status]
    
    # Paginate
    total = len(checks)
    start = (page - 1) * page_size
    end = start + page_size
    page_checks = checks[start:end]
    
    return ComplianceCheckListResponse(
        checks=[ComplianceCheckResponse(**c.to_dict()) for c in page_checks],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/checks/{check_id}",
    response_model=ComplianceCheckResponse,
    summary="Get compliance check",
    description="Get compliance check details by ID"
)
async def get_compliance_check(
    check_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> ComplianceCheckResponse:
    """Get compliance check by ID."""
    check = next(
        (c for c in _compliance_checks if c.check_id == check_id and c.tenant_id == tenant_id),
        None
    )
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance check {check_id} not found"
        )
    
    return ComplianceCheckResponse(**check.to_dict())


# Transaction Monitoring

@router.post(
    "/monitor-transaction",
    response_model=TransactionMonitoringResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Monitor transaction",
    description="Monitor transaction for suspicious activity"
)
async def monitor_transaction(
    request: TransactionMonitoringRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> TransactionMonitoringResponse:
    """Monitor transaction."""
    # Initialize service
    monitoring_service = TransactionMonitoringService(tenant_id=tenant_id)
    
    # Prepare transaction data
    transaction = {
        "transaction_id": request.transaction_id,
        "customer_id": request.customer_id,
        "account_id": request.account_id,
        "amount": request.amount,
        "currency": request.currency,
        "transaction_type": request.transaction_type,
        "destination_country": request.destination_country,
        "origin_country": request.origin_country,
        "timestamp": request.timestamp or datetime.utcnow().isoformat()
    }
    
    # Monitor transaction
    monitoring = monitoring_service.monitor_transaction(
        transaction=transaction,
        context={}  # Add transaction history if available
    )
    
    # Generate alert if needed
    if monitoring_service.should_generate_alert(monitoring):
        alert = monitoring_service.create_suspicious_activity_alert(
            monitoring=monitoring,
            customer_data={}  # Add customer data if available
        )
        _suspicious_activities.append(alert)
        monitoring.generate_alert(alert.alert_id)
    
    # Store monitoring result
    _transaction_monitoring.append(monitoring)
    
    return TransactionMonitoringResponse(**monitoring.to_dict())


@router.get(
    "/monitoring-rules",
    response_model=MonitoringRulesListResponse,
    summary="Get monitoring rules",
    description="Get list of transaction monitoring rules"
)
async def get_monitoring_rules(
    tenant_id: str = Depends(get_tenant_id)
) -> MonitoringRulesListResponse:
    """Get monitoring rules."""
    monitoring_service = TransactionMonitoringService(tenant_id=tenant_id)
    rules = monitoring_service.get_rules()
    
    return MonitoringRulesListResponse(
        rules=rules,
        total=len(rules)
    )


# Suspicious Activity Alerts

@router.get(
    "/alerts",
    response_model=SuspiciousActivityListResponse,
    summary="Get compliance alerts",
    description="Get list of suspicious activity alerts"
)
async def get_compliance_alerts(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
) -> SuspiciousActivityListResponse:
    """Get compliance alerts."""
    # Filter alerts
    alerts = [a for a in _suspicious_activities if a.tenant_id == tenant_id]
    
    if status:
        alerts = [a for a in alerts if a.status == status]
    if priority:
        alerts = [a for a in alerts if a.priority.value == priority]
    if assigned_to:
        alerts = [a for a in alerts if a.assigned_to == assigned_to]
    
    # Paginate
    total = len(alerts)
    start = (page - 1) * page_size
    end = start + page_size
    page_alerts = alerts[start:end]
    
    return SuspiciousActivityListResponse(
        alerts=[SuspiciousActivityResponse(**a.to_dict()) for a in page_alerts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=SuspiciousActivityResponse,
    summary="Get alert details",
    description="Get suspicious activity alert details"
)
async def get_alert(
    alert_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> SuspiciousActivityResponse:
    """Get alert by ID."""
    alert = next(
        (a for a in _suspicious_activities if a.alert_id == alert_id and a.tenant_id == tenant_id),
        None
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    return SuspiciousActivityResponse(**alert.to_dict())


@router.post(
    "/alerts/{alert_id}/assign",
    response_model=SuspiciousActivityResponse,
    summary="Assign alert",
    description="Assign alert to compliance officer"
)
async def assign_alert(
    alert_id: str,
    request: AssignAlertRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> SuspiciousActivityResponse:
    """Assign alert."""
    alert = next(
        (a for a in _suspicious_activities if a.alert_id == alert_id and a.tenant_id == tenant_id),
        None
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    alert.assign(request.user_id)
    
    return SuspiciousActivityResponse(**alert.to_dict())


@router.post(
    "/alerts/{alert_id}/notes",
    response_model=SuspiciousActivityResponse,
    summary="Add investigation note",
    description="Add note to alert investigation"
)
async def add_investigation_note(
    alert_id: str,
    request: InvestigationNoteRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> SuspiciousActivityResponse:
    """Add investigation note."""
    alert = next(
        (a for a in _suspicious_activities if a.alert_id == alert_id and a.tenant_id == tenant_id),
        None
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    alert.add_investigation_note(request.note, request.author)
    
    return SuspiciousActivityResponse(**alert.to_dict())


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=SuspiciousActivityResponse,
    summary="Resolve alert",
    description="Resolve suspicious activity alert"
)
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> SuspiciousActivityResponse:
    """Resolve alert."""
    alert = next(
        (a for a in _suspicious_activities if a.alert_id == alert_id and a.tenant_id == tenant_id),
        None
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    alert.resolve(request.resolution, request.is_false_positive)
    
    return SuspiciousActivityResponse(**alert.to_dict())


@router.post(
    "/alerts/{alert_id}/report-austrac",
    response_model=SuspiciousActivityResponse,
    summary="Report to AUSTRAC",
    description="Report suspicious activity to AUSTRAC"
)
async def report_to_austrac(
    alert_id: str,
    request: ReportToAUSTRACRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> SuspiciousActivityResponse:
    """Report to AUSTRAC."""
    alert = next(
        (a for a in _suspicious_activities if a.alert_id == alert_id and a.tenant_id == tenant_id),
        None
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    alert.report_to_austrac(request.report_id)
    
    return SuspiciousActivityResponse(**alert.to_dict())


# Regulatory Reports

@router.post(
    "/reports",
    response_model=RegulatoryReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate regulatory report",
    description="Generate AUSTRAC or APRA regulatory report"
)
async def generate_report(
    request: GenerateReportRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
) -> RegulatoryReportResponse:
    """Generate regulatory report."""
    reporting_service = RegulatoryReportingService(tenant_id=tenant_id)
    
    # Generate report based on type
    if request.report_type == "austrac_ttr":
        report = reporting_service.generate_austrac_ttr(
            transactions=request.data.get("transactions", []),
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            prepared_by=user_id
        )
    elif request.report_type == "austrac_smr":
        report = reporting_service.generate_austrac_smr(
            suspicious_activity=request.data.get("suspicious_activity", {}),
            prepared_by=user_id
        )
    elif request.report_type == "austrac_ift":
        report = reporting_service.generate_austrac_ifti(
            transfers=request.data.get("transfers", []),
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            prepared_by=user_id
        )
    elif request.report_type == "apra_quarterly":
        report = reporting_service.generate_apra_quarterly(
            financial_data=request.data.get("financial_data", {}),
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            prepared_by=user_id
        )
    elif request.report_type == "apra_annual":
        report = reporting_service.generate_apra_annual(
            financial_data=request.data.get("financial_data", {}),
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            prepared_by=user_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type: {request.report_type}"
        )
    
    # Store report
    _regulatory_reports.append(report)
    
    return RegulatoryReportResponse(**report.to_dict())


@router.get(
    "/reports",
    response_model=RegulatoryReportListResponse,
    summary="List regulatory reports",
    description="Get list of regulatory reports"
)
async def list_reports(
    tenant_id: str = Depends(get_tenant_id),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
) -> RegulatoryReportListResponse:
    """List regulatory reports."""
    # Filter reports
    reports = [r for r in _regulatory_reports if r.tenant_id == tenant_id]
    
    if report_type:
        reports = [r for r in reports if r.report_type.value == report_type]
    if status:
        reports = [r for r in reports if r.status.value == status]
    
    # Paginate
    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    page_reports = reports[start:end]
    
    return RegulatoryReportListResponse(
        reports=[RegulatoryReportResponse(**r.to_dict()) for r in page_reports],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/reports/{report_id}",
    response_model=RegulatoryReportResponse,
    summary="Get report",
    description="Get regulatory report details"
)
async def get_report(
    report_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> RegulatoryReportResponse:
    """Get report by ID."""
    report = next(
        (r for r in _regulatory_reports if r.report_id == report_id and r.tenant_id == tenant_id),
        None
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    
    return RegulatoryReportResponse(**report.to_dict())


@router.post(
    "/reports/{report_id}/approve",
    response_model=RegulatoryReportResponse,
    summary="Approve report",
    description="Approve regulatory report for submission"
)
async def approve_report(
    report_id: str,
    request: ApproveReportRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> RegulatoryReportResponse:
    """Approve report."""
    report = next(
        (r for r in _regulatory_reports if r.report_id == report_id and r.tenant_id == tenant_id),
        None
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    
    try:
        report.approve(request.approver_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return RegulatoryReportResponse(**report.to_dict())


@router.post(
    "/reports/{report_id}/submit",
    response_model=RegulatoryReportResponse,
    summary="Submit report",
    description="Submit regulatory report to regulator"
)
async def submit_report(
    report_id: str,
    request: SubmitReportRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> RegulatoryReportResponse:
    """Submit report."""
    report = next(
        (r for r in _regulatory_reports if r.report_id == report_id and r.tenant_id == tenant_id),
        None
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    
    reporting_service = RegulatoryReportingService(tenant_id=tenant_id)
    
    try:
        success = reporting_service.submit_report(report, request.submitter_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit report"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return RegulatoryReportResponse(**report.to_dict())


@router.get(
    "/reports/schedule",
    response_model=List[ReportScheduleResponse],
    summary="Get report schedule",
    description="Get schedule of upcoming regulatory reports"
)
async def get_report_schedule(
    tenant_id: str = Depends(get_tenant_id)
) -> List[ReportScheduleResponse]:
    """Get report schedule."""
    reporting_service = RegulatoryReportingService(tenant_id=tenant_id)
    schedule = reporting_service.schedule_periodic_reports()
    
    return [ReportScheduleResponse(**item) for item in schedule]


# Compliance Status & Metrics

@router.get(
    "/status",
    response_model=ComplianceStatusResponse,
    summary="Get compliance status",
    description="Get overall compliance status"
)
async def get_compliance_status(
    tenant_id: str = Depends(get_tenant_id)
) -> ComplianceStatusResponse:
    """Get compliance status."""
    # Calculate status metrics
    today = datetime.utcnow().date()
    
    checks_today = len([
        c for c in _compliance_checks
        if c.tenant_id == tenant_id and c.created_at.date() == today
    ])
    
    alerts_open = len([
        a for a in _suspicious_activities
        if a.tenant_id == tenant_id and a.status == "open"
    ])
    
    alerts_critical = len([
        a for a in _suspicious_activities
        if a.tenant_id == tenant_id and a.priority.value == "critical"
    ])
    
    reports_pending = len([
        r for r in _regulatory_reports
        if r.tenant_id == tenant_id and r.status.value in ["draft", "pending_review"]
    ])
    
    return ComplianceStatusResponse(
        tenant_id=tenant_id,
        overall_status="compliant",
        compliance_checks_today=checks_today,
        alerts_open=alerts_open,
        alerts_critical=alerts_critical,
        reports_pending=reports_pending,
        high_risk_customers=0,  # Calculate from risk profiles
        edd_pending=0,  # Calculate from risk profiles
        last_updated=datetime.utcnow().isoformat()
    )


@router.get(
    "/metrics",
    response_model=ComplianceMetricsResponse,
    summary="Get compliance metrics",
    description="Get compliance metrics for reporting period"
)
async def get_compliance_metrics(
    tenant_id: str = Depends(get_tenant_id),
    start_date: datetime = Query(..., description="Period start date"),
    end_date: datetime = Query(..., description="Period end date")
) -> ComplianceMetricsResponse:
    """Get compliance metrics."""
    reporting_service = RegulatoryReportingService(tenant_id=tenant_id)
    metrics = reporting_service.get_compliance_metrics(start_date, end_date)
    
    return ComplianceMetricsResponse(**metrics)

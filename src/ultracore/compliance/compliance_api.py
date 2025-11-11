"""
UltraCore Audit & Compliance API

Comprehensive REST API for audit and compliance management:
- Audit trail queries
- Compliance monitoring
- Anomaly investigation
- Dashboard data
- Reporting
- Real-time alerts
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio

from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity,
    AuditQuery, AuditStatistics
)
from ultracore.compliance.compliance_engine import (
    get_compliance_engine, ComplianceStatus, RuleCategory, RiskLevel,
    AlertPriority, RegulatoryFramework
)
from ultracore.compliance.anomaly_detection import (
    get_anomaly_engine, AnomalyType, AnomalyConfidence
)


# ============================================================================
# Pydantic Models
# ============================================================================

class AuditEventResponse(BaseModel):
    audit_id: str
    event_type: str
    category: str
    severity: str
    timestamp: str
    user_id: Optional[str]
    user_email: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    action: str
    description: str
    metadata: Dict[str, Any] = {}


class AuditQueryRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None
    regulatory_only: bool = False
    limit: int = 100
    offset: int = 0


class TransactionCheckRequest(BaseModel):
    transaction_id: str
    customer_id: str
    account_id: str
    amount: str  # Decimal as string
    currency: str = "AUD"
    transaction_type: str
    from_account: str
    to_account: str
    recipient: str
    timestamp: Optional[str] = None


class ViolationResponse(BaseModel):
    violation_id: str
    rule_id: str
    rule_name: str
    timestamp: str
    entity_type: str
    entity_id: str
    description: str
    severity: str
    risk_level: str
    blocked: bool
    resolved: bool
    evidence: Dict[str, Any]


class AlertResponse(BaseModel):
    alert_id: str
    priority: str
    title: str
    description: str
    category: str
    acknowledged: bool
    resolved: bool
    created_at: str
    violations: List[str]


class AnomalyResponse(BaseModel):
    anomaly_id: str
    anomaly_type: str
    confidence: str
    confidence_score: float
    entity_type: str
    entity_id: str
    detected_at: str
    description: str
    risk_level: str
    investigated: bool
    false_positive: Optional[bool]


class DashboardResponse(BaseModel):
    status: str
    summary: Dict[str, Any]
    recent_violations: List[ViolationResponse]
    open_alerts: List[AlertResponse]
    high_risk_entities: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    trends: Dict[str, Any]


class ResolveRequest(BaseModel):
    resolved_by: str
    resolution_notes: str


class InvestigationRequest(BaseModel):
    investigated_by: str
    notes: str
    false_positive: bool


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="UltraCore Audit & Compliance API",
    description="Comprehensive audit trail and compliance monitoring system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
audit_store = get_audit_store()
compliance_engine = get_compliance_engine()
anomaly_engine = get_anomaly_engine()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await compliance_engine.start_monitoring()
    print("✅ Compliance monitoring started")


# ============================================================================
# Audit Endpoints
# ============================================================================

@app.post("/api/audit/query", response_model=List[AuditEventResponse])
async def query_audit_trail(request: AuditQueryRequest):
    """Query audit trail with filters"""
    
    # Parse dates
    start_date = datetime.fromisoformat(request.start_date) if request.start_date else None
    end_date = datetime.fromisoformat(request.end_date) if request.end_date else None
    
    # Convert string enums
    event_types = [AuditEventType(et) for et in request.event_types] if request.event_types else None
    categories = [AuditCategory(c) for c in request.categories] if request.categories else None
    severities = [AuditSeverity(s) for s in request.severities] if request.severities else None
    
    # Create query
    query = AuditQuery(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        categories=categories,
        severities=severities,
        user_id=request.user_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        search_text=request.search_text,
        tags=request.tags,
        regulatory_only=request.regulatory_only,
        limit=request.limit,
        offset=request.offset
    )
    
    events = await audit_store.query_events(query)
    
    return [
        AuditEventResponse(
            audit_id=e.audit_id,
            event_type=e.event_type.value,
            category=e.category.value,
            severity=e.severity.value,
            timestamp=e.timestamp.isoformat(),
            user_id=e.user_id,
            user_email=e.user_email,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            action=e.action,
            description=e.description,
            metadata=e.metadata
        )
        for e in events
    ]


@app.get("/api/audit/events/{audit_id}", response_model=AuditEventResponse)
async def get_audit_event(audit_id: str):
    """Get specific audit event"""
    
    event = await audit_store.get_event(audit_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Audit event {audit_id} not found")
    
    return AuditEventResponse(
        audit_id=event.audit_id,
        event_type=event.event_type.value,
        category=event.category.value,
        severity=event.severity.value,
        timestamp=event.timestamp.isoformat(),
        user_id=event.user_id,
        user_email=event.user_email,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        action=event.action,
        description=event.description,
        metadata=event.metadata
    )


@app.get("/api/audit/statistics")
async def get_audit_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get audit trail statistics"""
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await audit_store.get_statistics(start_date=start, end_date=end)
    
    return {
        'total_events': stats.total_events,
        'events_by_type': stats.events_by_type,
        'events_by_category': stats.events_by_category,
        'events_by_severity': stats.events_by_severity,
        'events_by_user': stats.events_by_user,
        'regulatory_events': stats.regulatory_events,
        'time_range': stats.time_range
    }


@app.get("/api/audit/user-activity/{user_id}")
async def get_user_activity(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get all activity for a user"""
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    events = await audit_store.get_user_activity(user_id, start, end)
    
    return {
        'user_id': user_id,
        'event_count': len(events),
        'events': [
            {
                'audit_id': e.audit_id,
                'timestamp': e.timestamp.isoformat(),
                'event_type': e.event_type.value,
                'action': e.action,
                'resource_type': e.resource_type,
                'resource_id': e.resource_id
            }
            for e in events
        ]
    }


@app.get("/api/audit/resource-history/{resource_type}/{resource_id}")
async def get_resource_history(resource_type: str, resource_id: str):
    """Get complete history of a resource"""
    
    events = await audit_store.get_resource_history(resource_type, resource_id)
    
    return {
        'resource_type': resource_type,
        'resource_id': resource_id,
        'event_count': len(events),
        'events': [
            {
                'audit_id': e.audit_id,
                'timestamp': e.timestamp.isoformat(),
                'event_type': e.event_type.value,
                'action': e.action,
                'user_id': e.user_id,
                'description': e.description
            }
            for e in events
        ]
    }


@app.post("/api/audit/verify-integrity")
async def verify_audit_integrity():
    """Verify integrity of audit trail"""
    
    result = await audit_store.verify_integrity()
    
    return result


@app.get("/api/audit/export-regulatory/{regulator}")
async def export_for_regulator(
    regulator: str,
    start_date: str,
    end_date: str
):
    """Export audit trail for regulator"""
    
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    export_data = await audit_store.export_for_regulator(
        regulator=regulator,
        start_date=start,
        end_date=end
    )
    
    return export_data


# ============================================================================
# Compliance Endpoints
# ============================================================================

@app.post("/api/compliance/check-transaction")
async def check_transaction(request: TransactionCheckRequest):
    """Check transaction against compliance rules"""
    
    timestamp = datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.utcnow()
    
    result = await compliance_engine.check_transaction(
        transaction_id=request.transaction_id,
        transaction_type=request.transaction_type,
        amount=Decimal(request.amount),
        currency=request.currency,
        from_account=request.from_account,
        to_account=request.to_account,
        customer_id=request.customer_id,
        timestamp=timestamp
    )
    
    # Also run anomaly detection
    anomaly_score = await anomaly_engine.analyze_transaction(
        transaction_id=request.transaction_id,
        customer_id=request.customer_id,
        account_id=request.account_id,
        amount=Decimal(request.amount),
        transaction_type=request.transaction_type,
        recipient=request.recipient,
        timestamp=timestamp
    )
    
    return {
        'compliant': result['compliant'],
        'blocked': result['blocked'],
        'violations': result['violations'],
        'risk_assessment': {
            'score': result['risk_assessment'].score if result['risk_assessment'] else 0,
            'level': result['risk_assessment'].level.value if result['risk_assessment'] else 'LOW'
        },
        'anomaly_score': {
            'score': anomaly_score.score,
            'confidence': anomaly_score.confidence.value,
            'active_anomalies': len(anomaly_score.active_anomalies)
        }
    }


@app.get("/api/compliance/violations", response_model=List[ViolationResponse])
async def get_violations(
    resolved: Optional[bool] = Query(None),
    risk_level: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None)
):
    """Get compliance violations"""
    
    risk_enum = RiskLevel(risk_level) if risk_level else None
    
    violations = await compliance_engine.get_violations(
        resolved=resolved,
        risk_level=risk_enum,
        entity_type=entity_type
    )
    
    return [
        ViolationResponse(
            violation_id=v.violation_id,
            rule_id=v.rule_id,
            rule_name=v.rule_name,
            timestamp=v.timestamp.isoformat(),
            entity_type=v.entity_type,
            entity_id=v.entity_id,
            description=v.description,
            severity=v.severity.value,
            risk_level=v.risk_level.value,
            blocked=v.blocked,
            resolved=v.resolved,
            evidence=v.evidence
        )
        for v in violations
    ]


@app.post("/api/compliance/violations/{violation_id}/resolve")
async def resolve_violation(violation_id: str, request: ResolveRequest):
    """Resolve a compliance violation"""
    
    success = await compliance_engine.resolve_violation(
        violation_id=violation_id,
        resolved_by=request.resolved_by,
        resolution_notes=request.resolution_notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Violation {violation_id} not found")
    
    return {'status': 'resolved', 'violation_id': violation_id}


@app.get("/api/compliance/alerts", response_model=List[AlertResponse])
async def get_alerts(
    resolved: Optional[bool] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Get compliance alerts"""
    
    priority_enum = AlertPriority(priority) if priority else None
    
    alerts = await compliance_engine.get_alerts(
        resolved=resolved,
        priority=priority_enum
    )
    
    return [
        AlertResponse(
            alert_id=a.alert_id,
            priority=a.priority.value,
            title=a.title,
            description=a.description,
            category=a.category.value,
            acknowledged=a.acknowledged,
            resolved=a.resolved,
            created_at=a.created_at.isoformat(),
            violations=a.violations
        )
        for a in alerts
    ]


@app.get("/api/compliance/risk-score/{entity_type}/{entity_id}")
async def get_risk_score(entity_type: str, entity_id: str):
    """Get risk score for an entity"""
    
    risk_score = await compliance_engine.get_risk_score(entity_type, entity_id)
    
    if not risk_score:
        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'score': 0,
            'level': 'LOW',
            'message': 'No risk assessment available'
        }
    
    return {
        'entity_type': risk_score.entity_type,
        'entity_id': risk_score.entity_id,
        'score': risk_score.score,
        'level': risk_score.level.value,
        'factors': risk_score.factors,
        'calculated_at': risk_score.calculated_at.isoformat()
    }


@app.get("/api/compliance/report")
async def generate_compliance_report(
    start_date: str,
    end_date: str
):
    """Generate compliance report"""
    
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    report = await compliance_engine.generate_compliance_report(start, end)
    
    return {
        'report_id': report.report_id,
        'period_start': report.period_start.isoformat(),
        'period_end': report.period_end.isoformat(),
        'status': report.status.value,
        'total_transactions': report.total_transactions,
        'flagged_transactions': report.flagged_transactions,
        'violations': report.violations,
        'resolved_violations': report.resolved_violations,
        'open_alerts': report.open_alerts,
        'violations_by_category': report.violations_by_category,
        'risk_distribution': report.risk_distribution,
        'recommendations': report.recommendations,
        'generated_at': report.generated_at.isoformat()
    }


@app.get("/api/compliance/rules")
async def get_compliance_rules():
    """Get all compliance rules"""
    
    rules = compliance_engine.rules_registry.get_all_rules()
    
    return {
        'total_rules': len(rules),
        'rules': [
            {
                'rule_id': r.rule_id,
                'name': r.name,
                'description': r.description,
                'category': r.category.value,
                'regulatory_framework': r.regulatory_framework.value,
                'enabled': r.enabled,
                'severity': r.severity.value,
                'auto_block': r.auto_block,
                'auto_alert': r.auto_alert
            }
            for r in rules
        ]
    }


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================

@app.get("/api/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    investigated: Optional[bool] = Query(None)
):
    """Get detected anomalies"""
    
    anomaly_type_enum = AnomalyType(anomaly_type) if anomaly_type else None
    confidence_enum = AnomalyConfidence(confidence) if confidence else None
    
    anomalies = await anomaly_engine.get_anomalies(
        entity_type=entity_type,
        entity_id=entity_id,
        anomaly_type=anomaly_type_enum,
        confidence=confidence_enum,
        investigated=investigated
    )
    
    return [
        AnomalyResponse(
            anomaly_id=a.anomaly_id,
            anomaly_type=a.anomaly_type.value,
            confidence=a.confidence.value,
            confidence_score=a.confidence_score,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            detected_at=a.detected_at.isoformat(),
            description=a.description,
            risk_level=a.risk_level.value,
            investigated=a.investigated,
            false_positive=a.false_positive
        )
        for a in anomalies
    ]


@app.post("/api/anomalies/{anomaly_id}/investigate")
async def investigate_anomaly(anomaly_id: str, request: InvestigationRequest):
    """Mark anomaly investigation result"""
    
    success = await anomaly_engine.mark_false_positive(
        anomaly_id=anomaly_id,
        investigated_by=request.investigated_by,
        notes=request.notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
    
    return {
        'status': 'investigated',
        'anomaly_id': anomaly_id,
        'false_positive': request.false_positive
    }


@app.get("/api/anomalies/score/{entity_type}/{entity_id}")
async def get_anomaly_score(entity_type: str, entity_id: str):
    """Get anomaly score for an entity"""
    
    score = await anomaly_engine.get_anomaly_score(entity_type, entity_id)
    
    if not score:
        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'score': 0,
            'confidence': 'LOW',
            'message': 'No anomaly score available'
        }
    
    return {
        'entity_type': score.entity_type,
        'entity_id': score.entity_id,
        'score': score.score,
        'confidence': score.confidence.value,
        'statistical_score': score.statistical_score,
        'behavioral_score': score.behavioral_score,
        'temporal_score': score.temporal_score,
        'peer_score': score.peer_score,
        'active_anomalies': len(score.active_anomalies),
        'calculated_at': score.calculated_at.isoformat()
    }


@app.get("/api/anomalies/behavioral-profile/{entity_type}/{entity_id}")
async def get_behavioral_profile(entity_type: str, entity_id: str):
    """Get behavioral profile for an entity"""
    
    profile = await anomaly_engine.behavioral_profiler.get_profile(entity_type, entity_id)
    
    return {
        'entity_type': profile.entity_type,
        'entity_id': profile.entity_id,
        'avg_transaction_amount': str(profile.avg_transaction_amount),
        'median_transaction_amount': str(profile.median_transaction_amount),
        'max_transaction_amount': str(profile.max_transaction_amount),
        'avg_daily_transactions': profile.avg_daily_transactions,
        'avg_weekly_transactions': profile.avg_weekly_transactions,
        'common_transaction_hours': profile.common_transaction_hours,
        'common_transaction_days': profile.common_transaction_days,
        'common_recipients': profile.common_recipients,
        'transaction_count': profile.transaction_count,
        'profile_start_date': profile.profile_start_date.isoformat(),
        'profile_end_date': profile.profile_end_date.isoformat()
    }


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get comprehensive dashboard data"""
    
    # Get recent time ranges
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Get audit statistics
    audit_stats = await audit_store.get_statistics(start_date=last_30d)
    
    # Get compliance data
    violations = await compliance_engine.get_violations(resolved=False)
    alerts = await compliance_engine.get_alerts(resolved=False)
    
    # Get high risk entities
    high_risk_entities = []
    for violation in violations[:10]:  # Top 10
        if violation.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            risk_score = await compliance_engine.get_risk_score(
                violation.entity_type,
                violation.entity_id
            )
            if risk_score:
                high_risk_entities.append({
                    'entity_type': violation.entity_type,
                    'entity_id': violation.entity_id,
                    'risk_score': risk_score.score,
                    'risk_level': risk_score.level.value
                })
    
    # Calculate trends
    last_24h_violations = [v for v in violations if v.timestamp >= last_24h]
    last_7d_violations = [v for v in violations if v.timestamp >= last_7d]
    
    # Determine overall status
    if len([v for v in violations if v.risk_level == RiskLevel.CRITICAL]) > 0:
        status = ComplianceStatus.CRITICAL.value
    elif len([v for v in violations if v.risk_level == RiskLevel.HIGH]) > 5:
        status = ComplianceStatus.BREACH.value
    elif len(violations) > 10:
        status = ComplianceStatus.WARNING.value
    else:
        status = ComplianceStatus.COMPLIANT.value
    
    return DashboardResponse(
        status=status,
        summary={
            'total_violations': len(violations),
            'open_alerts': len(alerts),
            'high_risk_entities': len(high_risk_entities),
            'audit_events_30d': audit_stats.total_events,
            'regulatory_events_30d': audit_stats.regulatory_events
        },
        recent_violations=[
            ViolationResponse(
                violation_id=v.violation_id,
                rule_id=v.rule_id,
                rule_name=v.rule_name,
                timestamp=v.timestamp.isoformat(),
                entity_type=v.entity_type,
                entity_id=v.entity_id,
                description=v.description,
                severity=v.severity.value,
                risk_level=v.risk_level.value,
                blocked=v.blocked,
                resolved=v.resolved,
                evidence=v.evidence
            )
            for v in violations[:10]
        ],
        open_alerts=[
            AlertResponse(
                alert_id=a.alert_id,
                priority=a.priority.value,
                title=a.title,
                description=a.description,
                category=a.category.value,
                acknowledged=a.acknowledged,
                resolved=a.resolved,
                created_at=a.created_at.isoformat(),
                violations=a.violations
            )
            for a in alerts[:10]
        ],
        high_risk_entities=high_risk_entities[:10],
        statistics={
            'violations_by_severity': {
                'critical': len([v for v in violations if v.risk_level == RiskLevel.CRITICAL]),
                'high': len([v for v in violations if v.risk_level == RiskLevel.HIGH]),
                'medium': len([v for v in violations if v.risk_level == RiskLevel.MEDIUM]),
                'low': len([v for v in violations if v.risk_level == RiskLevel.LOW])
            },
            'audit_events_by_category': audit_stats.events_by_category
        },
        trends={
            'violations_24h': len(last_24h_violations),
            'violations_7d': len(last_7d_violations),
            'violations_30d': len(violations),
            'trend_24h_vs_7d': 'increasing' if len(last_24h_violations) * 7 > len(last_7d_violations) else 'decreasing'
        }
    )


@app.get("/api/dashboard/real-time-metrics")
async def get_realtime_metrics():
    """Get real-time monitoring metrics"""
    
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    
    # Get recent audit events
    query = AuditQuery(
        start_date=last_hour,
        end_date=now,
        limit=1000
    )
    recent_events = await audit_store.query_events(query)
    
    # Get recent violations
    violations = await compliance_engine.get_violations(resolved=False)
    recent_violations = [v for v in violations if v.timestamp >= last_hour]
    
    # Get anomalies
    anomalies = await anomaly_engine.get_anomalies(investigated=False)
    recent_anomalies = [a for a in anomalies if a.detected_at >= last_hour]
    
    return {
        'timestamp': now.isoformat(),
        'last_hour': {
            'audit_events': len(recent_events),
            'violations': len(recent_violations),
            'anomalies': len(recent_anomalies),
            'critical_violations': len([v for v in recent_violations if v.risk_level == RiskLevel.CRITICAL])
        },
        'event_types': {
            event_type: len([e for e in recent_events if e.event_type.value == event_type])
            for event_type in set(e.event_type.value for e in recent_events)
        }
    }


@app.get("/api/dashboard/investigation-queue")
async def get_investigation_queue():
    """Get items requiring investigation"""
    
    # Get unresolved violations
    violations = await compliance_engine.get_violations(resolved=False)
    high_priority_violations = [
        v for v in violations
        if v.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    ]
    
    # Get uninvestigated anomalies
    anomalies = await anomaly_engine.get_anomalies(investigated=False)
    high_confidence_anomalies = [
        a for a in anomalies
        if a.confidence in [AnomalyConfidence.HIGH, AnomalyConfidence.VERY_HIGH]
    ]
    
    # Get unacknowledged alerts
    alerts = await compliance_engine.get_alerts(resolved=False)
    high_priority_alerts = [
        a for a in alerts
        if a.priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]
    ]
    
    return {
        'total_items': len(high_priority_violations) + len(high_confidence_anomalies) + len(high_priority_alerts),
        'high_priority_violations': len(high_priority_violations),
        'high_confidence_anomalies': len(high_confidence_anomalies),
        'high_priority_alerts': len(high_priority_alerts),
        'violations': [
            {
                'violation_id': v.violation_id,
                'entity_type': v.entity_type,
                'entity_id': v.entity_id,
                'rule_name': v.rule_name,
                'risk_level': v.risk_level.value,
                'timestamp': v.timestamp.isoformat()
            }
            for v in high_priority_violations[:20]
        ],
        'anomalies': [
            {
                'anomaly_id': a.anomaly_id,
                'entity_type': a.entity_type,
                'entity_id': a.entity_id,
                'anomaly_type': a.anomaly_type.value,
                'confidence': a.confidence.value,
                'detected_at': a.detected_at.isoformat()
            }
            for a in high_confidence_anomalies[:20]
        ]
    }


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'UltraCore Audit & Compliance',
        'version': '1.0.0',
        'monitoring_active': compliance_engine._monitoring_active
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'UltraCore Audit & Compliance API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health'
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

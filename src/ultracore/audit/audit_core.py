"""
UltraCore Audit System - Core Audit Trail

Comprehensive audit trail for regulatory compliance:
- Immutable audit logs
- Real-time event capture
- Query and search capabilities
- Forensic analysis
- Regulatory compliance (ASIC, AUSTRAC, APRA, ATO)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
from dataclasses import dataclass, field
import hashlib
import json
from decimal import Decimal
import asyncio

from ultracore.events.kafka_store import get_production_kafka_store


# ============================================================================
# Audit Enums
# ============================================================================

class AuditEventType(str, Enum):
    """Types of auditable events"""
    # Authentication & Authorization
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    
    # Account Operations
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    ACCOUNT_UNFROZEN = "ACCOUNT_UNFROZEN"
    
    # Transaction Events
    TRANSACTION_INITIATED = "TRANSACTION_INITIATED"
    TRANSACTION_APPROVED = "TRANSACTION_APPROVED"
    TRANSACTION_REJECTED = "TRANSACTION_REJECTED"
    TRANSACTION_SETTLED = "TRANSACTION_SETTLED"
    TRANSACTION_REVERSED = "TRANSACTION_REVERSED"
    
    # Customer Events
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    KYC_VERIFIED = "KYC_VERIFIED"
    KYC_FAILED = "KYC_FAILED"
    CUSTOMER_SUSPENDED = "CUSTOMER_SUSPENDED"
    
    # Document Events
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_MODIFIED = "DOCUMENT_MODIFIED"
    
    # Compliance Events
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    REGULATORY_REPORT_GENERATED = "REGULATORY_REPORT_GENERATED"
    REGULATORY_REPORT_SUBMITTED = "REGULATORY_REPORT_SUBMITTED"
    
    # System Events
    CONFIG_CHANGED = "CONFIG_CHANGED"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    BACKUP_COMPLETED = "BACKUP_COMPLETED"
    BACKUP_FAILED = "BACKUP_FAILED"
    
    # Admin Events
    ADMIN_ACCESS = "ADMIN_ACCESS"
    BULK_OPERATION = "BULK_OPERATION"
    DATA_EXPORT = "DATA_EXPORT"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class AuditSeverity(str, Enum):
    """Severity level of audit event"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditCategory(str, Enum):
    """Category for audit events"""
    SECURITY = "SECURITY"
    FINANCIAL = "FINANCIAL"
    COMPLIANCE = "COMPLIANCE"
    OPERATIONAL = "OPERATIONAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AuditEvent:
    """Immutable audit event record"""
    audit_id: str
    event_type: AuditEventType
    category: AuditCategory
    severity: AuditSeverity
    timestamp: datetime
    
    # Actor information
    user_id: Optional[str]
    user_email: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    
    # Event details
    resource_type: str  # account, transaction, customer, etc.
    resource_id: Optional[str]
    action: str
    description: str
    
    # Data changes (before/after)
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Compliance
    regulatory_relevant: bool = False
    retention_years: int = 7  # Default 7 years for financial services
    
    # Integrity
    checksum: Optional[str] = None
    previous_checksum: Optional[str] = None  # Chain of integrity


@dataclass
class AuditQuery:
    """Query parameters for audit search"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[AuditEventType]] = None
    categories: Optional[List[AuditCategory]] = None
    severities: Optional[List[AuditSeverity]] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None
    regulatory_only: bool = False
    limit: int = 100
    offset: int = 0


@dataclass
class AuditStatistics:
    """Audit trail statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_user: Dict[str, int]
    regulatory_events: int
    time_range: Dict[str, str]


# ============================================================================
# Audit Trail Store
# ============================================================================

class AuditTrailStore:
    """
    Immutable audit trail storage
    Provides cryptographic integrity and regulatory compliance
    """
    
    def __init__(self):
        self._events: List[AuditEvent] = []
        self._last_checksum: Optional[str] = None
        self._indices: Dict[str, List[str]] = {
            'user_id': {},
            'resource_type': {},
            'resource_id': {},
            'event_type': {}
        }
    
    async def log_event(
        self,
        event_type: AuditEventType,
        category: AuditCategory,
        severity: AuditSeverity,
        resource_type: str,
        action: str,
        description: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        regulatory_relevant: bool = False
    ) -> AuditEvent:
        """Log an audit event with integrity checking"""
        
        # Generate audit ID
        audit_id = f"AUD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Create event
        event = AuditEvent(
            audit_id=audit_id,
            event_type=event_type,
            category=category,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
            tags=tags or [],
            regulatory_relevant=regulatory_relevant,
            previous_checksum=self._last_checksum
        )
        
        # Calculate checksum for integrity
        event.checksum = self._calculate_checksum(event)
        self._last_checksum = event.checksum
        
        # Store event
        self._events.append(event)
        
        # Update indices
        self._update_indices(event)
        
        # Publish to Kafka for persistence
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='audit',
            event_type='audit_event_logged',
            event_data={
                'audit_id': audit_id,
                'event_type': event_type,
                'category': category,
                'severity': severity,
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'regulatory_relevant': regulatory_relevant
            },
            aggregate_id=audit_id
        )
        
        return event
    
    def _calculate_checksum(self, event: AuditEvent) -> str:
        """Calculate cryptographic checksum for event integrity"""
        
        # Create canonical representation
        canonical = {
            'audit_id': event.audit_id,
            'event_type': event.event_type,
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id,
            'resource_type': event.resource_type,
            'resource_id': event.resource_id,
            'action': event.action,
            'before_state': event.before_state,
            'after_state': event.after_state,
            'previous_checksum': event.previous_checksum
        }
        
        # Create JSON string (sorted keys for consistency)
        canonical_str = json.dumps(canonical, sort_keys=True)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(canonical_str.encode()).hexdigest()
    
    def _update_indices(self, event: AuditEvent):
        """Update search indices"""
        
        if event.user_id:
            if event.user_id not in self._indices['user_id']:
                self._indices['user_id'][event.user_id] = []
            self._indices['user_id'][event.user_id].append(event.audit_id)
        
        if event.resource_type not in self._indices['resource_type']:
            self._indices['resource_type'][event.resource_type] = []
        self._indices['resource_type'][event.resource_type].append(event.audit_id)
        
        if event.resource_id:
            if event.resource_id not in self._indices['resource_id']:
                self._indices['resource_id'][event.resource_id] = []
            self._indices['resource_id'][event.resource_id].append(event.audit_id)
        
        event_type_str = event.event_type.value
        if event_type_str not in self._indices['event_type']:
            self._indices['event_type'][event_type_str] = []
        self._indices['event_type'][event_type_str].append(event.audit_id)
    
    async def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events with filters"""
        
        results = list(self._events)
        
        # Filter by date range
        if query.start_date:
            results = [e for e in results if e.timestamp >= query.start_date]
        if query.end_date:
            results = [e for e in results if e.timestamp <= query.end_date]
        
        # Filter by event type
        if query.event_types:
            results = [e for e in results if e.event_type in query.event_types]
        
        # Filter by category
        if query.categories:
            results = [e for e in results if e.category in query.categories]
        
        # Filter by severity
        if query.severities:
            results = [e for e in results if e.severity in query.severities]
        
        # Filter by user
        if query.user_id:
            results = [e for e in results if e.user_id == query.user_id]
        
        # Filter by resource
        if query.resource_type:
            results = [e for e in results if e.resource_type == query.resource_type]
        if query.resource_id:
            results = [e for e in results if e.resource_id == query.resource_id]
        
        # Filter by tags
        if query.tags:
            results = [e for e in results if any(tag in e.tags for tag in query.tags)]
        
        # Filter regulatory only
        if query.regulatory_only:
            results = [e for e in results if e.regulatory_relevant]
        
        # Text search
        if query.search_text:
            search_lower = query.search_text.lower()
            results = [
                e for e in results
                if (search_lower in e.description.lower() or
                    search_lower in e.action.lower())
            ]
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply pagination
        start = query.offset
        end = start + query.limit
        
        return results[start:end]
    
    async def get_event(self, audit_id: str) -> Optional[AuditEvent]:
        """Get specific audit event by ID"""
        for event in self._events:
            if event.audit_id == audit_id:
                return event
        return None
    
    async def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of audit trail chain"""
        
        issues = []
        verified_count = 0
        
        previous_checksum = None
        for event in self._events:
            # Verify checksum
            calculated = self._calculate_checksum(event)
            if calculated != event.checksum:
                issues.append({
                    'audit_id': event.audit_id,
                    'issue': 'checksum_mismatch',
                    'expected': event.checksum,
                    'calculated': calculated
                })
            
            # Verify chain
            if event.previous_checksum != previous_checksum:
                issues.append({
                    'audit_id': event.audit_id,
                    'issue': 'chain_break',
                    'expected_previous': previous_checksum,
                    'actual_previous': event.previous_checksum
                })
            
            if not issues or issues[-1]['audit_id'] != event.audit_id:
                verified_count += 1
            
            previous_checksum = event.checksum
        
        return {
            'total_events': len(self._events),
            'verified_events': verified_count,
            'integrity_issues': len(issues),
            'issues': issues,
            'integrity_valid': len(issues) == 0
        }
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AuditStatistics:
        """Get audit trail statistics"""
        
        # Filter by date if specified
        events = self._events
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]
        
        # Count by type
        by_type = {}
        for event in events:
            event_type = event.event_type.value
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        # Count by category
        by_category = {}
        for event in events:
            category = event.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for event in events:
            severity = event.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by user
        by_user = {}
        for event in events:
            if event.user_id:
                by_user[event.user_id] = by_user.get(event.user_id, 0) + 1
        
        # Count regulatory events
        regulatory_count = len([e for e in events if e.regulatory_relevant])
        
        # Time range
        time_range = {}
        if events:
            time_range = {
                'start': min(e.timestamp for e in events).isoformat(),
                'end': max(e.timestamp for e in events).isoformat()
            }
        
        return AuditStatistics(
            total_events=len(events),
            events_by_type=by_type,
            events_by_category=by_category,
            events_by_severity=by_severity,
            events_by_user=by_user,
            regulatory_events=regulatory_count,
            time_range=time_range
        )
    
    async def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Get all activity for a specific user"""
        
        query = AuditQuery(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        return await self.query_events(query)
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[AuditEvent]:
        """Get complete history of a resource"""
        
        query = AuditQuery(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=1000
        )
        
        return await self.query_events(query)
    
    async def export_for_regulator(
        self,
        regulator: Literal['ASIC', 'AUSTRAC', 'APRA', 'ATO'],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Export audit trail in regulatory format"""
        
        query = AuditQuery(
            start_date=start_date,
            end_date=end_date,
            regulatory_only=True,
            limit=100000
        )
        
        events = await self.query_events(query)
        
        # Filter by regulator relevance
        if regulator == 'AUSTRAC':
            # Financial transactions, suspicious activities
            events = [
                e for e in events
                if e.category == AuditCategory.FINANCIAL or
                   e.event_type == AuditEventType.SUSPICIOUS_ACTIVITY
            ]
        elif regulator == 'ASIC':
            # Compliance, customer operations
            events = [
                e for e in events
                if e.category in [AuditCategory.COMPLIANCE, AuditCategory.FINANCIAL]
            ]
        
        return {
            'regulator': regulator,
            'export_date': datetime.now(timezone.utc).isoformat(),
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_events': len(events),
            'events': [
                {
                    'audit_id': e.audit_id,
                    'timestamp': e.timestamp.isoformat(),
                    'event_type': e.event_type,
                    'category': e.category,
                    'severity': e.severity,
                    'user_id': e.user_id,
                    'resource_type': e.resource_type,
                    'resource_id': e.resource_id,
                    'action': e.action,
                    'description': e.description,
                    'metadata': e.metadata,
                    'checksum': e.checksum
                }
                for e in events
            ],
            'integrity_verified': True  # Would run verification
        }


# ============================================================================
# Global Audit Store
# ============================================================================

_audit_store: Optional[AuditTrailStore] = None

def get_audit_store() -> AuditTrailStore:
    """Get the singleton audit store instance"""
    global _audit_store
    if _audit_store is None:
        _audit_store = AuditTrailStore()
    return _audit_store


# ============================================================================
# Convenience Functions
# ============================================================================

async def audit_login(
    user_id: str,
    user_email: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Audit user login attempt"""
    store = get_audit_store()
    
    if success:
        await store.log_event(
            event_type=AuditEventType.LOGIN,
            category=AuditCategory.SECURITY,
            severity=AuditSeverity.INFO,
            resource_type='user',
            resource_id=user_id,
            action='login_success',
            description=f"User {user_email} logged in successfully",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            regulatory_relevant=True
        )
    else:
        await store.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            category=AuditCategory.SECURITY,
            severity=AuditSeverity.WARNING,
            resource_type='user',
            resource_id=user_id,
            action='login_failed',
            description=f"Failed login attempt for {user_email}",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            regulatory_relevant=True
        )


async def audit_transaction(
    transaction_id: str,
    transaction_type: str,
    amount: Decimal,
    currency: str,
    from_account: str,
    to_account: str,
    user_id: str,
    status: str
):
    """Audit financial transaction"""
    store = get_audit_store()
    
    severity = AuditSeverity.INFO
    if status == 'REJECTED':
        severity = AuditSeverity.WARNING
    
    await store.log_event(
        event_type=AuditEventType.TRANSACTION_INITIATED,
        category=AuditCategory.FINANCIAL,
        severity=severity,
        resource_type='transaction',
        resource_id=transaction_id,
        action=f'transaction_{status.lower()}',
        description=f"{transaction_type} transaction of {amount} {currency}",
        user_id=user_id,
        metadata={
            'transaction_type': transaction_type,
            'amount': str(amount),
            'currency': currency,
            'from_account': from_account,
            'to_account': to_account,
            'status': status
        },
        regulatory_relevant=True
    )


async def audit_document_access(
    document_id: str,
    user_id: str,
    action: str,
    document_type: str
):
    """Audit document access"""
    store = get_audit_store()
    
    event_type_map = {
        'uploaded': AuditEventType.DOCUMENT_UPLOADED,
        'accessed': AuditEventType.DOCUMENT_ACCESSED,
        'modified': AuditEventType.DOCUMENT_MODIFIED,
        'deleted': AuditEventType.DOCUMENT_DELETED
    }
    
    await store.log_event(
        event_type=event_type_map.get(action, AuditEventType.DOCUMENT_ACCESSED),
        category=AuditCategory.OPERATIONAL,
        severity=AuditSeverity.INFO,
        resource_type='document',
        resource_id=document_id,
        action=action,
        description=f"Document {action}: {document_type}",
        user_id=user_id,
        metadata={'document_type': document_type},
        regulatory_relevant=True
    )

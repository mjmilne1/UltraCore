"""
Security Event Repository
Data access for security events, threats, and incidents
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
import logging

from ultracore.database.models.security import SecurityEvent, ThreatEvent, SecurityIncident, AuditLog
from ultracore.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    """
    Security event repository
    
    Provides:
    - Security event CRUD
    - Event querying by type, severity, user, IP
    - Threat detection analytics
    - Audit trail queries
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(SecurityEvent, session)
        self.session = session
    
    # ========================================================================
    # Event Queries
    # ========================================================================
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[SecurityEvent]:
        """Get security events for tenant"""
        result = await self.session.execute(
            select(SecurityEvent)
            .where(SecurityEvent.tenant_id == tenant_id)
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
            .offset(offset)
        )
        
        return list(result.scalars().all())
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get security events for user"""
        result = await self.session.execute(
            select(SecurityEvent)
            .where(SecurityEvent.user_id == user_id)
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def get_by_type(
        self,
        tenant_id: UUID,
        event_type: str,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get security events by type"""
        result = await self.session.execute(
            select(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.event_type == event_type
                )
            )
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def get_by_severity(
        self,
        tenant_id: UUID,
        severity: str,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get security events by severity"""
        result = await self.session.execute(
            select(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.severity == severity
                )
            )
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def get_by_ip(
        self,
        ip_address: str,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get security events by IP address"""
        result = await self.session.execute(
            select(SecurityEvent)
            .where(SecurityEvent.ip_address == ip_address)
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def get_recent_events(
        self,
        tenant_id: UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get recent security events"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.timestamp >= since
                )
            )
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    # ========================================================================
    # Analytics
    # ========================================================================
    
    async def count_by_type(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> Dict[str, int]:
        """Count events by type in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(
                SecurityEvent.event_type,
                func.count(SecurityEvent.event_id).label('count')
            )
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.timestamp >= since
                )
            )
            .group_by(SecurityEvent.event_type)
        )
        
        return {row[0]: row[1] for row in result.all()}
    
    async def count_by_severity(
        self,
        tenant_id: UUID,
        hours: int = 24
    ) -> Dict[str, int]:
        """Count events by severity in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(
                SecurityEvent.severity,
                func.count(SecurityEvent.event_id).label('count')
            )
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.timestamp >= since
                )
            )
            .group_by(SecurityEvent.severity)
        )
        
        return {row[0]: row[1] for row in result.all()}
    
    async def get_failed_login_count(
        self,
        user_id: UUID,
        hours: int = 1
    ) -> int:
        """Count failed login attempts for user"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(func.count(SecurityEvent.event_id))
            .where(
                and_(
                    SecurityEvent.user_id == user_id,
                    SecurityEvent.event_type == 'login_failure',
                    SecurityEvent.timestamp >= since
                )
            )
        )
        
        return result.scalar()
    
    async def get_high_risk_events(
        self,
        tenant_id: UUID,
        min_risk_score: float = 70.0,
        hours: int = 24
    ) -> List[SecurityEvent]:
        """Get high-risk security events"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.tenant_id == tenant_id,
                    SecurityEvent.risk_score >= min_risk_score,
                    SecurityEvent.timestamp >= since
                )
            )
            .order_by(desc(SecurityEvent.risk_score))
        )
        
        return list(result.scalars().all())


class ThreatEventRepository(BaseRepository[ThreatEvent]):
    """Threat event repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ThreatEvent, session)
        self.session = session
    
    async def get_active_threats(self, tenant_id: UUID) -> List[ThreatEvent]:
        """Get active threats (not resolved)"""
        result = await self.session.execute(
            select(ThreatEvent)
            .where(
                and_(
                    ThreatEvent.tenant_id == tenant_id,
                    ThreatEvent.status.in_(['detected', 'investigating', 'mitigated'])
                )
            )
            .order_by(desc(ThreatEvent.detected_at))
        )
        
        return list(result.scalars().all())
    
    async def get_by_severity(
        self,
        tenant_id: UUID,
        severity: str
    ) -> List[ThreatEvent]:
        """Get threats by severity"""
        result = await self.session.execute(
            select(ThreatEvent)
            .where(
                and_(
                    ThreatEvent.tenant_id == tenant_id,
                    ThreatEvent.severity == severity
                )
            )
            .order_by(desc(ThreatEvent.detected_at))
        )
        
        return list(result.scalars().all())


class SecurityIncidentRepository(BaseRepository[SecurityIncident]):
    """Security incident repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SecurityIncident, session)
        self.session = session
    
    async def get_open_incidents(self, tenant_id: UUID) -> List[SecurityIncident]:
        """Get open incidents"""
        result = await self.session.execute(
            select(SecurityIncident)
            .where(
                and_(
                    SecurityIncident.tenant_id == tenant_id,
                    SecurityIncident.status.in_(['open', 'investigating'])
                )
            )
            .order_by(desc(SecurityIncident.created_at))
        )
        
        return list(result.scalars().all())
    
    async def get_by_priority(
        self,
        tenant_id: UUID,
        priority: str
    ) -> List[SecurityIncident]:
        """Get incidents by priority"""
        result = await self.session.execute(
            select(SecurityIncident)
            .where(
                and_(
                    SecurityIncident.tenant_id == tenant_id,
                    SecurityIncident.priority == priority
                )
            )
            .order_by(desc(SecurityIncident.created_at))
        )
        
        return list(result.scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    """Audit log repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
        self.session = session
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for an entity"""
        result = await self.session.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a user"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        
        return list(result.scalars().all())

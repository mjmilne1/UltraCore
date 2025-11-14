"""Tenant Aggregate (Event-Sourced)"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from ..events import *
from ..models import TenantConfig

@dataclass
class TenantAggregate:
    """Event-sourced tenant aggregate"""
    tenant_id: str
    version: int = 0
    events: List[Any] = field(default_factory=list)
    
    # State
    tenant_name: str = ""
    tier: Optional[TenantTier] = None
    status: TenantStatus = TenantStatus.PROVISIONING
    owner_email: str = ""
    db_name: Optional[str] = None
    schema_name: Optional[str] = None
    min_connections: int = 5
    max_connections: int = 20
    created_at: Optional[datetime] = None
    
    def create_tenant(self, tenant_name: str, tier: TenantTier, 
                     owner_email: str, created_by: str) -> 'TenantAggregate':
        """Create new tenant"""
        event = TenantCreatedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            tenant_name=tenant_name,
            tier=tier,
            owner_email=owner_email,
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        return self._apply_event(event)
    
    def start_provisioning(self, tier: TenantTier, 
                          db_name: Optional[str] = None,
                          schema_name: Optional[str] = None) -> 'TenantAggregate':
        """Start tenant provisioning"""
        event = TenantProvisioningStartedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            tier=tier,
            db_name=db_name,
            schema_name=schema_name,
            started_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def complete_database_creation(self, db_host: str, db_port: int,
                                   db_name: str, db_username: str) -> 'TenantAggregate':
        """Complete database creation (Enterprise tier)"""
        event = TenantDatabaseCreatedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_username=db_username,
            created_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def complete_schema_creation(self, db_name: str, 
                                 schema_name: str) -> 'TenantAggregate':
        """Complete schema creation (Standard tier)"""
        event = TenantSchemaCreatedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            db_name=db_name,
            schema_name=schema_name,
            created_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def complete_migrations(self, migration_version: str, 
                           tables_created: int) -> 'TenantAggregate':
        """Complete database migrations"""
        event = TenantMigrationsCompletedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            migration_version=migration_version,
            tables_created=tables_created,
            completed_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def activate(self) -> 'TenantAggregate':
        """Activate tenant"""
        event = TenantActivatedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            tier=self.tier,
            activated_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def suspend(self, reason: str, suspended_by: str) -> 'TenantAggregate':
        """Suspend tenant"""
        event = TenantSuspendedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            reason=reason,
            suspended_at=datetime.utcnow(),
            suspended_by=suspended_by
        )
        return self._apply_event(event)
    
    def reactivate(self, reactivated_by: str) -> 'TenantAggregate':
        """Reactivate tenant"""
        event = TenantReactivatedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            reactivated_at=datetime.utcnow(),
            reactivated_by=reactivated_by
        )
        return self._apply_event(event)
    
    def resize_connection_pool(self, new_min: int, new_max: int, 
                               reason: str) -> 'TenantAggregate':
        """Resize connection pool"""
        event = TenantConnectionPoolResizedEvent(
            event_id=str(uuid4()),
            tenant_id=self.tenant_id,
            old_min_connections=self.min_connections,
            old_max_connections=self.max_connections,
            new_min_connections=new_min,
            new_max_connections=new_max,
            reason=reason,
            resized_at=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def _apply_event(self, event: Any) -> 'TenantAggregate':
        """Apply event to aggregate"""
        # Update state based on event type
        if isinstance(event, TenantCreatedEvent):
            self.tenant_name = event.tenant_name
            self.tier = event.tier
            self.owner_email = event.owner_email
            self.created_at = event.created_at
            self.status = TenantStatus.PROVISIONING
        
        elif isinstance(event, TenantDatabaseCreatedEvent):
            self.db_name = event.db_name
        
        elif isinstance(event, TenantSchemaCreatedEvent):
            self.db_name = event.db_name
            self.schema_name = event.schema_name
        
        elif isinstance(event, TenantActivatedEvent):
            self.status = TenantStatus.ACTIVE
        
        elif isinstance(event, TenantSuspendedEvent):
            self.status = TenantStatus.SUSPENDED
        
        elif isinstance(event, TenantReactivatedEvent):
            self.status = TenantStatus.ACTIVE
        
        elif isinstance(event, TenantConnectionPoolResizedEvent):
            self.min_connections = event.new_min_connections
            self.max_connections = event.new_max_connections
        
        # Add event to history
        self.events.append(event)
        self.version += 1
        
        return self
    
    @classmethod
    def from_events(cls, tenant_id: str, events: List[Any]) -> 'TenantAggregate':
        """Rebuild aggregate from events"""
        aggregate = cls(tenant_id=tenant_id)
        for event in events:
            aggregate = aggregate._apply_event(event)
        return aggregate

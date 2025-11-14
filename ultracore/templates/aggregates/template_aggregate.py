"""Template Aggregate"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from ..events import *

@dataclass
class TemplateAggregate:
    """Event-sourced template aggregate"""
    template_id: str
    template_name: str = ""
    template_type: Optional[TemplateType] = None
    category: str = ""
    configuration: Dict = field(default_factory=dict)
    is_public: bool = False
    is_published: bool = False
    is_australian_compliant: bool = False
    application_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tenant_id: str = ""
    events: List = field(default_factory=list)
    
    def create(self, template_name: str, template_type: TemplateType,
               category: str, configuration: Dict, is_public: bool,
               is_australian_compliant: bool, created_by: str,
               tenant_id: str) -> 'TemplateAggregate':
        """Create template"""
        event = TemplateCreatedEvent(
            template_id=self.template_id,
            template_name=template_name,
            template_type=template_type,
            category=category,
            configuration=configuration,
            is_public=is_public,
            is_australian_compliant=is_australian_compliant,
            created_by=created_by,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def update(self, template_name: Optional[str] = None,
               configuration: Optional[Dict] = None,
               is_public: Optional[bool] = None,
               updated_by: str = "") -> 'TemplateAggregate':
        """Update template"""
        event = TemplateUpdatedEvent(
            template_id=self.template_id,
            template_name=template_name,
            configuration=configuration,
            is_public=is_public,
            updated_by=updated_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def apply_to(self, applied_to_type: str, applied_to_id: str,
                 user_id: str, tenant_id: str,
                 customizations: Optional[Dict] = None) -> 'TemplateAggregate':
        """Apply template to entity"""
        event = TemplateAppliedEvent(
            template_id=self.template_id,
            applied_to_type=applied_to_type,
            applied_to_id=applied_to_id,
            user_id=user_id,
            tenant_id=tenant_id,
            customizations=customizations,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def publish(self, published_by: str,
                price: Optional[Decimal] = None) -> 'TemplateAggregate':
        """Publish template to marketplace"""
        event = TemplatePublishedEvent(
            template_id=self.template_id,
            published_by=published_by,
            price=price,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def delete(self, deleted_by: str) -> 'TemplateAggregate':
        """Delete template"""
        event = TemplateDeletedEvent(
            template_id=self.template_id,
            deleted_by=deleted_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def _apply_event(self, event) -> 'TemplateAggregate':
        """Apply event to aggregate"""
        new_aggregate = TemplateAggregate(
            template_id=self.template_id,
            template_name=self.template_name,
            template_type=self.template_type,
            category=self.category,
            configuration=self.configuration.copy(),
            is_public=self.is_public,
            is_published=self.is_published,
            is_australian_compliant=self.is_australian_compliant,
            application_count=self.application_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tenant_id=self.tenant_id,
            events=self.events.copy()
        )
        
        if isinstance(event, TemplateCreatedEvent):
            new_aggregate.template_name = event.template_name
            new_aggregate.template_type = event.template_type
            new_aggregate.category = event.category
            new_aggregate.configuration = event.configuration
            new_aggregate.is_public = event.is_public
            new_aggregate.is_australian_compliant = event.is_australian_compliant
            new_aggregate.tenant_id = event.tenant_id
            new_aggregate.created_at = event.timestamp
            new_aggregate.updated_at = event.timestamp
        
        elif isinstance(event, TemplateUpdatedEvent):
            if event.template_name:
                new_aggregate.template_name = event.template_name
            if event.configuration:
                new_aggregate.configuration = event.configuration
            if event.is_public is not None:
                new_aggregate.is_public = event.is_public
            new_aggregate.updated_at = event.timestamp
        
        elif isinstance(event, TemplateAppliedEvent):
            new_aggregate.application_count += 1
        
        elif isinstance(event, TemplatePublishedEvent):
            new_aggregate.is_published = True
        
        new_aggregate.events.append(event)
        return new_aggregate

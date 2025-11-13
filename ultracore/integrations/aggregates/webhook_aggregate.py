"""Webhook Aggregate"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from ..events import *

@dataclass
class WebhookAggregate:
    """Event-sourced webhook aggregate"""
    webhook_id: str
    url: str = ""
    events: List[WebhookEvent] = field(default_factory=list)
    secret: str = ""
    is_active: bool = True
    user_id: str = ""
    tenant_id: str = ""
    delivery_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_triggered_at: Optional[datetime] = None
    last_delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    event_history: List = field(default_factory=list)
    
    def register(self, url: str, events: List[WebhookEvent], secret: str,
                 is_active: bool, user_id: str, tenant_id: str,
                 created_by: str) -> 'WebhookAggregate':
        """Register webhook"""
        event = WebhookRegisteredEvent(
            webhook_id=self.webhook_id,
            url=url,
            events=events,
            secret=secret,
            is_active=is_active,
            user_id=user_id,
            tenant_id=tenant_id,
            created_by=created_by,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def trigger(self, event_type: WebhookEvent,
                payload: Dict) -> 'WebhookAggregate':
        """Trigger webhook"""
        event = WebhookTriggeredEvent(
            webhook_id=self.webhook_id,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def mark_delivered(self, delivery_id: str, event_type: WebhookEvent,
                       status_code: int,
                       response_time_ms: float) -> 'WebhookAggregate':
        """Mark webhook as delivered"""
        event = WebhookDeliveredEvent(
            webhook_id=self.webhook_id,
            delivery_id=delivery_id,
            event_type=event_type,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def mark_failed(self, delivery_id: str, event_type: WebhookEvent,
                    error_message: str, status_code: Optional[int],
                    retry_count: int) -> 'WebhookAggregate':
        """Mark webhook delivery as failed"""
        event = WebhookFailedEvent(
            webhook_id=self.webhook_id,
            delivery_id=delivery_id,
            event_type=event_type,
            error_message=error_message,
            status_code=status_code,
            retry_count=retry_count,
            timestamp=datetime.utcnow()
        )
        return self._apply_event(event)
    
    def _apply_event(self, event) -> 'WebhookAggregate':
        """Apply event to aggregate"""
        new_aggregate = WebhookAggregate(
            webhook_id=self.webhook_id,
            url=self.url,
            events=self.events.copy(),
            secret=self.secret,
            is_active=self.is_active,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            delivery_count=self.delivery_count,
            success_count=self.success_count,
            failure_count=self.failure_count,
            last_triggered_at=self.last_triggered_at,
            last_delivered_at=self.last_delivered_at,
            created_at=self.created_at,
            event_history=self.event_history.copy()
        )
        
        if isinstance(event, WebhookRegisteredEvent):
            new_aggregate.url = event.url
            new_aggregate.events = event.events
            new_aggregate.secret = event.secret
            new_aggregate.is_active = event.is_active
            new_aggregate.user_id = event.user_id
            new_aggregate.tenant_id = event.tenant_id
            new_aggregate.created_at = event.timestamp
        
        elif isinstance(event, WebhookTriggeredEvent):
            new_aggregate.last_triggered_at = event.timestamp
            new_aggregate.delivery_count += 1
        
        elif isinstance(event, WebhookDeliveredEvent):
            new_aggregate.success_count += 1
            new_aggregate.last_delivered_at = event.timestamp
        
        elif isinstance(event, WebhookFailedEvent):
            new_aggregate.failure_count += 1
        
        new_aggregate.event_history.append(event)
        return new_aggregate

"""
Business Rule Aggregate
Event-sourced aggregate for business rules
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from ultracore.rules_engine.events import RuleType, RuleStatus, RuleCreated, RuleActivated, RulePaused, RuleExecuted
from ultracore.rules_engine.event_publisher import get_rules_event_publisher


@dataclass
class BusinessRuleAggregate:
    """Event-sourced aggregate for business rules"""
    
    tenant_id: str
    rule_id: str
    name: str = ""
    rule_type: RuleType = RuleType.CUSTOM
    description: Optional[str] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0
    status: RuleStatus = RuleStatus.DRAFT
    created_by: str = ""
    created_at: Optional[datetime] = None
    execution_count: int = 0
    _events: List[Any] = field(default_factory=list)
    
    def create(self, name: str, rule_type: RuleType, description: Optional[str],
               conditions: List[Dict[str, Any]], actions: List[Dict[str, Any]],
               priority: int, created_by: str):
        event = RuleCreated(
            tenant_id=self.tenant_id, rule_id=self.rule_id, name=name,
            rule_type=rule_type, description=description, conditions=conditions,
            actions=actions, priority=priority, created_by=created_by,
            created_at=datetime.utcnow()
        )
        self._apply_event(event)
        self._publish_event(event)
    
    def activate(self, activated_by: str):
        event = RuleActivated(tenant_id=self.tenant_id, rule_id=self.rule_id,
                            activated_by=activated_by, activated_at=datetime.utcnow())
        self._apply_event(event)
        self._publish_event(event)
    
    def _apply_event(self, event: Any):
        if isinstance(event, RuleCreated):
            self.name, self.rule_type = event.name, event.rule_type
            self.conditions, self.actions = event.conditions, event.actions
            self.status = RuleStatus.DRAFT
        elif isinstance(event, RuleActivated):
            self.status = RuleStatus.ACTIVE
        self._events.append(event)
    
    def _publish_event(self, event: Any):
        get_rules_event_publisher().publish_rule_event(event)

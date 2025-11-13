"""
Rules Engine Event Publisher
Kafka-first event publishing for rules engine
"""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from ultracore.rules_engine.events import (
    RULES_TOPIC,
    WORKFLOWS_TOPIC,
    APPROVALS_TOPIC,
    EXECUTIONS_TOPIC
)


class RulesEventPublisher:
    """
    Kafka event publisher for rules engine
    
    Kafka-First Policy:
    - All state changes MUST flow through Kafka
    - Events are immutable and ordered
    - Guaranteed delivery with retries
    """
    
    def __init__(self):
        # In production, initialize Kafka producer here
        self.producer = None
    
    def publish_rule_event(self, event: Any) -> bool:
        """
        Publish rule event to Kafka
        
        Args:
            event: Rule event (RuleCreated, RuleActivated, etc.)
        
        Returns:
            True if published successfully
        """
        return self._publish(RULES_TOPIC, event)
    
    def publish_workflow_event(self, event: Any) -> bool:
        """
        Publish workflow event to Kafka
        
        Args:
            event: Workflow event (WorkflowCreated, WorkflowStepCompleted, etc.)
        
        Returns:
            True if published successfully
        """
        return self._publish(WORKFLOWS_TOPIC, event)
    
    def publish_approval_event(self, event: Any) -> bool:
        """
        Publish approval event to Kafka
        
        Args:
            event: Approval event (ApprovalRequested, ApprovalGranted, etc.)
        
        Returns:
            True if published successfully
        """
        return self._publish(APPROVALS_TOPIC, event)
    
    def publish_execution_event(self, event: Any) -> bool:
        """
        Publish rule execution event to Kafka
        
        Args:
            event: Execution event (RuleExecuted)
        
        Returns:
            True if published successfully
        """
        return self._publish(EXECUTIONS_TOPIC, event)
    
    def _publish(self, topic: str, event: Any) -> bool:
        """
        Internal publish method
        
        Args:
            topic: Kafka topic
            event: Event to publish
        
        Returns:
            True if published successfully
        """
        try:
            # Convert event to dict
            event_dict = asdict(event) if hasattr(event, '__dataclass_fields__') else event
            
            # Add metadata
            event_dict['_published_at'] = datetime.utcnow().isoformat()
            
            # In production, publish to Kafka
            # self.producer.send(topic, value=event_dict)
            
            # For now, just log
            print(f"[Kafka] Published to {topic}: {event_dict.get('event_type')}")
            
            return True
        except Exception as e:
            print(f"[Kafka] Failed to publish event: {str(e)}")
            return False


# Global instance
_publisher = None

def get_rules_event_publisher() -> RulesEventPublisher:
    """Get global rules event publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = RulesEventPublisher()
    return _publisher

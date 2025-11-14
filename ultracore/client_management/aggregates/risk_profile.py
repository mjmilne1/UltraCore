"""
RiskProfile Aggregate
Event-sourced risk profile with questionnaire and ML-calculated score
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.events import (
    ClientManagementEvent,
    RiskQuestionnaireCompletedEvent,
    RiskScoreCalculatedEvent,
    RiskProfileUpdatedEvent
)
from ultracore.client_management.event_publisher import get_event_publisher, ClientManagementTopic


class RiskProfileAggregate:
    """
    Risk Profile aggregate for investment risk assessment
    Implements event sourcing pattern
    """
    
    def __init__(self, profile_id: str, tenant_id: str):
        self.profile_id = profile_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.questionnaire_responses: Dict[str, Any] = {}
        self.calculated_score: Optional[float] = None
        self.risk_category: Optional[str] = None  # conservative, moderate, balanced, growth, aggressive
        self.risk_factors: Dict[str, Any] = {}
        self.completed_at: Optional[datetime] = None
        self.last_updated: Optional[datetime] = None
    
    def complete_questionnaire(
        self,
        user_id: str,
        client_id: str,
        responses: Dict[str, Any]
    ):
        """Complete risk questionnaire"""
        event = RiskQuestionnaireCompletedEvent(
            aggregate_id=self.profile_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "responses": responses
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def calculate_score(
        self,
        user_id: str,
        score: float,
        risk_category: str,
        risk_factors: Dict[str, Any]
    ):
        """Calculate risk score (ML-powered)"""
        event = RiskScoreCalculatedEvent(
            aggregate_id=self.profile_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "calculated_score": score,
                "risk_category": risk_category,
                "risk_factors": risk_factors
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_profile(
        self,
        user_id: str,
        **updates
    ):
        """Update risk profile"""
        event = RiskProfileUpdatedEvent(
            aggregate_id=self.profile_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=updates
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, RiskQuestionnaireCompletedEvent):
            self.client_id = event.event_data["client_id"]
            self.questionnaire_responses = event.event_data["responses"]
            self.completed_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, RiskScoreCalculatedEvent):
            self.calculated_score = event.event_data["calculated_score"]
            self.risk_category = event.event_data["risk_category"]
            self.risk_factors = event.event_data["risk_factors"]
        
        elif isinstance(event, RiskProfileUpdatedEvent):
            for key, value in event.event_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.last_updated = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.RISK_PROFILES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, profile_id: str, tenant_id: str, events: List[ClientManagementEvent]) -> 'RiskProfileAggregate':
        """Rebuild aggregate from event history"""
        aggregate = cls(profile_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

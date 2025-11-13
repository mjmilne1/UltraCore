"""
ClientProfile Aggregate
Event-sourced client profile with investment history and financial health
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.events import (
    ClientManagementEvent,
    ClientProfileCreatedEvent,
    ClientProfileUpdatedEvent,
    ClientInvestmentHistoryRecordedEvent,
    ClientFinancialHealthScoredEvent
)
from ultracore.client_management.event_publisher import get_event_publisher, ClientManagementTopic


class ClientProfileAggregate:
    """
    Client Profile aggregate for enhanced client management
    Implements event sourcing pattern
    """
    
    def __init__(self, client_id: str, tenant_id: str):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.full_name: Optional[str] = None
        self.email: Optional[str] = None
        self.phone: Optional[str] = None
        self.date_of_birth: Optional[datetime] = None
        self.address: Optional[str] = None
        self.occupation: Optional[str] = None
        self.annual_income: Optional[float] = None
        self.net_worth: Optional[float] = None
        self.investment_experience: Optional[str] = None
        self.investment_history: List[Dict[str, Any]] = []
        self.financial_health_score: Optional[float] = None
        self.financial_health_factors: Dict[str, Any] = {}
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def create_profile(
        self,
        user_id: str,
        full_name: str,
        email: str,
        phone: str,
        date_of_birth: datetime,
        address: str,
        occupation: Optional[str] = None,
        annual_income: Optional[float] = None,
        net_worth: Optional[float] = None,
        investment_experience: str = "beginner"
    ):
        """Create client profile"""
        event = ClientProfileCreatedEvent(
            aggregate_id=self.client_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "date_of_birth": date_of_birth.isoformat(),
                "address": address,
                "occupation": occupation,
                "annual_income": annual_income,
                "net_worth": net_worth,
                "investment_experience": investment_experience
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_profile(
        self,
        user_id: str,
        **updates
    ):
        """Update client profile"""
        event = ClientProfileUpdatedEvent(
            aggregate_id=self.client_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=updates
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def record_investment_history(
        self,
        user_id: str,
        investment_type: str,
        amount: float,
        date: datetime,
        return_percentage: Optional[float] = None,
        notes: Optional[str] = None
    ):
        """Record investment history entry"""
        history_entry = {
            "investment_type": investment_type,
            "amount": amount,
            "date": date.isoformat(),
            "return_percentage": return_percentage,
            "notes": notes
        }
        
        event = ClientInvestmentHistoryRecordedEvent(
            aggregate_id=self.client_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=history_entry
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def score_financial_health(
        self,
        user_id: str,
        score: float,
        factors: Dict[str, Any]
    ):
        """Calculate and record financial health score"""
        event = ClientFinancialHealthScoredEvent(
            aggregate_id=self.client_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "score": score,
                "factors": factors,
                "scored_at": datetime.utcnow().isoformat()
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, ClientProfileCreatedEvent):
            self.full_name = event.event_data["full_name"]
            self.email = event.event_data["email"]
            self.phone = event.event_data["phone"]
            self.date_of_birth = datetime.fromisoformat(event.event_data["date_of_birth"])
            self.address = event.event_data["address"]
            self.occupation = event.event_data.get("occupation")
            self.annual_income = event.event_data.get("annual_income")
            self.net_worth = event.event_data.get("net_worth")
            self.investment_experience = event.event_data["investment_experience"]
            self.created_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ClientProfileUpdatedEvent):
            for key, value in event.event_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, ClientInvestmentHistoryRecordedEvent):
            self.investment_history.append(event.event_data)
        
        elif isinstance(event, ClientFinancialHealthScoredEvent):
            self.financial_health_score = event.event_data["score"]
            self.financial_health_factors = event.event_data["factors"]
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.CLIENTS, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, client_id: str, tenant_id: str, events: List[ClientManagementEvent]) -> 'ClientProfileAggregate':
        """Rebuild aggregate from event history"""
        aggregate = cls(client_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

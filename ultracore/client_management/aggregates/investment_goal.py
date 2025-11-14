"""
InvestmentGoal Aggregate
Event-sourced investment goals tracking (retirement, house, education, etc.)
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.events import (
    ClientManagementEvent,
    InvestmentGoalCreatedEvent,
    InvestmentGoalProgressUpdatedEvent,
    InvestmentGoalAchievedEvent,
    InvestmentGoalModifiedEvent
)
from ultracore.client_management.event_publisher import get_event_publisher, ClientManagementTopic


class InvestmentGoalAggregate:
    """
    Investment Goal aggregate for goal tracking
    Implements event sourcing pattern
    """
    
    def __init__(self, goal_id: str, tenant_id: str):
        self.goal_id = goal_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.goal_type: Optional[str] = None  # retirement, house, education, vacation, emergency_fund, wealth_building
        self.goal_name: Optional[str] = None
        self.target_amount: Optional[float] = None
        self.current_amount: float = 0.0
        self.target_date: Optional[datetime] = None
        self.progress_percentage: float = 0.0
        self.status: str = "active"  # active, achieved, abandoned
        self.monthly_contribution: Optional[float] = None
        self.created_at: Optional[datetime] = None
        self.achieved_at: Optional[datetime] = None
    
    def create_goal(
        self,
        user_id: str,
        client_id: str,
        goal_type: str,
        goal_name: str,
        target_amount: float,
        target_date: datetime,
        monthly_contribution: Optional[float] = None
    ):
        """Create investment goal"""
        event = InvestmentGoalCreatedEvent(
            aggregate_id=self.goal_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "goal_type": goal_type,
                "goal_name": goal_name,
                "target_amount": target_amount,
                "target_date": target_date.isoformat(),
                "monthly_contribution": monthly_contribution
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_progress(
        self,
        user_id: str,
        current_amount: float
    ):
        """Update goal progress"""
        progress_percentage = min((current_amount / self.target_amount * 100) if self.target_amount else 0, 100)
        
        event = InvestmentGoalProgressUpdatedEvent(
            aggregate_id=self.goal_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "current_amount": current_amount,
                "progress_percentage": progress_percentage
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
        
        # Check if goal achieved
        if progress_percentage >= 100:
            self.mark_achieved(user_id)
    
    def mark_achieved(self, user_id: str):
        """Mark goal as achieved"""
        event = InvestmentGoalAchievedEvent(
            aggregate_id=self.goal_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "achieved_amount": self.current_amount,
                "target_amount": self.target_amount
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def modify_goal(
        self,
        user_id: str,
        **modifications
    ):
        """Modify goal parameters"""
        event = InvestmentGoalModifiedEvent(
            aggregate_id=self.goal_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=modifications
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, InvestmentGoalCreatedEvent):
            self.client_id = event.event_data["client_id"]
            self.goal_type = event.event_data["goal_type"]
            self.goal_name = event.event_data["goal_name"]
            self.target_amount = event.event_data["target_amount"]
            self.target_date = datetime.fromisoformat(event.event_data["target_date"])
            self.monthly_contribution = event.event_data.get("monthly_contribution")
            self.status = "active"
            self.created_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, InvestmentGoalProgressUpdatedEvent):
            self.current_amount = event.event_data["current_amount"]
            self.progress_percentage = event.event_data["progress_percentage"]
        
        elif isinstance(event, InvestmentGoalAchievedEvent):
            self.status = "achieved"
            self.achieved_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, InvestmentGoalModifiedEvent):
            for key, value in event.event_data.items():
                if hasattr(self, key):
                    if key == "target_date" and isinstance(value, str):
                        setattr(self, key, datetime.fromisoformat(value))
                    else:
                        setattr(self, key, value)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.INVESTMENT_GOALS, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, goal_id: str, tenant_id: str, events: List[ClientManagementEvent]) -> 'InvestmentGoalAggregate':
        """Rebuild aggregate from event history"""
        aggregate = cls(goal_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

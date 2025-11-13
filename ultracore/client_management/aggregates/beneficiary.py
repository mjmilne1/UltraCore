"""
Beneficiary and FamilyPortfolio Aggregates
Event-sourced beneficiary designation and family portfolio management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.client_management.events import (
    ClientManagementEvent,
    BeneficiaryAddedEvent,
    BeneficiaryUpdatedEvent,
    BeneficiaryRemovedEvent,
    FamilyPortfolioCreatedEvent,
    FamilyMemberAddedEvent,
    FamilyMemberRemovedEvent,
    JointAccountCreatedEvent
)
from ultracore.client_management.event_publisher import get_event_publisher, ClientManagementTopic


class BeneficiaryAggregate:
    """
    Beneficiary aggregate for account beneficiary designation
    Implements event sourcing pattern
    """
    
    def __init__(self, beneficiary_id: str, tenant_id: str):
        self.beneficiary_id = beneficiary_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.client_id: Optional[str] = None
        self.account_id: Optional[str] = None
        self.full_name: Optional[str] = None
        self.relationship: Optional[str] = None  # spouse, child, parent, sibling, other
        self.percentage: Optional[float] = None
        self.contact_email: Optional[str] = None
        self.contact_phone: Optional[str] = None
        self.date_of_birth: Optional[datetime] = None
        self.address: Optional[str] = None
        self.is_active: bool = True
        self.added_at: Optional[datetime] = None
        self.removed_at: Optional[datetime] = None
    
    def add_beneficiary(
        self,
        user_id: str,
        client_id: str,
        account_id: str,
        full_name: str,
        relationship: str,
        percentage: float,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
        address: Optional[str] = None
    ):
        """Add beneficiary to account"""
        event = BeneficiaryAddedEvent(
            aggregate_id=self.beneficiary_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "account_id": account_id,
                "full_name": full_name,
                "relationship": relationship,
                "percentage": percentage,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
                "address": address
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def update_beneficiary(
        self,
        user_id: str,
        **updates
    ):
        """Update beneficiary information"""
        event = BeneficiaryUpdatedEvent(
            aggregate_id=self.beneficiary_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data=updates
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def remove_beneficiary(self, user_id: str):
        """Remove beneficiary"""
        event = BeneficiaryRemovedEvent(
            aggregate_id=self.beneficiary_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={}
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, BeneficiaryAddedEvent):
            self.client_id = event.event_data["client_id"]
            self.account_id = event.event_data["account_id"]
            self.full_name = event.event_data["full_name"]
            self.relationship = event.event_data["relationship"]
            self.percentage = event.event_data["percentage"]
            self.contact_email = event.event_data.get("contact_email")
            self.contact_phone = event.event_data.get("contact_phone")
            if event.event_data.get("date_of_birth"):
                self.date_of_birth = datetime.fromisoformat(event.event_data["date_of_birth"])
            self.address = event.event_data.get("address")
            self.is_active = True
            self.added_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, BeneficiaryUpdatedEvent):
            for key, value in event.event_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        elif isinstance(event, BeneficiaryRemovedEvent):
            self.is_active = False
            self.removed_at = datetime.fromisoformat(event.event_timestamp)
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.BENEFICIARIES, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success


class FamilyPortfolioAggregate:
    """
    Family Portfolio aggregate for shared/joint account management
    Implements event sourcing pattern
    """
    
    def __init__(self, portfolio_id: str, tenant_id: str):
        self.portfolio_id = portfolio_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ClientManagementEvent] = []
        
        # State
        self.portfolio_name: Optional[str] = None
        self.primary_client_id: Optional[str] = None
        self.family_members: List[Dict[str, Any]] = []
        self.joint_accounts: List[str] = []
        self.total_value: float = 0.0
        self.created_at: Optional[datetime] = None
    
    def create_portfolio(
        self,
        user_id: str,
        portfolio_name: str,
        primary_client_id: str
    ):
        """Create family portfolio"""
        event = FamilyPortfolioCreatedEvent(
            aggregate_id=self.portfolio_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "portfolio_name": portfolio_name,
                "primary_client_id": primary_client_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def add_family_member(
        self,
        user_id: str,
        client_id: str,
        relationship: str,
        access_level: str = "view"  # view, trade, admin
    ):
        """Add family member to portfolio"""
        event = FamilyMemberAddedEvent(
            aggregate_id=self.portfolio_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id,
                "relationship": relationship,
                "access_level": access_level
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def remove_family_member(
        self,
        user_id: str,
        client_id: str
    ):
        """Remove family member from portfolio"""
        event = FamilyMemberRemovedEvent(
            aggregate_id=self.portfolio_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "client_id": client_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def create_joint_account(
        self,
        user_id: str,
        account_id: str,
        account_type: str,
        owners: List[str]
    ):
        """Create joint account"""
        event = JointAccountCreatedEvent(
            aggregate_id=self.portfolio_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "account_id": account_id,
                "account_type": account_type,
                "owners": owners
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ClientManagementEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, FamilyPortfolioCreatedEvent):
            self.portfolio_name = event.event_data["portfolio_name"]
            self.primary_client_id = event.event_data["primary_client_id"]
            self.created_at = datetime.fromisoformat(event.event_timestamp)
        
        elif isinstance(event, FamilyMemberAddedEvent):
            self.family_members.append({
                "client_id": event.event_data["client_id"],
                "relationship": event.event_data["relationship"],
                "access_level": event.event_data["access_level"],
                "added_at": event.event_timestamp
            })
        
        elif isinstance(event, FamilyMemberRemovedEvent):
            self.family_members = [
                m for m in self.family_members 
                if m["client_id"] != event.event_data["client_id"]
            ]
        
        elif isinstance(event, JointAccountCreatedEvent):
            self.joint_accounts.append(event.event_data["account_id"])
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ClientManagementTopic.FAMILY_PORTFOLIOS, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success

"""
Customer Aggregate (AML/CTF)
Event-sourced customer identification and verification
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from ultracore.compliance.events import (
    ComplianceEvent,
    CustomerIdentifiedEvent,
    CustomerVerifiedEvent
)
from ultracore.compliance.event_publisher import get_event_publisher, ComplianceTopic


class CustomerAggregate:
    """
    Customer aggregate for AML/CTF compliance
    Implements event sourcing pattern
    """
    
    def __init__(self, customer_id: str, tenant_id: str):
        self.customer_id = customer_id
        self.tenant_id = tenant_id
        self.uncommitted_events: List[ComplianceEvent] = []
        
        # State (rebuilt from events)
        self.full_name: Optional[str] = None
        self.date_of_birth: Optional[datetime] = None
        self.residential_address: Optional[str] = None
        self.identification_type: Optional[str] = None
        self.identification_number: Optional[str] = None
        self.risk_level: str = "medium"
        self.is_verified: bool = False
        self.pep_check_passed: bool = False
        self.sanctions_check_passed: bool = False
    
    def identify(
        self,
        user_id: str,
        full_name: str,
        date_of_birth: datetime,
        residential_address: str,
        identification_type: str,
        identification_number: str,
        risk_level: str = "medium"
    ):
        """Create customer identification (KYC)"""
        event = CustomerIdentifiedEvent(
            aggregate_id=self.customer_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "full_name": full_name,
                "date_of_birth": date_of_birth.isoformat(),
                "residential_address": residential_address,
                "identification_type": identification_type,
                "identification_number": identification_number,
                "risk_level": risk_level
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def verify(
        self,
        user_id: str,
        verification_method: str,
        pep_check_result: bool,
        sanctions_check_result: bool
    ):
        """Verify customer identity"""
        event = CustomerVerifiedEvent(
            aggregate_id=self.customer_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            event_data={
                "verification_method": verification_method,
                "verification_status": "verified" if (pep_check_result and sanctions_check_result) else "failed",
                "pep_check_result": pep_check_result,
                "sanctions_check_result": sanctions_check_result,
                "verified_by": user_id
            }
        )
        
        self.apply(event)
        self.uncommitted_events.append(event)
    
    def apply(self, event: ComplianceEvent):
        """Apply event to update aggregate state"""
        if isinstance(event, CustomerIdentifiedEvent):
            self.full_name = event.event_data["full_name"]
            self.date_of_birth = datetime.fromisoformat(event.event_data["date_of_birth"])
            self.residential_address = event.event_data["residential_address"]
            self.identification_type = event.event_data["identification_type"]
            self.identification_number = event.event_data["identification_number"]
            self.risk_level = event.event_data["risk_level"]
        
        elif isinstance(event, CustomerVerifiedEvent):
            self.is_verified = event.event_data["verification_status"] == "verified"
            self.pep_check_passed = event.event_data["pep_check_result"]
            self.sanctions_check_passed = event.event_data["sanctions_check_result"]
    
    def commit(self) -> bool:
        """Publish uncommitted events to Kafka"""
        publisher = get_event_publisher()
        success = True
        
        for event in self.uncommitted_events:
            if not publisher.publish(ComplianceTopic.AML, event):
                success = False
        
        if success:
            self.uncommitted_events.clear()
        
        return success
    
    @classmethod
    def from_events(cls, customer_id: str, tenant_id: str, events: List[ComplianceEvent]) -> 'CustomerAggregate':
        """Rebuild aggregate from event history"""
        aggregate = cls(customer_id, tenant_id)
        for event in events:
            aggregate.apply(event)
        return aggregate

"""
UltraCore Customer Management - Customer Manager

Core customer management orchestration:
- Customer lifecycle (create, update, verify, close)
- Event sourcing integration
- Graph database integration
- Vector embeddings for search
- Audit trail
- Data mesh integration
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from decimal import Decimal
from dataclasses import asdict
import uuid

from ultracore.customers.core.customer_models import (
    Customer, CustomerType, CustomerStatus, CustomerSegment, RiskRating,
    Address, ContactDetails, Identification, IdentificationType,
    KYCRecord, KYCStatus, DueDiligenceLevel, PEPStatus,
    CustomerRelationship, RelationshipType,
    VectorEmbedding, CustomerSegmentProfile,
    CustomerEvent, CustomerEventType
)
from ultracore.customers.core.customer_graph import (
    get_customer_graph, CustomerGraph, BeneficialOwner
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Customer Manager
# ============================================================================

class CustomerManager:
    """
    Core customer management system
    
    ARCHITECTURE:
    - Event sourcing (all changes as events)
    - Graph database (relationships)
    - Vector embeddings (semantic search)
    - CQRS (command/query separation)
    - Multi-tenancy support
    - Audit trail
    """
    
    def __init__(self):
        # Storage (in-memory for now, would use database in production)
        self.customers: Dict[str, Customer] = {}
        self.relationships: Dict[str, CustomerRelationship] = {}
        self.embeddings: Dict[str, VectorEmbedding] = {}
        self.events: List[CustomerEvent] = []
        
        # Graph database
        self.graph = get_customer_graph()
        
        # Audit
        self.audit_store = get_audit_store()
        
        # Indexes for fast lookup
        self.by_email: Dict[str, str] = {}  # email -> customer_id
        self.by_mobile: Dict[str, str] = {}  # mobile -> customer_id
        self.by_abn: Dict[str, str] = {}  # ABN -> customer_id
        self.by_tenant: Dict[str, Set[str]] = {}  # tenant_id -> {customer_ids}
        self.by_segment: Dict[CustomerSegment, Set[str]] = {}  # segment -> {customer_ids}
    
    async def create_customer(
        self,
        customer_type: CustomerType,
        created_by: str,
        tenant_id: str = "default",
        **kwargs
    ) -> Customer:
        """
        Create new customer
        
        Args:
            customer_type: Type of customer
            created_by: User creating customer
            tenant_id: Tenant ID (for multi-tenancy)
            **kwargs: Additional customer attributes
        """
        
        customer_id = f"CUST-{uuid.uuid4().hex[:12].upper()}"
        
        # Create customer entity
        customer = Customer(
            customer_id=customer_id,
            customer_type=customer_type,
            customer_status=CustomerStatus.PROSPECT,
            tenant_id=tenant_id,
            created_by=created_by,
            updated_by=created_by,
            **kwargs
        )
        
        # Store customer
        self.customers[customer_id] = customer
        
        # Update indexes
        if customer.contact_details.email:
            self.by_email[customer.contact_details.email] = customer_id
        if customer.contact_details.mobile:
            self.by_mobile[customer.contact_details.mobile] = customer_id
        if customer.abn:
            self.by_abn[customer.abn] = customer_id
        
        # Tenant index
        if tenant_id not in self.by_tenant:
            self.by_tenant[tenant_id] = set()
        self.by_tenant[tenant_id].add(customer_id)
        
        # Segment index
        if customer.segment not in self.by_segment:
            self.by_segment[customer.segment] = set()
        self.by_segment[customer.segment].add(customer_id)
        
        # Add to graph
        self.graph.add_node(customer)
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.CUSTOMER_CREATED,
            customer_id=customer_id,
            tenant_id=tenant_id,
            event_data={
                'customer_type': customer_type.value,
                'name': customer.get_full_name(),
                'segment': customer.segment.value
            },
            caused_by=created_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_CREATED,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='customer_created',
            description=f"Customer created: {customer.get_full_name()}",
            user_id=created_by,
            metadata={
                'customer_type': customer_type.value,
                'tenant_id': tenant_id
            },
            regulatory_relevant=True
        )
        
        return customer
    
    async def update_customer(
        self,
        customer_id: str,
        updated_by: str,
        **updates
    ) -> Customer:
        """Update customer details"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Capture previous state
        previous_state = {
            'status': customer.customer_status.value,
            'segment': customer.segment.value,
            'risk_rating': customer.risk_rating.value
        }
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        customer.updated_by = updated_by
        customer.updated_at = datetime.now(timezone.utc)
        customer.version += 1
        
        # Update indexes if needed
        if 'contact_details' in updates:
            contact = updates['contact_details']
            if hasattr(contact, 'email') and contact.email:
                self.by_email[contact.email] = customer_id
            if hasattr(contact, 'mobile') and contact.mobile:
                self.by_mobile[contact.mobile] = customer_id
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.CUSTOMER_UPDATED,
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            event_data={'updates': list(updates.keys())},
            previous_state=previous_state,
            caused_by=updated_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFIED,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='customer_updated',
            description=f"Customer updated: {customer.get_full_name()}",
            user_id=updated_by,
            metadata={'updates': list(updates.keys())},
            regulatory_relevant=True
        )
        
        return customer
    
    async def add_address(
        self,
        customer_id: str,
        address: Address,
        updated_by: str
    ) -> Customer:
        """Add address to customer"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # If this is primary, remove primary from others
        if address.is_primary:
            for addr in customer.addresses:
                addr.is_primary = False
        
        customer.addresses.append(address)
        customer.updated_by = updated_by
        customer.updated_at = datetime.now(timezone.utc)
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFIED,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='address_added',
            description=f"Address added: {address.address_type}",
            user_id=updated_by,
            regulatory_relevant=True
        )
        
        return customer
    
    async def add_identification(
        self,
        customer_id: str,
        identification: Identification,
        updated_by: str
    ) -> Customer:
        """Add identification document"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # If this is primary, remove primary from others
        if identification.is_primary:
            for id_doc in customer.identifications:
                id_doc.is_primary = False
        
        customer.identifications.append(identification)
        customer.updated_by = updated_by
        customer.updated_at = datetime.now(timezone.utc)
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFIED,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='identification_added',
            description=f"ID added: {identification.id_type.value}",
            user_id=updated_by,
            regulatory_relevant=True
        )
        
        return customer
    
    async def create_relationship(
        self,
        from_customer_id: str,
        to_customer_id: str,
        relationship_type: RelationshipType,
        created_by: str,
        ownership_percentage: Optional[Decimal] = None,
        verified: bool = False
    ) -> CustomerRelationship:
        """
        Create relationship between customers
        Updates graph database
        """
        
        # Validate customers exist
        if from_customer_id not in self.customers:
            raise ValueError(f"Customer {from_customer_id} not found")
        if to_customer_id not in self.customers:
            raise ValueError(f"Customer {to_customer_id} not found")
        
        relationship_id = f"REL-{uuid.uuid4().hex[:12].upper()}"
        
        relationship = CustomerRelationship(
            relationship_id=relationship_id,
            from_customer_id=from_customer_id,
            to_customer_id=to_customer_id,
            relationship_type=relationship_type,
            ownership_percentage=ownership_percentage,
            verified=verified,
            verification_date=date.today() if verified else None
        )
        
        self.relationships[relationship_id] = relationship
        
        # Update customers
        self.customers[from_customer_id].add_relationship(relationship_id)
        self.customers[to_customer_id].add_relationship(relationship_id)
        
        # Add to graph
        self.graph.add_edge(relationship)
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.RELATIONSHIP_ADDED,
            customer_id=from_customer_id,
            tenant_id=self.customers[from_customer_id].tenant_id,
            event_data={
                'relationship_id': relationship_id,
                'to_customer_id': to_customer_id,
                'relationship_type': relationship_type.value,
                'ownership_percentage': str(ownership_percentage) if ownership_percentage else None
            },
            caused_by=created_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer_relationship',
            resource_id=relationship_id,
            action='relationship_created',
            description=f"Relationship created: {relationship_type.value}",
            user_id=created_by,
            metadata={
                'from': from_customer_id,
                'to': to_customer_id,
                'type': relationship_type.value
            },
            regulatory_relevant=True
        )
        
        return relationship
    
    async def complete_kyc(
        self,
        customer_id: str,
        kyc_record: KYCRecord,
        verified_by: str
    ) -> Customer:
        """
        Complete KYC verification
        Updates customer status
        """
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Add KYC record
        customer.kyc_records.append(kyc_record)
        customer.current_kyc_status = kyc_record.kyc_status
        
        # Update PEP status
        if kyc_record.pep_status != PEPStatus.NOT_PEP:
            customer.pep_status = kyc_record.pep_status
        
        # Update risk rating if provided
        if kyc_record.risk_score:
            if kyc_record.risk_score >= 80:
                customer.risk_rating = RiskRating.VERY_HIGH
            elif kyc_record.risk_score >= 60:
                customer.risk_rating = RiskRating.HIGH
            elif kyc_record.risk_score >= 40:
                customer.risk_rating = RiskRating.MEDIUM
            else:
                customer.risk_rating = RiskRating.LOW
        
        # If KYC verified, update status
        if kyc_record.kyc_status == KYCStatus.VERIFIED:
            if customer.customer_status == CustomerStatus.ONBOARDING:
                customer.customer_status = CustomerStatus.ACTIVE
                customer.activation_date = date.today()
        
        customer.updated_by = verified_by
        customer.updated_at = datetime.now(timezone.utc)
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.KYC_COMPLETED,
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            event_data={
                'kyc_status': kyc_record.kyc_status.value,
                'risk_score': str(kyc_record.risk_score) if kyc_record.risk_score else None,
                'pep_status': kyc_record.pep_status.value
            },
            caused_by=verified_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.INFO,
            resource_type='customer_kyc',
            resource_id=kyc_record.kyc_id,
            action='kyc_completed',
            description=f"KYC completed: {kyc_record.kyc_status.value}",
            user_id=verified_by,
            metadata={
                'customer_id': customer_id,
                'kyc_status': kyc_record.kyc_status.value,
                'risk_rating': customer.risk_rating.value
            },
            regulatory_relevant=True
        )
        
        return customer
    
    async def change_status(
        self,
        customer_id: str,
        new_status: CustomerStatus,
        reason: str,
        changed_by: str
    ) -> Customer:
        """Change customer status"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        previous_status = customer.customer_status
        customer.customer_status = new_status
        customer.updated_by = changed_by
        customer.updated_at = datetime.now(timezone.utc)
        
        # Update lifecycle dates
        if new_status == CustomerStatus.ACTIVE and not customer.activation_date:
            customer.activation_date = date.today()
        elif new_status == CustomerStatus.CLOSED:
            customer.closure_date = date.today()
            customer.closure_reason = reason
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.STATUS_CHANGED,
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            event_data={
                'previous_status': previous_status.value,
                'new_status': new_status.value,
                'reason': reason
            },
            caused_by=changed_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFIED,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.WARNING if new_status in [CustomerStatus.SUSPENDED, CustomerStatus.CLOSED] else AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='status_changed',
            description=f"Status changed: {previous_status.value} -> {new_status.value}",
            user_id=changed_by,
            metadata={
                'previous_status': previous_status.value,
                'new_status': new_status.value,
                'reason': reason
            },
            regulatory_relevant=True
        )
        
        return customer
    
    async def update_risk_rating(
        self,
        customer_id: str,
        new_rating: RiskRating,
        reason: str,
        updated_by: str
    ) -> Customer:
        """Update customer risk rating"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        previous_rating = customer.risk_rating
        customer.risk_rating = new_rating
        customer.updated_by = updated_by
        customer.updated_at = datetime.now(timezone.utc)
        
        # Create event
        await self._publish_event(
            event_type=CustomerEventType.RISK_RATING_CHANGED,
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            event_data={
                'previous_rating': previous_rating.value,
                'new_rating': new_rating.value,
                'reason': reason
            },
            caused_by=updated_by
        )
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            category=AuditCategory.CUSTOMER,
            severity=AuditSeverity.WARNING if new_rating in [RiskRating.HIGH, RiskRating.VERY_HIGH] else AuditSeverity.INFO,
            resource_type='customer',
            resource_id=customer_id,
            action='risk_rating_changed',
            description=f"Risk rating changed: {previous_rating.value} -> {new_rating.value}",
            user_id=updated_by,
            metadata={
                'previous_rating': previous_rating.value,
                'new_rating': new_rating.value,
                'reason': reason
            },
            regulatory_relevant=True
        )
        
        return customer
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return self.customers.get(customer_id)
    
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        customer_id = self.by_email.get(email)
        return self.customers.get(customer_id) if customer_id else None
    
    async def find_by_mobile(self, mobile: str) -> Optional[Customer]:
        """Find customer by mobile"""
        customer_id = self.by_mobile.get(mobile)
        return self.customers.get(customer_id) if customer_id else None
    
    async def find_by_abn(self, abn: str) -> Optional[Customer]:
        """Find customer by ABN"""
        customer_id = self.by_abn.get(abn)
        return self.customers.get(customer_id) if customer_id else None
    
    async def get_customers_by_segment(
        self,
        segment: CustomerSegment,
        tenant_id: Optional[str] = None
    ) -> List[Customer]:
        """Get customers by segment"""
        
        customer_ids = self.by_segment.get(segment, set())
        
        if tenant_id:
            tenant_ids = self.by_tenant.get(tenant_id, set())
            customer_ids = customer_ids.intersection(tenant_ids)
        
        return [self.customers[cid] for cid in customer_ids if cid in self.customers]
    
    async def get_beneficial_owners(
        self,
        customer_id: str,
        ownership_threshold: Decimal = Decimal('25.0')
    ) -> List[BeneficialOwner]:
        """
        Get beneficial owners (AUSTRAC compliance)
        25% threshold as per AML/CTF regulations
        """
        return self.graph.find_beneficial_owners(customer_id, ownership_threshold)
    
    async def get_related_customers(
        self,
        customer_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        max_depth: int = 2
    ) -> List[Customer]:
        """Get related customers up to max depth"""
        
        # Get from graph
        neighbors = self.graph.get_neighbors(
            customer_id,
            relationship_types,
            direction="BOTH"
        )
        
        return [self.customers[cid] for cid in neighbors if cid in self.customers]
    
    async def detect_fraud_rings(
        self,
        min_ring_size: int = 3
    ) -> List[List[Customer]]:
        """Detect potential fraud rings"""
        
        rings = self.graph.find_fraud_rings(min_ring_size)
        
        result = []
        for ring in rings:
            customers = [self.customers[cid] for cid in ring if cid in self.customers]
            if customers:
                result.append(customers)
        
        return result
    
    async def get_customer_network_analysis(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive network analysis"""
        
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Relationship summary
        rel_summary = self.graph.get_relationship_summary(customer_id)
        
        # Connected component
        connected = self.graph.find_connected_component(customer_id)
        
        # Centrality metrics
        centrality = {
            'degree': float(self.graph.calculate_centrality(customer_id, "DEGREE")),
            'betweenness': float(self.graph.calculate_centrality(customer_id, "BETWEENNESS"))
        }
        
        # Beneficial owners
        beneficial_owners = await self.get_beneficial_owners(customer_id)
        
        return {
            'customer_id': customer_id,
            'name': customer.get_full_name(),
            'relationship_summary': rel_summary,
            'network_size': len(connected),
            'centrality_metrics': centrality,
            'beneficial_owners': [
                {
                    'customer_id': bo.customer_id,
                    'ownership': str(bo.ownership_percentage),
                    'direct': bo.direct,
                    'ultimate': bo.ultimate
                }
                for bo in beneficial_owners
            ]
        }
    
    async def _publish_event(
        self,
        event_type: CustomerEventType,
        customer_id: str,
        tenant_id: str,
        event_data: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None,
        caused_by: str = "SYSTEM"
    ):
        """Publish event to event store (Event Sourcing)"""
        
        event = CustomerEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:16].upper()}",
            event_type=event_type,
            event_timestamp=datetime.now(timezone.utc),
            customer_id=customer_id,
            tenant_id=tenant_id,
            event_data=event_data,
            previous_state=previous_state,
            caused_by=caused_by
        )
        
        self.events.append(event)
    
    async def get_customer_events(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CustomerEvent]:
        """Get customer event history"""
        
        events = [e for e in self.events if e.customer_id == customer_id]
        
        if start_date:
            events = [e for e in events if e.event_timestamp >= start_date]
        
        if end_date:
            events = [e for e in events if e.event_timestamp <= end_date]
        
        return sorted(events, key=lambda x: x.event_timestamp)
    
    async def get_high_risk_customers(
        self,
        tenant_id: Optional[str] = None
    ) -> List[Customer]:
        """Get all high-risk customers"""
        
        customers = self.customers.values()
        
        if tenant_id:
            tenant_ids = self.by_tenant.get(tenant_id, set())
            customers = [c for c in customers if c.customer_id in tenant_ids]
        
        return [
            c for c in customers
            if c.risk_rating in [RiskRating.HIGH, RiskRating.VERY_HIGH, RiskRating.UNACCEPTABLE]
        ]
    
    async def get_pep_customers(
        self,
        tenant_id: Optional[str] = None
    ) -> List[Customer]:
        """Get all PEP customers"""
        
        customers = self.customers.values()
        
        if tenant_id:
            tenant_ids = self.by_tenant.get(tenant_id, set())
            customers = [c for c in customers if c.customer_id in tenant_ids]
        
        return [c for c in customers if c.pep_status != PEPStatus.NOT_PEP]


# ============================================================================
# Global Singleton
# ============================================================================

_customer_manager: Optional[CustomerManager] = None

def get_customer_manager() -> CustomerManager:
    """Get singleton customer manager"""
    global _customer_manager
    if _customer_manager is None:
        _customer_manager = CustomerManager()
    return _customer_manager

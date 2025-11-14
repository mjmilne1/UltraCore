"""
Complete Insurance Domain - Policy & Claims with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.enhanced_pipeline import enhanced_ml


class PolicyType(str, Enum):
    LIFE = 'LIFE'
    HEALTH = 'HEALTH'
    HOME = 'HOME'
    AUTO = 'AUTO'


class PolicyStatus(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    LAPSED = 'LAPSED'
    CANCELLED = 'CANCELLED'


class ClaimStatus(str, Enum):
    SUBMITTED = 'SUBMITTED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    PAID = 'PAID'


class CompleteInsuranceAggregate:
    """Complete insurance policy lifecycle"""
    
    def __init__(self, policy_id: str):
        self.policy_id = policy_id
        self.client_id: Optional[str] = None
        self.policy_type: Optional[PolicyType] = None
        self.status: PolicyStatus = PolicyStatus.PENDING
        self.premium: Decimal = Decimal('0')
        self.coverage_amount: Decimal = Decimal('0')
        self.claims: List[Dict] = []
        self.total_claims_paid: Decimal = Decimal('0')
    
    async def underwrite_policy(
        self,
        client_id: str,
        policy_type: PolicyType,
        coverage_amount: Decimal,
        applicant_data: Dict
    ):
        """AI-powered underwriting"""
        kafka_store = get_production_kafka_store()
        
        # Calculate premium based on risk
        age = applicant_data.get('age', 30)
        base_premium = coverage_amount * Decimal('0.01')
        
        if policy_type == PolicyType.LIFE:
            if age > 50:
                base_premium *= Decimal('1.5')
        
        event_data = {
            'policy_id': self.policy_id,
            'client_id': client_id,
            'policy_type': policy_type.value,
            'coverage_amount': str(coverage_amount),
            'premium': str(base_premium),
            'underwritten_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='policy_underwritten',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        self.client_id = client_id
        self.policy_type = policy_type
        self.coverage_amount = coverage_amount
        self.premium = base_premium
        self.status = PolicyStatus.PENDING
    
    async def activate_policy(self):
        """Activate insurance policy"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'policy_id': self.policy_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='policy_activated',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        self.status = PolicyStatus.ACTIVE
    
    async def submit_claim(
        self,
        claim_amount: Decimal,
        incident_date: str,
        description: str,
        supporting_docs: List[str]
    ):
        """Submit insurance claim with fraud detection"""
        kafka_store = get_production_kafka_store()
        
        claim_id = f'CLM-{self.policy_id}-{datetime.now(timezone.utc).timestamp()}'
        
        # ML fraud detection
        policy_age_days = 365
        fraud_result = await enhanced_ml.detect_insurance_claim_fraud({
            'claim_amount': float(claim_amount),
            'incident_date': incident_date,
            'policy_age_days': policy_age_days
        })
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'claim_amount': str(claim_amount),
            'incident_date': incident_date,
            'description': description,
            'fraud_score': fraud_result['fraud_score'],
            'fraud_flags': fraud_result['flags'],
            'status': ClaimStatus.SUBMITTED.value,
            'submitted_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='claim_submitted',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        self.claims.append(event_data)
        
        if fraud_result['is_fraudulent']:
            await self._reject_claim(claim_id, 'Suspected fraud')
        else:
            await self._review_claim(claim_id)
        
        return claim_id
    
    async def _review_claim(self, claim_id: str):
        """Review claim"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'status': ClaimStatus.UNDER_REVIEW.value,
            'review_started': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='claim_under_review',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        for claim in self.claims:
            if claim['claim_id'] == claim_id:
                claim['status'] = ClaimStatus.UNDER_REVIEW.value
    
    async def approve_claim(self, claim_id: str, approved_amount: Decimal):
        """Approve claim"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'approved_amount': str(approved_amount),
            'status': ClaimStatus.APPROVED.value,
            'approved_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='claim_approved',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        for claim in self.claims:
            if claim['claim_id'] == claim_id:
                claim['status'] = ClaimStatus.APPROVED.value
    
    async def pay_claim(self, claim_id: str):
        """Pay approved claim"""
        claim = next((c for c in self.claims if c['claim_id'] == claim_id), None)
        if not claim or claim['status'] != ClaimStatus.APPROVED.value:
            raise ValueError('Claim not approved')
        
        kafka_store = get_production_kafka_store()
        
        approved_amount = Decimal(claim['approved_amount'])
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'paid_amount': str(approved_amount),
            'status': ClaimStatus.PAID.value,
            'paid_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='claim_paid',
            event_data=event_data,
            aggregate_id=self.policy_id,
            exactly_once=True
        )
        
        self.total_claims_paid += approved_amount
        claim['status'] = ClaimStatus.PAID.value
    
    async def _reject_claim(self, claim_id: str, reason: str):
        """Reject claim"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'reason': reason,
            'status': ClaimStatus.REJECTED.value,
            'rejected_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='insurance',
            event_type='claim_rejected',
            event_data=event_data,
            aggregate_id=self.policy_id
        )
        
        for claim in self.claims:
            if claim['claim_id'] == claim_id:
                claim['status'] = ClaimStatus.REJECTED.value
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.policy_id)
        
        for event in events:
            if event.event_type == 'policy_underwritten':
                self.client_id = event.event_data['client_id']
                self.policy_type = PolicyType(event.event_data['policy_type'])
                self.coverage_amount = Decimal(event.event_data['coverage_amount'])
                self.premium = Decimal(event.event_data['premium'])
                self.status = PolicyStatus.PENDING
            elif event.event_type == 'policy_activated':
                self.status = PolicyStatus.ACTIVE
            elif event.event_type == 'claim_submitted':
                self.claims.append(event.event_data)
            elif event.event_type == 'claim_paid':
                self.total_claims_paid += Decimal(event.event_data['paid_amount'])

"""
Insurance Domain - Life, Health, Property Insurance
Complete insurance platform: Quotes, Policies, Claims
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store


class InsuranceType(str, Enum):
    LIFE = 'LIFE'
    HEALTH = 'HEALTH'
    HOME = 'HOME'
    AUTO = 'AUTO'
    TRAVEL = 'TRAVEL'


class PolicyStatus(str, Enum):
    QUOTE = 'QUOTE'
    ACTIVE = 'ACTIVE'
    LAPSED = 'LAPSED'
    CANCELLED = 'CANCELLED'


class ClaimStatus(str, Enum):
    SUBMITTED = 'SUBMITTED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    PAID = 'PAID'


class QuoteRequest(BaseModel):
    client_id: str
    insurance_type: InsuranceType
    coverage_amount: float
    term_years: int = 20


class FileClaimRequest(BaseModel):
    incident_date: str
    incident_description: str
    claim_amount: float


class PolicyAggregate:
    def __init__(self, policy_id: str):
        self.policy_id = policy_id
        self.client_id: Optional[str] = None
        self.insurance_type: Optional[InsuranceType] = None
        self.coverage_amount: Decimal = Decimal('0')
        self.premium: Decimal = Decimal('0')
        self.status: PolicyStatus = PolicyStatus.QUOTE
        self.claims: List[Dict] = []
    
    async def generate_quote(
        self,
        client_id: str,
        insurance_type: InsuranceType,
        coverage_amount: Decimal,
        term_years: int
    ):
        """Generate insurance quote"""
        store = get_event_store()
        
        # Calculate premium (simplified)
        base_rate = {
            InsuranceType.LIFE: 0.015,
            InsuranceType.HEALTH: 0.08,
            InsuranceType.HOME: 0.012,
            InsuranceType.AUTO: 0.06,
            InsuranceType.TRAVEL: 0.05
        }
        
        annual_premium = coverage_amount * Decimal(str(base_rate[insurance_type]))
        monthly_premium = annual_premium / 12
        
        event_data = {
            'policy_id': self.policy_id,
            'client_id': client_id,
            'insurance_type': insurance_type.value,
            'coverage_amount': str(coverage_amount),
            'term_years': term_years,
            'annual_premium': str(annual_premium),
            'monthly_premium': str(monthly_premium),
            'quoted_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.policy_id,
            aggregate_type='Policy',
            event_type='QuoteGenerated',
            event_data=event_data,
            user_id='insurance_system'
        )
        
        self.client_id = client_id
        self.insurance_type = insurance_type
        self.coverage_amount = coverage_amount
        self.premium = monthly_premium
        self.status = PolicyStatus.QUOTE
    
    async def activate_policy(self):
        """Activate insurance policy"""
        store = get_event_store()
        
        event_data = {
            'policy_id': self.policy_id,
            'activated_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        }
        
        await store.append(
            aggregate_id=self.policy_id,
            aggregate_type='Policy',
            event_type='PolicyActivated',
            event_data=event_data,
            user_id='insurance_system'
        )
        
        self.status = PolicyStatus.ACTIVE
    
    async def file_claim(
        self,
        incident_date: str,
        incident_description: str,
        claim_amount: Decimal
    ):
        """File insurance claim"""
        if self.status != PolicyStatus.ACTIVE:
            raise ValueError('Policy is not active')
        
        store = get_event_store()
        
        claim_id = f'CLM-{str(__import__("uuid").uuid4())[:8]}'
        
        # Auto-approve claims under coverage amount
        claim_status = ClaimStatus.APPROVED if claim_amount <= self.coverage_amount else ClaimStatus.UNDER_REVIEW
        
        event_data = {
            'policy_id': self.policy_id,
            'claim_id': claim_id,
            'incident_date': incident_date,
            'incident_description': incident_description,
            'claim_amount': str(claim_amount),
            'claim_status': claim_status.value,
            'filed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.policy_id,
            aggregate_type='Policy',
            event_type='ClaimFiled',
            event_data=event_data,
            user_id='insurance_system'
        )
        
        self.claims.append(event_data)
        
        return claim_id
    
    async def load_from_events(self):
        """Rebuild policy state from events"""
        store = get_event_store()
        events = await store.get_events(self.policy_id)
        
        for event in events:
            if event.event_type == 'QuoteGenerated':
                self.client_id = event.event_data['client_id']
                self.insurance_type = InsuranceType(event.event_data['insurance_type'])
                self.coverage_amount = Decimal(event.event_data['coverage_amount'])
                self.premium = Decimal(event.event_data['monthly_premium'])
                self.status = PolicyStatus.QUOTE
            elif event.event_type == 'PolicyActivated':
                self.status = PolicyStatus.ACTIVE
            elif event.event_type == 'ClaimFiled':
                self.claims.append(event.event_data)

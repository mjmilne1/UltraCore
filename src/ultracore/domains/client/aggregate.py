"""
Client Domain - Customer Management with Event Sourcing
"""
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store


class KYCStatus(str, Enum):
    NOT_STARTED = 'NOT_STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'


class ClientStatus(str, Enum):
    PROSPECT = 'PROSPECT'
    ACTIVE = 'ACTIVE'
    SUSPENDED = 'SUSPENDED'


class OnboardingRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    address_line1: str
    city: str
    state: str
    postcode: str
    country: str = 'Australia'


class KYCDocumentRequest(BaseModel):
    document_type: str
    document_number: str
    document_expiry: str


class ClientAggregate:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.email: Optional[str] = None
        self.status: ClientStatus = ClientStatus.PROSPECT
        self.kyc_status: KYCStatus = KYCStatus.NOT_STARTED
        self.risk_score: Optional[int] = None
    
    async def onboard(self, data: OnboardingRequest, user_id: str = 'system'):
        store = get_event_store()
        
        event_data = {
            'client_id': self.client_id,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'email': data.email,
            'phone': data.phone,
            'date_of_birth': data.date_of_birth,
            'address': {
                'line1': data.address_line1,
                'city': data.city,
                'state': data.state,
                'postcode': data.postcode,
                'country': data.country
            },
            'onboarded_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.client_id,
            aggregate_type='Client',
            event_type='ClientOnboarded',
            event_data=event_data,
            user_id=user_id
        )
        
        self.first_name = data.first_name
        self.last_name = data.last_name
        self.email = data.email
        self.status = ClientStatus.PROSPECT
    
    async def submit_kyc_document(self, doc: KYCDocumentRequest):
        store = get_event_store()
        
        event_data = {
            'client_id': self.client_id,
            'document_type': doc.document_type,
            'document_number': doc.document_number,
            'document_expiry': doc.document_expiry,
            'submitted_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.client_id,
            aggregate_type='Client',
            event_type='KYCDocumentSubmitted',
            event_data=event_data,
            user_id='client'
        )
        
        self.kyc_status = KYCStatus.IN_PROGRESS
    
    async def verify_kyc(self, verification_result: Dict):
        store = get_event_store()
        
        event_data = {
            'client_id': self.client_id,
            'verification_status': verification_result['status'],
            'risk_score': verification_result.get('risk_score', 50),
            'verified_by': verification_result.get('verified_by', 'ai_system'),
            'notes': verification_result.get('notes', ''),
            'verified_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.client_id,
            aggregate_type='Client',
            event_type='KYCVerified',
            event_data=event_data,
            user_id='kyc_system'
        )
        
        self.kyc_status = KYCStatus.VERIFIED if verification_result['status'] == 'APPROVED' else KYCStatus.REJECTED
        self.risk_score = verification_result.get('risk_score', 50)
        
        if self.kyc_status == KYCStatus.VERIFIED:
            self.status = ClientStatus.ACTIVE
    
    async def load_from_events(self):
        store = get_event_store()
        events = await store.get_events(self.client_id)
        
        for event in events:
            if event.event_type == 'ClientOnboarded':
                self.first_name = event.event_data['first_name']
                self.last_name = event.event_data['last_name']
                self.email = event.event_data['email']
                self.status = ClientStatus.PROSPECT
            elif event.event_type == 'KYCDocumentSubmitted':
                self.kyc_status = KYCStatus.IN_PROGRESS
            elif event.event_type == 'KYCVerified':
                if event.event_data['verification_status'] == 'APPROVED':
                    self.kyc_status = KYCStatus.VERIFIED
                    self.status = ClientStatus.ACTIVE
                else:
                    self.kyc_status = KYCStatus.REJECTED
                self.risk_score = event.event_data.get('risk_score')

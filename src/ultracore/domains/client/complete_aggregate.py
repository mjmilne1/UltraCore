"""
Complete Client Domain - Full KYC Lifecycle with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.data_mesh.integration import DataMeshPublisher
from ultracore.ml_models.enhanced_pipeline import enhanced_ml


class ClientStatus(str, Enum):
    PENDING = 'PENDING'
    KYC_IN_PROGRESS = 'KYC_IN_PROGRESS'
    KYC_APPROVED = 'KYC_APPROVED'
    KYC_REJECTED = 'KYC_REJECTED'
    ACTIVE = 'ACTIVE'
    SUSPENDED = 'SUSPENDED'
    CLOSED = 'CLOSED'


class KYCStatus(str, Enum):
    NOT_STARTED = 'NOT_STARTED'
    DOCUMENTS_SUBMITTED = 'DOCUMENTS_SUBMITTED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'


class RiskLevel(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    VERY_HIGH = 'VERY_HIGH'


class CompleteClientAggregate:
    """Complete client lifecycle management"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.email: Optional[str] = None
        self.status: ClientStatus = ClientStatus.PENDING
        self.kyc_status: KYCStatus = KYCStatus.NOT_STARTED
        self.risk_level: RiskLevel = RiskLevel.MEDIUM
        self.risk_score: int = 50
        self.accounts: List[str] = []
        self.loans: List[str] = []
        self.kyc_documents: List[Dict] = []
        self.aml_checks: List[Dict] = []
        self.credit_score: Optional[int] = None
        self.churn_probability: Optional[float] = None
    
    async def onboard_client(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        date_of_birth: str,
        address: Dict
    ):
        """Onboard new client"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'client_id': self.client_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'date_of_birth': date_of_birth,
            'address': address,
            'onboarded_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Write to Kafka FIRST
        await kafka_store.append_event(
            entity='clients',
            event_type='client_onboarded',
            event_data=event_data,
            aggregate_id=self.client_id,
            user_id='onboarding_system'
        )
        
        # Publish to Data Mesh
        await DataMeshPublisher.publish_client_data(
            self.client_id,
            {
                'client_id': self.client_id,
                'name': f"{first_name} {last_name}",
                'email': email,
                'status': ClientStatus.PENDING.value,
                'kyc_status': KYCStatus.NOT_STARTED.value
            }
        )
        
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.status = ClientStatus.PENDING
    
    async def submit_kyc_documents(self, documents: List[Dict]):
        """Submit KYC documents"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'client_id': self.client_id,
            'documents': documents,
            'submitted_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='clients',
            event_type='kyc_documents_submitted',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        self.kyc_documents.extend(documents)
        self.kyc_status = KYCStatus.DOCUMENTS_SUBMITTED
        self.status = ClientStatus.KYC_IN_PROGRESS
    
    async def verify_kyc(self):
        """AI-powered KYC verification"""
        kafka_store = get_production_kafka_store()
        
        # Perform AML checks
        aml_result = await self._perform_aml_check()
        
        # ML risk assessment
        risk_assessment = await self._assess_client_risk()
        
        # Determine verification outcome
        is_approved = (
            not aml_result['is_suspicious'] and
            risk_assessment['risk_level'] != 'VERY_HIGH'
        )
        
        event_data = {
            'client_id': self.client_id,
            'kyc_approved': is_approved,
            'aml_result': aml_result,
            'risk_assessment': risk_assessment,
            'verified_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='clients',
            event_type='kyc_verified',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        # Publish to compliance topic
        await kafka_store.append_event(
            entity='compliance',
            event_type='kyc_verification_completed',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        if is_approved:
            self.kyc_status = KYCStatus.VERIFIED
            self.status = ClientStatus.KYC_APPROVED
        else:
            self.kyc_status = KYCStatus.REJECTED
            self.status = ClientStatus.KYC_REJECTED
        
        self.risk_level = RiskLevel(risk_assessment['risk_level'])
        self.risk_score = risk_assessment['risk_score']
        
        # Update Data Mesh
        await DataMeshPublisher.publish_client_data(
            self.client_id,
            {
                'client_id': self.client_id,
                'kyc_status': self.kyc_status.value,
                'risk_level': self.risk_level.value,
                'risk_score': self.risk_score
            }
        )
    
    async def activate_client(self):
        """Activate client account"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'client_id': self.client_id,
            'activated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='clients',
            event_type='client_activated',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        self.status = ClientStatus.ACTIVE
    
    async def link_account(self, account_id: str):
        """Link account to client"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'client_id': self.client_id,
            'account_id': account_id,
            'linked_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='clients',
            event_type='account_linked',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        self.accounts.append(account_id)
    
    async def link_loan(self, loan_id: str):
        """Link loan to client"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'client_id': self.client_id,
            'loan_id': loan_id,
            'linked_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='clients',
            event_type='loan_linked',
            event_data=event_data,
            aggregate_id=self.client_id
        )
        
        self.loans.append(loan_id)
    
    async def predict_churn(self):
        """ML-powered churn prediction"""
        churn_result = await enhanced_ml.predict_customer_churn({
            'client_id': self.client_id,
            'monthly_transactions': len(self.accounts) * 5,
            'balance': 1000,
            'support_tickets': 0
        })
        
        self.churn_probability = churn_result['churn_probability']
        
        # Publish churn alert if high risk
        if churn_result['churn_probability'] > 0.6:
            kafka_store = get_production_kafka_store()
            await kafka_store.append_event(
                entity='risk',
                event_type='churn_risk_detected',
                event_data={
                    'client_id': self.client_id,
                    'churn_probability': churn_result['churn_probability'],
                    'recommended_actions': churn_result['retention_actions']
                },
                aggregate_id=self.client_id
            )
        
        return churn_result
    
    async def _perform_aml_check(self) -> Dict:
        """Perform AML/CTF check"""
        # Simulate AML screening
        aml_flags = []
        
        # Check against watchlists (simulated)
        if self.first_name and 'test' in self.first_name.lower():
            aml_flags.append('TEST_NAME')
        
        is_suspicious = len(aml_flags) > 0
        
        return {
            'is_suspicious': is_suspicious,
            'aml_flags': aml_flags,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def _assess_client_risk(self) -> Dict:
        """ML-powered risk assessment"""
        # Base risk score
        risk_score = 30
        
        # Adjust based on factors
        if self.kyc_documents and len(self.kyc_documents) < 2:
            risk_score += 20
        
        # Determine risk level
        if risk_score > 70:
            risk_level = 'VERY_HIGH'
        elif risk_score > 50:
            risk_level = 'HIGH'
        elif risk_score > 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level
        }
    
    async def load_from_events(self):
        """Rebuild state from Kafka events"""
        store = get_event_store()
        events = await store.get_events(self.client_id)
        
        for event in events:
            if event.event_type == 'ClientOnboarded' or event.event_type == 'client_onboarded':
                self.first_name = event.event_data.get('first_name')
                self.last_name = event.event_data.get('last_name')
                self.email = event.event_data.get('email')
                self.status = ClientStatus.PENDING
            elif event.event_type == 'kyc_documents_submitted':
                self.kyc_status = KYCStatus.DOCUMENTS_SUBMITTED
                self.status = ClientStatus.KYC_IN_PROGRESS
            elif event.event_type == 'kyc_verified':
                if event.event_data.get('kyc_approved'):
                    self.kyc_status = KYCStatus.VERIFIED
                    self.status = ClientStatus.KYC_APPROVED
                else:
                    self.kyc_status = KYCStatus.REJECTED
                    self.status = ClientStatus.KYC_REJECTED
            elif event.event_type == 'client_activated':
                self.status = ClientStatus.ACTIVE
            elif event.event_type == 'account_linked':
                account_id = event.event_data.get('account_id')
                if account_id and account_id not in self.accounts:
                    self.accounts.append(account_id)
            elif event.event_type == 'loan_linked':
                loan_id = event.event_data.get('loan_id')
                if loan_id and loan_id not in self.loans:
                    self.loans.append(loan_id)

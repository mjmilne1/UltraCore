"""
Risk Domain - Risk Management
"""
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.ml_models.pipeline import ml_pipeline


class RiskLevel(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class RiskType(str, Enum):
    CREDIT_RISK = 'CREDIT_RISK'
    FRAUD_RISK = 'FRAUD_RISK'
    COMPLIANCE_RISK = 'COMPLIANCE_RISK'


class RiskAssessmentRequest(BaseModel):
    entity_id: str
    entity_type: str
    risk_type: RiskType


class RiskAggregate:
    def __init__(self, risk_id: str):
        self.risk_id = risk_id
        self.entity_id: Optional[str] = None
        self.entity_type: Optional[str] = None
        self.risk_type: Optional[RiskType] = None
        self.risk_level: RiskLevel = RiskLevel.LOW
        self.risk_score: float = 0.0
    
    async def assess_risk(
        self,
        entity_id: str,
        entity_type: str,
        risk_type: RiskType,
        data: Dict
    ):
        store = get_event_store()
        
        if risk_type == RiskType.CREDIT_RISK:
            risk_result = await self._assess_credit_risk(data)
        elif risk_type == RiskType.FRAUD_RISK:
            risk_result = await self._assess_fraud_risk(data)
        else:
            risk_result = {
                'risk_score': 30.0,
                'risk_level': RiskLevel.MEDIUM,
                'factors': []
            }
        
        event_data = {
            'risk_id': self.risk_id,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'risk_type': risk_type.value,
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['risk_level'].value,
            'assessed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.risk_id,
            aggregate_type='RiskAssessment',
            event_type='RiskAssessed',
            event_data=event_data,
            user_id='risk_system'
        )
        
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.risk_type = risk_type
        self.risk_score = risk_result['risk_score']
        self.risk_level = risk_result['risk_level']
        
        return risk_result
    
    async def _assess_credit_risk(self, data: Dict) -> Dict:
        loan_amount = Decimal(str(data.get('loan_amount', 50000)))
        
        ml_result = await ml_pipeline.predict_credit_risk(
            client_data=data,
            loan_amount=loan_amount
        )
        
        risk_score = ml_result['risk_score']
        
        if risk_score < 30:
            risk_level = RiskLevel.LOW
        elif risk_score < 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': [f"Default probability: {ml_result['default_probability']:.2%}"]
        }
    
    async def _assess_fraud_risk(self, data: Dict) -> Dict:
        fraud_result = await ml_pipeline.detect_fraud(data)
        
        fraud_score = fraud_result['fraud_score']
        
        if fraud_score < 30:
            risk_level = RiskLevel.LOW
        elif fraud_score < 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return {
            'risk_score': fraud_score,
            'risk_level': risk_level,
            'factors': fraud_result['flags']
        }
    
    async def load_from_events(self):
        store = get_event_store()
        events = await store.get_events(self.risk_id)
        
        for event in events:
            if event.event_type == 'RiskAssessed':
                self.entity_id = event.event_data['entity_id']
                self.entity_type = event.event_data['entity_type']
                self.risk_type = RiskType(event.event_data['risk_type'])
                self.risk_score = event.event_data['risk_score']
                self.risk_level = RiskLevel(event.event_data['risk_level'])

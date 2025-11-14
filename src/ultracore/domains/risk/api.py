"""
Complete Risk API - Portfolio Monitoring
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.risk.complete_aggregate import CompleteRiskAggregate  # TODO: Fix import path

router = APIRouter()


@router.post('/assess-credit/{client_id}')
async def assess_credit_risk(client_id: str, loan_amount: float):
    '''
    ML-powered credit risk assessment
    
    Returns credit score and risk category
    '''
    risk_id = f'RSK-{str(uuid.uuid4())[:8]}'
    
    risk = CompleteRiskAggregate(risk_id)
    result = await risk.assess_credit_risk(client_id, Decimal(str(loan_amount)))
    
    return {
        'risk_id': risk_id,
        'client_id': client_id,
        'credit_score': result['credit_score'],
        'risk_category': result['risk_category'],
        'recommended_action': result['recommended_action']
    }


@router.post('/monitor-default/{loan_id}')
async def monitor_payment_default(loan_id: str, loan_data: dict):
    '''
    Monitor payment default risk
    
    Predicts default probability
    '''
    risk_id = f'RSK-{str(uuid.uuid4())[:8]}'
    
    risk = CompleteRiskAggregate(risk_id)
    result = await risk.monitor_payment_default(loan_id, loan_data)
    
    return {
        'risk_id': risk_id,
        'loan_id': loan_id,
        'default_probability': result['default_probability'],
        'risk_score': result['risk_score'],
        'risk_category': result['risk_category'],
        'recommended_action': result['recommended_action']
    }


@router.get('/{risk_id}/alerts')
async def get_risk_alerts(risk_id: str):
    '''Get all risk alerts'''
    risk = CompleteRiskAggregate(risk_id)
    await risk.load_from_events()
    
    return {
        'risk_id': risk_id,
        'alerts': risk.alerts
    }

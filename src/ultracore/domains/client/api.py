"""
Complete Client API - Full KYC Lifecycle
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uuid

# from ultracore.domains.client.complete_aggregate import (  # TODO: Fix import path
    CompleteClientAggregate,
    ClientStatus,
    KYCStatus
)

router = APIRouter()


class OnboardClientRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    address: Dict


class SubmitKYCDocumentsRequest(BaseModel):
    documents: List[Dict]


@router.post('/onboard')
async def onboard_client(request: OnboardClientRequest):
    '''
    Onboard new client
    
    Start KYC process
    '''
    client_id = f'CLI-{str(uuid.uuid4())[:8]}'
    
    client = CompleteClientAggregate(client_id)
    await client.onboard_client(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        phone=request.phone,
        date_of_birth=request.date_of_birth,
        address=request.address
    )
    
    return {
        'client_id': client_id,
        'status': client.status.value,
        'kyc_status': client.kyc_status.value
    }


@router.post('/{client_id}/kyc/submit')
async def submit_kyc_documents(client_id: str, request: SubmitKYCDocumentsRequest):
    '''Submit KYC documents'''
    client = CompleteClientAggregate(client_id)
    await client.load_from_events()
    
    if not client.first_name:
        raise HTTPException(status_code=404, detail='Client not found')
    
    await client.submit_kyc_documents(request.documents)
    
    return {
        'client_id': client_id,
        'kyc_status': client.kyc_status.value,
        'documents_count': len(client.kyc_documents)
    }


@router.post('/{client_id}/kyc/verify')
async def verify_kyc(client_id: str):
    '''
    AI-powered KYC verification
    
    Runs AML checks and risk assessment
    '''
    client = CompleteClientAggregate(client_id)
    await client.load_from_events()
    
    if not client.first_name:
        raise HTTPException(status_code=404, detail='Client not found')
    
    await client.verify_kyc()
    
    return {
        'client_id': client_id,
        'kyc_status': client.kyc_status.value,
        'status': client.status.value,
        'risk_level': client.risk_level.value,
        'risk_score': client.risk_score
    }


@router.post('/{client_id}/activate')
async def activate_client(client_id: str):
    '''Activate client after KYC approval'''
    client = CompleteClientAggregate(client_id)
    await client.load_from_events()
    
    if not client.first_name:
        raise HTTPException(status_code=404, detail='Client not found')
    
    if client.status != ClientStatus.KYC_APPROVED:
        raise HTTPException(status_code=400, detail='KYC not approved')
    
    await client.activate_client()
    
    return {
        'client_id': client_id,
        'status': client.status.value
    }


@router.get('/{client_id}')
async def get_client(client_id: str):
    '''Get complete client profile'''
    client = CompleteClientAggregate(client_id)
    await client.load_from_events()
    
    if not client.first_name:
        raise HTTPException(status_code=404, detail='Client not found')
    
    return {
        'client_id': client_id,
        'name': f'{client.first_name} {client.last_name}',
        'email': client.email,
        'status': client.status.value,
        'kyc_status': client.kyc_status.value,
        'risk_level': client.risk_level.value,
        'risk_score': client.risk_score,
        'accounts': client.accounts,
        'loans': client.loans
    }


@router.get('/{client_id}/churn-prediction')
async def predict_churn(client_id: str):
    '''
    ML-powered churn prediction
    
    Predicts customer churn risk
    '''
    client = CompleteClientAggregate(client_id)
    await client.load_from_events()
    
    if not client.first_name:
        raise HTTPException(status_code=404, detail='Client not found')
    
    churn_result = await client.predict_churn()
    
    return {
        'client_id': client_id,
        'churn_probability': churn_result['churn_probability'],
        'churn_score': churn_result['churn_score'],
        'risk_level': churn_result['risk_level'],
        'retention_actions': churn_result['retention_actions']
    }

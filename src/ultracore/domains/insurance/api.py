"""
Complete Insurance API - Policy & Claims
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import List
import uuid

# from ultracore.domains.insurance.complete_aggregate import (  # TODO: Fix import path
    CompleteInsuranceAggregate,
    PolicyType,
    PolicyStatus
)

router = APIRouter()


class UnderwritePolicyRequest(BaseModel):
    client_id: str
    policy_type: PolicyType
    coverage_amount: float
    applicant_data: dict


class SubmitClaimRequest(BaseModel):
    claim_amount: float
    incident_date: str
    description: str
    supporting_docs: List[str]


@router.post('/policies')
async def underwrite_policy(request: UnderwritePolicyRequest):
    '''
    AI-powered policy underwriting
    
    Calculates premium based on risk
    '''
    policy_id = f'POL-{str(uuid.uuid4())[:8]}'
    
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.underwrite_policy(
        client_id=request.client_id,
        policy_type=request.policy_type,
        coverage_amount=Decimal(str(request.coverage_amount)),
        applicant_data=request.applicant_data
    )
    
    await policy.activate_policy()
    
    return {
        'policy_id': policy_id,
        'client_id': request.client_id,
        'policy_type': policy.policy_type.value,
        'coverage_amount': str(policy.coverage_amount),
        'premium': str(policy.premium),
        'status': policy.status.value
    }


@router.post('/policies/{policy_id}/claims')
async def submit_claim(policy_id: str, request: SubmitClaimRequest):
    '''
    Submit insurance claim
    
    ML fraud detection included
    '''
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    claim_id = await policy.submit_claim(
        claim_amount=Decimal(str(request.claim_amount)),
        incident_date=request.incident_date,
        description=request.description,
        supporting_docs=request.supporting_docs
    )
    
    return {
        'policy_id': policy_id,
        'claim_id': claim_id,
        'claim_amount': str(request.claim_amount)
    }


@router.post('/policies/{policy_id}/claims/{claim_id}/approve')
async def approve_claim(policy_id: str, claim_id: str, approved_amount: float):
    '''Approve insurance claim'''
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    await policy.approve_claim(claim_id, Decimal(str(approved_amount)))
    
    return {
        'policy_id': policy_id,
        'claim_id': claim_id,
        'approved_amount': str(approved_amount)
    }


@router.post('/policies/{policy_id}/claims/{claim_id}/pay')
async def pay_claim(policy_id: str, claim_id: str):
    '''Pay approved claim'''
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    try:
        await policy.pay_claim(claim_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'policy_id': policy_id,
        'claim_id': claim_id,
        'paid': True
    }


@router.get('/policies/{policy_id}')
async def get_policy(policy_id: str):
    '''Get policy details'''
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    return {
        'policy_id': policy_id,
        'client_id': policy.client_id,
        'policy_type': policy.policy_type.value if policy.policy_type else None,
        'status': policy.status.value,
        'coverage_amount': str(policy.coverage_amount),
        'premium': str(policy.premium),
        'total_claims_paid': str(policy.total_claims_paid),
        'claims_count': len(policy.claims)
    }

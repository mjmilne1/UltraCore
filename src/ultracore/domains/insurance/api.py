"""
Insurance Domain API
"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal
import uuid

from ultracore.domains.insurance.aggregate import (
    PolicyAggregate, QuoteRequest, FileClaimRequest, InsuranceType
)

router = APIRouter()


@router.post('/quote')
async def get_quote(request: QuoteRequest):
    '''Get insurance quote'''
    policy_id = f'POL-{str(uuid.uuid4())[:8]}'
    
    policy = PolicyAggregate(policy_id)
    await policy.generate_quote(
        client_id=request.client_id,
        insurance_type=request.insurance_type,
        coverage_amount=Decimal(str(request.coverage_amount)),
        term_years=request.term_years
    )
    
    return {
        'policy_id': policy_id,
        'insurance_type': request.insurance_type.value,
        'coverage_amount': str(policy.coverage_amount),
        'monthly_premium': str(policy.premium),
        'annual_premium': str(policy.premium * 12),
        'status': 'QUOTE'
    }


@router.post('/{policy_id}/activate')
async def activate_policy(policy_id: str):
    '''Activate insurance policy'''
    policy = PolicyAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    await policy.activate_policy()
    
    return {
        'policy_id': policy_id,
        'status': 'ACTIVE',
        'coverage_amount': str(policy.coverage_amount),
        'monthly_premium': str(policy.premium)
    }


@router.get('/{policy_id}')
async def get_policy(policy_id: str):
    '''Get policy details'''
    policy = PolicyAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    return {
        'policy_id': policy.policy_id,
        'client_id': policy.client_id,
        'insurance_type': policy.insurance_type.value if policy.insurance_type else None,
        'coverage_amount': str(policy.coverage_amount),
        'monthly_premium': str(policy.premium),
        'status': policy.status.value,
        'claims_count': len(policy.claims)
    }


@router.post('/{policy_id}/claims')
async def file_claim(policy_id: str, request: FileClaimRequest):
    '''File insurance claim'''
    policy = PolicyAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    try:
        claim_id = await policy.file_claim(
            incident_date=request.incident_date,
            incident_description=request.incident_description,
            claim_amount=Decimal(str(request.claim_amount))
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'claim_id': claim_id,
        'policy_id': policy_id,
        'claim_amount': str(request.claim_amount),
        'status': 'SUBMITTED'
    }


@router.get('/{policy_id}/claims')
async def get_claims(policy_id: str):
    '''Get all claims for policy'''
    policy = PolicyAggregate(policy_id)
    await policy.load_from_events()
    
    if not policy.client_id:
        raise HTTPException(status_code=404, detail='Policy not found')
    
    return {
        'policy_id': policy_id,
        'claims': policy.claims,
        'total_claims': len(policy.claims)
    }

"""
Australian Compliance API Endpoints
"""
from fastapi import APIRouter
# from ultracore.domains.client.compliance import (  # TODO: Fix import path
    ComplianceService, AustralianKYCRequirements
)

router = APIRouter()


@router.get('/compliance/checklist')
async def get_compliance_checklist():
    '''
    Get Australian banking compliance checklist
    
    Returns complete requirements for:
    - AML/CTF Act 2006
    - AUSTRAC obligations
    - ASIC requirements
    '''
    return AustralianKYCRequirements.get_compliance_checklist()


@router.post('/compliance/validate-tfn')
async def validate_tfn(tfn: str):
    '''Validate Australian Tax File Number'''
    is_valid = ComplianceService.validate_tfn(tfn)
    return {
        'tfn': tfn,
        'valid': is_valid,
        'format': 'XXX XXX XXX (9 digits)'
    }


@router.post('/compliance/validate-abn')
async def validate_abn(abn: str):
    '''Validate Australian Business Number'''
    is_valid = ComplianceService.validate_abn(abn)
    return {
        'abn': abn,
        'valid': is_valid,
        'format': 'XX XXX XXX XXX (11 digits)'
    }


@router.post('/compliance/austrac-threshold-check')
async def austrac_threshold_check(amount: float):
    '''
    Check AUSTRAC reporting thresholds
    
    Threshold Transaction Report (TTR) required for AUD ,000+
    '''
    return ComplianceService.austrac_reporting_threshold_check(amount)

"""
AI-Powered KYC Verification Service with Australian Compliance
"""
from typing import Dict, List
from openai import OpenAI
import os
import datetime

from ultracore.domains.client.compliance import (
    ComplianceService, AustralianKYCRequirements
)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-dummy')) if os.getenv('OPENAI_API_KEY') else None


class KYCVerificationService:
    def __init__(self):
        self.model = 'gpt-4-turbo-preview'
        self.compliance = ComplianceService()
    
    async def verify_identity(self, client_data: Dict, documents: List[Dict]) -> Dict:
        '''
        AI-powered identity verification with Australian compliance
        '''
        
        # Calculate 100 point check
        id_points = self.compliance.calculate_id_points(documents)
        
        # Age verification
        age_check = self.compliance.check_age_restriction(
            client_data.get('date_of_birth', '')
        )
        
        # AML risk assessment
        aml_assessment = self.compliance.assess_aml_risk(client_data)
        
        # TFN validation if provided
        tfn_valid = self.compliance.validate_tfn(
            client_data.get('tax_file_number')
        )
        
        prompt = f'''You are an AI KYC compliance officer for TuringDynamics Bank.

CUSTOMER DATA:
- Name: {client_data.get("first_name")} {client_data.get("last_name")}
- Email: {client_data.get("email")}  
- Date of Birth: {client_data.get("date_of_birth")}
- Age: {age_check.get("age")} years

IDENTITY DOCUMENTS:
{self._format_documents(documents)}

100 POINT CHECK: {id_points} points (minimum 100 required)

AUSTRALIAN COMPLIANCE:
- AML/CTF Act 2006
- AUSTRAC reporting
- Age 18+ required
- PEP and sanctions screening

Provide JSON analysis (respond ONLY with valid JSON):
{{
    "status": "APPROVED or REJECTED",
    "risk_score": 25,
    "risk_level": "LOW",
    "verification_confidence": 0.95,
    "compliance_checks": {{
        "age_verified": true,
        "identity_verified": true,
        "100_point_check_passed": true,
        "pep_screening_clear": true,
        "sanctions_screening_clear": true
    }},
    "checks_passed": ["age_18+", "100_point_id"],
    "checks_failed": [],
    "aml_flags": [],
    "recommendation": "Approve for account opening"
}}'''

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Australian banking compliance AI. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            import json
            result_text = response.choices[0].message.content
            result_text = result_text.replace('`json', '').replace('`', '').strip()
            result = json.loads(result_text)
            
            # Add compliance metadata
            result['verified_by'] = 'ai_kyc_system_austrac_compliant'
            result['id_points_achieved'] = id_points
            result['age_verification'] = age_check
            result['aml_assessment'] = aml_assessment
            result['tfn_valid'] = tfn_valid
            result['compliance_framework'] = 'AML/CTF Act 2006, AUSTRAC, ASIC'
            result['verification_timestamp'] = datetime.datetime.utcnow().isoformat()
            
            # Enforce 100 point check
            if id_points < 100:
                result['status'] = 'REJECTED'
                if 'checks_failed' not in result:
                    result['checks_failed'] = []
                result['checks_failed'].append('100_POINT_CHECK_FAILED')
                result['recommendation'] = f'Additional identification required. Current points: {id_points}/100'
            
            # Enforce age restriction
            if not age_check['meets_requirement']:
                result['status'] = 'REJECTED'
                if 'checks_failed' not in result:
                    result['checks_failed'] = []
                result['checks_failed'].append('AGE_REQUIREMENT_NOT_MET')
                result['recommendation'] = age_check['reason']
            
            return result
            
        except Exception as e:
            return {
                'status': 'REJECTED',
                'risk_score': 100,
                'risk_level': 'HIGH',
                'verification_confidence': 0.0,
                'compliance_checks': {
                    'age_verified': False,
                    'identity_verified': False,
                    '100_point_check_passed': False
                },
                'checks_passed': [],
                'checks_failed': ['AI_VERIFICATION_ERROR'],
                'aml_flags': ['SYSTEM_ERROR'],
                'recommendation': 'System error - manual review required',
                'error': str(e),
                'verified_by': 'ai_kyc_system_error'
            }
    
    def _format_documents(self, documents: List[Dict]) -> str:
        '''Format documents for AI analysis'''
        if not documents:
            return "- No documents submitted"
        
        formatted = []
        for i, doc in enumerate(documents, 1):
            formatted.append(
                f"{i}. {doc.get('document_type')}: {doc.get('document_number')} "
                f"(Expires: {doc.get('document_expiry')})"
            )
        
        return '\n'.join(formatted)


kyc_service = KYCVerificationService()


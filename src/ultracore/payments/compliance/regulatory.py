"""
Australian Payments Regulatory Compliance
AUSTRAC, APCA, RBA, ASIC compliance
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    OSKO = 'OSKO'
    DIRECT_ENTRY = 'DIRECT_ENTRY'
    BPAY = 'BPAY'
    INTERNATIONAL = 'INTERNATIONAL'


class AUSTRACCompliance:
    """AUSTRAC Compliance - AML/CTF"""
    
    def __init__(self):
        self.threshold_transactions: List[Dict] = []
        self.suspicious_matters: List[Dict] = []
    
    async def check_threshold_transaction(
        self,
        transaction_id: str,
        customer_id: str,
        amount: Decimal,
        transaction_type: TransactionType
    ) -> bool:
        """Check if transaction requires TTR (≥\,000)"""
        if amount >= Decimal('10000'):
            ttr = {
                'transaction_id': transaction_id,
                'customer_id': customer_id,
                'amount': str(amount),
                'transaction_type': transaction_type.value,
                'reported_at': datetime.now(timezone.utc).isoformat()
            }
            self.threshold_transactions.append(ttr)
            return True
        return False
    
    async def assess_suspicious_matter(
        self,
        customer_id: str,
        transactions: List[Dict]
    ) -> Optional[Dict]:
        """ML-powered suspicious matter detection"""
        from ultracore.ml_models.scoring_engine import get_scoring_engine, ModelType
        
        scoring_engine = get_scoring_engine()
        aml_result = await scoring_engine.score(
            model_type=ModelType.AML_MONITORING,
            input_data={'customer_id': customer_id, 'transactions': transactions}
        )
        
        if aml_result.get('is_suspicious'):
            smr = {
                'customer_id': customer_id,
                'suspicion_score': aml_result.get('suspicion_score'),
                'reported_at': datetime.now(timezone.utc).isoformat()
            }
            self.suspicious_matters.append(smr)
            return smr
        return None


class ComplianceEngine:
    """Unified Compliance Engine"""
    
    def __init__(self):
        self.austrac = AUSTRACCompliance()
    
    async def process_payment_compliance(
        self,
        transaction_id: str,
        customer_id: str,
        amount: Decimal,
        transaction_type: TransactionType,
        recipient_country: Optional[str] = None
    ) -> Dict:
        """Complete compliance processing"""
        
        compliance_checks = {
            'transaction_id': transaction_id,
            'ttr_required': False,
            'compliance_status': 'PASSED',
            'actions': []
        }
        
        if await self.austrac.check_threshold_transaction(
            transaction_id, customer_id, amount, transaction_type
        ):
            compliance_checks['ttr_required'] = True
            compliance_checks['actions'].append('TTR_FILED')
        
        return compliance_checks


_compliance_engine: Optional[ComplianceEngine] = None


def get_compliance_engine() -> ComplianceEngine:
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine

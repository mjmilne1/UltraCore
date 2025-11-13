"""
NPP (New Payments Platform) Integration
Real-time payments infrastructure for Australia

Includes:
- Osko instant payments (sub-minute settlement)
- PayID (phone/email → account mapping)
- PayTo (real-time mandates)
- ISO 20022 messaging standard
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import uuid

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.scoring_engine import get_scoring_engine, ModelType


class PayIDType(str, Enum):
    PHONE = 'PHONE'
    EMAIL = 'EMAIL'
    ABN = 'ABN'
    ORG_ID = 'ORG_ID'


class PaymentPurpose(str, Enum):
    PERSONAL = 'PERSONAL'
    BILL_PAYMENT = 'BILL_PAYMENT'
    SALARY = 'SALARY'
    BUSINESS = 'BUSINESS'
    GOVERNMENT = 'GOVERNMENT'


class NPPPaymentStatus(str, Enum):
    INITIATED = 'INITIATED'
    VALIDATED = 'VALIDATED'
    SUBMITTED = 'SUBMITTED'
    CLEARING = 'CLEARING'
    SETTLED = 'SETTLED'
    REJECTED = 'REJECTED'
    RETURNED = 'RETURNED'


class PayIDRegistry:
    """PayID Registry - Maps PayIDs to BSB+Account"""
    
    def __init__(self):
        self.registry: Dict[str, Dict] = {}
    
    async def register_payid(
        self,
        payid: str,
        payid_type: PayIDType,
        bsb: str,
        account_number: str,
        account_name: str
    ):
        """Register PayID"""
        kafka_store = get_production_kafka_store()
        
        if payid_type == PayIDType.PHONE:
            if not payid.startswith('04'):
                raise ValueError('Invalid Australian mobile number')
        elif payid_type == PayIDType.EMAIL:
            if '@' not in payid:
                raise ValueError('Invalid email address')
        
        if payid in self.registry:
            raise ValueError(f'PayID {payid} already registered')
        
        self.registry[payid] = {
            'payid': payid,
            'payid_type': payid_type.value,
            'bsb': bsb,
            'account_number': account_number,
            'account_name': account_name,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='npp',
            event_type='payid_registered',
            event_data=self.registry[payid],
            aggregate_id=payid
        )
        
        return self.registry[payid]
    
    async def resolve_payid(self, payid: str) -> Optional[Dict]:
        """Resolve PayID to BSB+Account"""
        return self.registry.get(payid)


class OskoPayment:
    """Osko Instant Payment - Real-time via NPP"""
    
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        self.status: NPPPaymentStatus = NPPPaymentStatus.INITIATED
        self.amount: Optional[Decimal] = None
        self.from_bsb: Optional[str] = None
        self.from_account: Optional[str] = None
        self.to_bsb: Optional[str] = None
        self.to_account: Optional[str] = None
        self.end_to_end_id: Optional[str] = None
    
    async def initiate(
        self,
        from_bsb: str,
        from_account: str,
        to_identifier: str,
        amount: Decimal,
        remittance_info: str,
        purpose: PaymentPurpose = PaymentPurpose.PERSONAL
    ):
        """Initiate Osko payment"""
        
        scoring_engine = get_scoring_engine()
        fraud_check = await scoring_engine.score(
            model_type=ModelType.FRAUD_DETECTION,
            input_data={'amount': float(amount), 'payment_type': 'OSKO'}
        )
        
        if fraud_check.get('is_fraudulent'):
            raise ValueError('Payment blocked: Fraud detected')
        
        if '@' in to_identifier or to_identifier.startswith('04'):
            payid_registry = PayIDRegistry()
            resolved = await payid_registry.resolve_payid(to_identifier)
            if not resolved:
                raise ValueError(f'PayID {to_identifier} not found')
            self.to_bsb = resolved['bsb']
            self.to_account = resolved['account_number']
        else:
            parts = to_identifier.split('-')
            self.to_bsb = parts[0]
            self.to_account = parts[1]
        
        if amount > Decimal('10000') and purpose == PaymentPurpose.PERSONAL:
            raise ValueError('Osko limit: \,000 per transaction')
        
        self.from_bsb = from_bsb
        self.from_account = from_account
        self.amount = amount
        self.end_to_end_id = f'E2E{uuid.uuid4().hex[:20].upper()}'
        self.status = NPPPaymentStatus.VALIDATED
        
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='npp',
            event_type='osko_payment_initiated',
            event_data={
                'payment_id': self.payment_id,
                'amount': str(amount),
                'end_to_end_id': self.end_to_end_id
            },
            aggregate_id=self.payment_id,
            exactly_once=True
        )
    
    async def submit_to_npp(self):
        """Submit to NPP for clearing"""
        self.status = NPPPaymentStatus.SUBMITTED
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='npp',
            event_type='osko_payment_submitted',
            event_data={'payment_id': self.payment_id},
            aggregate_id=self.payment_id
        )
    
    async def settle(self):
        """Settlement via RBA RITS"""
        self.status = NPPPaymentStatus.SETTLED
        
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        
        from_account = CompleteAccountAggregate(f'{self.from_bsb}-{self.from_account}')
        await from_account.load_from_events()
        await from_account.withdraw(self.amount, 'Osko payment', self.payment_id)
        
        to_account = CompleteAccountAggregate(f'{self.to_bsb}-{self.to_account}')
        await to_account.load_from_events()
        await to_account.deposit(self.amount, 'Osko payment', self.payment_id)
        
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='npp',
            event_type='osko_payment_settled',
            event_data={'payment_id': self.payment_id},
            aggregate_id=self.payment_id,
            exactly_once=True
        )


class PayToMandate:
    """PayTo - NPP Mandated Payments"""
    
    def __init__(self, mandate_id: str):
        self.mandate_id = mandate_id
        self.status: str = 'PENDING'
    
    async def create_mandate(
        self,
        payer_bsb: str,
        payer_account: str,
        payee_bsb: str,
        payee_account: str,
        max_amount: Decimal,
        frequency: str,
        purpose: str
    ):
        """Create PayTo mandate"""
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='npp',
            event_type='payto_mandate_created',
            event_data={
                'mandate_id': self.mandate_id,
                'max_amount': str(max_amount),
                'frequency': frequency
            },
            aggregate_id=self.mandate_id
        )

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from ultracore.infrastructure.event_store.store import get_event_store


class LoanApplicationRequest(BaseModel):
    customer_id: str
    amount: float
    term_months: int
    purpose: str


class LoanAggregate:
    def __init__(self, loan_id: str):
        self.loan_id = loan_id
        self.customer_id: Optional[str] = None
        self.amount: Optional[Decimal] = None
        self.term_months: Optional[int] = None
        self.status: str = 'NEW'
    
    async def apply_for_loan(
        self,
        customer_id: str,
        amount: Decimal,
        term_months: int,
        purpose: str,
        user_id: str = 'system'
    ):
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'customer_id': customer_id,
            'amount': str(amount),
            'term_months': term_months,
            'purpose': purpose,
            'applied_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='Loan',
            event_type='LoanApplied',
            event_data=event_data,
            user_id=user_id
        )
        
        self.customer_id = customer_id
        self.amount = amount
        self.term_months = term_months
        self.status = 'PENDING'
    
    async def approve(self, approved_by: str, ml_score: float):
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'approved_by': approved_by,
            'ml_score': ml_score,
            'approved_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='Loan',
            event_type='LoanApproved',
            event_data=event_data,
            user_id=approved_by
        )
        
        self.status = 'APPROVED'
    
    async def load_from_events(self):
        store = get_event_store()
        events = await store.get_events(self.loan_id)
        
        for event in events:
            if event.event_type == 'LoanApplied':
                self.customer_id = event.event_data['customer_id']
                self.amount = Decimal(event.event_data['amount'])
                self.term_months = event.event_data['term_months']
                self.status = 'PENDING'
            elif event.event_type == 'LoanApproved':
                self.status = 'APPROVED'

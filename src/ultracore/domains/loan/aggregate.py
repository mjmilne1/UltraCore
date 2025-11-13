"""
Loan Domain with AI-Powered Decision Making
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.agentic_ai.agents.anya import anya
from ultracore.ml_models.credit_scoring import credit_model


class LoanApplicationRequest(BaseModel):
    customer_id: str
    amount: float
    term_months: int
    purpose: str
    annual_income: float = 80000.0
    existing_debt: float = 10000.0
    employment_months: int = 24
    credit_history_score: int = 700


class LoanAggregate:
    def __init__(self, loan_id: str):
        self.loan_id = loan_id
        self.customer_id: Optional[str] = None
        self.amount: Optional[Decimal] = None
        self.term_months: Optional[int] = None
        self.status: str = 'NEW'
        self.ai_analysis: Optional[dict] = None
        self.credit_score: Optional[int] = None
    
    async def apply_for_loan(
        self,
        customer_id: str,
        amount: Decimal,
        term_months: int,
        purpose: str,
        user_id: str = 'system',
        customer_data: Optional[dict] = None
    ):
        """Apply for loan - creates LoanApplied event"""
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'customer_id': customer_id,
            'amount': str(amount),
            'term_months': term_months,
            'purpose': purpose,
            'applied_at': datetime.now(timezone.utc).isoformat()
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
    
    async def ai_review(self, customer_data: dict):
        """AI-powered loan review by Anya"""
        store = get_event_store()
        
        # Get AI analysis from Anya
        ai_result = await anya.analyze_loan_application(
            customer_id=self.customer_id,
            amount=self.amount,
            term_months=self.term_months,
            purpose='loan_application',
            customer_data=customer_data
        )
        
        # Get ML credit score
        ml_score = credit_model.calculate_score(
            annual_income=Decimal(str(customer_data.get('annual_income', 80000))),
            existing_debt=Decimal(str(customer_data.get('existing_debt', 10000))),
            employment_months=customer_data.get('employment_months', 24),
            loan_amount=self.amount,
            loan_term=self.term_months,
            payment_history_score=customer_data.get('credit_history_score', 700)
        )
        
        event_data = {
            'loan_id': self.loan_id,
            'ai_agent': 'Anya',
            'ai_recommendation': ai_result['analysis']['recommendation'],
            'ai_confidence': ai_result['analysis']['confidence'],
            'ai_reasoning': ai_result['analysis']['reasoning'],
            'credit_score': ml_score['credit_score'],
            'risk_category': ml_score['risk_category'],
            'approval_probability': ml_score['approval_probability'],
            'reviewed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='Loan',
            event_type='LoanReviewedByAI',
            event_data=event_data,
            user_id='anya_ai'
        )
        
        self.ai_analysis = ai_result
        self.credit_score = ml_score['credit_score']
        self.status = 'AI_REVIEWED'
        
        return {
            'ai_analysis': ai_result,
            'credit_score': ml_score
        }
    
    async def auto_decide(self):
        """Automatic decision based on AI analysis"""
        store = get_event_store()
        
        if not self.ai_analysis:
            raise ValueError('Loan must be AI reviewed before auto-decision')
        
        recommendation = self.ai_analysis['analysis']['recommendation']
        confidence = self.ai_analysis['analysis']['confidence']
        
        # Auto-approve if AI highly confident and score is good
        if recommendation == 'APPROVE' and confidence >= 0.80 and self.credit_score >= 700:
            await self.approve('anya_ai_auto', self.credit_score)
            return {'decision': 'APPROVED', 'method': 'AUTOMATIC'}
        
        # Auto-reject if AI confident and score is poor
        elif recommendation == 'REJECT' and confidence >= 0.80 and self.credit_score < 600:
            await self.reject('anya_ai_auto', self.ai_analysis['analysis']['reasoning'])
            return {'decision': 'REJECTED', 'method': 'AUTOMATIC'}
        
        # Otherwise, send to manual review
        else:
            event_data = {
                'loan_id': self.loan_id,
                'reason': 'Low AI confidence or borderline score',
                'routed_at': datetime.now(timezone.utc).isoformat()
            }
            
            await store.append(
                aggregate_id=self.loan_id,
                aggregate_type='Loan',
                event_type='LoanRoutedToManualReview',
                event_data=event_data,
                user_id='system'
            )
            
            self.status = 'MANUAL_REVIEW'
            return {'decision': 'MANUAL_REVIEW_REQUIRED', 'method': 'ESCALATED'}
    
    async def approve(self, approved_by: str, ml_score: float):
        """Approve loan"""
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'approved_by': approved_by,
            'credit_score': ml_score,
            'approved_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='Loan',
            event_type='LoanApproved',
            event_data=event_data,
            user_id=approved_by
        )
        
        self.status = 'APPROVED'
    
    async def reject(self, rejected_by: str, reason: str):
        """Reject loan"""
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'rejected_by': rejected_by,
            'reason': reason,
            'rejected_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='Loan',
            event_type='LoanRejected',
            event_data=event_data,
            user_id=rejected_by
        )
        
        self.status = 'REJECTED'
    
    async def load_from_events(self):
        """Rebuild state from events"""
        store = get_event_store()
        events = await store.get_events(self.loan_id)
        
        for event in events:
            if event.event_type == 'LoanApplied':
                self.customer_id = event.event_data['customer_id']
                self.amount = Decimal(event.event_data['amount'])
                self.term_months = event.event_data['term_months']
                self.status = 'PENDING'
            elif event.event_type == 'LoanReviewedByAI':
                self.credit_score = event.event_data['credit_score']
                self.status = 'AI_REVIEWED'
            elif event.event_type == 'LoanApproved':
                self.status = 'APPROVED'
            elif event.event_type == 'LoanRejected':
                self.status = 'REJECTED'

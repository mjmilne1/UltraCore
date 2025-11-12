from typing import Dict
from decimal import Decimal
from datetime import datetime, timedelta

class CreditLineManager:
    def __init__(self):
        self.credit_lines = {}
        
    async def establish_credit_line(self, customer_id: str, assessment: Dict) -> Dict:
        credit_limit = await self.calculate_credit_limit(assessment)
        
        facility_id = f'CREDIT_{customer_id}_{datetime.now().timestamp():.0f}'
        
        self.credit_lines[facility_id] = {
            'facility_id': facility_id,
            'customer_id': customer_id,
            'credit_limit': credit_limit,
            'available_balance': credit_limit,
            'utilized_amount': Decimal('0'),
            'interest_rate': assessment.get('interest_rate', 0.129),
            'minimum_payment_percent': 0.02,
            'status': 'ACTIVE',
            'established_date': datetime.now().isoformat()
        }
        
        return self.credit_lines[facility_id]
    
    async def calculate_credit_limit(self, assessment: Dict) -> Decimal:
        annual_income = Decimal(str(assessment.get('annual_income', 0)))
        risk_score = assessment.get('risk_score', 0.5)
        
        base_limit = annual_income * Decimal('0.3')
        risk_multiplier = Decimal(str(risk_score))
        credit_limit = base_limit * risk_multiplier
        
        credit_limit = min(credit_limit, Decimal('100000'))
        credit_limit = max(credit_limit, Decimal('1000'))
        
        return credit_limit.quantize(Decimal('100'))
    
    async def drawdown(self, facility_id: str, amount: Decimal) -> Dict:
        facility = self.credit_lines.get(facility_id)
        if not facility:
            return {'success': False, 'error': 'Invalid facility'}
        
        if amount > facility['available_balance']:
            return {'success': False, 'error': 'Insufficient credit'}
        
        facility['utilized_amount'] += amount
        facility['available_balance'] -= amount
        
        transaction_id = f'DRAW_{datetime.now().timestamp():.0f}'
        
        await self.calculate_interest(facility_id)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'amount_drawn': float(amount),
            'new_balance': float(facility['utilized_amount']),
            'available_credit': float(facility['available_balance'])
        }
    
    async def calculate_interest(self, facility_id: str):
        facility = self.credit_lines.get(facility_id)
        if not facility:
            return
        
        daily_rate = facility['interest_rate'] / 365
        daily_interest = facility['utilized_amount'] * Decimal(str(daily_rate))
        
        facility['utilized_amount'] += daily_interest
        
        return daily_interest

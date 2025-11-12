from typing import Dict, List
from decimal import Decimal
from datetime import datetime, timedelta

class BNPLProvider:
    def __init__(self):
        self.merchant_partners = {}
        self.active_plans = {}
        self.installment_options = [
            {'installments': 4, 'frequency': 'fortnightly', 'interest': 0},
            {'installments': 3, 'frequency': 'monthly', 'interest': 0},
            {'installments': 6, 'frequency': 'monthly', 'interest': 0.05}
        ]
    
    async def instant_approval(self, customer_id: str, purchase: Dict) -> Dict:
        risk_check = await self.quick_risk_assessment(customer_id, purchase)
        
        if risk_check['approved']:
            plan = await self.create_payment_plan(
                customer_id,
                purchase,
                risk_check['recommended_plan']
            )
            
            await self.settle_merchant(purchase['merchant_id'], purchase['amount'])
            
            return {
                'approved': True,
                'plan_id': plan['plan_id'],
                'payment_schedule': plan['schedule'],
                'first_payment': plan['first_payment_date']
            }
        else:
            return {
                'approved': False,
                'reason': risk_check.get('reason', 'Risk threshold exceeded')
            }
    
    async def quick_risk_assessment(self, customer_id: str, purchase: Dict) -> Dict:
        amount = Decimal(str(purchase['amount']))
        
        if amount > 5000:
            return {'approved': False, 'reason': 'Amount exceeds limit'}
        
        if amount < 500:
            recommended_plan = self.installment_options[0]
        elif amount < 2000:
            recommended_plan = self.installment_options[1]
        else:
            recommended_plan = self.installment_options[2]
        
        return {
            'approved': True,
            'recommended_plan': recommended_plan
        }
    
    async def create_payment_plan(self, customer_id: str,
                                 purchase: Dict,
                                 plan_option: Dict) -> Dict:
        plan_id = f'BNPL_{datetime.now().timestamp():.0f}'
        amount = Decimal(str(purchase['amount']))
        installment_amount = amount / plan_option['installments']
        
        schedule = []
        current_date = datetime.now()
        
        for i in range(plan_option['installments']):
            if plan_option['frequency'] == 'fortnightly':
                payment_date = current_date + timedelta(weeks=2*(i+1))
            else:
                payment_date = current_date + timedelta(days=30*(i+1))
            
            schedule.append({
                'installment_number': i + 1,
                'due_date': payment_date.isoformat(),
                'amount': float(installment_amount),
                'status': 'PENDING'
            })
        
        self.active_plans[plan_id] = {
            'customer_id': customer_id,
            'merchant_id': purchase['merchant_id'],
            'total_amount': float(amount),
            'schedule': schedule,
            'status': 'ACTIVE'
        }
        
        return {
            'plan_id': plan_id,
            'schedule': schedule,
            'first_payment_date': schedule[0]['due_date']
        }
    
    async def settle_merchant(self, merchant_id: str, amount: Decimal):
        merchant_fee = amount * Decimal('0.04')
        settlement_amount = amount - merchant_fee
        
        return {
            'merchant_id': merchant_id,
            'gross_amount': float(amount),
            'fee': float(merchant_fee),
            'net_amount': float(settlement_amount),
            'settlement_date': datetime.now().isoformat()
        }
    
    async def get_customer_bnpl_history(self, customer_id: str) -> Dict:
        return {
            'outstanding_balance': 0,
            'missed_payments': 0,
            'completed_plans': 0
        }

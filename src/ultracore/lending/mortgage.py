from typing import Dict, List
from decimal import Decimal
from datetime import datetime, timedelta
import random

class MortgageEngine:
    def __init__(self):
        self.applications = {}
        self.property_valuations = {}
        
    async def process_mortgage_application(self, application: Dict) -> Dict:
        stages = {}
        
        pre_approval = await self.pre_approve(application)
        stages['pre_approval'] = pre_approval
        
        if not pre_approval['approved']:
            return {
                'status': 'DECLINED',
                'stage': 'pre_approval',
                'reason': pre_approval['reason']
            }
        
        valuation = await self.value_property(application['property'])
        stages['property_valuation'] = valuation
        
        conditional = await self.conditional_approval(application, valuation)
        stages['conditional_approval'] = conditional
        
        if not conditional['approved']:
            return {
                'status': 'DECLINED',
                'stage': 'conditional_approval',
                'reason': conditional['reason']
            }
        
        docs_complete = await self.verify_documentation(application)
        
        if docs_complete:
            final_approval = await self.final_approval(application, stages)
            
            if final_approval['approved']:
                settlement = await self.prepare_settlement(application, final_approval)
                
                return {
                    'status': 'APPROVED',
                    'mortgage_id': settlement['mortgage_id'],
                    'loan_amount': application['loan_amount'],
                    'interest_rate': final_approval['interest_rate'],
                    'term_years': application['term_years'],
                    'monthly_payment': final_approval['monthly_payment'],
                    'settlement_date': settlement['settlement_date']
                }
        
        return {'status': 'PENDING_DOCUMENTATION'}
    
    async def pre_approve(self, application: Dict) -> Dict:
        income = Decimal(str(application.get('annual_income', 0)))
        expenses = Decimal(str(application.get('annual_expenses', 0)))
        
        net_income = income - expenses
        loan_amount = Decimal(str(application['loan_amount']))
        
        annual_payment = loan_amount * Decimal('0.07')
        
        if annual_payment > net_income * Decimal('0.3'):
            return {'approved': False, 'reason': 'Insufficient income'}
        
        if application.get('credit_score', 0) < 650:
            return {'approved': False, 'reason': 'Credit score too low'}
        
        return {
            'approved': True,
            'pre_approved_amount': float(loan_amount),
            'expires': (datetime.now() + timedelta(days=90)).isoformat()
        }
    
    async def value_property(self, property_details: Dict) -> Dict:
        estimated_value = Decimal(str(property_details.get('purchase_price', 0)))
        variance = Decimal(str(random.uniform(0.95, 1.05)))
        valued_amount = estimated_value * variance
        
        return {
            'property_id': property_details.get('property_id'),
            'valued_amount': float(valued_amount),
            'valuation_date': datetime.now().isoformat()
        }
    
    async def conditional_approval(self, application: Dict, valuation: Dict) -> Dict:
        loan_amount = Decimal(str(application['loan_amount']))
        property_value = Decimal(str(valuation['valued_amount']))
        
        lvr = loan_amount / property_value
        
        if lvr > Decimal('0.95'):
            return {'approved': False, 'reason': 'LVR too high'}
        
        base_rate = 0.059
        if lvr > Decimal('0.80'):
            base_rate += 0.005
        
        return {
            'approved': True,
            'lvr': float(lvr),
            'interest_rate': base_rate
        }
    
    async def verify_documentation(self, application: Dict) -> bool:
        required_docs = [
            'proof_of_income',
            'bank_statements',
            'identification',
            'employment_letter',
            'property_contract'
        ]
        
        for doc in required_docs:
            if doc not in application.get('documents', {}):
                return False
        
        return True
    
    async def final_approval(self, application: Dict, stages: Dict) -> Dict:
        loan_amount = Decimal(str(application['loan_amount']))
        interest_rate = stages['conditional_approval']['interest_rate']
        term_years = application['term_years']
        
        monthly_rate = interest_rate / 12
        term_months = term_years * 12
        
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
        
        return {
            'approved': True,
            'loan_amount': float(loan_amount),
            'interest_rate': interest_rate,
            'term_years': term_years,
            'monthly_payment': float(monthly_payment)
        }
    
    async def prepare_settlement(self, application: Dict, approval: Dict) -> Dict:
        mortgage_id = f'MORT_{datetime.now().timestamp():.0f}'
        
        return {
            'mortgage_id': mortgage_id,
            'settlement_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'settlement_agent': 'UltraCore Settlement',
            'documents_prepared': True
        }

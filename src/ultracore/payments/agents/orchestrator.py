"""
AI Payment Agents - MCP (Model Context Protocol) Based
Agentic AI for intelligent payment processing

Agents:
1. Payment Router Agent - Selects optimal payment rail
2. Fraud Prevention Agent - Real-time fraud detection
3. Compliance Agent - Ensures regulatory compliance
4. Settlement Agent - Manages settlement and reconciliation
5. Customer Support Agent - Handles payment queries via Anya
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from ultracore.ml_models.scoring_engine import get_scoring_engine, ModelType
# from ultracore.payments.compliance.regulatory import get_compliance_engine  # TODO: Fix import path


class PaymentRail(str, Enum):
    NPP_OSKO = 'NPP_OSKO'
    DIRECT_ENTRY = 'DIRECT_ENTRY'
    BPAY = 'BPAY'
    SWIFT = 'SWIFT'
    CARD = 'CARD'


class PaymentRouterAgent:
    """AI-powered payment rail selection"""
    
    async def select_optimal_rail(
        self,
        amount: Decimal,
        recipient: Dict,
        urgency: str,
        sender_preferences: Dict
    ) -> Dict:
        """Select optimal payment rail using ML"""
        
        recommendations = []
        
        if urgency == 'URGENT' and amount <= Decimal('10000'):
            recommendations.append({
                'rail': PaymentRail.NPP_OSKO.value,
                'confidence': 0.95,
                'speed': 'Instant (<60 seconds)',
                'cost': 'Low',
                'reasoning': 'Optimal for urgent small payments'
            })
        
        if urgency in ['STANDARD', 'LOW'] or amount > Decimal('10000'):
            recommendations.append({
                'rail': PaymentRail.DIRECT_ENTRY.value,
                'confidence': 0.88,
                'speed': 'T+1 (next business day)',
                'cost': 'Very Low',
                'reasoning': 'Most cost-effective for non-urgent payments'
            })
        
        if recipient.get('type') == 'BILLER':
            recommendations.append({
                'rail': PaymentRail.BPAY.value,
                'confidence': 0.92,
                'speed': 'T+1',
                'cost': 'Low',
                'reasoning': 'Standard for bill payments'
            })
        
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        selected = recommendations[0] if recommendations else None
        
        return {
            'selected_rail': selected['rail'] if selected else None,
            'recommendations': recommendations,
            'decision_rationale': selected['reasoning'] if selected else 'No suitable rail'
        }


class FraudPreventionAgent:
    """Real-time fraud detection and prevention"""
    
    async def analyze_payment(
        self,
        payment_data: Dict,
        customer_history: Dict
    ) -> Dict:
        """Multi-layered fraud analysis"""
        
        scoring_engine = get_scoring_engine()
        
        fraud_check = await scoring_engine.score(
            model_type=ModelType.FRAUD_DETECTION,
            input_data=payment_data
        )
        
        aml_check = await scoring_engine.score(
            model_type=ModelType.AML_MONITORING,
            input_data={
                'transactions': [payment_data],
                'customer_id': payment_data.get('customer_id')
            }
        )
        
        combined_score = (
            fraud_check.get('fraud_score', 0) * 0.5 +
            aml_check.get('suspicion_score', 0) * 0.5
        )
        
        if combined_score > 70:
            decision = 'BLOCK'
            action = 'Transaction blocked - High fraud risk'
        elif combined_score > 50:
            decision = 'REVIEW'
            action = 'Manual review required'
        else:
            decision = 'APPROVE'
            action = 'Approved'
        
        return {
            'decision': decision,
            'combined_fraud_score': combined_score,
            'fraud_score': fraud_check.get('fraud_score'),
            'aml_score': aml_check.get('suspicion_score'),
            'action': action,
            'flags': fraud_check.get('flags', []) + aml_check.get('flags', [])
        }


class ComplianceAgent:
    """Ensures all payments meet regulatory requirements"""
    
    async def validate_compliance(self, payment_data: Dict) -> Dict:
        """Complete compliance validation"""
        
        compliance_engine = get_compliance_engine()
        
        compliance_result = await compliance_engine.process_payment_compliance(
            transaction_id=payment_data['transaction_id'],
            customer_id=payment_data['customer_id'],
            amount=Decimal(str(payment_data['amount'])),
            transaction_type=payment_data['transaction_type'],
            recipient_country=payment_data.get('recipient_country')
        )
        
        return {
            'compliant': compliance_result['compliance_status'] == 'PASSED',
            'checks_performed': ['AUSTRAC_TTR', 'AUSTRAC_SMR', 'AUSTRAC_IFTI'],
            'actions_required': compliance_result['actions'],
            'compliance_details': compliance_result
        }


class SettlementAgent:
    """Manages payment settlement and reconciliation"""
    
    async def orchestrate_settlement(
        self,
        payment_id: str,
        payment_rail: PaymentRail,
        amount: Decimal
    ) -> Dict:
        """Orchestrate payment settlement"""
        
        if payment_rail == PaymentRail.NPP_OSKO:
            settlement_time = 'REALTIME'
            settlement_steps = ['Submit to NPP', 'NPP clearing', 'RBA RITS settlement', 'Account credit']
        else:
            settlement_time = 'T+1'
            settlement_steps = ['Queue for batch', 'Submit to clearing', 'Next day settlement', 'Account credit']
        
        return {
            'payment_id': payment_id,
            'settlement_time': settlement_time,
            'settlement_steps': settlement_steps,
            'estimated_completion': self._calculate_settlement_time(payment_rail)
        }
    
    def _calculate_settlement_time(self, rail: PaymentRail) -> str:
        """Calculate estimated settlement time"""
        if rail == PaymentRail.NPP_OSKO:
            return (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        else:
            settlement_date = datetime.now(timezone.utc) + timedelta(days=1)
            while settlement_date.weekday() >= 5:
                settlement_date += timedelta(days=1)
            return settlement_date.isoformat()


class PaymentOrchestrator:
    """Coordinates all payment agents for end-to-end processing"""
    
    def __init__(self):
        self.router_agent = PaymentRouterAgent()
        self.fraud_agent = FraudPreventionAgent()
        self.compliance_agent = ComplianceAgent()
        self.settlement_agent = SettlementAgent()
    
    async def process_payment(self, payment_request: Dict) -> Dict:
        """End-to-end payment processing with all agents"""
        
        result = {
            'payment_id': payment_request['payment_id'],
            'status': 'PROCESSING',
            'steps': []
        }
        
        # Step 1: Route selection
        route = await self.router_agent.select_optimal_rail(
            amount=Decimal(str(payment_request['amount'])),
            recipient=payment_request.get('recipient', {}),
            urgency=payment_request.get('urgency', 'STANDARD'),
            sender_preferences=payment_request.get('preferences', {})
        )
        result['steps'].append({'step': 'ROUTING', 'decision': route})
        
        if not route['selected_rail']:
            result['status'] = 'FAILED'
            result['reason'] = 'No suitable payment rail'
            return result
        
        # Step 2: Fraud check
        fraud_check = await self.fraud_agent.analyze_payment(
            payment_data=payment_request,
            customer_history={}
        )
        result['steps'].append({'step': 'FRAUD_CHECK', 'result': fraud_check})
        
        if fraud_check['decision'] == 'BLOCK':
            result['status'] = 'BLOCKED'
            result['reason'] = fraud_check['action']
            return result
        
        # Step 3: Compliance check
        compliance = await self.compliance_agent.validate_compliance(
            payment_data=payment_request
        )
        result['steps'].append({'step': 'COMPLIANCE', 'result': compliance})
        
        if not compliance['compliant']:
            result['status'] = 'FAILED'
            result['reason'] = 'Compliance check failed'
            return result
        
        # Step 4: Settlement
        settlement = await self.settlement_agent.orchestrate_settlement(
            payment_id=payment_request['payment_id'],
            payment_rail=PaymentRail(route['selected_rail']),
            amount=Decimal(str(payment_request['amount']))
        )
        result['steps'].append({'step': 'SETTLEMENT', 'plan': settlement})
        
        result['status'] = 'APPROVED'
        result['selected_rail'] = route['selected_rail']
        result['estimated_completion'] = settlement['estimated_completion']
        
        return result


# Global orchestrator
_payment_orchestrator: Optional[PaymentOrchestrator] = None


def get_payment_orchestrator() -> PaymentOrchestrator:
    global _payment_orchestrator
    if _payment_orchestrator is None:
        _payment_orchestrator = PaymentOrchestrator()
    return _payment_orchestrator

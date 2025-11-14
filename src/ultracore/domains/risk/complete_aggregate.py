"""
Complete Risk Domain - Portfolio Monitoring with Kafka
"""
from typing import Dict, List
from datetime import datetime
from decimal import Decimal

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.enhanced_pipeline import enhanced_ml


class CompleteRiskAggregate:
    """Complete risk monitoring"""
    
    def __init__(self, risk_id: str):
        self.risk_id = risk_id
        self.alerts: List[Dict] = []
    
    async def assess_credit_risk(self, client_id: str, loan_amount: Decimal):
        """Assess credit risk"""
        kafka_store = get_production_kafka_store()
        
        credit_result = await enhanced_ml.assess_credit_risk({
            'annual_income': 75000,
            'employment_years': 5,
            'existing_debt': 10000,
            'requested_amount': float(loan_amount)
        })
        
        event_data = {
            'risk_id': self.risk_id,
            'client_id': client_id,
            'risk_type': 'CREDIT',
            'risk_score': credit_result['credit_score'],
            'risk_category': credit_result['risk_category'],
            'assessed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='risk',
            event_type='credit_risk_assessed',
            event_data=event_data,
            aggregate_id=self.risk_id
        )
        
        return credit_result
    
    async def monitor_payment_default(self, loan_id: str, loan_data: Dict):
        """Monitor payment default risk"""
        kafka_store = get_production_kafka_store()
        
        default_result = await enhanced_ml.predict_payment_default(loan_data)
        
        if default_result['default_probability'] > 0.7:
            event_data = {
                'risk_id': self.risk_id,
                'loan_id': loan_id,
                'alert_type': 'DEFAULT_RISK',
                'default_probability': default_result['default_probability'],
                'recommended_action': default_result['recommended_action'],
                'triggered_at': datetime.now(timezone.utc).isoformat()
            }
            
            await kafka_store.append_event(
                entity='risk',
                event_type='default_risk_alert',
                event_data=event_data,
                aggregate_id=self.risk_id
            )
            
            self.alerts.append(event_data)
        
        return default_result
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.risk_id)
        
        for event in events:
            if event.event_type == 'default_risk_alert':
                self.alerts.append(event.event_data)

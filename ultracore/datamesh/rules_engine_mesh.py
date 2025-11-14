"""Rules Engine Data Product"""
from ultracore.rules_engine.rete import get_rete_engine

class RulesEngineDataProduct:
    """Data mesh rules engine domain"""
    def __init__(self):
        self.engine = get_rete_engine()
        self.sla_availability = 0.999
        self.sla_latency_p99_ms = 10
    
    def get_active_rules(self, tenant_id: str):
        return self.engine.get_rules()
    
    def execute_rules(self, tenant_id: str, facts: list):
        return self.engine.fire_rules({"tenant_id": tenant_id})

"""Rules Engine Integration Tests"""
def test_rete_engine():
    from ultracore.rules_engine.rete import get_rete_engine
    engine = get_rete_engine()
    assert engine is not None

def test_rule_aggregate():
    from ultracore.rules_engine.aggregates.rule import BusinessRuleAggregate
    rule = BusinessRuleAggregate(tenant_id="t1", rule_id="r1")
    assert rule.tenant_id == "t1"

"""Permissions Integration Tests"""
def test_role_aggregate():
    from ultracore.permissions.aggregates.role import RoleAggregate
    role = RoleAggregate(tenant_id="t1", role_id="r1")
    assert role.tenant_id == "t1"

def test_api_key_aggregate():
    from ultracore.permissions.aggregates.api_key import ApiKeyAggregate
    key = ApiKeyAggregate(tenant_id="t1", api_key_id="k1")
    assert key.tenant_id == "t1"

"""MCP Tools for Rules Engine"""
def create_rule_tool(name: str, conditions: list, actions: list):
    return {"tool": "create_rule", "params": {"name": name}}

def execute_rules_tool(facts: list):
    return {"tool": "execute_rules", "params": {"facts": facts}}

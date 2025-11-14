# Business Rules MCP Tools

## Overview
MCP tools for creating, evaluating, and managing business rules.

## Functions

### `create_rule()`
Create a new business rule with conditions and actions.

**Parameters:**
- `name` - Rule name
- `rule_type` - Type (validation, calculation, workflow, compliance, notification)
- `condition` - Rule condition (field, operator, value)
- `action` - Action to take when condition is met
- `priority` - Rule priority (1-1000)
- `enabled` - Whether rule is active
- `description` - Rule description

**Returns:** Created rule details

**Example:**
```python
rule = await create_rule(
    name="High Risk Transaction Alert",
    rule_type="compliance",
    condition={"field": "transaction_amount", "operator": "greater_than", "value": 10000},
    action={"type": "alert", "recipients": ["compliance@example.com"]},
    priority=900
)
```

### `evaluate_rule()`
Evaluate a business rule against provided data.

**Parameters:**
- `rule_id` - Rule identifier
- `data` - Data to evaluate against rule

**Returns:** Evaluation result with matched status and action

### `update_rule()`
Update an existing business rule.

**Parameters:**
- `rule_id` - Rule identifier
- `updates` - Fields to update

**Returns:** Updated rule details

### `get_rule_violations()`
Get rule violations for an entity.

**Parameters:**
- `entity_type` - Type of entity (client, transaction, portfolio)
- `entity_id` - Entity identifier
- `date_range_start` - Start date (ISO format)
- `date_range_end` - End date (ISO format)

**Returns:** List of rule violations

### `simulate_rule()`
Simulate rule execution against test data.

**Parameters:**
- `rule_id` - Rule identifier
- `test_data` - List of test data samples

**Returns:** Simulation results with match statistics

## Usage

```python
from ultracore.mcp.rules_tools.rules_mcp_tools import create_rule, evaluate_rule

# Create a rule
rule = await create_rule(
    name="Large Withdrawal Alert",
    rule_type="compliance",
    condition={"field": "withdrawal_amount", "operator": "greater_than", "value": 50000},
    action={"type": "alert", "recipients": ["aml@example.com"]}
)

# Evaluate rule
result = await evaluate_rule(
    rule_id=rule["rule"]["rule_id"],
    data={"withdrawal_amount": 75000}
)

if result["matched"]:
    print(f"Rule triggered: {result['action_taken']}")
```

## Supported Operators

- `equals` - Exact match
- `not_equals` - Not equal
- `greater_than` - Greater than
- `less_than` - Less than
- `greater_than_or_equal` - Greater than or equal
- `less_than_or_equal` - Less than or equal
- `contains` - Contains substring
- `not_contains` - Does not contain
- `in` - In list
- `not_in` - Not in list
- `between` - Between two values

## Supported Actions

- `alert` - Send alert notification
- `reject` - Reject operation
- `approve` - Approve operation
- `calculate` - Perform calculation
- `notify` - Send notification
- `log` - Log event

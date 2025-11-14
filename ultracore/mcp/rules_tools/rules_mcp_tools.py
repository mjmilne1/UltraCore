"""Business Rules MCP Tools"""
from typing import Dict, List, Any
from datetime import datetime
import uuid

async def create_rule(
    name: str,
    rule_type: str,
    condition: Dict,
    action: Dict,
    priority: int = 100,
    enabled: bool = True,
    description: str = ""
) -> Dict:
    """
    Create a new business rule
    
    Args:
        name: Rule name
        rule_type: Type (validation, calculation, workflow, compliance)
        condition: Rule condition (field, operator, value)
        action: Action to take when condition is met
        priority: Rule priority (1-1000, higher = more important)
        enabled: Whether rule is active
        description: Rule description
        
    Returns:
        Created rule details
        
    Example:
        >>> rule = await create_rule(
        ...     name="High Risk Transaction Alert",
        ...     rule_type="compliance",
        ...     condition={"field": "transaction_amount", "operator": "greater_than", "value": 10000},
        ...     action={"type": "alert", "recipients": ["compliance@example.com"]},
        ...     priority=900
        ... )
    """
    rule_id = f"rule_{uuid.uuid4().hex[:12]}"
    
    # Validate rule type
    valid_types = ["validation", "calculation", "workflow", "compliance", "notification"]
    if rule_type not in valid_types:
        raise ValueError(f"Invalid rule_type. Must be one of: {valid_types}")
    
    # Validate condition
    required_condition_fields = ["field", "operator", "value"]
    if not all(field in condition for field in required_condition_fields):
        raise ValueError(f"Condition must contain: {required_condition_fields}")
    
    valid_operators = ["equals", "not_equals", "greater_than", "less_than", 
                      "greater_than_or_equal", "less_than_or_equal", "contains", 
                      "not_contains", "in", "not_in", "between"]
    if condition["operator"] not in valid_operators:
        raise ValueError(f"Invalid operator. Must be one of: {valid_operators}")
    
    # Validate action
    if "type" not in action:
        raise ValueError("Action must contain 'type' field")
    
    valid_action_types = ["alert", "reject", "approve", "calculate", "notify", "log"]
    if action["type"] not in valid_action_types:
        raise ValueError(f"Invalid action type. Must be one of: {valid_action_types}")
    
    rule = {
        "rule_id": rule_id,
        "name": name,
        "rule_type": rule_type,
        "condition": condition,
        "action": action,
        "priority": priority,
        "enabled": enabled,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 1,
        "execution_count": 0,
        "last_executed_at": None
    }
    
    return {
        "status": "created",
        "rule": rule,
        "message": f"Rule '{name}' created successfully"
    }

async def evaluate_rule(
    rule_id: str,
    data: Dict[str, Any]
) -> Dict:
    """
    Evaluate a business rule against provided data
    
    Args:
        rule_id: Rule identifier
        data: Data to evaluate against rule
        
    Returns:
        Evaluation result with matched status and action
        
    Example:
        >>> result = await evaluate_rule(
        ...     rule_id="rule_abc123",
        ...     data={"transaction_amount": 15000, "client_risk_score": 8}
        ... )
    """
    # In production, fetch rule from database
    # For now, simulate evaluation
    
    evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
    
    # Simulate rule evaluation logic
    matched = False
    action_taken = None
    
    # Example: If transaction_amount > 10000, trigger alert
    if "transaction_amount" in data and data["transaction_amount"] > 10000:
        matched = True
        action_taken = {
            "type": "alert",
            "message": "High value transaction detected",
            "triggered_at": datetime.utcnow().isoformat()
        }
    
    return {
        "evaluation_id": evaluation_id,
        "rule_id": rule_id,
        "matched": matched,
        "action_taken": action_taken,
        "evaluated_data": data,
        "evaluated_at": datetime.utcnow().isoformat(),
        "execution_time_ms": 12.5
    }

async def update_rule(
    rule_id: str,
    updates: Dict[str, Any]
) -> Dict:
    """
    Update an existing business rule
    
    Args:
        rule_id: Rule identifier
        updates: Fields to update
        
    Returns:
        Updated rule details
        
    Example:
        >>> result = await update_rule(
        ...     rule_id="rule_abc123",
        ...     updates={"priority": 950, "enabled": False}
        ... )
    """
    # Validate updatable fields
    updatable_fields = ["name", "condition", "action", "priority", "enabled", "description"]
    invalid_fields = [field for field in updates.keys() if field not in updatable_fields]
    
    if invalid_fields:
        raise ValueError(f"Cannot update fields: {invalid_fields}. Updatable fields: {updatable_fields}")
    
    # In production, fetch and update rule in database
    updated_rule = {
        "rule_id": rule_id,
        "updated_fields": list(updates.keys()),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 2  # Increment version
    }
    
    return {
        "status": "updated",
        "rule": updated_rule,
        "message": f"Rule {rule_id} updated successfully"
    }

async def get_rule_violations(
    entity_type: str,
    entity_id: str,
    date_range_start: str = None,
    date_range_end: str = None
) -> List[Dict]:
    """
    Get rule violations for an entity
    
    Args:
        entity_type: Type of entity (client, transaction, portfolio)
        entity_id: Entity identifier
        date_range_start: Start date (ISO format)
        date_range_end: End date (ISO format)
        
    Returns:
        List of rule violations
        
    Example:
        >>> violations = await get_rule_violations(
        ...     entity_type="client",
        ...     entity_id="client_123",
        ...     date_range_start="2024-01-01T00:00:00Z",
        ...     date_range_end="2024-12-31T23:59:59Z"
        ... )
    """
    # In production, query violations from database
    # For now, return simulated violations
    
    violations = [
        {
            "violation_id": f"violation_{uuid.uuid4().hex[:12]}",
            "rule_id": "rule_abc123",
            "rule_name": "High Risk Transaction Alert",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "severity": "high",
            "violation_data": {
                "transaction_amount": 15000,
                "threshold": 10000
            },
            "detected_at": "2024-11-14T10:30:00Z",
            "status": "open",
            "assigned_to": "compliance@example.com"
        },
        {
            "violation_id": f"violation_{uuid.uuid4().hex[:12]}",
            "rule_id": "rule_def456",
            "rule_name": "KYC Document Expiry",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "severity": "medium",
            "violation_data": {
                "document_type": "passport",
                "expiry_date": "2024-11-01",
                "days_overdue": 13
            },
            "detected_at": "2024-11-01T00:00:00Z",
            "status": "in_progress",
            "assigned_to": "kyc@example.com"
        }
    ]
    
    return violations

async def simulate_rule(
    rule_id: str,
    test_data: List[Dict[str, Any]]
) -> Dict:
    """
    Simulate rule execution against test data
    
    Args:
        rule_id: Rule identifier
        test_data: List of test data samples
        
    Returns:
        Simulation results with match statistics
        
    Example:
        >>> result = await simulate_rule(
        ...     rule_id="rule_abc123",
        ...     test_data=[
        ...         {"transaction_amount": 5000},
        ...         {"transaction_amount": 15000},
        ...         {"transaction_amount": 25000}
        ...     ]
        ... )
    """
    simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
    
    # Simulate rule evaluation on test data
    results = []
    matched_count = 0
    
    for i, data in enumerate(test_data):
        # Example: transaction_amount > 10000
        matched = data.get("transaction_amount", 0) > 10000
        if matched:
            matched_count += 1
        
        results.append({
            "test_case": i + 1,
            "data": data,
            "matched": matched,
            "action": "alert" if matched else None
        })
    
    total_cases = len(test_data)
    match_rate = (matched_count / total_cases * 100) if total_cases > 0 else 0
    
    return {
        "simulation_id": simulation_id,
        "rule_id": rule_id,
        "total_test_cases": total_cases,
        "matched_cases": matched_count,
        "match_rate_percent": match_rate,
        "results": results,
        "simulated_at": datetime.utcnow().isoformat(),
        "recommendation": "Rule is working as expected" if match_rate > 0 else "Rule may need adjustment"
    }

# MCP Tool Registry
MCP_TOOLS = {
    "create_rule": create_rule,
    "evaluate_rule": evaluate_rule,
    "update_rule": update_rule,
    "get_rule_violations": get_rule_violations,
    "simulate_rule": simulate_rule
}

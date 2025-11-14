# Agentic AI Developer Guide

**Version:** 1.0  
**Last Updated:** January 14, 2025

---

## Overview

UltraCore's Agentic AI framework enables autonomous AI agents to perform banking operations. Agents use perception-decision-action loops to understand context, make decisions, and execute actions.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Agent Architecture](#agent-architecture)
3. [Creating Agents](#creating-agents)
4. [Agent Orchestration](#agent-orchestration)
5. [Multi-Agent Collaboration](#multi-agent-collaboration)
6. [Agent Memory](#agent-memory)
7. [Tools and Capabilities](#tools-and-capabilities)
8. [Best Practices](#best-practices)

---

## Core Concepts

### Agents

An **agent** is an autonomous entity that:
- **Perceives** its environment
- **Decides** what action to take
- **Acts** on its decision
- **Learns** from outcomes

### Agent Lifecycle

```
┌─────────────┐
│   IDLE      │ ← Agent waiting for tasks
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  THINKING   │ ← Perceiving and deciding
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   ACTING    │ ← Executing action
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  WAITING    │ ← Waiting for action result
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   IDLE      │ ← Ready for next task
└─────────────┘
```

### Agent Capabilities

Agents have specific capabilities:
- **Data Analysis** - Analyze data and generate insights
- **Risk Assessment** - Evaluate risk and make recommendations
- **Fraud Detection** - Detect fraudulent patterns
- **Loan Underwriting** - Assess loan applications
- **Investment Recommendations** - Provide investment advice
- **Credit Scoring** - Calculate credit scores
- **Compliance Checking** - Verify regulatory compliance
- **Customer Support** - Assist customers
- **Transaction Processing** - Process transactions
- **Report Generation** - Generate reports
- **Pattern Recognition** - Identify patterns in data

---

## Agent Architecture

### Agent Base Class

All agents inherit from the `Agent` base class:

```python
from ultracore.agentic_ai import Agent, AgentCapability, AgentState
from typing import Dict, Any

class MyAgent(Agent):
    """Custom agent implementation."""
    
    def __init__(self):
        super().__init__(
            name="My Agent",
            agent_id="my_agent",
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.PATTERN_RECOGNITION
            ]
        )
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment and extract relevant information."""
        # Extract and process context
        perceived_state = {
            "key_data": context.get("data"),
            "timestamp": datetime.utcnow()
        }
        return perceived_state
    
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """Decide what action to take based on perceived state."""
        # Decision logic
        action = AgentAction(
            action_type="analyze_data",
            parameters={"data": perceived_state["key_data"]}
        )
        return action
    
    async def act(self, action: AgentAction) -> Any:
        """Execute the decided action."""
        # Execute action
        result = self._perform_analysis(action.parameters["data"])
        return result
```

### Perception-Decision-Action Loop

The agent's `run()` method implements the PDA loop:

```python
async def run(self, context: Dict[str, Any]) -> Any:
    """Run agent on given context."""
    try:
        # 1. Perceive
        self.state = AgentState.THINKING
        perceived_state = await self.perceive(context)
        
        # 2. Decide
        action = await self.decide(perceived_state)
        
        # 3. Act
        self.state = AgentState.ACTING
        result = await self.act(action)
        
        # 4. Record
        self._record_action(action, result)
        
        self.state = AgentState.IDLE
        return result
        
    except Exception as e:
        self.state = AgentState.ERROR
        raise
```

---

## Creating Agents

### Simple Agent

```python
from ultracore.agentic_ai import Agent, AgentCapability, AgentAction

class DataAnalysisAgent(Agent):
    """Agent for data analysis tasks."""
    
    def __init__(self):
        super().__init__(
            name="Data Analysis Agent",
            agent_id="data_analysis_agent",
            capabilities=[AgentCapability.DATA_ANALYSIS]
        )
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data to analyze."""
        return {
            "dataset": context.get("data"),
            "analysis_type": context.get("type", "summary")
        }
    
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """Decide analysis method."""
        analysis_type = perceived_state["analysis_type"]
        
        return AgentAction(
            action_type=f"perform_{analysis_type}_analysis",
            parameters={"data": perceived_state["dataset"]}
        )
    
    async def act(self, action: AgentAction) -> Any:
        """Perform analysis."""
        data = action.parameters["data"]
        
        if action.action_type == "perform_summary_analysis":
            return self._summarize(data)
        elif action.action_type == "perform_trend_analysis":
            return self._analyze_trends(data)
        
        return None
    
    def _summarize(self, data: Any) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "count": len(data),
            "summary": "Data summary here"
        }
    
    def _analyze_trends(self, data: Any) -> Dict[str, Any]:
        """Analyze trends in data."""
        return {
            "trend": "upward",
            "confidence": 0.85
        }
```

### Using the Agent

```python
# Create agent
agent = DataAnalysisAgent()

# Prepare context
context = {
    "data": [1, 2, 3, 4, 5],
    "type": "summary"
}

# Run agent
result = await agent.run(context)
print(result)
# Output: {'count': 5, 'summary': 'Data summary here'}
```

---

## Agent Orchestration

### Agent Orchestrator

The orchestrator manages multiple agents and routes tasks:

```python
from ultracore.agentic_ai import AgentOrchestrator, orchestrator

# Get global orchestrator instance
orch = orchestrator

# Register agents
from ultracore.agentic_ai.agents import (
    CustomerAgent,
    RiskAgent,
    LoanAgent
)

orch.register_agent(CustomerAgent())
orch.register_agent(RiskAgent())
orch.register_agent(LoanAgent())

# List available agents
agents = orch.list_agents()
for agent in agents:
    print(f"{agent.name}: {agent.capabilities}")
```

### Task Execution

```python
# Execute single-agent task
task = {
    "task_id": "task_001",
    "customer_id": "CUST001",
    "request_type": "support"
}

result = await orch.execute_task(task, agent_id="customer_agent")
print(result)

# Get task history
history = orch.get_task_history()
for task in history:
    print(f"Task {task['task_id']}: {task['status']}")
```

### Agent Selection

```python
# Automatic agent selection based on capabilities
def select_agent_for_task(task_type: str) -> str:
    """Select appropriate agent for task."""
    capability_map = {
        "risk_assessment": AgentCapability.RISK_ASSESSMENT,
        "loan_underwriting": AgentCapability.LOAN_UNDERWRITING,
        "fraud_detection": AgentCapability.FRAUD_DETECTION,
        "customer_support": AgentCapability.CUSTOMER_SUPPORT
    }
    
    required_capability = capability_map.get(task_type)
    
    for agent in orch.list_agents():
        if agent.has_capability(required_capability):
            return agent.agent_id
    
    return None

# Use it
agent_id = select_agent_for_task("risk_assessment")
result = await orch.execute_task(task, agent_id=agent_id)
```

---

## Multi-Agent Collaboration

### Multi-Agent Tasks

Execute tasks requiring multiple agents:

```python
# Complex task requiring multiple agents
task = {
    "task_id": "complex_001",
    "customer_id": "CUST001",
    "loan_application": {
        "amount": 50000,
        "term": 60
    }
}

# Execute with multiple agents
results = await orch.execute_multi_agent_task(
    task,
    agent_ids=["customer_agent", "risk_agent", "loan_agent"]
)

# Results from each agent
customer_result = results["customer_agent"]
risk_result = results["risk_agent"]
loan_result = results["loan_agent"]

# Combine results
final_decision = combine_agent_results(results)
```

### Agent-to-Agent Communication

```python
# Agent A sends message to Agent B
await orch.send_agent_message(
    from_agent_id="risk_agent",
    to_agent_id="loan_agent",
    content={
        "risk_score": 0.75,
        "recommendation": "approve_with_conditions"
    }
)

# Agent B receives and processes message
# (Handled automatically by orchestrator)
```

### Collaborative Decision Making

```python
class CollaborativeAgent(Agent):
    """Agent that collaborates with others."""
    
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """Make decision with input from other agents."""
        
        # Request input from risk agent
        risk_input = await self._request_agent_input(
            "risk_agent",
            {"customer_id": perceived_state["customer_id"]}
        )
        
        # Request input from compliance agent
        compliance_input = await self._request_agent_input(
            "compliance_agent",
            {"customer_id": perceived_state["customer_id"]}
        )
        
        # Make decision based on inputs
        if risk_input["score"] > 0.7 and compliance_input["status"] == "clear":
            action_type = "approve"
        else:
            action_type = "reject"
        
        return AgentAction(action_type=action_type, parameters={})
    
    async def _request_agent_input(
        self,
        agent_id: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request input from another agent."""
        # Send message and wait for response
        await orchestrator.send_agent_message(
            from_agent_id=self.agent_id,
            to_agent_id=agent_id,
            content=request
        )
        # Response handling logic here
        return {}
```

---

## Agent Memory

### Memory Types

Agents have three types of memory:

**Short-term Memory:**
- Stores recent actions (last 100)
- Automatically managed
- Used for immediate context

**Long-term Memory:**
- Persistent key-value storage
- Manually managed
- Used for learned patterns

**Working Memory:**
- Current task context
- Cleared after task completion
- Used for task-specific data

### Using Memory

```python
class MemoryAwareAgent(Agent):
    """Agent that uses memory."""
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive with memory context."""
        
        # Recall from long-term memory
        customer_preferences = self.memory.recall(
            "customer_preferences",
            "long_term"
        )
        
        # Recall from working memory
        current_task = self.memory.recall(
            "current_task",
            "working"
        )
        
        return {
            "context": context,
            "preferences": customer_preferences,
            "task": current_task
        }
    
    async def act(self, action: AgentAction) -> Any:
        """Act and store in memory."""
        
        # Execute action
        result = self._execute_action(action)
        
        # Store in long-term memory
        if result.get("learn"):
            self.memory.remember(
                "learned_pattern",
                result["pattern"],
                "long_term"
            )
        
        # Store in working memory
        self.memory.remember(
            "last_result",
            result,
            "working"
        )
        
        return result
```

### Memory Patterns

```python
# Pattern 1: Learning from actions
async def learn_from_action(agent: Agent, action: AgentAction, result: Any):
    """Learn pattern from action result."""
    if result.get("success"):
        # Store successful pattern
        agent.memory.remember(
            f"success_pattern_{action.action_type}",
            {
                "action": action.action_type,
                "parameters": action.parameters,
                "outcome": result
            },
            "long_term"
        )

# Pattern 2: Context retention
async def retain_context(agent: Agent, context: Dict[str, Any]):
    """Retain important context."""
    if context.get("important"):
        agent.memory.remember(
            "important_context",
            context,
            "long_term"
        )

# Pattern 3: Recent actions review
def review_recent_actions(agent: Agent, count: int = 10):
    """Review recent actions."""
    history = agent.get_action_history(limit=count)
    
    # Analyze patterns
    success_rate = sum(1 for h in history if h.get("success")) / len(history)
    
    return {
        "success_rate": success_rate,
        "total_actions": len(history)
    }
```

---

## Tools and Capabilities

### Tool Framework

Agents use tools to extend their capabilities:

```python
from ultracore.agentic_ai.base import Tool

class DataQueryTool(Tool):
    """Tool for querying data."""
    
    def __init__(self):
        super().__init__(
            name="data_query",
            description="Query data from database"
        )
    
    async def execute(self, **kwargs) -> Any:
        """Execute data query."""
        query = kwargs.get("query")
        filters = kwargs.get("filters", {})
        
        # Execute query
        results = await self._query_database(query, filters)
        
        return results
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Query filters"
                    }
                },
                "required": ["query"]
            }
        }
```

### Using Tools

```python
class ToolUsingAgent(Agent):
    """Agent that uses tools."""
    
    def __init__(self):
        super().__init__(
            name="Tool Using Agent",
            agent_id="tool_agent",
            capabilities=[AgentCapability.DATA_ANALYSIS]
        )
        
        # Register tools
        self.tools = {
            "data_query": DataQueryTool(),
            "data_analysis": DataAnalysisTool()
        }
    
    async def act(self, action: AgentAction) -> Any:
        """Execute action using tools."""
        
        # Select appropriate tool
        tool_name = action.parameters.get("tool")
        tool = self.tools.get(tool_name)
        
        if tool:
            # Execute tool
            result = await tool.execute(**action.parameters)
            return result
        
        # Fallback to direct action
        return await self._execute_direct(action)
```

---

## Best Practices

### Agent Design

1. **Single Responsibility:** Each agent should have a clear, focused purpose
2. **Capability-Based:** Design agents around capabilities, not tasks
3. **Stateless Perception:** Perception should not modify agent state
4. **Idempotent Actions:** Actions should be safe to retry
5. **Error Handling:** Always handle errors gracefully

### Example: Well-Designed Agent

```python
class WellDesignedAgent(Agent):
    """Example of well-designed agent."""
    
    def __init__(self):
        super().__init__(
            name="Well Designed Agent",
            agent_id="well_designed_agent",
            capabilities=[AgentCapability.DATA_ANALYSIS]
        )
        self.max_retries = 3
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Stateless perception."""
        try:
            # Extract only what's needed
            return {
                "data": context.get("data"),
                "operation": context.get("operation", "analyze")
            }
        except Exception as e:
            self.logger.error(f"Perception error: {e}")
            return {}
    
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """Clear decision logic."""
        operation = perceived_state.get("operation")
        
        # Simple, clear decision tree
        if operation == "analyze":
            action_type = "perform_analysis"
        elif operation == "summarize":
            action_type = "generate_summary"
        else:
            action_type = "default_action"
        
        return AgentAction(
            action_type=action_type,
            parameters=perceived_state
        )
    
    async def act(self, action: AgentAction) -> Any:
        """Idempotent action with retry."""
        for attempt in range(self.max_retries):
            try:
                result = await self._execute_action(action)
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Action failed after {self.max_retries} attempts")
                    raise
                await asyncio.sleep(2 ** attempt)
```

### Testing Agents

```python
import pytest

@pytest.mark.asyncio
async def test_agent_perception():
    """Test agent perception."""
    agent = WellDesignedAgent()
    
    context = {"data": [1, 2, 3], "operation": "analyze"}
    perceived = await agent.perceive(context)
    
    assert "data" in perceived
    assert perceived["operation"] == "analyze"

@pytest.mark.asyncio
async def test_agent_decision():
    """Test agent decision making."""
    agent = WellDesignedAgent()
    
    perceived_state = {"operation": "analyze", "data": [1, 2, 3]}
    action = await agent.decide(perceived_state)
    
    assert action.action_type == "perform_analysis"

@pytest.mark.asyncio
async def test_agent_run():
    """Test complete agent run."""
    agent = WellDesignedAgent()
    
    context = {"data": [1, 2, 3], "operation": "analyze"}
    result = await agent.run(context)
    
    assert result is not None
    assert agent.state == AgentState.IDLE
```

### Monitoring

```python
# Log agent activity
import logging

logger = logging.getLogger(__name__)

async def monitored_agent_run(agent: Agent, context: Dict[str, Any]):
    """Run agent with monitoring."""
    start_time = time.time()
    
    logger.info(f"Agent {agent.name} starting task")
    
    try:
        result = await agent.run(context)
        
        duration = time.time() - start_time
        logger.info(
            f"Agent {agent.name} completed task in {duration:.2f}s"
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Agent {agent.name} failed: {str(e)}",
            exc_info=True
        )
        raise
```

---

## Available Agents

### Domain Agents

- **CustomerAgent** - Customer support, onboarding, sentiment analysis
- **RiskAgent** - Risk assessment, VaR calculation, stress testing
- **LoanAgent** - Loan underwriting, application processing
- **InvestmentAgent** - Investment recommendations, portfolio optimization
- **ComplianceAgent** - AML/CTF checks, regulatory compliance
- **FraudAgent** - Fraud detection, pattern recognition
- **PaymentAgent** - Payment routing, authorization
- **TransactionAgent** - Transaction validation, posting
- **AccountAgent** - Account analytics, monitoring
- **PortfolioAgent** - Portfolio performance, rebalancing
- **AnalyticsAgent** - Customer behavior, product usage
- **ReportingAgent** - Automated reporting, dashboards
- **NotificationAgent** - Alert routing, delivery
- **AuditAgent** - Audit trail analysis
- **SystemAgent** - System health, performance monitoring

---

## Resources

- [Autonomous Agents](https://en.wikipedia.org/wiki/Autonomous_agent)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)
- [Reinforcement Learning](https://en.wikipedia.org/wiki/Reinforcement_learning)

---

**For support, contact:** agentic-ai-team@ultracore.com

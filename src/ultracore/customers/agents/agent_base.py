"""
UltraCore Customer Management - AI Agent Base Framework

Base classes and utilities for AI agents:
- Agent lifecycle management
- Tool use (function calling)
- Memory management (short & long term)
- Multi-agent orchestration
- Explainability & reasoning traces
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json


# ============================================================================
# Agent Enums
# ============================================================================

class AgentType(str, Enum):
    """Types of agents"""
    KYC_AML = "KYC_AML"
    ONBOARDING = "ONBOARDING"
    FRAUD_DETECTION = "FRAUD_DETECTION"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    RECOMMENDATION = "RECOMMENDATION"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "IDLE"
    THINKING = "THINKING"
    ACTING = "ACTING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ToolType(str, Enum):
    """Types of tools agents can use"""
    DATABASE_QUERY = "DATABASE_QUERY"
    API_CALL = "API_CALL"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    TEXT_ANALYSIS = "TEXT_ANALYSIS"
    GRAPH_QUERY = "GRAPH_QUERY"
    ML_MODEL = "ML_MODEL"
    CALCULATION = "CALCULATION"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AgentMessage:
    """Message in agent conversation"""
    role: str  # SYSTEM, USER, ASSISTANT, TOOL
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTool:
    """Tool that agent can use"""
    tool_id: str
    tool_name: str
    tool_type: ToolType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    function: Optional[Callable] = None
    
    def to_function_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling schema"""
        return {
            'name': self.tool_name,
            'description': self.description,
            'parameters': self.parameters
        }


@dataclass
class ToolCall:
    """Record of tool usage"""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0


@dataclass
class AgentMemory:
    """
    Agent memory system
    - Short-term: Current conversation context
    - Long-term: Persistent knowledge
    """
    agent_id: str
    
    # Short-term memory (conversation)
    messages: List[AgentMessage] = field(default_factory=list)
    
    # Long-term memory (facts, learnings)
    facts: Dict[str, Any] = field(default_factory=dict)
    
    # Tool usage history
    tool_calls: List[ToolCall] = field(default_factory=list)
    
    # Reasoning traces
    reasoning_steps: List[str] = field(default_factory=list)
    
    # Working memory (scratch pad)
    working_memory: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation"""
        self.messages.append(AgentMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
    
    def add_reasoning_step(self, step: str):
        """Add reasoning step for explainability"""
        self.reasoning_steps.append(step)
    
    def get_context_window(self, max_messages: int = 10) -> List[AgentMessage]:
        """Get recent messages for context"""
        return self.messages[-max_messages:]


@dataclass
class AgentDecision:
    """Agent decision with reasoning"""
    decision_id: str
    agent_id: str
    decision_type: str  # APPROVE, REJECT, ESCALATE, RECOMMEND
    decision: Any
    confidence: float  # 0.0 to 1.0
    
    # Explainability
    reasoning: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Alternative options considered
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Human review
    requires_human_review: bool = False
    review_reason: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Base Agent Class
# ============================================================================

class BaseAgent(ABC):
    """
    Base class for all AI agents
    
    Features:
    - Tool use (function calling)
    - Memory management
    - Reasoning traces
    - Explainability
    - Human-in-the-loop
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        agent_name: str,
        system_prompt: str
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.status = AgentStatus.IDLE
        
        # Memory
        self.memory = AgentMemory(agent_id=agent_id)
        
        # Tools
        self.available_tools: Dict[str, AgentTool] = {}
        
        # Configuration
        self.temperature = 0.1  # Low temperature for deterministic outputs
        self.max_iterations = 10  # Max reasoning loops
        self.confidence_threshold = 0.8  # Min confidence for auto-approval
        
        # Initialize tools
        self._register_tools()
    
    @abstractmethod
    def _register_tools(self):
        """Register tools that this agent can use"""
        pass
    
    def register_tool(self, tool: AgentTool):
        """Register a tool"""
        self.available_tools[tool.tool_name] = tool
    
    async def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentDecision:
        """
        Main processing method
        Implements agentic reasoning loop
        """
        
        self.status = AgentStatus.THINKING
        
        # Add user message to memory
        self.memory.add_message("USER", user_input, metadata=context)
        
        # Initialize decision
        decision = await self._make_decision(user_input, context or {})
        
        self.status = AgentStatus.COMPLETED
        
        return decision
    
    @abstractmethod
    async def _make_decision(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AgentDecision:
        """Make decision based on input"""
        pass
    
    async def use_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolCall:
        """Execute a tool"""
        
        tool = self.available_tools.get(tool_name)
        if not tool:
            return ToolCall(
                call_id=f"CALL-{datetime.utcnow().timestamp()}",
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=f"Tool {tool_name} not found"
            )
        
        self.status = AgentStatus.ACTING
        
        start_time = datetime.utcnow()
        
        try:
            if tool.function:
                result = await tool.function(**arguments)
            else:
                result = {"status": "simulated"}
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            tool_call = ToolCall(
                call_id=f"CALL-{datetime.utcnow().timestamp()}",
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            tool_call = ToolCall(
                call_id=f"CALL-{datetime.utcnow().timestamp()}",
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
        
        # Add to memory
        self.memory.tool_calls.append(tool_call)
        
        self.status = AgentStatus.THINKING
        
        return tool_call
    
    def explain_decision(self, decision: AgentDecision) -> str:
        """
        Generate human-readable explanation of decision
        Critical for compliance and trust
        """
        
        explanation = f"Decision: {decision.decision_type}\n"
        explanation += f"Confidence: {decision.confidence:.1%}\n\n"
        
        if decision.reasoning:
            explanation += "Reasoning:\n"
            for i, step in enumerate(decision.reasoning, 1):
                explanation += f"{i}. {step}\n"
        
        if decision.evidence:
            explanation += "\nEvidence:\n"
            for key, value in decision.evidence.items():
                explanation += f"- {key}: {value}\n"
        
        if decision.requires_human_review:
            explanation += f"\n⚠️ Human review required: {decision.review_reason}\n"
        
        return explanation


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================

class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents working together
    
    Features:
    - Task decomposition
    - Agent assignment
    - Result aggregation
    - Conflict resolution
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_history: List[Dict[str, Any]] = []
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.agent_id] = agent
    
    async def execute_task(
        self,
        task: str,
        context: Dict[str, Any],
        required_agents: Optional[List[AgentType]] = None
    ) -> Dict[str, AgentDecision]:
        """
        Execute task with multiple agents
        Returns decisions from each agent
        """
        
        decisions = {}
        
        # If no specific agents required, use all
        if not required_agents:
            agents_to_use = list(self.agents.values())
        else:
            agents_to_use = [
                agent for agent in self.agents.values()
                if agent.agent_type in required_agents
            ]
        
        # Execute task with each agent
        for agent in agents_to_use:
            decision = await agent.process(task, context)
            decisions[agent.agent_id] = decision
        
        # Record task
        self.task_history.append({
            'task': task,
            'timestamp': datetime.utcnow(),
            'agents': [a.agent_id for a in agents_to_use],
            'decisions': {k: v.decision for k, v in decisions.items()}
        })
        
        return decisions
    
    def aggregate_decisions(
        self,
        decisions: Dict[str, AgentDecision],
        aggregation_strategy: str = "CONSENSUS"
    ) -> AgentDecision:
        """
        Aggregate decisions from multiple agents
        
        Strategies:
        - CONSENSUS: Majority vote
        - HIGHEST_CONFIDENCE: Use most confident agent
        - WEIGHTED: Weight by agent expertise
        """
        
        if aggregation_strategy == "HIGHEST_CONFIDENCE":
            best_decision = max(decisions.values(), key=lambda d: d.confidence)
            return best_decision
        
        elif aggregation_strategy == "CONSENSUS":
            # Simple majority vote on decision type
            decision_counts = {}
            for decision in decisions.values():
                decision_type = decision.decision_type
                decision_counts[decision_type] = decision_counts.get(decision_type, 0) + 1
            
            majority_decision_type = max(decision_counts.items(), key=lambda x: x[1])[0]
            
            # Return the decision with highest confidence of majority type
            majority_decisions = [
                d for d in decisions.values()
                if d.decision_type == majority_decision_type
            ]
            return max(majority_decisions, key=lambda d: d.confidence)
        
        # Default: return first decision
        return list(decisions.values())[0]


# ============================================================================
# Utility Functions
# ============================================================================

def create_reasoning_chain(steps: List[str]) -> str:
    """Create chain-of-thought reasoning trace"""
    chain = "Reasoning Chain:\n"
    for i, step in enumerate(steps, 1):
        chain += f"Step {i}: {step}\n"
    return chain


def calculate_confidence(
    evidence_scores: List[float],
    weights: Optional[List[float]] = None
) -> float:
    """
    Calculate overall confidence from multiple evidence scores
    Uses weighted average
    """
    if not evidence_scores:
        return 0.0
    
    if weights:
        if len(weights) != len(evidence_scores):
            raise ValueError("Weights must match evidence scores length")
        weighted_sum = sum(score * weight for score, weight in zip(evidence_scores, weights))
        return weighted_sum / sum(weights)
    
    return sum(evidence_scores) / len(evidence_scores)


def check_human_review_required(
    confidence: float,
    risk_factors: List[str],
    threshold: float = 0.8
) -> Tuple[bool, Optional[str]]:
    """
    Determine if human review is required
    
    Rules:
    - Low confidence requires review
    - High risk factors require review
    - Regulatory flags require review
    """
    
    if confidence < threshold:
        return True, f"Low confidence: {confidence:.1%}"
    
    high_risk_flags = ['PEP', 'SANCTIONS', 'ADVERSE_MEDIA', 'HIGH_RISK_COUNTRY']
    for flag in risk_factors:
        if flag in high_risk_flags:
            return True, f"High risk flag: {flag}"
    
    return False, None

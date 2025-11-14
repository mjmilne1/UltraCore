"""
Agentic AI Base Classes.

Core abstractions for autonomous AI agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AgentState(str, Enum):
    """Agent state."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    # Analysis capabilities
    DATA_ANALYSIS = "data_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    FRAUD_DETECTION = "fraud_detection"
    
    # Decision capabilities
    LOAN_UNDERWRITING = "loan_underwriting"
    INVESTMENT_RECOMMENDATION = "investment_recommendation"
    CREDIT_SCORING = "credit_scoring"
    
    # Automation capabilities
    TRANSACTION_PROCESSING = "transaction_processing"
    COMPLIANCE_CHECKING = "compliance_checking"
    REPORT_GENERATION = "report_generation"
    
    # Communication capabilities
    CUSTOMER_SUPPORT = "customer_support"
    NOTIFICATION_MANAGEMENT = "notification_management"
    
    # Learning capabilities
    PATTERN_RECOGNITION = "pattern_recognition"
    PREDICTIVE_MODELING = "predictive_modeling"
    REINFORCEMENT_LEARNING = "reinforcement_learning"


@dataclass
class AgentAction:
    """Agent action."""
    action_id: UUID = field(default_factory=uuid4)
    action_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentMemory:
    """Agent memory for context retention."""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: Dict[str, Any] = field(default_factory=dict)
    working_memory: Dict[str, Any] = field(default_factory=dict)
    
    def remember(self, key: str, value: Any, memory_type: str = "short_term") -> None:
        """Store information in memory."""
        if memory_type == "short_term":
            self.short_term.append({"key": key, "value": value, "timestamp": datetime.utcnow()})
            # Keep only last 100 items
            if len(self.short_term) > 100:
                self.short_term = self.short_term[-100:]
        elif memory_type == "long_term":
            self.long_term[key] = value
        elif memory_type == "working":
            self.working_memory[key] = value
    
    def recall(self, key: str, memory_type: str = "long_term") -> Optional[Any]:
        """Retrieve information from memory."""
        if memory_type == "long_term":
            return self.long_term.get(key)
        elif memory_type == "working":
            return self.working_memory.get(key)
        elif memory_type == "short_term":
            for item in reversed(self.short_term):
                if item["key"] == key:
                    return item["value"]
        return None


class Agent(ABC):
    """
    Base agent class.
    
    All domain agents inherit from this class.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[AgentCapability]
    ):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        self.action_history: List[AgentAction] = []
    
    @abstractmethod
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive the environment.
        
        Args:
            context: Current context
            
        Returns:
            Perceived state
        """
        pass
    
    @abstractmethod
    async def decide(self, perceived_state: Dict[str, Any]) -> AgentAction:
        """
        Decide on an action.
        
        Args:
            perceived_state: Perceived state
            
        Returns:
            Decided action
        """
        pass
    
    @abstractmethod
    async def act(self, action: AgentAction) -> Any:
        """
        Execute an action.
        
        Args:
            action: Action to execute
            
        Returns:
            Action result
        """
        pass
    
    async def run(self, context: Dict[str, Any]) -> Any:
        """
        Run the agent's perception-decision-action loop.
        
        Args:
            context: Current context
            
        Returns:
            Final result
        """
        try:
            # Perceive
            self.state = AgentState.THINKING
            perceived_state = await self.perceive(context)
            
            # Decide
            action = await self.decide(perceived_state)
            
            # Act
            self.state = AgentState.ACTING
            result = await self.act(action)
            
            # Record action
            action.result = result
            self.action_history.append(action)
            
            # Update state
            self.state = AgentState.IDLE
            
            return result
            
        except Exception as e:
            self.state = AgentState.ERROR
            raise e
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has capability."""
        return capability in self.capabilities
    
    def get_action_history(self, limit: int = 10) -> List[AgentAction]:
        """Get recent action history."""
        return self.action_history[-limit:]


class Tool(ABC):
    """
    Base tool class.
    
    Tools are functions that agents can use.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema."""
        pass


@dataclass
class AgentMessage:
    """Message for agent communication."""
    message_id: UUID = field(default_factory=uuid4)
    from_agent: str = ""
    to_agent: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[UUID] = None


class AgentCommunicationProtocol(ABC):
    """Protocol for agent-to-agent communication."""
    
    @abstractmethod
    async def send_message(self, message: AgentMessage) -> bool:
        """Send message to another agent."""
        pass
    
    @abstractmethod
    async def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """Receive messages for an agent."""
        pass

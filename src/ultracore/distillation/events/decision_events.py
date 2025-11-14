"""Agent Decision Events for Tool Calling Distillation"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about an available tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: Optional[str] = None


@dataclass
class DecisionOutcome:
    """Outcome of a tool execution."""
    success: bool
    execution_time_ms: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cost_usd: Optional[float] = None


@dataclass
class AgentDecisionEvent:
    """Event capturing an agent's tool selection decision."""
    
    # Event metadata
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "AGENT_TOOL_SELECTED"
    aggregate_id: str = ""  # agent_id
    aggregate_type: str = "Agent"
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    causation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Decision data
    agent_id: str = ""
    session_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    tools_available: List[ToolInfo] = field(default_factory=list)
    tool_selected: str = ""
    tool_parameters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.0
    
    # Teacher model info (OpenAI)
    teacher_model: str = "gpt-4"
    teacher_confidence: float = 0.0
    teacher_reasoning: Optional[str] = None
    
    # Outcome
    outcome: Optional[DecisionOutcome] = None
    
    # Metadata
    environment: str = "production"
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event store."""
        return {
            "metadata": {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "aggregate_id": self.aggregate_id,
                "aggregate_type": self.aggregate_type,
                "version": self.version,
                "timestamp": self.timestamp,
                "causation_id": self.causation_id,
                "correlation_id": self.correlation_id,
            },
            "data": {
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "context": self.context,
                "tools_available": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                        "category": t.category
                    }
                    for t in self.tools_available
                ],
                "tool_selected": self.tool_selected,
                "tool_parameters": self.tool_parameters,
                "reasoning": self.reasoning,
                "confidence": self.confidence,
                "teacher_model": self.teacher_model,
                "teacher_confidence": self.teacher_confidence,
                "teacher_reasoning": self.teacher_reasoning,
                "outcome": {
                    "success": self.outcome.success,
                    "execution_time_ms": self.outcome.execution_time_ms,
                    "result": self.outcome.result,
                    "error": self.outcome.error,
                    "cost_usd": self.outcome.cost_usd
                } if self.outcome else None,
                "environment": self.environment,
                "user_id": self.user_id
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDecisionEvent":
        """Create from dictionary."""
        metadata = data.get("metadata", {})
        event_data = data.get("data", {})
        
        tools_available = [
            ToolInfo(**t) for t in event_data.get("tools_available", [])
        ]
        
        outcome_data = event_data.get("outcome")
        outcome = DecisionOutcome(**outcome_data) if outcome_data else None
        
        return cls(
            event_id=metadata.get("event_id", str(uuid4())),
            event_type=metadata.get("event_type", "AGENT_TOOL_SELECTED"),
            aggregate_id=metadata.get("aggregate_id", ""),
            aggregate_type=metadata.get("aggregate_type", "Agent"),
            version=metadata.get("version", 1),
            timestamp=metadata.get("timestamp", datetime.utcnow().isoformat()),
            causation_id=metadata.get("causation_id"),
            correlation_id=metadata.get("correlation_id"),
            agent_id=event_data.get("agent_id", ""),
            session_id=event_data.get("session_id", ""),
            context=event_data.get("context", {}),
            tools_available=tools_available,
            tool_selected=event_data.get("tool_selected", ""),
            tool_parameters=event_data.get("tool_parameters", {}),
            reasoning=event_data.get("reasoning", ""),
            confidence=event_data.get("confidence", 0.0),
            teacher_model=event_data.get("teacher_model", "gpt-4"),
            teacher_confidence=event_data.get("teacher_confidence", 0.0),
            teacher_reasoning=event_data.get("teacher_reasoning"),
            outcome=outcome,
            environment=event_data.get("environment", "production"),
            user_id=event_data.get("user_id")
        )


@dataclass
class TrainingDataCuratedEvent:
    """Event indicating new training data has been curated."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "TRAINING_DATA_CURATED"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    dataset_id: str = ""
    source_event_count: int = 0
    curated_count: int = 0
    deduplication_rate: float = 0.0
    cluster_count: int = 0
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
            },
            "data": {
                "dataset_id": self.dataset_id,
                "source_event_count": self.source_event_count,
                "curated_count": self.curated_count,
                "deduplication_rate": self.deduplication_rate,
                "cluster_count": self.cluster_count,
                "quality_score": self.quality_score
            }
        }


@dataclass
class PromptsOptimizedEvent:
    """Event indicating prompts have been optimized."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "PROMPTS_OPTIMIZED"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    agent_ids: List[str] = field(default_factory=list)
    optimization_method: str = ""  # "dspy", "gepa", "combined"
    iteration: int = 0
    accuracy_before: float = 0.0
    accuracy_after: float = 0.0
    improvement: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
            },
            "data": {
                "agent_ids": self.agent_ids,
                "optimization_method": self.optimization_method,
                "iteration": self.iteration,
                "accuracy_before": self.accuracy_before,
                "accuracy_after": self.accuracy_after,
                "improvement": self.improvement
            }
        }


@dataclass
class ModelDeployedEvent:
    """Event indicating a distilled model has been deployed."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "MODEL_DEPLOYED"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    model_id: str = ""
    model_name: str = ""
    model_size: str = ""  # e.g., "3B", "7B", "20B"
    accuracy_vs_teacher: float = 0.0
    latency_ms: float = 0.0
    cost_per_request_usd: float = 0.0
    training_duration_hours: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
            },
            "data": {
                "model_id": self.model_id,
                "model_name": self.model_name,
                "model_size": self.model_size,
                "accuracy_vs_teacher": self.accuracy_vs_teacher,
                "latency_ms": self.latency_ms,
                "cost_per_request_usd": self.cost_per_request_usd,
                "training_duration_hours": self.training_duration_hours
            }
        }


@dataclass
class RetrainTriggeredEvent:
    """Event indicating model retraining has been triggered."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "RETRAIN_TRIGGERED"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    model_id: str = ""
    reason: str = ""  # "accuracy_drop", "drift_detected", "scheduled"
    current_accuracy: float = 0.0
    threshold_accuracy: float = 0.9
    drift_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
            },
            "data": {
                "model_id": self.model_id,
                "reason": self.reason,
                "current_accuracy": self.current_accuracy,
                "threshold_accuracy": self.threshold_accuracy,
                "drift_score": self.drift_score
            }
        }


class DecisionEventPublisher:
    """Publishes agent decision events to event store."""
    
    def __init__(self, event_store):
        self.event_store = event_store
        logger.info("DecisionEventPublisher initialized")
    
    async def publish_decision(self, event: AgentDecisionEvent) -> None:
        """Publish an agent decision event."""
        try:
            await self.event_store.append_event(event.to_dict())
            logger.debug(f"Published decision event: {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to publish decision event: {e}")
            raise
    
    async def publish_training_data_curated(self, event: TrainingDataCuratedEvent) -> None:
        """Publish a training data curated event."""
        try:
            await self.event_store.append_event(event.to_dict())
            logger.info(f"Published training data curated event: {event.dataset_id}")
        except Exception as e:
            logger.error(f"Failed to publish training data curated event: {e}")
            raise
    
    async def publish_prompts_optimized(self, event: PromptsOptimizedEvent) -> None:
        """Publish a prompts optimized event."""
        try:
            await self.event_store.append_event(event.to_dict())
            logger.info(f"Published prompts optimized event: iteration {event.iteration}")
        except Exception as e:
            logger.error(f"Failed to publish prompts optimized event: {e}")
            raise
    
    async def publish_model_deployed(self, event: ModelDeployedEvent) -> None:
        """Publish a model deployed event."""
        try:
            await self.event_store.append_event(event.to_dict())
            logger.info(f"Published model deployed event: {event.model_id}")
        except Exception as e:
            logger.error(f"Failed to publish model deployed event: {e}")
            raise
    
    async def publish_retrain_triggered(self, event: RetrainTriggeredEvent) -> None:
        """Publish a retrain triggered event."""
        try:
            await self.event_store.append_event(event.to_dict())
            logger.warning(f"Published retrain triggered event: {event.reason}")
        except Exception as e:
            logger.error(f"Failed to publish retrain triggered event: {e}")
            raise

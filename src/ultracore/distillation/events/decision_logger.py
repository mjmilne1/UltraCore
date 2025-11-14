"""Decision Logger for Agent Tool Calling"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4
import logging

from .decision_events import (
    AgentDecisionEvent,
    ToolInfo,
    DecisionOutcome,
    DecisionEventPublisher
)

logger = logging.getLogger(__name__)


class AgentDecisionLogger:
    """Logs agent tool calling decisions for distillation."""
    
    def __init__(self, event_publisher: DecisionEventPublisher):
        self.event_publisher = event_publisher
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("AgentDecisionLogger initialized")
    
    def start_session(self, agent_id: str, context: Dict[str, Any]) -> str:
        """Start a new decision session."""
        session_id = str(uuid4())
        self.active_sessions[session_id] = {
            "agent_id": agent_id,
            "context": context,
            "start_time": time.time(),
            "decisions": []
        }
        logger.debug(f"Started session {session_id} for agent {agent_id}")
        return session_id
    
    async def log_decision(
        self,
        session_id: str,
        tools_available: List[Dict[str, Any]],
        tool_selected: str,
        tool_parameters: Dict[str, Any],
        reasoning: str,
        confidence: float = 0.0,
        teacher_model: str = "gpt-4",
        teacher_confidence: float = 0.0,
        teacher_reasoning: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Log a tool selection decision."""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.active_sessions[session_id] = {
                "agent_id": "unknown",
                "context": {},
                "start_time": time.time(),
                "decisions": []
            }
        
        session = self.active_sessions[session_id]
        
        # Convert tools to ToolInfo objects
        tool_infos = [
            ToolInfo(
                name=t.get("name", ""),
                description=t.get("description", ""),
                parameters=t.get("parameters", {}),
                category=t.get("category")
            )
            for t in tools_available
        ]
        
        # Create decision event
        event = AgentDecisionEvent(
            aggregate_id=session["agent_id"],
            agent_id=session["agent_id"],
            session_id=session_id,
            context=session["context"],
            tools_available=tool_infos,
            tool_selected=tool_selected,
            tool_parameters=tool_parameters,
            reasoning=reasoning,
            confidence=confidence,
            teacher_model=teacher_model,
            teacher_confidence=teacher_confidence,
            teacher_reasoning=teacher_reasoning,
            user_id=user_id
        )
        
        # Store in session
        session["decisions"].append(event)
        
        logger.debug(
            f"Logged decision for session {session_id}: "
            f"selected {tool_selected} from {len(tools_available)} tools"
        )
        
        return event.event_id
    
    async def log_outcome(
        self,
        session_id: str,
        event_id: str,
        success: bool,
        execution_time_ms: float,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        cost_usd: Optional[float] = None
    ) -> None:
        """Log the outcome of a tool execution."""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        session = self.active_sessions[session_id]
        
        # Find the decision event
        decision_event = None
        for decision in session["decisions"]:
            if decision.event_id == event_id:
                decision_event = decision
                break
        
        if not decision_event:
            logger.warning(f"Decision event {event_id} not found in session {session_id}")
            return
        
        # Add outcome
        decision_event.outcome = DecisionOutcome(
            success=success,
            execution_time_ms=execution_time_ms,
            result=result,
            error=error,
            cost_usd=cost_usd
        )
        
        # Publish event
        await self.event_publisher.publish_decision(decision_event)
        
        logger.debug(
            f"Logged outcome for event {event_id}: "
            f"success={success}, time={execution_time_ms}ms"
        )
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a decision session and return summary."""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return {}
        
        session = self.active_sessions.pop(session_id)
        duration = time.time() - session["start_time"]
        
        summary = {
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "duration_seconds": duration,
            "decision_count": len(session["decisions"]),
            "successful_decisions": sum(
                1 for d in session["decisions"]
                if d.outcome and d.outcome.success
            ),
            "total_cost_usd": sum(
                d.outcome.cost_usd or 0
                for d in session["decisions"]
                if d.outcome
            )
        }
        
        logger.info(
            f"Ended session {session_id}: "
            f"{summary['decision_count']} decisions in {duration:.2f}s"
        )
        
        return summary
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an active session."""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        decisions = session["decisions"]
        
        return {
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "decision_count": len(decisions),
            "successful_decisions": sum(
                1 for d in decisions
                if d.outcome and d.outcome.success
            ),
            "average_confidence": (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0
            ),
            "average_execution_time_ms": (
                sum(d.outcome.execution_time_ms for d in decisions if d.outcome)
                / len([d for d in decisions if d.outcome])
                if any(d.outcome for d in decisions) else 0
            )
        }


class DecisionLoggerMixin:
    """Mixin to add decision logging to agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decision_logger: Optional[AgentDecisionLogger] = None
        self.current_session_id: Optional[str] = None
    
    def set_decision_logger(self, logger: AgentDecisionLogger) -> None:
        """Set the decision logger."""
        self.decision_logger = logger
    
    async def start_logging_session(self, context: Dict[str, Any]) -> str:
        """Start a new logging session."""
        if not self.decision_logger:
            logger.warning(f"No decision logger set for agent {self.agent_id}")
            return ""
        
        self.current_session_id = self.decision_logger.start_session(
            agent_id=self.agent_id,
            context=context
        )
        return self.current_session_id
    
    async def log_tool_decision(
        self,
        tools_available: List[Dict[str, Any]],
        tool_selected: str,
        tool_parameters: Dict[str, Any],
        reasoning: str,
        confidence: float = 0.0,
        teacher_model: str = "gpt-4",
        teacher_confidence: float = 0.0,
        teacher_reasoning: Optional[str] = None
    ) -> str:
        """Log a tool selection decision."""
        if not self.decision_logger or not self.current_session_id:
            logger.warning(f"No active logging session for agent {self.agent_id}")
            return ""
        
        return await self.decision_logger.log_decision(
            session_id=self.current_session_id,
            tools_available=tools_available,
            tool_selected=tool_selected,
            tool_parameters=tool_parameters,
            reasoning=reasoning,
            confidence=confidence,
            teacher_model=teacher_model,
            teacher_confidence=teacher_confidence,
            teacher_reasoning=teacher_reasoning
        )
    
    async def log_tool_outcome(
        self,
        event_id: str,
        success: bool,
        execution_time_ms: float,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        cost_usd: Optional[float] = None
    ) -> None:
        """Log the outcome of a tool execution."""
        if not self.decision_logger or not self.current_session_id:
            logger.warning(f"No active logging session for agent {self.agent_id}")
            return
        
        await self.decision_logger.log_outcome(
            session_id=self.current_session_id,
            event_id=event_id,
            success=success,
            execution_time_ms=execution_time_ms,
            result=result,
            error=error,
            cost_usd=cost_usd
        )
    
    async def end_logging_session(self) -> Dict[str, Any]:
        """End the current logging session."""
        if not self.decision_logger or not self.current_session_id:
            logger.warning(f"No active logging session for agent {self.agent_id}")
            return {}
        
        summary = self.decision_logger.end_session(self.current_session_id)
        self.current_session_id = None
        return summary

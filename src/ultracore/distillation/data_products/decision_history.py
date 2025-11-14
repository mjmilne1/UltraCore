"""Agent Decision History Data Product"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AgentDecisionHistoryProduct:
    """Data product for agent decision history."""
    
    def __init__(self, event_store, registry):
        self.event_store = event_store
        self.registry = registry
        self.product_id = "agent_decision_history"
        self.domain = "agentic_ai"
        self.owner = "ai_team"
        logger.info("AgentDecisionHistoryProduct initialized")
    
    async def register(self) -> None:
        """Register this data product with the registry."""
        metadata = {
            "product_id": self.product_id,
            "name": "Agent Decision History",
            "domain": self.domain,
            "owner": self.owner,
            "description": "Complete history of agent tool selection decisions",
            "schema": {
                "event_id": "string",
                "agent_id": "string",
                "session_id": "string",
                "timestamp": "datetime",
                "context": "object",
                "tools_available": "array",
                "tool_selected": "string",
                "tool_parameters": "object",
                "reasoning": "string",
                "confidence": "float",
                "teacher_model": "string",
                "teacher_confidence": "float",
                "outcome": "object"
            },
            "quality_metrics": {
                "completeness": 0.99,
                "accuracy": 0.95,
                "timeliness": "real-time",
                "consistency": 0.98,
                "uniqueness": 1.0
            },
            "refresh_frequency": "continuous",
            "sla": {
                "availability": 0.999,
                "latency_ms": 100,
                "freshness_seconds": 1
            },
            "lineage": {
                "upstream": ["event_store"],
                "downstream": ["distillation_training_data", "model_evaluation"]
            },
            "tags": ["agent", "decisions", "tool_calling", "distillation"]
        }
        
        await self.registry.register_product(self.product_id, metadata)
        logger.info(f"Registered data product: {self.product_id}")
    
    async def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query agent decision history."""
        
        # Build event query
        event_type = "AGENT_TOOL_SELECTED"
        
        # Get events from event store
        events = await self.event_store.get_events_by_type(
            event_type,
            limit=limit,
            offset=offset
        )
        
        # Apply filters
        if filters:
            events = self._apply_filters(events, filters)
        
        # Transform to data product format
        decisions = [self._transform_event(e) for e in events]
        
        logger.debug(f"Queried {len(decisions)} decisions")
        return decisions
    
    def _apply_filters(
        self,
        events: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to events."""
        filtered = events
        
        # Agent ID filter
        if "agent_id" in filters:
            agent_id = filters["agent_id"]
            filtered = [
                e for e in filtered
                if e.get("data", {}).get("agent_id") == agent_id
            ]
        
        # Timestamp filter
        if "timestamp" in filters:
            ts_filter = filters["timestamp"]
            if "gte" in ts_filter:
                gte = datetime.fromisoformat(ts_filter["gte"])
                filtered = [
                    e for e in filtered
                    if datetime.fromisoformat(e["metadata"]["timestamp"]) >= gte
                ]
            if "lte" in ts_filter:
                lte = datetime.fromisoformat(ts_filter["lte"])
                filtered = [
                    e for e in filtered
                    if datetime.fromisoformat(e["metadata"]["timestamp"]) <= lte
                ]
        
        # Success filter
        if "success" in filters:
            success = filters["success"]
            filtered = [
                e for e in filtered
                if e.get("data", {}).get("outcome", {}).get("success") == success
            ]
        
        return filtered
    
    def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Transform event to data product format."""
        metadata = event.get("metadata", {})
        data = event.get("data", {})
        
        return {
            "event_id": metadata.get("event_id"),
            "agent_id": data.get("agent_id"),
            "session_id": data.get("session_id"),
            "timestamp": metadata.get("timestamp"),
            "context": data.get("context", {}),
            "tools_available": data.get("tools_available", []),
            "tool_selected": data.get("tool_selected"),
            "tool_parameters": data.get("tool_parameters", {}),
            "reasoning": data.get("reasoning"),
            "confidence": data.get("confidence", 0.0),
            "teacher_model": data.get("teacher_model"),
            "teacher_confidence": data.get("teacher_confidence", 0.0),
            "teacher_reasoning": data.get("teacher_reasoning"),
            "outcome": data.get("outcome")
        }
    
    async def get_statistics(
        self,
        agent_id: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get statistics for decision history."""
        
        # Query recent decisions
        start_time = (datetime.utcnow() - timedelta(hours=time_window_hours)).isoformat()
        filters = {"timestamp": {"gte": start_time}}
        if agent_id:
            filters["agent_id"] = agent_id
        
        decisions = await self.query(filters=filters, limit=10000)
        
        if not decisions:
            return {
                "total_decisions": 0,
                "time_window_hours": time_window_hours
            }
        
        # Calculate statistics
        successful = [d for d in decisions if d.get("outcome", {}).get("success")]
        
        total_time = sum(
            d.get("outcome", {}).get("execution_time_ms", 0)
            for d in decisions
            if d.get("outcome")
        )
        
        total_cost = sum(
            d.get("outcome", {}).get("cost_usd", 0)
            for d in decisions
            if d.get("outcome")
        )
        
        return {
            "total_decisions": len(decisions),
            "successful_decisions": len(successful),
            "success_rate": len(successful) / len(decisions) if decisions else 0,
            "average_confidence": (
                sum(d.get("confidence", 0) for d in decisions) / len(decisions)
            ),
            "average_execution_time_ms": (
                total_time / len(decisions) if decisions else 0
            ),
            "total_cost_usd": total_cost,
            "average_cost_per_decision_usd": (
                total_cost / len(decisions) if decisions else 0
            ),
            "unique_agents": len(set(d.get("agent_id") for d in decisions)),
            "unique_tools": len(set(d.get("tool_selected") for d in decisions)),
            "time_window_hours": time_window_hours
        }
    
    async def get_quality_metrics(self) -> Dict[str, float]:
        """Get quality metrics for this data product."""
        
        # Query recent decisions
        decisions = await self.query(limit=1000)
        
        if not decisions:
            return {
                "completeness": 0.0,
                "accuracy": 0.0,
                "timeliness": 0.0,
                "consistency": 0.0,
                "uniqueness": 0.0
            }
        
        # Completeness: % of decisions with all required fields
        complete = sum(
            1 for d in decisions
            if all(k in d for k in [
                "event_id", "agent_id", "tool_selected", "outcome"
            ])
        )
        completeness = complete / len(decisions)
        
        # Accuracy: % of successful decisions
        successful = sum(
            1 for d in decisions
            if d.get("outcome", {}).get("success")
        )
        accuracy = successful / len(decisions)
        
        # Timeliness: % of decisions within 1 second of now
        now = datetime.utcnow()
        recent = sum(
            1 for d in decisions
            if (now - datetime.fromisoformat(d["timestamp"])).total_seconds() < 1
        )
        timeliness = recent / len(decisions)
        
        # Consistency: % of decisions with teacher confidence > 0.8
        consistent = sum(
            1 for d in decisions
            if d.get("teacher_confidence", 0) > 0.8
        )
        consistency = consistent / len(decisions)
        
        # Uniqueness: % of unique events
        unique_ids = len(set(d["event_id"] for d in decisions))
        uniqueness = unique_ids / len(decisions)
        
        return {
            "completeness": completeness,
            "accuracy": accuracy,
            "timeliness": timeliness,
            "consistency": consistency,
            "uniqueness": uniqueness
        }

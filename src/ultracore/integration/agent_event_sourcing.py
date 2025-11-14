"""Agent-Driven Event Sourcing"""
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EventSourcingAgent:
    """Agent that publishes events for actions."""
    
    def __init__(self, agent, event_store):
        self.agent = agent
        self.event_store = event_store
        logger.info(f"EventSourcingAgent wrapping {agent.agent_id}")
    
    async def act(self, action):
        """Execute action and publish event."""
        result = await self.agent.act(action)
        
        event = {
            "metadata": {
                "event_id": str(uuid4()),
                "event_type": "AGENT_ACTION_EXECUTED",
                "aggregate_id": self.agent.agent_id,
                "aggregate_type": "Agent",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "data": {
                "agent_id": self.agent.agent_id,
                "action_type": action.action_type,
                "parameters": action.parameters,
                "result": result
            }
        }
        
        await self.event_store.append_event(event)
        logger.debug(f"Published event for agent action: {action.action_type}")
        
        return result

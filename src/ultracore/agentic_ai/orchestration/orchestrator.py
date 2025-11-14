"""
Agent Orchestrator.

Coordinates multiple agents to accomplish complex tasks.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import Agent, AgentMessage, AgentCommunicationProtocol


logger = logging.getLogger(__name__)


class SimpleMessageBus(AgentCommunicationProtocol):
    """Simple in-memory message bus for agent communication."""
    
    def __init__(self):
        self.messages: Dict[str, List[AgentMessage]] = {}
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send message to another agent."""
        if message.to_agent not in self.messages:
            self.messages[message.to_agent] = []
        
        self.messages[message.to_agent].append(message)
        logger.debug(f"Message sent from {message.from_agent} to {message.to_agent}")
        return True
    
    async def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """Receive messages for an agent."""
        messages = self.messages.get(agent_id, [])
        self.messages[agent_id] = []  # Clear after receiving
        return messages


class AgentOrchestrator:
    """
    Agent orchestrator.
    
    Coordinates multiple agents to accomplish complex tasks.
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_bus = SimpleMessageBus()
        self.task_history: List[Dict[str, Any]] = []
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Agent]:
        """List all registered agents."""
        return list(self.agents.values())
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> Any:
        """
        Execute a task using appropriate agent(s).
        
        Args:
            task: Task to execute
            agent_id: Optional specific agent ID
            
        Returns:
            Task result
        """
        task_id = task.get("task_id", f"task_{datetime.utcnow().timestamp()}")
        
        logger.info(f"Executing task {task_id}")
        
        # Record task start
        task_record = {
            "task_id": task_id,
            "task": task,
            "started_at": datetime.utcnow(),
            "agent_id": agent_id,
        }
        
        try:
            if agent_id:
                # Execute with specific agent
                agent = self.get_agent(agent_id)
                if not agent:
                    raise ValueError(f"Agent {agent_id} not found")
                
                result = await agent.run(task)
            else:
                # Select appropriate agent based on task
                agent = self._select_agent(task)
                if not agent:
                    raise ValueError("No suitable agent found for task")
                
                result = await agent.run(task)
            
            # Record task completion
            task_record["completed_at"] = datetime.utcnow()
            task_record["result"] = result
            task_record["status"] = "success"
            
            self.task_history.append(task_record)
            
            logger.info(f"Task {task_id} completed successfully")
            
            return result
            
        except Exception as e:
            # Record task failure
            task_record["completed_at"] = datetime.utcnow()
            task_record["error"] = str(e)
            task_record["status"] = "failed"
            
            self.task_history.append(task_record)
            
            logger.error(f"Task {task_id} failed: {e}")
            raise e
    
    def _select_agent(self, task: Dict[str, Any]) -> Optional[Agent]:
        """
        Select appropriate agent for task.
        
        Args:
            task: Task to execute
            
        Returns:
            Selected agent or None
        """
        required_capability = task.get("required_capability")
        
        if not required_capability:
            # Return first available agent
            return list(self.agents.values())[0] if self.agents else None
        
        # Find agent with required capability
        for agent in self.agents.values():
            if agent.has_capability(required_capability):
                return agent
        
        return None
    
    async def execute_multi_agent_task(
        self,
        task: Dict[str, Any],
        agent_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a task using multiple agents in collaboration.
        
        Args:
            task: Task to execute
            agent_ids: List of agent IDs to collaborate
            
        Returns:
            Combined results from all agents
        """
        logger.info(f"Executing multi-agent task with {len(agent_ids)} agents")
        
        results = {}
        
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if not agent:
                logger.warning(f"Agent {agent_id} not found, skipping")
                continue
            
            try:
                result = await agent.run(task)
                results[agent_id] = result
            except Exception as e:
                logger.error(f"Agent {agent_id} failed: {e}")
                results[agent_id] = {"error": str(e)}
        
        return results
    
    async def send_agent_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        content: Dict[str, Any]
    ) -> bool:
        """
        Send message from one agent to another.
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            content: Message content
            
        Returns:
            True if successful
        """
        message = AgentMessage(
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            content=content
        )
        
        return await self.message_bus.send_message(message)
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history."""
        return self.task_history[-limit:]
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about agents and tasks."""
        total_tasks = len(self.task_history)
        successful_tasks = len([t for t in self.task_history if t.get("status") == "success"])
        failed_tasks = len([t for t in self.task_history if t.get("status") == "failed"])
        
        return {
            "total_agents": len(self.agents),
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
        }


# Global orchestrator instance
orchestrator = AgentOrchestrator()

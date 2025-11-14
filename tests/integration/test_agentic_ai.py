"""
Integration tests for Agentic AI.

Tests agents, orchestration, and multi-agent collaboration.
"""

import pytest
from ultracore.agentic_ai import (
    Agent,
    AgentAction,
    AgentCapability,
    AgentState,
    AgentOrchestrator,
    orchestrator,
)
from ultracore.agentic_ai.agents.customer_agent import CustomerAgent


class TestAgentBasics:
    """Test basic agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_perception(self):
        """Test agent perception."""
        agent = CustomerAgent()
        
        context = {
            "customer_id": "CUST001",
            "customer_data": {"name": "John Doe"},
            "interaction_history": [],
        }
        
        perceived_state = await agent.perceive(context)
        
        assert perceived_state is not None
        assert "customer_id" in perceived_state
    
    @pytest.mark.asyncio
    async def test_agent_decision(self):
        """Test agent decision making."""
        agent = CustomerAgent()
        
        perceived_state = {
            "customer_id": "CUST001",
            "needs": ["support"],
            "sentiment": "neutral",
        }
        
        action = await agent.decide(perceived_state)
        
        assert isinstance(action, AgentAction)
        assert action.action_type is not None
    
    @pytest.mark.asyncio
    async def test_agent_action(self):
        """Test agent action execution."""
        agent = CustomerAgent()
        
        action = AgentAction(
            action_type="provide_support",
            parameters={"customer_id": "CUST001"}
        )
        
        result = await agent.act(action)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_agent_run_loop(self):
        """Test complete agent run loop."""
        agent = CustomerAgent()
        
        context = {
            "customer_id": "CUST001",
            "customer_data": {"name": "John Doe"},
            "support_request": True,
        }
        
        result = await agent.run(context)
        
        assert result is not None
        assert agent.state == AgentState.IDLE


class TestAgentMemory:
    """Test agent memory system."""
    
    def test_short_term_memory(self):
        """Test short-term memory."""
        agent = CustomerAgent()
        
        agent.memory.remember("last_action", "provide_support", "short_term")
        
        # Short-term memory stores in list
        assert len(agent.memory.short_term) == 1
    
    def test_long_term_memory(self):
        """Test long-term memory."""
        agent = CustomerAgent()
        
        agent.memory.remember("customer_preference", "email", "long_term")
        
        recalled = agent.memory.recall("customer_preference", "long_term")
        
        assert recalled == "email"
    
    def test_working_memory(self):
        """Test working memory."""
        agent = CustomerAgent()
        
        agent.memory.remember("current_task", "onboarding", "working")
        
        recalled = agent.memory.recall("current_task", "working")
        
        assert recalled == "onboarding"
    
    def test_memory_capacity(self):
        """Test short-term memory capacity limit."""
        agent = CustomerAgent()
        
        # Add more than 100 items
        for i in range(150):
            agent.memory.remember(f"action_{i}", f"value_{i}", "short_term")
        
        # Should keep only last 100
        assert len(agent.memory.short_term) == 100


class TestAgentCapabilities:
    """Test agent capabilities."""
    
    def test_has_capability(self):
        """Test capability checking."""
        agent = CustomerAgent()
        
        assert agent.has_capability(AgentCapability.CUSTOMER_SUPPORT)
        assert agent.has_capability(AgentCapability.DATA_ANALYSIS)
        assert not agent.has_capability(AgentCapability.LOAN_UNDERWRITING)
    
    def test_capability_based_routing(self):
        """Test routing tasks based on capabilities."""
        agent = CustomerAgent()
        
        # Agent should handle customer support tasks
        can_handle = agent.has_capability(AgentCapability.CUSTOMER_SUPPORT)
        
        assert can_handle is True


class TestAgentOrchestrator:
    """Test agent orchestrator."""
    
    def test_register_agent(self):
        """Test agent registration."""
        orch = AgentOrchestrator()
        agent = CustomerAgent()
        
        orch.register_agent(agent)
        
        assert orch.get_agent("customer_agent") is not None
        assert len(orch.list_agents()) == 1
    
    def test_list_agents(self):
        """Test listing agents."""
        orch = AgentOrchestrator()
        
        orch.register_agent(CustomerAgent())
        
        agents = orch.list_agents()
        
        assert len(agents) == 1
        assert agents[0].name == "Customer Agent"
    
    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test task execution."""
        orch = AgentOrchestrator()
        agent = CustomerAgent()
        orch.register_agent(agent)
        
        task = {
            "task_id": "task_001",
            "customer_id": "CUST001",
            "support_request": True,
        }
        
        result = await orch.execute_task(task, agent_id="customer_agent")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_task_history(self):
        """Test task history tracking."""
        orch = AgentOrchestrator()
        agent = CustomerAgent()
        orch.register_agent(agent)
        
        task = {
            "task_id": "task_001",
            "customer_id": "CUST001",
        }
        
        await orch.execute_task(task, agent_id="customer_agent")
        
        history = orch.get_task_history()
        
        assert len(history) > 0
        assert history[0]["task_id"] == "task_001"
    
    def test_agent_statistics(self):
        """Test agent statistics."""
        orch = AgentOrchestrator()
        orch.register_agent(CustomerAgent())
        
        stats = orch.get_agent_statistics()
        
        assert stats["total_agents"] == 1
        assert "total_tasks" in stats
        assert "success_rate" in stats


class TestMultiAgentCollaboration:
    """Test multi-agent collaboration."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_task(self):
        """Test multi-agent task execution."""
        orch = AgentOrchestrator()
        
        # Register multiple agents
        orch.register_agent(CustomerAgent())
        
        task = {
            "task_id": "task_001",
            "customer_id": "CUST001",
            "complex_request": True,
        }
        
        results = await orch.execute_multi_agent_task(
            task,
            agent_ids=["customer_agent"]
        )
        
        assert len(results) == 1
        assert "customer_agent" in results
    
    @pytest.mark.asyncio
    async def test_agent_message_passing(self):
        """Test agent-to-agent messaging."""
        orch = AgentOrchestrator()
        
        orch.register_agent(CustomerAgent())
        
        # Send message
        result = await orch.send_agent_message(
            from_agent_id="customer_agent",
            to_agent_id="customer_agent",
            content={"message": "test"}
        )
        
        assert result is True


class TestAgentActionHistory:
    """Test agent action history."""
    
    @pytest.mark.asyncio
    async def test_action_recording(self):
        """Test action history recording."""
        agent = CustomerAgent()
        
        context = {
            "customer_id": "CUST001",
            "support_request": True,
        }
        
        await agent.run(context)
        
        history = agent.get_action_history()
        
        assert len(history) > 0
    
    @pytest.mark.asyncio
    async def test_action_history_limit(self):
        """Test action history limit."""
        agent = CustomerAgent()
        
        # Execute multiple tasks
        for i in range(15):
            context = {"customer_id": f"CUST{i:03d}"}
            await agent.run(context)
        
        # Get last 10
        history = agent.get_action_history(limit=10)
        
        assert len(history) == 10


class TestAgentErrorHandling:
    """Test agent error handling."""
    
    @pytest.mark.asyncio
    async def test_agent_error_state(self):
        """Test agent error state."""
        agent = CustomerAgent()
        
        # Provide invalid context to trigger error
        context = None
        
        with pytest.raises(Exception):
            await agent.run(context)
        
        # Agent should be in error state
        assert agent.state == AgentState.ERROR


class TestAgentIntegration:
    """Test agent integration with other systems."""
    
    @pytest.mark.asyncio
    async def test_agent_with_data_mesh(self):
        """Test agent integration with Data Mesh."""
        agent = CustomerAgent()
        
        # Agent queries customer data from Data Mesh
        context = {
            "customer_id": "CUST001",
            "query_data_mesh": True,
        }
        
        result = await agent.run(context)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_agent_with_event_sourcing(self):
        """Test agent integration with Event Sourcing."""
        agent = CustomerAgent()
        
        # Agent publishes events
        context = {
            "customer_id": "CUST001",
            "action": "create_customer",
        }
        
        result = await agent.run(context)
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

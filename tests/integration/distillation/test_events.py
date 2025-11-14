"""Tests for Distillation Event System"""
import pytest
from ultracore.distillation.events import (
    AgentDecisionEvent,
    AgentDecisionLogger,
    DecisionLoggerMixin
)


@pytest.mark.asyncio
async def test_decision_event_creation():
    """Test creating agent decision events."""
    event = AgentDecisionEvent(
        agent_id="test_agent",
        context={"customer_id": "123"},
        tools_available=[{"name": "check_balance"}],
        tool_selected="check_balance",
        reasoning="Customer requested balance",
        confidence=0.95
    )
    
    assert event.agent_id == "test_agent"
    assert event.tool_selected == "check_balance"
    assert event.confidence == 0.95


@pytest.mark.asyncio
async def test_decision_logger():
    """Test decision logging."""
    logger = AgentDecisionLogger()
    
    await logger.log_decision(
        agent_id="test_agent",
        context={},
        tools_available=[],
        tool_selected="test_tool",
        reasoning="test",
        confidence=0.9
    )
    
    history = logger.get_history()
    assert len(history) == 1
    assert history[0]["tool_selected"] == "test_tool"


@pytest.mark.asyncio
async def test_decision_logger_mixin():
    """Test mixin integration."""
    class TestAgent(DecisionLoggerMixin):
        def __init__(self):
            super().__init__()
            self.agent_id = "test"
    
    agent = TestAgent()
    
    await agent.log_decision(
        context={},
        tools_available=[],
        tool_selected="test",
        reasoning="test"
    )
    
    assert len(agent.decision_logger.get_history()) == 1

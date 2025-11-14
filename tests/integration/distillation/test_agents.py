"""Tests for Distillation Agents"""
import pytest
from ultracore.distillation.agents import (
    DataCuratorAgent,
    ModelTrainerAgent,
    EvaluationAgent
)


@pytest.mark.asyncio
async def test_data_curator_agent():
    """Test data curator agent."""
    agent = DataCuratorAgent()
    
    context = {
        "raw_decisions": [
            {"context": {}, "tool_selected": "test1"},
            {"context": {}, "tool_selected": "test2"},
        ] * 10  # 20 decisions
    }
    
    perception = await agent.perceive(context)
    decision = await agent.decide(perception)
    result = await agent.act(decision)
    
    assert result["status"] == "curated"
    assert "curated_data" in result


@pytest.mark.asyncio
async def test_model_trainer_agent():
    """Test model trainer agent."""
    agent = ModelTrainerAgent()
    
    context = {
        "training_data": [{"example": i} for i in range(150)],
        "teacher_model": "gpt-4"
    }
    
    perception = await agent.perceive(context)
    decision = await agent.decide(perception)
    result = await agent.act(decision)
    
    assert result["status"] in ["deployed", "retraining"]


@pytest.mark.asyncio
async def test_evaluation_agent():
    """Test evaluation agent."""
    agent = EvaluationAgent()
    
    context = {
        "recent_decisions": [
            {"outcome": {"success": True, "execution_time_ms": 100}}
            for _ in range(50)
        ]
    }
    
    perception = await agent.perceive(context)
    decision = await agent.decide(perception)
    result = await agent.act(decision)
    
    assert "metrics" in result
    assert result["metrics"]["accuracy"] > 0.9

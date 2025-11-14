"""Tests for Prompt Optimization (DSPy + GEPA)"""
import pytest
from ultracore.distillation.optimization import (
    DSPyOptimizer,
    GEPAOptimizer,
    CombinedOptimizer
)


async def mock_evaluation(prompt: str, examples: list) -> float:
    """Mock evaluation function."""
    # Simple mock: longer prompts score higher
    return min(len(prompt) / 1000, 1.0)


@pytest.mark.asyncio
async def test_dspy_optimization():
    """Test DSPy optimizer."""
    optimizer = DSPyOptimizer()
    
    initial_prompt = "Select the best tool."
    examples = [
        {"context": {}, "tool_selected": "test", "reasoning": "test"}
    ]
    
    result = await optimizer.optimize(
        initial_prompt,
        examples,
        mock_evaluation,
        iterations=2
    )
    
    assert "optimized_prompt" in result
    assert result["final_score"] >= result["initial_score"]


@pytest.mark.asyncio
async def test_gepa_optimization():
    """Test GEPA optimizer."""
    optimizer = GEPAOptimizer()
    
    initial_prompt = "Select the best tool."
    examples = [
        {"context": {}, "tool_selected": "test", "reasoning": "test"}
    ]
    
    result = await optimizer.optimize(
        initial_prompt,
        examples,
        mock_evaluation,
        generations=2
    )
    
    assert "optimized_prompt" in result
    assert result["final_score"] >= result["initial_score"]


@pytest.mark.asyncio
async def test_combined_optimization():
    """Test combined DSPy + GEPA."""
    optimizer = CombinedOptimizer()
    
    initial_prompt = "Select the best tool."
    examples = [
        {"context": {}, "tool_selected": "test", "reasoning": "test"}
    ]
    
    result = await optimizer.optimize(
        initial_prompt,
        examples,
        mock_evaluation
    )
    
    assert "optimized_prompt" in result
    assert "dspy_score" in result
    assert "final_score" in result

"""Tests for Execution Optimizer Agent"""
import pytest
from ultracore.agents.execution_optimizer.execution_optimizer_agent import ExecutionOptimizerAgent

@pytest.mark.asyncio
async def test_optimize_execution_strategy():
    """Test execution strategy optimization"""
    agent = ExecutionOptimizerAgent(llm_client=None)
    
    order = {
        "symbol": "CBA.AX",
        "quantity": 10000,
        "order_type": "limit",
        "side": "buy",
        "limit_price": 95.50
    }
    
    market_conditions = {
        "current_price": 95.45,
        "spread": 0.05,
        "volume": 1500000,
        "volatility": 0.15,
        "avg_daily_volume": 2000000
    }
    
    strategy = await agent.optimize_execution_strategy(order, market_conditions)
    
    assert "strategy" in strategy
    assert "confidence" in strategy
    assert strategy["confidence"] > 0.8

@pytest.mark.asyncio
async def test_select_optimal_venue():
    """Test venue selection"""
    agent = ExecutionOptimizerAgent(llm_client=None)
    
    result = await agent.select_optimal_venue(
        symbol="BHP.AX",
        order_side="buy",
        quantity=5000
    )
    
    assert "primary_venue" in result
    assert result["primary_venue"] in ["ASX", "Chi-X"]

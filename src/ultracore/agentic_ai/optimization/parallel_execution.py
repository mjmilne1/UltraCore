"""Parallel Agent Execution"""
import asyncio
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ParallelAgentExecutor:
    """Execute multiple agents in parallel."""
    
    async def execute_parallel(self, agents: List, context: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Execute agents in parallel with timeout."""
        logger.info(f"Executing {len(agents)} agents in parallel")
        
        tasks = [asyncio.create_task(agent.run(context)) for agent in agents]
        
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Parallel execution timed out after {timeout}s")
            for task in tasks:
                task.cancel()
            results = [{"error": "timeout"} for _ in agents]
        
        aggregated = {}
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                aggregated[agent.agent_id] = {"error": str(result)}
            else:
                aggregated[agent.agent_id] = result
        
        return aggregated

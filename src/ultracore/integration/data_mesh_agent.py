"""Data Mesh-Powered Agents"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataMeshAgent:
    """Agent that uses data mesh for context."""
    
    def __init__(self, agent, registry):
        self.agent = agent
        self.registry = registry
        self.product_cache = {}
        logger.info(f"DataMeshAgent wrapping {agent.agent_id}")
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive with data mesh context."""
        customer_id = context.get("customer_id")
        
        customer_data = await self._query_product("customer_360", {"customer_id": customer_id})
        account_data = await self._query_product("account_balances", {"customer_id": customer_id})
        
        return {
            **context,
            "customer": customer_data,
            "accounts": account_data
        }
    
    async def _query_product(self, product_id: str, filters: dict):
        """Query data product with caching."""
        cache_key = f"{product_id}:{hash(str(filters))}"
        
        if cache_key in self.product_cache:
            return self.product_cache[cache_key]
        
        result = await self.registry.query_product(product_id, filters)
        self.product_cache[cache_key] = result
        
        return result

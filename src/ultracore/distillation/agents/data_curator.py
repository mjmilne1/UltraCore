"""Data Curator Agent for Training Data"""
from typing import Dict, List, Any
import logging
from ...agentic_ai.base import Agent
from ..optimization import SemDeDup, CaR

logger = logging.getLogger(__name__)


class DataCuratorAgent(Agent):
    """Agent that curates training data using SemDeDup + CaR."""
    
    def __init__(self, agent_id: str = "data_curator"):
        super().__init__(agent_id)
        self.capabilities = [
            "semantic_deduplication",
            "clustering",
            "representative_selection",
            "quality_assessment"
        ]
        self.semdedup = SemDeDup(similarity_threshold=0.95)
        self.car = CaR(n_clusters=10, examples_per_cluster=5)
        logger.info("DataCuratorAgent initialized")
    
    async def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive raw decision data."""
        raw_decisions = context.get("raw_decisions", [])
        return {"raw_decisions": raw_decisions}
    
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Decide how to curate the data."""
        raw_decisions = perception["raw_decisions"]
        
        if len(raw_decisions) < 10:
            return {
                "action": "skip",
                "reason": "insufficient_data"
            }
        
        return {
            "action": "curate",
            "data": raw_decisions
        }
    
    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data curation."""
        if decision["action"] == "skip":
            logger.info("Skipping curation: insufficient data")
            return {"status": "skipped"}
        
        raw_data = decision["data"]
        
        # Apply SemDeDup
        deduplicated, dedup_stats = await self.semdedup.deduplicate(raw_data)
        logger.info(f"Deduplication: {dedup_stats['reduction_rate']:.1%} reduction")
        
        # Apply CaR (need embeddings)
        # For now, just return deduplicated data
        curated = deduplicated
        
        return {
            "status": "curated",
            "curated_data": curated,
            "stats": {
                "original_count": len(raw_data),
                "curated_count": len(curated),
                "deduplication_rate": dedup_stats["reduction_rate"]
            }
        }

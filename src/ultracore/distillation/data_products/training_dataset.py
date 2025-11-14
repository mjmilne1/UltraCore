"""Curated Training Dataset Data Product"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DistillationTrainingDataProduct:
    """Data product for curated training data."""
    
    def __init__(self, registry):
        self.registry = registry
        self.product_id = "distillation_training_data"
        self.domain = "ml_training"
        self.owner = "ml_team"
        self.current_dataset: List[Dict[str, Any]] = []
        self.dataset_version = 0
        logger.info("DistillationTrainingDataProduct initialized")
    
    async def register(self) -> None:
        """Register this data product."""
        metadata = {
            "product_id": self.product_id,
            "name": "Distillation Training Data",
            "domain": self.domain,
            "owner": self.owner,
            "description": "SemDeDup + CaR curated agent decisions for distillation",
            "schema": {
                "example_id": "string",
                "agent_id": "string",
                "context": "object",
                "tools_available": "array",
                "tool_selected": "string",
                "reasoning": "string",
                "teacher_confidence": "float",
                "cluster_id": "integer",
                "representativeness_score": "float"
            },
            "quality_metrics": {
                "deduplication_rate": 0.50,
                "cluster_quality": 0.85,
                "diversity_score": 0.78,
                "representativeness": 0.90
            },
            "refresh_frequency": "daily",
            "lineage": {
                "upstream": ["agent_decision_history"],
                "downstream": ["model_training", "prompt_optimization"]
            }
        }
        
        await self.registry.register_product(self.product_id, metadata)
        logger.info(f"Registered data product: {self.product_id}")
    
    async def publish(self, dataset: List[Dict[str, Any]]) -> None:
        """Publish a new curated dataset."""
        self.current_dataset = dataset
        self.dataset_version += 1
        logger.info(
            f"Published dataset version {self.dataset_version} "
            f"with {len(dataset)} examples"
        )
    
    async def query(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the training dataset."""
        if not filters:
            return self.current_dataset
        
        # Apply filters
        filtered = self.current_dataset
        
        if "agent_id" in filters:
            filtered = [d for d in filtered if d["agent_id"] == filters["agent_id"]]
        
        if "cluster_id" in filters:
            filtered = [d for d in filtered if d["cluster_id"] == filters["cluster_id"]]
        
        return filtered
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self.current_dataset:
            return {"example_count": 0}
        
        return {
            "example_count": len(self.current_dataset),
            "dataset_version": self.dataset_version,
            "unique_agents": len(set(d["agent_id"] for d in self.current_dataset)),
            "unique_tools": len(set(d["tool_selected"] for d in self.current_dataset)),
            "unique_clusters": len(set(d["cluster_id"] for d in self.current_dataset)),
            "average_representativeness": (
                sum(d["representativeness_score"] for d in self.current_dataset)
                / len(self.current_dataset)
            ),
            "average_teacher_confidence": (
                sum(d["teacher_confidence"] for d in self.current_dataset)
                / len(self.current_dataset)
            )
        }

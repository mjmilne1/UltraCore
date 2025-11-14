"""Model Performance Metrics Data Product"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DistilledModelMetricsProduct:
    """Data product for distilled model performance metrics."""
    
    def __init__(self, registry):
        self.registry = registry
        self.product_id = "distilled_model_metrics"
        self.domain = "ml_ops"
        self.owner = "ml_team"
        self.metrics_history: List[Dict[str, Any]] = []
        logger.info("DistilledModelMetricsProduct initialized")
    
    async def register(self) -> None:
        """Register this data product."""
        metadata = {
            "product_id": self.product_id,
            "name": "Distilled Model Metrics",
            "domain": self.domain,
            "owner": self.owner,
            "description": "Performance metrics for distilled models",
            "schema": {
                "model_id": "string",
                "timestamp": "datetime",
                "accuracy_vs_teacher": "float",
                "latency_ms": "float",
                "throughput_rps": "float",
                "cost_per_request_usd": "float",
                "cost_reduction": "float",
                "consistency_score": "float"
            },
            "quality_metrics": {
                "accuracy_vs_teacher": 0.93,
                "latency_improvement": 5.0,
                "cost_reduction": 0.90
            },
            "refresh_frequency": "hourly",
            "lineage": {
                "upstream": ["model_training", "benchmarks"],
                "downstream": ["agent_deployment", "optimization_feedback"]
            }
        }
        
        await self.registry.register_product(self.product_id, metadata)
        logger.info(f"Registered data product: {self.product_id}")
    
    async def publish(self, metrics: Dict[str, Any]) -> None:
        """Publish new metrics."""
        metrics["timestamp"] = datetime.utcnow().isoformat()
        self.metrics_history.append(metrics)
        logger.info(f"Published metrics for model {metrics['model_id']}")
    
    async def query(
        self,
        model_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query metrics history."""
        metrics = self.metrics_history[-limit:]
        
        if model_id:
            metrics = [m for m in metrics if m["model_id"] == model_id]
        
        return metrics
    
    async def get_latest(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get latest metrics for a model."""
        model_metrics = [m for m in self.metrics_history if m["model_id"] == model_id]
        return model_metrics[-1] if model_metrics else None

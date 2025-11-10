"""
ML Model Registry
Version control, A/B testing, model lifecycle management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json


class ModelStatus(str, Enum):
    DEVELOPMENT = 'DEVELOPMENT'
    STAGING = 'STAGING'
    PRODUCTION = 'PRODUCTION'
    DEPRECATED = 'DEPRECATED'
    ARCHIVED = 'ARCHIVED'


class ModelVersion:
    """Model version with metadata"""
    
    def __init__(
        self,
        model_id: str,
        version: str,
        model_type: str
    ):
        self.model_id = model_id
        self.version = version
        self.model_type = model_type
        self.status: ModelStatus = ModelStatus.DEVELOPMENT
        self.metrics: Dict[str, float] = {}
        self.created_at: str = datetime.utcnow().isoformat()
        self.deployed_at: Optional[str] = None
        self.traffic_percentage: float = 0.0
    
    def set_metrics(self, metrics: Dict[str, float]):
        """Set model performance metrics"""
        self.metrics = metrics
    
    def promote_to_staging(self):
        """Promote model to staging"""
        self.status = ModelStatus.STAGING
    
    def promote_to_production(self, traffic_percentage: float = 100.0):
        """Promote model to production with traffic split"""
        self.status = ModelStatus.PRODUCTION
        self.traffic_percentage = traffic_percentage
        self.deployed_at = datetime.utcnow().isoformat()
    
    def deprecate(self):
        """Deprecate model"""
        self.status = ModelStatus.DEPRECATED
        self.traffic_percentage = 0.0


class ModelRegistry:
    """
    ML Model Registry
    
    Manages model versions, A/B testing, rollbacks
    """
    
    def __init__(self):
        self.models: Dict[str, List[ModelVersion]] = {}
    
    def register_model(
        self,
        model_id: str,
        version: str,
        model_type: str,
        metrics: Optional[Dict[str, float]] = None
    ) -> ModelVersion:
        """Register new model version"""
        
        model_version = ModelVersion(model_id, version, model_type)
        
        if metrics:
            model_version.set_metrics(metrics)
        
        if model_id not in self.models:
            self.models[model_id] = []
        
        self.models[model_id].append(model_version)
        
        return model_version
    
    def get_production_model(self, model_id: str) -> Optional[ModelVersion]:
        """Get current production model"""
        if model_id not in self.models:
            return None
        
        production_models = [
            m for m in self.models[model_id]
            if m.status == ModelStatus.PRODUCTION
        ]
        
        if not production_models:
            return None
        
        # Return model with highest traffic
        return max(production_models, key=lambda m: m.traffic_percentage)
    
    def ab_test(
        self,
        model_id: str,
        champion_version: str,
        challenger_version: str,
        challenger_traffic: float = 10.0
    ):
        """
        A/B test two model versions
        
        Champion gets (100 - challenger_traffic)%
        Challenger gets challenger_traffic%
        """
        
        models = self.models.get(model_id, [])
        
        champion = next((m for m in models if m.version == champion_version), None)
        challenger = next((m for m in models if m.version == challenger_version), None)
        
        if not champion or not challenger:
            raise ValueError('Champion or challenger not found')
        
        # Set traffic split
        champion.traffic_percentage = 100.0 - challenger_traffic
        challenger.traffic_percentage = challenger_traffic
        
        # Promote both to production
        champion.promote_to_production(champion.traffic_percentage)
        challenger.promote_to_production(challenger.traffic_percentage)
        
        print(f"🧪 A/B Test Started: {model_id}")
        print(f"   Champion {champion_version}: {champion.traffic_percentage}%")
        print(f"   Challenger {challenger_version}: {challenger.traffic_percentage}%")
    
    def promote_winner(self, model_id: str, winning_version: str):
        """Promote A/B test winner to 100% traffic"""
        
        models = self.models.get(model_id, [])
        
        for model in models:
            if model.version == winning_version:
                model.traffic_percentage = 100.0
                model.status = ModelStatus.PRODUCTION
            else:
                model.traffic_percentage = 0.0
                model.deprecate()
        
        print(f"✅ Winner Promoted: {model_id} v{winning_version} → 100% traffic")
    
    def rollback(self, model_id: str, target_version: str):
        """Rollback to previous model version"""
        
        models = self.models.get(model_id, [])
        
        for model in models:
            if model.version == target_version:
                model.promote_to_production(100.0)
            else:
                model.traffic_percentage = 0.0
                model.status = ModelStatus.DEPRECATED
        
        print(f"⏪ Rollback Complete: {model_id} → v{target_version}")
    
    def get_model_metrics(self, model_id: str) -> List[Dict]:
        """Get metrics for all versions of a model"""
        
        models = self.models.get(model_id, [])
        
        return [
            {
                'version': m.version,
                'status': m.status.value,
                'traffic': m.traffic_percentage,
                'metrics': m.metrics,
                'deployed_at': m.deployed_at
            }
            for m in models
        ]


# Global registry
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry

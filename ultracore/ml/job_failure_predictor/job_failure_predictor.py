"""Job Failure Predictor ML Model"""
import numpy as np
from typing import List, Dict

class JobFailurePredictor:
    """ML model for predicting job failures"""
    
    def __init__(self):
        """Initialize model"""
        self.model = None  # Placeholder for trained model
    
    def predict_failure_probability(self, job_features: Dict) -> float:
        """Predict probability of job failure (0-1)"""
        # Features: execution_time, resource_usage, dependency_health, etc.
        
        # Placeholder logic
        failure_indicators = 0
        
        if job_features.get("avg_duration_seconds", 0) > 300:
            failure_indicators += 1
        
        if job_features.get("recent_failure_rate", 0) > 0.1:
            failure_indicators += 2
        
        if job_features.get("dependency_health", 1.0) < 0.8:
            failure_indicators += 1
        
        # Simple scoring
        failure_probability = min(failure_indicators * 0.2, 0.9)
        return failure_probability
    
    def recommend_preventive_actions(self, job_id: str,
                                     failure_probability: float) -> List[str]:
        """Recommend actions to prevent failure"""
        actions = []
        
        if failure_probability > 0.7:
            actions.append("Increase timeout limit")
            actions.append("Add retry logic")
            actions.append("Check dependency health")
        
        elif failure_probability > 0.4:
            actions.append("Monitor resource usage")
            actions.append("Review recent failures")
        
        return actions
    
    def analyze_failure_patterns(self, failures: List[Dict]) -> Dict:
        """Analyze failure patterns"""
        if not failures:
            return {"pattern": "no_failures"}
        
        # Group by error type
        error_types = {}
        for failure in failures:
            error = failure.get("error_message", "unknown")
            error_types[error] = error_types.get(error, 0) + 1
        
        most_common_error = max(error_types, key=error_types.get)
        
        return {
            "total_failures": len(failures),
            "unique_error_types": len(error_types),
            "most_common_error": most_common_error,
            "error_distribution": error_types
        }

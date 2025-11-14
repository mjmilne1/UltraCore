"""ML Model for Tenant Resource Prediction"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
import numpy as np

class TenantResourcePredictor:
    """Predict future tenant resource needs using time series analysis"""
    
    def __init__(self, data_product):
        """Initialize with data product"""
        self.data_product = data_product
    
    async def predict_resource_needs(self, tenant_id: str, 
                                    days_ahead: int = 7) -> Dict:
        """Predict resource needs for next N days"""
        # Get historical data (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        usage = await self.data_product.get_tenant_resource_usage(
            tenant_id, start_date, end_date
        )
        
        if len(usage) < 7:
            return {
                "tenant_id": tenant_id,
                "error": "Insufficient historical data for prediction"
            }
        
        # Extract time series
        cpu_series = [float(u['cpu_usage_percent']) for u in usage]
        memory_series = [float(u['memory_usage_mb']) for u in usage]
        
        # Simple moving average prediction (placeholder for more sophisticated ML)
        cpu_prediction = self._predict_moving_average(cpu_series, days_ahead)
        memory_prediction = self._predict_moving_average(memory_series, days_ahead)
        
        # Calculate confidence intervals
        cpu_std = np.std(cpu_series)
        memory_std = np.std(memory_series)
        
        return {
            "tenant_id": tenant_id,
            "prediction_date": datetime.utcnow().isoformat(),
            "days_ahead": days_ahead,
            "predictions": {
                "cpu_percent": {
                    "predicted": float(cpu_prediction),
                    "lower_bound": float(max(0, cpu_prediction - 2 * cpu_std)),
                    "upper_bound": float(min(100, cpu_prediction + 2 * cpu_std)),
                    "confidence": 0.95
                },
                "memory_mb": {
                    "predicted": float(memory_prediction),
                    "lower_bound": float(max(0, memory_prediction - 2 * memory_std)),
                    "upper_bound": float(memory_prediction + 2 * memory_std),
                    "confidence": 0.95
                }
            },
            "recommendations": self._generate_recommendations(
                cpu_prediction, memory_prediction, cpu_std, memory_std
            )
        }
    
    def _predict_moving_average(self, series: List[float], 
                               days_ahead: int) -> float:
        """Simple moving average prediction"""
        # Use last 7 days for prediction
        recent = series[-7:]
        return sum(recent) / len(recent)
    
    def _generate_recommendations(self, cpu_pred: float, memory_pred: float,
                                 cpu_std: float, memory_std: float) -> List[Dict]:
        """Generate recommendations based on predictions"""
        recommendations = []
        
        if cpu_pred + 2 * cpu_std > 80:
            recommendations.append({
                "type": "scale_up",
                "resource": "cpu",
                "reason": f"Predicted CPU usage ({cpu_pred:.1f}%) may exceed capacity",
                "urgency": "high"
            })
        
        if memory_pred + 2 * memory_std > 1800:  # 90% of 2GB
            recommendations.append({
                "type": "scale_up",
                "resource": "memory",
                "reason": f"Predicted memory usage ({memory_pred:.0f} MB) may exceed capacity",
                "urgency": "medium"
            })
        
        return recommendations

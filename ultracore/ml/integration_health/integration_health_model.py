"""Integration Health ML Model"""
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class IntegrationHealthModel:
    """ML model for integration failure prediction and performance optimization"""
    
    def __init__(self):
        """Initialize model"""
        self.model_version = "1.0.0"
        self.trained_at = datetime.utcnow()
    
    def predict_failure_probability(self, features: Dict) -> float:
        """Predict probability of integration failure in next 24 hours"""
        # Extract features
        success_rate = features.get('success_rate', 100.0)
        avg_response_time_ms = features.get('avg_response_time_ms', 200)
        error_count_last_hour = features.get('error_count_last_hour', 0)
        rate_limit_hits = features.get('rate_limit_hits', 0)
        uptime_percent = features.get('uptime_percent_7d', 100.0)
        
        # Simple logistic regression-style scoring
        score = 0.0
        
        # Success rate impact (most important)
        if success_rate < 95:
            score += (95 - success_rate) * 0.05
        
        # Response time impact
        if avg_response_time_ms > 1000:
            score += (avg_response_time_ms - 1000) / 1000 * 0.1
        
        # Error count impact
        if error_count_last_hour > 10:
            score += error_count_last_hour * 0.01
        
        # Rate limiting impact
        if rate_limit_hits > 0:
            score += rate_limit_hits * 0.02
        
        # Uptime impact
        if uptime_percent < 99:
            score += (99 - uptime_percent) * 0.03
        
        # Convert to probability (0-1)
        probability = 1 / (1 + np.exp(-score))
        
        return min(max(probability, 0.0), 1.0)
    
    def predict_performance_degradation(self, time_series_data: List[Dict]) -> Dict:
        """Predict if performance will degrade"""
        if len(time_series_data) < 10:
            return {"prediction": "insufficient_data"}
        
        # Extract response times
        response_times = [d.get('avg_response_time_ms', 200) for d in time_series_data]
        
        # Calculate trend
        x = np.arange(len(response_times))
        y = np.array(response_times)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        # Predict next value
        predicted_next = response_times[-1] + slope
        
        degradation_probability = 0.0
        
        # Increasing trend
        if slope > 10:  # More than 10ms increase per period
            degradation_probability += 0.4
        
        # Current state
        if response_times[-1] > 500:
            degradation_probability += 0.3
        
        # Volatility
        volatility = np.std(response_times)
        if volatility > 100:
            degradation_probability += 0.2
        
        degradation_probability = min(degradation_probability, 1.0)
        
        return {
            "degradation_probability": degradation_probability,
            "current_response_time_ms": response_times[-1],
            "predicted_response_time_ms": predicted_next,
            "trend_slope_ms_per_period": slope,
            "risk_level": "high" if degradation_probability > 0.7 else "medium" if degradation_probability > 0.4 else "low"
        }
    
    def optimize_cache_strategy(self, usage_patterns: Dict) -> Dict:
        """Recommend optimal caching strategy"""
        request_frequency = usage_patterns.get('requests_per_hour', 0)
        data_freshness_requirement_minutes = usage_patterns.get('freshness_requirement_minutes', 60)
        data_size_kb = usage_patterns.get('avg_response_size_kb', 10)
        
        # Determine cache TTL
        if data_freshness_requirement_minutes <= 5:
            cache_ttl_minutes = 5
            cache_strategy = "short_ttl"
        elif data_freshness_requirement_minutes <= 60:
            cache_ttl_minutes = 30
            cache_strategy = "medium_ttl"
        else:
            cache_ttl_minutes = 240
            cache_strategy = "long_ttl"
        
        # Calculate expected hit rate
        if request_frequency > 100:
            expected_hit_rate = 0.8
        elif request_frequency > 10:
            expected_hit_rate = 0.6
        else:
            expected_hit_rate = 0.3
        
        # Calculate savings
        current_api_calls = request_frequency * 24  # Per day
        expected_api_calls = current_api_calls * (1 - expected_hit_rate)
        api_calls_saved = current_api_calls - expected_api_calls
        
        return {
            "recommended_strategy": cache_strategy,
            "cache_ttl_minutes": cache_ttl_minutes,
            "expected_hit_rate": expected_hit_rate,
            "current_api_calls_per_day": current_api_calls,
            "expected_api_calls_per_day": expected_api_calls,
            "api_calls_saved_per_day": api_calls_saved,
            "cost_savings_percent": (api_calls_saved / current_api_calls) * 100 if current_api_calls > 0 else 0
        }
    
    def detect_integration_patterns(self, historical_data: List[Dict]) -> Dict:
        """Detect usage patterns in integration data"""
        if len(historical_data) < 24:
            return {"pattern": "insufficient_data"}
        
        # Extract hourly request counts
        hourly_requests = [d.get('request_count', 0) for d in historical_data[-24:]]
        
        # Find peak hours
        peak_hour = hourly_requests.index(max(hourly_requests))
        min_hour = hourly_requests.index(min(hourly_requests))
        
        avg_requests = np.mean(hourly_requests)
        std_requests = np.std(hourly_requests)
        
        # Determine pattern
        if std_requests < avg_requests * 0.2:
            pattern = "steady"
        elif max(hourly_requests) > avg_requests * 2:
            pattern = "bursty"
        else:
            pattern = "variable"
        
        return {
            "pattern_type": pattern,
            "peak_hour": peak_hour,
            "min_hour": min_hour,
            "avg_requests_per_hour": avg_requests,
            "peak_requests": max(hourly_requests),
            "min_requests": min(hourly_requests),
            "variability_coefficient": (std_requests / avg_requests) if avg_requests > 0 else 0,
            "recommendations": self._get_pattern_recommendations(pattern)
        }
    
    def _get_pattern_recommendations(self, pattern: str) -> List[str]:
        """Get recommendations based on usage pattern"""
        recommendations = {
            "steady": [
                "Implement simple caching with fixed TTL",
                "Use connection pooling for consistent performance"
            ],
            "bursty": [
                "Implement request queuing for burst handling",
                "Use auto-scaling for peak periods",
                "Consider pre-warming cache before peak hours"
            ],
            "variable": [
                "Implement adaptive caching with dynamic TTL",
                "Use rate limiting to smooth out spikes",
                "Monitor closely for anomalies"
            ]
        }
        return recommendations.get(pattern, [])
    
    def calculate_integration_roi(self, integration_data: Dict) -> Dict:
        """Calculate ROI of integration"""
        api_calls_per_month = integration_data.get('api_calls_per_month', 0)
        cost_per_call = integration_data.get('cost_per_call_aud', 0.001)
        time_saved_per_call_minutes = integration_data.get('time_saved_per_call_minutes', 5)
        hourly_rate_aud = integration_data.get('hourly_rate_aud', 100)
        
        # Calculate costs
        monthly_api_cost = api_calls_per_month * cost_per_call
        
        # Calculate benefits (time saved)
        monthly_time_saved_hours = (api_calls_per_month * time_saved_per_call_minutes) / 60
        monthly_value_saved = monthly_time_saved_hours * hourly_rate_aud
        
        # ROI
        net_benefit = monthly_value_saved - monthly_api_cost
        roi_percent = (net_benefit / monthly_api_cost) * 100 if monthly_api_cost > 0 else 0
        
        return {
            "monthly_api_cost_aud": monthly_api_cost,
            "monthly_value_saved_aud": monthly_value_saved,
            "net_monthly_benefit_aud": net_benefit,
            "roi_percent": roi_percent,
            "payback_period_months": (monthly_api_cost / net_benefit) if net_benefit > 0 else float('inf'),
            "recommendation": "highly_valuable" if roi_percent > 500 else "valuable" if roi_percent > 100 else "marginal"
        }

"""Integration Monitor AI Agent"""
from typing import Dict, List
from datetime import datetime, timedelta

class IntegrationMonitorAgent:
    """AI agent for integration health monitoring and anomaly detection"""
    
    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm = llm_client
    
    async def monitor_integration_health(self, integration_id: str,
                                        metrics: Dict) -> Dict:
        """Monitor integration health and detect issues"""
        success_rate = metrics.get('success_rate', 100.0)
        avg_response_time_ms = metrics.get('avg_response_time_ms', 200)
        error_count = metrics.get('error_count_last_hour', 0)
        rate_limit_hits = metrics.get('rate_limit_hits', 0)
        
        health_score = 100.0
        issues = []
        recommendations = []
        
        # Success rate check
        if success_rate < 95:
            health_score -= (95 - success_rate) * 2
            issues.append({
                "type": "low_success_rate",
                "severity": "high" if success_rate < 90 else "medium",
                "message": f"Success rate {success_rate}% below threshold"
            })
            recommendations.append("Investigate recent API changes or authentication issues")
        
        # Response time check
        if avg_response_time_ms > 1000:
            health_score -= 10
            issues.append({
                "type": "slow_response",
                "severity": "medium",
                "message": f"Average response time {avg_response_time_ms}ms exceeds threshold"
            })
            recommendations.append("Consider implementing caching or upgrading API tier")
        
        # Error rate check
        if error_count > 10:
            health_score -= 15
            issues.append({
                "type": "high_error_rate",
                "severity": "high",
                "message": f"{error_count} errors in last hour"
            })
            recommendations.append("Check error logs for patterns and implement retry logic")
        
        # Rate limiting check
        if rate_limit_hits > 0:
            health_score -= 5
            issues.append({
                "type": "rate_limiting",
                "severity": "low",
                "message": f"Hit rate limit {rate_limit_hits} times"
            })
            recommendations.append("Implement request throttling or upgrade API plan")
        
        health_status = "healthy" if health_score >= 90 else "degraded" if health_score >= 70 else "unhealthy"
        
        return {
            "integration_id": integration_id,
            "health_score": max(health_score, 0),
            "health_status": health_status,
            "issues": issues,
            "recommendations": recommendations,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def detect_anomalies(self, integration_id: str,
                              historical_metrics: List[Dict]) -> List[Dict]:
        """Detect anomalies in integration behavior"""
        if len(historical_metrics) < 10:
            return []
        
        anomalies = []
        
        # Calculate baseline
        recent_success_rates = [m.get('success_rate', 100) for m in historical_metrics[-10:]]
        avg_success_rate = sum(recent_success_rates) / len(recent_success_rates)
        
        # Check latest metric
        latest = historical_metrics[-1]
        latest_success_rate = latest.get('success_rate', 100)
        
        # Anomaly: Sudden drop in success rate
        if latest_success_rate < avg_success_rate - 10:
            anomalies.append({
                "type": "success_rate_drop",
                "severity": "high",
                "description": f"Success rate dropped from {avg_success_rate:.1f}% to {latest_success_rate:.1f}%",
                "detected_at": datetime.utcnow().isoformat(),
                "recommended_action": "Investigate API endpoint health and authentication"
            })
        
        # Anomaly: Response time spike
        recent_response_times = [m.get('avg_response_time_ms', 200) for m in historical_metrics[-10:]]
        avg_response_time = sum(recent_response_times) / len(recent_response_times)
        latest_response_time = latest.get('avg_response_time_ms', 200)
        
        if latest_response_time > avg_response_time * 2:
            anomalies.append({
                "type": "response_time_spike",
                "severity": "medium",
                "description": f"Response time spiked from {avg_response_time:.0f}ms to {latest_response_time:.0f}ms",
                "detected_at": datetime.utcnow().isoformat(),
                "recommended_action": "Check API provider status and network connectivity"
            })
        
        return anomalies
    
    async def predict_integration_failure(self, integration_id: str,
                                         recent_metrics: List[Dict]) -> Dict:
        """Predict likelihood of integration failure"""
        if len(recent_metrics) < 5:
            return {"prediction": "insufficient_data"}
        
        # Trend analysis
        success_rates = [m.get('success_rate', 100) for m in recent_metrics]
        error_counts = [m.get('error_count_last_hour', 0) for m in recent_metrics]
        
        # Calculate trends
        success_rate_trend = success_rates[-1] - success_rates[0]
        error_trend = error_counts[-1] - error_counts[0]
        
        failure_probability = 0.0
        
        # Declining success rate
        if success_rate_trend < -5:
            failure_probability += 0.3
        
        # Increasing errors
        if error_trend > 5:
            failure_probability += 0.3
        
        # Current state
        if success_rates[-1] < 90:
            failure_probability += 0.2
        
        if error_counts[-1] > 20:
            failure_probability += 0.2
        
        failure_probability = min(failure_probability, 1.0)
        
        risk_level = "high" if failure_probability > 0.7 else "medium" if failure_probability > 0.4 else "low"
        
        return {
            "integration_id": integration_id,
            "failure_probability": failure_probability,
            "risk_level": risk_level,
            "contributing_factors": [
                f"Success rate trend: {success_rate_trend:+.1f}%",
                f"Error trend: {error_trend:+d} errors"
            ],
            "recommended_actions": [
                "Enable proactive monitoring",
                "Implement circuit breaker pattern",
                "Set up fallback integration"
            ] if risk_level == "high" else []
        }
    
    async def recommend_integration_optimization(self, integration_id: str,
                                                usage_data: Dict) -> List[Dict]:
        """Recommend integration optimizations"""
        request_count = usage_data.get('requests_per_day', 0)
        cache_hit_rate = usage_data.get('cache_hit_rate', 0)
        avg_response_time_ms = usage_data.get('avg_response_time_ms', 200)
        
        optimizations = []
        
        # Caching optimization
        if cache_hit_rate < 50 and request_count > 1000:
            optimizations.append({
                "type": "implement_caching",
                "priority": "high",
                "description": "Low cache hit rate with high request volume",
                "expected_benefit": "Reduce API calls by 40-60%",
                "implementation_effort": "medium"
            })
        
        # Request batching
        if request_count > 10000:
            optimizations.append({
                "type": "batch_requests",
                "priority": "medium",
                "description": "High request volume suitable for batching",
                "expected_benefit": "Reduce API calls by 30-50%",
                "implementation_effort": "low"
            })
        
        # Response time optimization
        if avg_response_time_ms > 500:
            optimizations.append({
                "type": "optimize_response_time",
                "priority": "medium",
                "description": "Slow response times impacting user experience",
                "expected_benefit": "Improve response time by 40-60%",
                "implementation_effort": "medium",
                "suggestions": [
                    "Implement connection pooling",
                    "Use async requests",
                    "Optimize payload size"
                ]
            })
        
        return optimizations

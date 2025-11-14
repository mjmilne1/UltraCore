"""Tenant Optimizer AI Agent"""
from typing import Dict, List
from datetime import datetime

class TenantOptimizerAgent:
    """AI agent for tenant resource optimization and cost management"""
    
    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm = llm_client
    
    async def optimize_tenant_resources(self, tenant_id: str,
                                       resource_usage: Dict,
                                       cost_data: Dict) -> Dict:
        """Optimize tenant resource allocation"""
        prompt = f"""
        Analyze tenant resource usage and recommend optimizations:
        
        Tenant ID: {tenant_id}
        Resource Usage: {resource_usage}
        Cost Data: {cost_data}
        
        Consider:
        - Database connection pool sizing
        - Storage tier selection
        - Compute resource allocation
        - API rate limits
        - Cost vs performance tradeoffs
        
        Recommend specific optimizations with expected savings and risks.
        """
        
        # Placeholder logic
        db_connections = resource_usage.get('database', {}).get('current_connections', 0)
        max_connections = resource_usage.get('database', {}).get('max_connections', 20)
        utilization = (db_connections / max_connections) * 100 if max_connections > 0 else 0
        
        recommendations = []
        
        # Over-provisioned database
        if utilization < 50:
            recommendations.append({
                "type": "downsize_database_pool",
                "current_size": max_connections,
                "recommended_size": int(max_connections * 0.7),
                "estimated_savings_aud": 100.00,
                "confidence": 0.9
            })
        
        # Storage optimization
        storage_used = resource_usage.get('storage', {}).get('used_gb', 0)
        if storage_used > 100:
            recommendations.append({
                "type": "archive_old_data",
                "current_storage_gb": storage_used,
                "archivable_gb": storage_used * 0.3,
                "estimated_savings_aud": 40.00,
                "confidence": 0.85
            })
        
        return {
            "tenant_id": tenant_id,
            "recommendations": recommendations,
            "total_estimated_savings_aud": sum(r.get("estimated_savings_aud", 0) for r in recommendations),
            "implementation_priority": "high" if len(recommendations) > 2 else "medium"
        }
    
    async def predict_resource_needs(self, tenant_id: str,
                                    historical_usage: List[Dict],
                                    growth_rate: float) -> Dict:
        """Predict future resource needs"""
        current_storage = historical_usage[-1].get('storage_gb', 0) if historical_usage else 0
        current_users = historical_usage[-1].get('active_users', 0) if historical_usage else 0
        
        # Simple linear projection
        months_ahead = 6
        projected_storage = current_storage * (1 + growth_rate) ** months_ahead
        projected_users = current_users * (1 + growth_rate) ** months_ahead
        
        return {
            "tenant_id": tenant_id,
            "projection_months": months_ahead,
            "current_state": {
                "storage_gb": current_storage,
                "active_users": current_users
            },
            "projected_state": {
                "storage_gb": projected_storage,
                "active_users": projected_users
            },
            "recommendations": [
                {
                    "resource": "storage",
                    "action": "upgrade_tier" if projected_storage > current_storage * 1.5 else "maintain",
                    "timing": "Q2 2025" if projected_storage > current_storage * 1.5 else "no_action_needed"
                }
            ]
        }
    
    async def recommend_tier_upgrade(self, tenant_id: str,
                                    current_tier: str,
                                    usage_metrics: Dict) -> Dict:
        """Recommend tier upgrade/downgrade"""
        # Tier thresholds
        tier_limits = {
            "SMALL": {"max_users": 10, "max_storage_gb": 10},
            "STANDARD": {"max_users": 100, "max_storage_gb": 100},
            "ENTERPRISE": {"max_users": 1000, "max_storage_gb": 1000}
        }
        
        active_users = usage_metrics.get('active_users', 0)
        storage_gb = usage_metrics.get('storage_gb', 0)
        
        # Check if current tier is appropriate
        current_limits = tier_limits.get(current_tier, {})
        
        if active_users > current_limits.get('max_users', 999999) * 0.8:
            return {
                "recommendation": "upgrade",
                "current_tier": current_tier,
                "recommended_tier": "ENTERPRISE" if current_tier == "STANDARD" else "STANDARD",
                "reason": "Approaching user limit",
                "urgency": "high"
            }
        elif active_users < current_limits.get('max_users', 0) * 0.3:
            return {
                "recommendation": "downgrade",
                "current_tier": current_tier,
                "recommended_tier": "STANDARD" if current_tier == "ENTERPRISE" else "SMALL",
                "reason": "Under-utilizing current tier",
                "urgency": "low",
                "potential_savings_aud": 200.00
            }
        else:
            return {
                "recommendation": "maintain",
                "current_tier": current_tier,
                "reason": "Current tier is optimal"
            }
    
    async def allocate_costs(self, tenant_id: str,
                           total_costs: Dict,
                           usage_metrics: Dict) -> Dict:
        """Allocate costs across tenant departments/users"""
        total_cost = sum(total_costs.values())
        active_users = usage_metrics.get('active_users', 1)
        
        return {
            "tenant_id": tenant_id,
            "total_cost_aud": total_cost,
            "cost_per_user_aud": total_cost / active_users,
            "cost_breakdown": total_costs,
            "allocation_method": "equal_per_user",
            "departments": [
                {
                    "name": "Trading",
                    "users": int(active_users * 0.4),
                    "allocated_cost_aud": total_cost * 0.4
                },
                {
                    "name": "Analytics",
                    "users": int(active_users * 0.3),
                    "allocated_cost_aud": total_cost * 0.3
                },
                {
                    "name": "Operations",
                    "users": int(active_users * 0.3),
                    "allocated_cost_aud": total_cost * 0.3
                }
            ]
        }

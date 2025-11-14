"""Tenant Resource Optimization Agent"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

class TenantOptimizerAgent:
    """AI agent for tenant resource optimization"""
    
    def __init__(self, pool_manager, data_product):
        """Initialize with pool manager and data product"""
        self.pool_manager = pool_manager
        self.data_product = data_product
    
    async def optimize_tenant_resources(self, tenant_id: str) -> Dict:
        """Analyze and optimize tenant resources"""
        # Get recent resource usage
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        usage = await self.data_product.get_tenant_resource_usage(
            tenant_id, start_date, end_date
        )
        
        if not usage:
            return {"tenant_id": tenant_id, "recommendations": []}
        
        recommendations = []
        
        # Analyze CPU usage
        avg_cpu = sum(u['cpu_usage_percent'] for u in usage) / len(usage)
        max_cpu = max(u['cpu_usage_percent'] for u in usage)
        
        if avg_cpu < 20:
            recommendations.append({
                "type": "scale_down",
                "resource": "cpu",
                "reason": f"Average CPU usage is low ({avg_cpu:.1f}%)",
                "action": "Consider downgrading to lower tier",
                "potential_savings": "30%"
            })
        elif max_cpu > 90:
            recommendations.append({
                "type": "scale_up",
                "resource": "cpu",
                "reason": f"Peak CPU usage is high ({max_cpu:.1f}%)",
                "action": "Consider upgrading to higher tier",
                "risk": "Performance degradation"
            })
        
        # Analyze memory usage
        avg_memory = sum(u['memory_usage_mb'] for u in usage) / len(usage)
        max_memory = max(u['memory_usage_mb'] for u in usage)
        
        if avg_memory < 512:
            recommendations.append({
                "type": "scale_down",
                "resource": "memory",
                "reason": f"Average memory usage is low ({avg_memory:.0f} MB)",
                "action": "Reduce memory allocation",
                "potential_savings": "20%"
            })
        
        # Analyze connection pool
        pool_stats = await self.pool_manager.get_pool_stats(tenant_id)
        utilization = (pool_stats['total_connections'] - pool_stats['idle_connections']) / pool_stats['max_size'] * 100
        
        if utilization < 30:
            recommendations.append({
                "type": "resize_pool",
                "resource": "connections",
                "reason": f"Connection pool utilization is low ({utilization:.1f}%)",
                "action": f"Reduce max connections from {pool_stats['max_size']} to {int(pool_stats['max_size'] * 0.7)}",
                "potential_savings": "10%"
            })
        elif utilization > 80:
            recommendations.append({
                "type": "resize_pool",
                "resource": "connections",
                "reason": f"Connection pool utilization is high ({utilization:.1f}%)",
                "action": f"Increase max connections from {pool_stats['max_size']} to {int(pool_stats['max_size'] * 1.3)}",
                "risk": "Connection exhaustion"
            })
        
        return {
            "tenant_id": tenant_id,
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "current_metrics": {
                "avg_cpu_percent": float(avg_cpu),
                "max_cpu_percent": float(max_cpu),
                "avg_memory_mb": float(avg_memory),
                "max_memory_mb": float(max_memory),
                "pool_utilization_percent": float(utilization)
            },
            "recommendations": recommendations,
            "estimated_total_savings": sum(
                float(r.get("potential_savings", "0%").rstrip("%")) 
                for r in recommendations if "potential_savings" in r
            )
        }

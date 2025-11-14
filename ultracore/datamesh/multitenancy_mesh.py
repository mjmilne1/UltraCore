"""Multi-Tenancy Data Mesh Product"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

class MultiTenancyDataProduct:
    """Data mesh product for multi-tenancy analytics and compliance"""
    
    def __init__(self, pool_manager):
        """Initialize with connection pool manager"""
        self.pool_manager = pool_manager
    
    async def get_tenant_resource_usage(self, tenant_id: str, 
                                       start_date: datetime,
                                       end_date: datetime) -> List[Dict]:
        """Get tenant resource usage over time"""
        pool = await self.pool_manager.get_pool(tenant_id, readonly=True)
        
        query = """
            SELECT 
                timestamp,
                cpu_usage_percent,
                memory_usage_mb,
                storage_usage_gb,
                connection_count,
                active_query_count
            FROM tenant_resource_usage
            WHERE tenant_id = $1
            AND timestamp BETWEEN $2 AND $3
            ORDER BY timestamp
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, start_date, end_date)
            return [dict(row) for row in rows]
    
    async def get_tenant_cost_allocation(self, tenant_id: str,
                                         month: str) -> Dict:
        """Calculate tenant cost allocation (ASIC compliance)"""
        usage = await self.get_tenant_resource_usage(
            tenant_id,
            datetime.fromisoformat(f"{month}-01"),
            datetime.fromisoformat(f"{month}-31")
        )
        
        # Calculate costs
        total_cpu_hours = sum(u['cpu_usage_percent'] for u in usage) / 100
        total_memory_gb_hours = sum(u['memory_usage_mb'] for u in usage) / 1024
        total_storage_gb_days = sum(u['storage_usage_gb'] for u in usage) / 24
        
        # Pricing (example rates)
        cpu_cost_per_hour = Decimal("0.05")
        memory_cost_per_gb_hour = Decimal("0.01")
        storage_cost_per_gb_day = Decimal("0.10")
        
        total_cost = (
            Decimal(str(total_cpu_hours)) * cpu_cost_per_hour +
            Decimal(str(total_memory_gb_hours)) * memory_cost_per_gb_hour +
            Decimal(str(total_storage_gb_days)) * storage_cost_per_gb_day
        )
        
        return {
            "tenant_id": tenant_id,
            "month": month,
            "cpu_hours": float(total_cpu_hours),
            "cpu_cost": float(Decimal(str(total_cpu_hours)) * cpu_cost_per_hour),
            "memory_gb_hours": float(total_memory_gb_hours),
            "memory_cost": float(Decimal(str(total_memory_gb_hours)) * memory_cost_per_gb_hour),
            "storage_gb_days": float(total_storage_gb_days),
            "storage_cost": float(Decimal(str(total_storage_gb_days)) * storage_cost_per_gb_day),
            "total_cost": float(total_cost),
        }
    
    async def get_tenant_compliance_report(self, tenant_id: str) -> Dict:
        """Generate ASIC compliance report for tenant data isolation"""
        pool = await self.pool_manager.get_pool(tenant_id, readonly=True)
        
        # Check data isolation
        async with pool.acquire() as conn:
            # Verify no cross-tenant data leakage
            cross_tenant_check = await conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT tenant_id FROM portfolios
                    UNION
                    SELECT DISTINCT tenant_id FROM transactions
                    UNION
                    SELECT DISTINCT tenant_id FROM holdings
                ) AS all_tenants
            """)
            
            # Get tenant data summary
            portfolio_count = await conn.fetchval(
                "SELECT COUNT(*) FROM portfolios WHERE tenant_id = $1", tenant_id
            )
            transaction_count = await conn.fetchval(
                "SELECT COUNT(*) FROM transactions WHERE tenant_id = $1", tenant_id
            )
        
        return {
            "tenant_id": tenant_id,
            "compliance_status": "COMPLIANT" if cross_tenant_check == 1 else "NON_COMPLIANT",
            "data_isolation_verified": cross_tenant_check == 1,
            "portfolio_count": portfolio_count,
            "transaction_count": transaction_count,
            "report_date": datetime.utcnow().isoformat(),
        }

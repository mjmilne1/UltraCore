"""Advanced Search Engine"""
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
import time
from ..events import SearchType, SearchOperator

class AdvancedSearchEngine:
    """Advanced search engine with multiple criteria support"""
    
    def __init__(self, db_pool_manager):
        """Initialize with database pool manager"""
        self.pool_manager = db_pool_manager
    
    async def search_etfs(self, criteria: Dict, tenant_id: str) -> List[Dict]:
        """Search ETFs with complex criteria
        
        Criteria examples:
        {
            "expense_ratio": {"operator": "less_than", "value": 0.20},
            "aum": {"operator": "greater_than", "value": 1000000000},
            "asset_class": {"operator": "in", "values": ["equity", "fixed_income"]},
            "dividend_yield": {"operator": "between", "min": 2.0, "max": 5.0},
            "name": {"operator": "contains", "value": "Australia"}
        }
        """
        pool = await self.pool_manager.get_pool(tenant_id, readonly=True)
        
        # Build dynamic query
        where_clauses = ["tenant_id = $1"]
        params = [tenant_id]
        param_count = 1
        
        for field, condition in criteria.items():
            operator = condition.get("operator")
            
            if operator == "equals":
                param_count += 1
                where_clauses.append(f"{field} = ${param_count}")
                params.append(condition["value"])
            
            elif operator == "less_than":
                param_count += 1
                where_clauses.append(f"{field} < ${param_count}")
                params.append(condition["value"])
            
            elif operator == "greater_than":
                param_count += 1
                where_clauses.append(f"{field} > ${param_count}")
                params.append(condition["value"])
            
            elif operator == "between":
                param_count += 1
                where_clauses.append(f"{field} >= ${param_count}")
                params.append(condition["min"])
                param_count += 1
                where_clauses.append(f"{field} <= ${param_count}")
                params.append(condition["max"])
            
            elif operator == "in":
                param_count += 1
                where_clauses.append(f"{field} = ANY(${param_count})")
                params.append(condition["values"])
            
            elif operator == "contains":
                param_count += 1
                where_clauses.append(f"{field} ILIKE ${param_count}")
                params.append(f"%{condition['value']}%")
        
        query = f"""
            SELECT *
            FROM etfs
            WHERE {' AND '.join(where_clauses)}
            ORDER BY aum DESC
            LIMIT 100
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def search_portfolios(self, criteria: Dict, tenant_id: str) -> List[Dict]:
        """Search portfolios with filtering
        
        Criteria examples:
        {
            "total_value": {"operator": "greater_than", "value": 100000},
            "client_name": {"operator": "contains", "value": "Smith"},
            "created_date": {"operator": "between", "min": "2024-01-01", "max": "2024-12-31"}
        }
        """
        pool = await self.pool_manager.get_pool(tenant_id, readonly=True)
        
        where_clauses = ["p.tenant_id = $1"]
        params = [tenant_id]
        param_count = 1
        
        # Build query similar to ETF search
        for field, condition in criteria.items():
            operator = condition.get("operator")
            
            if operator == "equals":
                param_count += 1
                where_clauses.append(f"p.{field} = ${param_count}")
                params.append(condition["value"])
            
            elif operator == "greater_than":
                param_count += 1
                where_clauses.append(f"p.{field} > ${param_count}")
                params.append(condition["value"])
            
            elif operator == "contains":
                param_count += 1
                where_clauses.append(f"p.{field} ILIKE ${param_count}")
                params.append(f"%{condition['value']}%")
        
        query = f"""
            SELECT p.*, c.name as client_name
            FROM portfolios p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY p.created_at DESC
            LIMIT 100
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def search_transactions(self, criteria: Dict, tenant_id: str) -> List[Dict]:
        """Search transactions with date ranges
        
        Criteria examples:
        {
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "transaction_type": {"operator": "in", "values": ["BUY", "SELL"]},
            "amount": {"operator": "greater_than", "value": 10000},
            "symbol": {"operator": "equals", "value": "AAPL"}
        }
        """
        pool = await self.pool_manager.get_pool(tenant_id, readonly=True)
        
        where_clauses = ["tenant_id = $1"]
        params = [tenant_id]
        param_count = 1
        
        for field, condition in criteria.items():
            if field == "date_range":
                param_count += 1
                where_clauses.append(f"transaction_date >= ${param_count}")
                params.append(condition["start"])
                param_count += 1
                where_clauses.append(f"transaction_date <= ${param_count}")
                params.append(condition["end"])
            
            elif condition.get("operator") == "in":
                param_count += 1
                where_clauses.append(f"{field} = ANY(${param_count})")
                params.append(condition["values"])
            
            elif condition.get("operator") == "equals":
                param_count += 1
                where_clauses.append(f"{field} = ${param_count}")
                params.append(condition["value"])
            
            elif condition.get("operator") == "greater_than":
                param_count += 1
                where_clauses.append(f"{field} > ${param_count}")
                params.append(condition["value"])
        
        query = f"""
            SELECT *
            FROM transactions
            WHERE {' AND '.join(where_clauses)}
            ORDER BY transaction_date DESC
            LIMIT 1000
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def execute_search(self, search_type: SearchType, criteria: Dict,
                            user_id: str, tenant_id: str) -> Dict:
        """Execute search and record analytics"""
        start_time = time.time()
        
        if search_type == SearchType.ETF:
            results = await self.search_etfs(criteria, tenant_id)
        elif search_type == SearchType.PORTFOLIO:
            results = await self.search_portfolios(criteria, tenant_id)
        elif search_type == SearchType.TRANSACTION:
            results = await self.search_transactions(criteria, tenant_id)
        else:
            results = []
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "result_count": len(results),
            "execution_time_ms": execution_time_ms,
            "search_type": search_type.value,
            "criteria": criteria
        }

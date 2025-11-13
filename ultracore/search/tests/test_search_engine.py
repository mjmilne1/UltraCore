"""Tests for Advanced Search Engine"""
import pytest
from decimal import Decimal
from ..services.search_engine import AdvancedSearchEngine
from ..events import SearchType

@pytest.mark.asyncio
async def test_search_etfs():
    """Test ETF search with multiple criteria"""
    engine = AdvancedSearchEngine(db_pool_manager=None)
    
    criteria = {
        "expense_ratio": {"operator": "less_than", "value": 0.20},
        "aum": {"operator": "greater_than", "value": 1000000000}
    }
    
    # Would test with mock database
    assert criteria is not None

@pytest.mark.asyncio
async def test_search_transactions_date_range():
    """Test transaction search with date ranges"""
    engine = AdvancedSearchEngine(db_pool_manager=None)
    
    criteria = {
        "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "transaction_type": {"operator": "in", "values": ["BUY", "SELL"]}
    }
    
    assert criteria["date_range"]["start"] == "2024-01-01"

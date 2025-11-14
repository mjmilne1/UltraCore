"""Data Mesh Performance Optimizations"""
from .cache import DataProductCache, get_cache, init_cache
from .search import ProductSearchIndex
from .connection_pool import DatabaseConnectionPool

__all__ = [
    'DataProductCache',
    'get_cache',
    'init_cache',
    'ProductSearchIndex',
    'DatabaseConnectionPool'
]

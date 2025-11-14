"""Agent Memory Cache"""
from collections import OrderedDict
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class AgentMemoryCache:
    """LRU cache for agent memory."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        logger.info(f"AgentMemoryCache initialized (max_size={max_size})")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1
        
        self.cache[key] = value
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        return {**self.stats, "size": len(self.cache), "hit_rate": hit_rate}

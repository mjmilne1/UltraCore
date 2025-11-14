"""Product Search and Discovery"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ProductSearchIndex:
    """Search index for data products (in-memory implementation)."""
    
    def __init__(self):
        self.products = {}
        self.inverted_index = {}
        logger.info("ProductSearchIndex initialized")
    
    def index_product(self, product):
        """Index a data product."""
        self.products[product.id] = {
            "id": product.id,
            "name": product.name,
            "domain": product.domain,
            "description": product.description,
            "quality_level": product.quality_level,
            "tags": getattr(product, 'tags', [])
        }
        
        # Build inverted index
        terms = self._tokenize(f"{product.name} {product.description}")
        for term in terms:
            if term not in self.inverted_index:
                self.inverted_index[term] = set()
            self.inverted_index[term].add(product.id)
        
        logger.debug(f"Indexed product: {product.id}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()
    
    def search(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """Search for products."""
        terms = self._tokenize(query)
        
        # Find matching products
        matching_ids = set()
        for term in terms:
            if term in self.inverted_index:
                if not matching_ids:
                    matching_ids = self.inverted_index[term].copy()
                else:
                    matching_ids &= self.inverted_index[term]
        
        # Apply filters
        results = []
        for product_id in matching_ids:
            product = self.products.get(product_id)
            if product and self._matches_filters(product, filters):
                results.append(product)
        
        return results[:limit]
    
    def _matches_filters(self, product: Dict, filters: Optional[Dict]) -> bool:
        """Check if product matches filters."""
        if not filters:
            return True
        
        for key, value in filters.items():
            if product.get(key) != value:
                return False
        
        return True
    
    def autocomplete(self, prefix: str, limit: int = 5) -> List[str]:
        """Autocomplete product names."""
        prefix = prefix.lower()
        suggestions = []
        
        for product in self.products.values():
            if product["name"].lower().startswith(prefix):
                suggestions.append(product["name"])
        
        return suggestions[:limit]

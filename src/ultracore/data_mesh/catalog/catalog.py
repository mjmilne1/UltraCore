"""
Data Mesh Catalog
Centralized registry of all data products across domains
"""
from typing import List, Dict, Optional
from datetime import datetime


class DataCatalog:
    """
    Central catalog for data product discovery
    
    Enables:
    - Data product discovery
    - Schema browsing
    - Lineage tracking
    - Quality metrics
    """
    
    def __init__(self):
        self.products = {}
        self._load_products()
    
    def _load_products(self):
        """Load all registered data products"""
        # Client domain products
        self.products["customer_360"] = {
            "domain": "client",
            "name": "customer_360",
            "description": "Complete customer view across all touchpoints",
            "schema_url": "/api/v1/data-products/client/customer_360/schema",
            "data_url": "/api/v1/data-products/client/customer_360/data",
            "owner": "client-team@turingdynamics.com.au",
            "tags": ["customer", "360", "analytics"]
        }
        
        self.products["kyc_status"] = {
            "domain": "client",
            "name": "kyc_status",
            "description": "KYC verification status and compliance data",
            "schema_url": "/api/v1/data-products/client/kyc_status/schema",
            "data_url": "/api/v1/data-products/client/kyc_status/data",
            "owner": "client-team@turingdynamics.com.au",
            "tags": ["kyc", "compliance", "verification"]
        }
        
        # Account domain products
        self.products["account_balances"] = {
            "domain": "account",
            "name": "account_balances",
            "description": "Real-time account balance data",
            "schema_url": "/api/v1/data-products/account/account_balances/schema",
            "data_url": "/api/v1/data-products/account/account_balances/data",
            "owner": "account-team@turingdynamics.com.au",
            "tags": ["balance", "accounts", "realtime"]
        }
        
        # Loan domain products
        self.products["loan_portfolio"] = {
            "domain": "loan",
            "name": "loan_portfolio",
            "description": "Comprehensive loan portfolio analytics",
            "schema_url": "/api/v1/data-products/loan/loan_portfolio/schema",
            "data_url": "/api/v1/data-products/loan/loan_portfolio/data",
            "owner": "loan-team@turingdynamics.com.au",
            "tags": ["loans", "portfolio", "analytics"]
        }
        
        self.products["default_risk"] = {
            "domain": "loan",
            "name": "default_risk",
            "description": "ML-based default risk predictions",
            "schema_url": "/api/v1/data-products/loan/default_risk/schema",
            "data_url": "/api/v1/data-products/loan/default_risk/data",
            "owner": "loan-team@turingdynamics.com.au",
            "tags": ["risk", "ml", "prediction"]
        }
    
    def search(self, query: str) -> List[Dict]:
        """Search data products by name, description, or tags"""
        results = []
        query_lower = query.lower()
        
        for product_id, product in self.products.items():
            if (query_lower in product["name"].lower() or
                query_lower in product["description"].lower() or
                any(query_lower in tag for tag in product["tags"])):
                results.append(product)
        
        return results
    
    def get_by_domain(self, domain: str) -> List[Dict]:
        """Get all data products from a specific domain"""
        return [p for p in self.products.values() if p["domain"] == domain]
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get details for a specific data product"""
        return self.products.get(product_id)
    
    def list_all(self) -> List[Dict]:
        """List all available data products"""
        return list(self.products.values())


# Global catalog instance
catalog = DataCatalog()

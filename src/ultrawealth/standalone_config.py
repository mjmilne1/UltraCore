"""
UltraWealth Standalone Product Configuration
Allows independent deployment with optional UltraCore integration
"""

from typing import Dict, Optional
from enum import Enum
import uuid

class ProductMode(Enum):
    STANDALONE = "standalone"          # UltraWealth only
    INTEGRATED = "integrated"           # With UltraCore
    WHITE_LABEL = "white_label"        # For partners
    API_ONLY = "api_only"              # Headless

class IntegrationLevel(Enum):
    NONE = "none"                      # No integration
    DATA_SYNC = "data_sync"            # Share customer data
    FULL_STACK = "full_stack"          # Complete integration
    FEDERATED = "federated"            # SSO + limited data

class UltraWealthProductConfig:
    """
    Configuration for UltraWealth as a separate product
    """
    
    def __init__(self, mode: ProductMode = ProductMode.STANDALONE):
        self.mode = mode
        self.product_id = "ultrawealth"
        self.version = "1.0.0"
        self.integration_config = self._configure_integration()
        
    def _configure_integration(self) -> Dict:
        """Configure integration points with UltraCore"""
        
        if self.mode == ProductMode.STANDALONE:
            return {
                "integration_level": IntegrationLevel.NONE,
                "data_sharing": False,
                "shared_auth": False,
                "kafka_topics": self._get_standalone_topics(),
                "api_endpoints": self._get_standalone_apis(),
                "database": "ultrawealth_standalone_db"
            }
            
        elif self.mode == ProductMode.INTEGRATED:
            return {
                "integration_level": IntegrationLevel.FULL_STACK,
                "data_sharing": True,
                "shared_auth": True,
                "kafka_topics": self._get_integrated_topics(),
                "api_endpoints": self._get_integrated_apis(),
                "database": "ultrawealth_db",
                "ultracore_connection": {
                    "enabled": True,
                    "sync_accounts": True,
                    "sync_transactions": True,
                    "sync_kyc": True
                }
            }
            
        elif self.mode == ProductMode.WHITE_LABEL:
            return {
                "integration_level": IntegrationLevel.FEDERATED,
                "data_sharing": False,
                "shared_auth": False,
                "custom_branding": True,
                "partner_config": {
                    "customizable": ["branding", "features", "limits"],
                    "locked": ["core_ml", "risk_models"]
                }
            }
            
        else:  # API_ONLY
            return {
                "integration_level": IntegrationLevel.DATA_SYNC,
                "api_gateway": "ultrawealth.api.gateway",
                "rate_limits": {"requests_per_second": 100},
                "authentication": "oauth2"
            }
    
    def _get_standalone_topics(self) -> Dict:
        """Kafka topics for standalone mode"""
        return {
            "capsules": "ultrawealth.capsules",
            "portfolios": "ultrawealth.portfolios",
            "rebalancing": "ultrawealth.rebalancing",
            "ml_optimization": "ultrawealth.ml_optimization"
        }
    
    def _get_integrated_topics(self) -> Dict:
        """Kafka topics for integrated mode"""
        return {
            # UltraWealth specific
            "capsules": "ultrawealth.capsules",
            "portfolios": "ultrawealth.portfolios",
            
            # Shared with UltraCore
            "accounts": "ultracore.accounts",  # Subscribe only
            "transactions": "ultracore.transactions",  # Subscribe only
            "customer_events": "shared.customer_events",  # Pub/Sub
            
            # Cross-product
            "wealth_to_banking": "integration.wealth_to_banking",
            "banking_to_wealth": "integration.banking_to_wealth"
        }
    
    def _get_standalone_apis(self) -> Dict:
        """API endpoints for standalone deployment"""
        return {
            "base_url": "https://api.ultrawealth.com",
            "endpoints": {
                "capsules": "/api/v1/capsules",
                "portfolios": "/api/v1/portfolios",
                "optimization": "/api/v1/optimize",
                "rebalancing": "/api/v1/rebalance"
            }
        }
    
    def _get_integrated_apis(self) -> Dict:
        """API endpoints for integrated deployment"""
        return {
            "base_url": "https://api.ultracore.com",
            "wealth_prefix": "/wealth",
            "endpoints": {
                "capsules": "/wealth/api/v1/capsules",
                "portfolios": "/wealth/api/v1/portfolios",
                
                # Shared endpoints
                "accounts": "/api/v1/accounts",  # From UltraCore
                "customers": "/api/v1/customers"  # From UltraCore
            }
        }

class UltraWealthDeployment:
    """
    Deployment configuration for different scenarios
    """
    
    def __init__(self):
        self.deployment_modes = {
            "standalone_saas": self._standalone_saas(),
            "integrated_suite": self._integrated_suite(),
            "white_label_partners": self._white_label(),
            "api_marketplace": self._api_marketplace()
        }
    
    def _standalone_saas(self) -> Dict:
        """UltraWealth as independent SaaS"""
        return {
            "infrastructure": {
                "kubernetes_namespace": "ultrawealth",
                "database": "PostgreSQL (separate)",
                "cache": "Redis (dedicated)",
                "message_broker": "Kafka (separate cluster)",
                "ml_compute": "GPU cluster (dedicated)"
            },
            "features": {
                "onboarding": "Independent KYC",
                "authentication": "Own auth system",
                "payments": "Stripe/PayPal integration",
                "banking": "Plaid/Yodlee connection"
            },
            "pricing": {
                "model": "Subscription",
                "tiers": ["Basic: $9/mo", "Pro: $29/mo", "Elite: $99/mo"]
            }
        }
    
    def _integrated_suite(self) -> Dict:
        """UltraWealth + UltraCore bundle"""
        return {
            "infrastructure": {
                "kubernetes_namespace": "ultracore-suite",
                "database": "PostgreSQL (shared + separate schemas)",
                "cache": "Redis (shared)",
                "message_broker": "Kafka (shared cluster)",
                "ml_compute": "GPU cluster (shared)"
            },
            "features": {
                "onboarding": "Unified KYC",
                "authentication": "SSO",
                "payments": "UltraCore payments",
                "banking": "Native integration"
            },
            "benefits": {
                "seamless_transfers": True,
                "unified_dashboard": True,
                "cross_product_insights": True,
                "single_customer_view": True
            },
            "pricing": {
                "model": "Bundle discount",
                "bundle": "Banking + Wealth: 20% off"
            }
        }
    
    def _white_label(self) -> Dict:
        """Partner white label deployment"""
        return {
            "customization": {
                "branding": "Full custom",
                "features": "Configurable",
                "ml_models": "Core + custom"
            },
            "deployment": {
                "model": "Multi-tenant",
                "isolation": "Schema-per-tenant",
                "data": "Complete isolation"
            },
            "revenue": {
                "model": "Revenue share",
                "split": "70/30 partner/platform"
            }
        }
    
    def _api_marketplace(self) -> Dict:
        """API-first marketplace model"""
        return {
            "distribution": {
                "channels": ["AWS Marketplace", "Azure Marketplace", "Direct API"],
                "documentation": "OpenAPI 3.0",
                "sdk": ["Python", "JavaScript", "Java", ".NET"]
            },
            "monetization": {
                "model": "Usage-based",
                "pricing": "$0.001 per API call",
                "volume_discounts": True
            }
        }

# Data Contract for Integration
class UltraWealthDataContract:
    """
    Defines data contracts between UltraWealth and UltraCore
    """
    
    def __init__(self):
        self.contracts = {
            "customer_sync": {
                "source": "ultracore.customers",
                "destination": "ultrawealth.investors",
                "fields": ["customer_id", "name", "kyc_status", "risk_profile"],
                "frequency": "real-time",
                "method": "kafka"
            },
            
            "account_balance": {
                "source": "ultracore.accounts",
                "destination": "ultrawealth.funding_sources",
                "fields": ["account_id", "available_balance", "currency"],
                "frequency": "on-demand",
                "method": "api"
            },
            
            "investment_transactions": {
                "source": "ultrawealth.transactions",
                "destination": "ultracore.ledger",
                "fields": ["transaction_id", "amount", "type", "status"],
                "frequency": "real-time",
                "method": "kafka"
            },
            
            "wealth_insights": {
                "source": "ultrawealth.analytics",
                "destination": "ultracore.customer_360",
                "fields": ["net_worth", "portfolio_value", "risk_score"],
                "frequency": "daily",
                "method": "batch"
            }
        }

# MCP Tool Namespacing
class UltraWealthMCPNamespace:
    """
    Separate MCP tool namespace for UltraWealth
    """
    
    def __init__(self):
        self.namespace = "ultrawealth"
        self.tools = {
            f"{self.namespace}.create_capsule": "Create investment capsule",
            f"{self.namespace}.optimize_portfolio": "ML optimization",
            f"{self.namespace}.rebalance": "Rebalance portfolio",
            f"{self.namespace}.get_performance": "Get performance metrics",
            
            # Integration tools (optional)
            f"{self.namespace}.sync_from_banking": "Sync banking data",
            f"{self.namespace}.transfer_to_investment": "Transfer from bank",
        }
    
    def get_standalone_tools(self):
        """Tools available in standalone mode"""
        return {k: v for k, v in self.tools.items() 
                if not "banking" in k and not "transfer" in k}
    
    def get_integrated_tools(self):
        """All tools for integrated mode"""
        return self.tools

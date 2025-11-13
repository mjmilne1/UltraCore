"""
UltraWealth Tenant Provisioning
Sets up UltraWealth as a separate tenant in UltraCore
"""

from decimal import Decimal
from typing import Dict, List


class UltraWealthTenant:
    """
    UltraWealth tenant configuration
    
    Provisions UltraWealth as a separate tenant with:
    - Tenant-specific settings
    - ETF universe
    - Fee structure
    - Compliance rules
    """
    
    TENANT_ID = "ultrawealth"
    TENANT_NAME = "UltraWealth Automated Investment Service"
    
    # Fee structure
    MANAGEMENT_FEE = Decimal("0.50")  # 0.50% p.a.
    PERFORMANCE_FEE = Decimal("0.00")  # No performance fee
    TRANSACTION_FEE = Decimal("0.00")  # No transaction fees
    
    # Investment universe (ASX ETFs)
    ETF_UNIVERSE = [
        # Australian Equity
        {"code": "VAS", "name": "Vanguard Australian Shares", "provider": "Vanguard", "category": "equity"},
        {"code": "IOZ", "name": "iShares Core S&P/ASX 200", "provider": "iShares", "category": "equity"},
        {"code": "A200", "name": "BetaShares Australia 200", "provider": "BetaShares", "category": "equity"},
        {"code": "STW", "name": "SPDR S&P/ASX 200", "provider": "SPDR", "category": "equity"},
        
        # International Equity
        {"code": "VGS", "name": "Vanguard MSCI Index International Shares", "provider": "Vanguard", "category": "equity"},
        {"code": "IVV", "name": "iShares S&P 500", "provider": "iShares", "category": "equity"},
        {"code": "NDQ", "name": "BetaShares NASDAQ 100", "provider": "BetaShares", "category": "equity"},
        
        # Fixed Income
        {"code": "VAF", "name": "Vanguard Australian Fixed Interest", "provider": "Vanguard", "category": "defensive"},
        {"code": "VGB", "name": "Vanguard Australian Government Bond", "provider": "Vanguard", "category": "defensive"},
        {"code": "BOND", "name": "BetaShares Australian Investment Grade Bond", "provider": "BetaShares", "category": "defensive"},
        
        # Cash
        {"code": "BILL", "name": "BetaShares Australian Bank Senior Floating Rate Bond", "provider": "BetaShares", "category": "defensive"},
        {"code": "AAA", "name": "BetaShares Australian High Interest Cash", "provider": "BetaShares", "category": "defensive"},
    ]
    
    # Business rules
    RULES = {
        "max_etfs_per_pod": 6,
        "min_etf_weight": Decimal("5.0"),
        "max_etf_weight": Decimal("40.0"),
        "max_single_provider": Decimal("60.0"),
        "rebalance_threshold": Decimal("5.0"),
        "circuit_breaker_threshold": Decimal("15.0"),
        "min_pod_value": Decimal("1000"),
        "min_contribution": Decimal("100"),
    }
    
    # Glide path settings
    GLIDE_PATH_CONFIG = {
        "first_home": {
            "10y_equity": Decimal("80"),
            "5y_equity": Decimal("60"),
            "2y_equity": Decimal("30"),
            "1y_equity": Decimal("10"),
        },
        "retirement": {
            "10y_equity": Decimal("90"),
            "5y_equity": Decimal("70"),
            "2y_equity": Decimal("50"),
            "1y_equity": Decimal("30"),
        },
        "wealth_accumulation": {
            "10y_equity": Decimal("85"),
            "5y_equity": Decimal("65"),
            "2y_equity": Decimal("40"),
            "1y_equity": Decimal("20"),
        },
    }
    
    # Tax settings (Australian)
    TAX_CONFIG = {
        "company_tax_rate": Decimal("30.0"),  # For franking credits
        "cgt_discount": Decimal("50.0"),  # 50% CGT discount
        "fhss_enabled": True,
        "fhss_max_contribution": Decimal("15000"),  # Per year
        "fhss_total_limit": Decimal("50000"),
    }
    
    # Compliance settings
    COMPLIANCE = {
        "regulatory_body": "ASIC",
        "afsl_required": True,
        "client_categorization": "retail",
        "soa_required": True,
        "ongoing_advice": True,
    }
    
    # Anya AI settings
    ANYA_CONFIG = {
        "enabled": True,
        "proactive_notifications": True,
        "24_7_support": True,
        "educational_content": True,
        "conversation_logging": True,
    }
    
    @classmethod
    def provision(cls) -> Dict:
        """
        Provision UltraWealth tenant
        
        Returns:
            Dict with tenant configuration
        """
        return {
            "tenant_id": cls.TENANT_ID,
            "tenant_name": cls.TENANT_NAME,
            "fees": {
                "management_fee": float(cls.MANAGEMENT_FEE),
                "performance_fee": float(cls.PERFORMANCE_FEE),
                "transaction_fee": float(cls.TRANSACTION_FEE),
            },
            "etf_universe": cls.ETF_UNIVERSE,
            "business_rules": {k: float(v) if isinstance(v, Decimal) else v for k, v in cls.RULES.items()},
            "glide_path_config": {
                goal: {k: float(v) for k, v in config.items()}
                for goal, config in cls.GLIDE_PATH_CONFIG.items()
            },
            "tax_config": {k: float(v) if isinstance(v, Decimal) else v for k, v in cls.TAX_CONFIG.items()},
            "compliance": cls.COMPLIANCE,
            "anya_config": cls.ANYA_CONFIG,
        }
    
    @classmethod
    def get_etf_universe(cls) -> List[Dict]:
        """Get ETF universe for UltraWealth"""
        return cls.ETF_UNIVERSE
    
    @classmethod
    def get_fee_structure(cls) -> Dict:
        """Get fee structure"""
        return {
            "management_fee": cls.MANAGEMENT_FEE,
            "performance_fee": cls.PERFORMANCE_FEE,
            "transaction_fee": cls.TRANSACTION_FEE,
        }
    
    @classmethod
    def get_business_rules(cls) -> Dict:
        """Get business rules"""
        return cls.RULES.copy()
    
    @classmethod
    def validate_pod_parameters(cls, **kwargs) -> Dict:
        """
        Validate Pod parameters against tenant rules
        
        Returns:
            Dict with validation result and errors
        """
        errors = []
        
        # Validate minimum pod value
        if "initial_value" in kwargs:
            if kwargs["initial_value"] < cls.RULES["min_pod_value"]:
                errors.append(f"Minimum pod value is ${cls.RULES['min_pod_value']}")
        
        # Validate minimum contribution
        if "monthly_contribution" in kwargs:
            if kwargs["monthly_contribution"] < cls.RULES["min_contribution"]:
                errors.append(f"Minimum monthly contribution is ${cls.RULES['min_contribution']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# Tenant registry
TENANT_REGISTRY = {
    "ultrawealth": UltraWealthTenant,
}


def get_tenant_config(tenant_id: str) -> Dict:
    """Get tenant configuration"""
    tenant_class = TENANT_REGISTRY.get(tenant_id)
    if not tenant_class:
        raise ValueError(f"Unknown tenant: {tenant_id}")
    
    return tenant_class.provision()


def get_tenant(tenant_id: str):
    """Get tenant class"""
    tenant_class = TENANT_REGISTRY.get(tenant_id)
    if not tenant_class:
        raise ValueError(f"Unknown tenant: {tenant_id}")
    
    return tenant_class

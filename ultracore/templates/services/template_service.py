"""Template Service with Australian Compliance"""
from typing import List, Dict, Optional
from decimal import Decimal
from ..events import TemplateType, PortfolioStrategy, RebalancingFrequency

class TemplateService:
    """Template management service"""
    
    # Australian-compliant portfolio templates
    AUSTRALIAN_PORTFOLIO_TEMPLATES = {
        "smsf_balanced": {
            "name": "SMSF Balanced Portfolio",
            "strategy": PortfolioStrategy.SMSF_BALANCED,
            "target_allocations": {
                "australian_equities": Decimal("35.0"),
                "international_equities": Decimal("25.0"),
                "australian_fixed_income": Decimal("25.0"),
                "property": Decimal("10.0"),
                "cash": Decimal("5.0")
            },
            "risk_level": 5,
            "min_investment": Decimal("50000"),
            "rebalancing_threshold": Decimal("5.0"),
            "includes_franking_credits": True,
            "is_australian_compliant": True
        },
        "franking_credit_focus": {
            "name": "Franking Credit Focus",
            "strategy": PortfolioStrategy.FRANKING_CREDIT_FOCUS,
            "target_allocations": {
                "australian_dividend_stocks": Decimal("60.0"),
                "australian_etfs": Decimal("25.0"),
                "cash": Decimal("15.0")
            },
            "risk_level": 6,
            "min_investment": Decimal("25000"),
            "rebalancing_threshold": Decimal("5.0"),
            "includes_franking_credits": True,
            "is_australian_compliant": True
        },
        "aggressive_growth": {
            "name": "Aggressive Growth",
            "strategy": PortfolioStrategy.AGGRESSIVE,
            "target_allocations": {
                "australian_equities": Decimal("40.0"),
                "international_equities": Decimal("50.0"),
                "cash": Decimal("10.0")
            },
            "risk_level": 8,
            "min_investment": Decimal("10000"),
            "rebalancing_threshold": Decimal("10.0"),
            "includes_franking_credits": False,
            "is_australian_compliant": True
        },
        "balanced": {
            "name": "Balanced Portfolio",
            "strategy": PortfolioStrategy.BALANCED,
            "target_allocations": {
                "australian_equities": Decimal("30.0"),
                "international_equities": Decimal("25.0"),
                "fixed_income": Decimal("30.0"),
                "property": Decimal("10.0"),
                "cash": Decimal("5.0")
            },
            "risk_level": 5,
            "min_investment": Decimal("5000"),
            "rebalancing_threshold": Decimal("5.0"),
            "includes_franking_credits": True,
            "is_australian_compliant": True
        },
        "conservative_income": {
            "name": "Conservative Income",
            "strategy": PortfolioStrategy.INCOME,
            "target_allocations": {
                "fixed_income": Decimal("50.0"),
                "australian_dividend_stocks": Decimal("25.0"),
                "property": Decimal("15.0"),
                "cash": Decimal("10.0")
            },
            "risk_level": 3,
            "min_investment": Decimal("10000"),
            "rebalancing_threshold": Decimal("3.0"),
            "includes_franking_credits": True,
            "is_australian_compliant": True
        }
    }
    
    # Rebalancing templates
    REBALANCING_TEMPLATES = {
        "quarterly_threshold": {
            "name": "Quarterly Threshold Rebalancing",
            "frequency": RebalancingFrequency.QUARTERLY,
            "threshold_percent": Decimal("5.0"),
            "min_trade_size": Decimal("1000"),
            "tax_loss_harvesting_enabled": True,
            "respect_wash_sale_rules": True  # Australian 30-day rule
        },
        "monthly_strict": {
            "name": "Monthly Strict Rebalancing",
            "frequency": RebalancingFrequency.MONTHLY,
            "threshold_percent": Decimal("3.0"),
            "min_trade_size": Decimal("500"),
            "tax_loss_harvesting_enabled": True,
            "respect_wash_sale_rules": True
        },
        "threshold_based": {
            "name": "Threshold-Based Rebalancing",
            "frequency": RebalancingFrequency.THRESHOLD_BASED,
            "threshold_percent": Decimal("10.0"),
            "min_trade_size": Decimal("2000"),
            "tax_loss_harvesting_enabled": True,
            "respect_wash_sale_rules": True
        }
    }
    
    # Alert rule templates
    ALERT_RULE_TEMPLATES = {
        "price_drop_10_percent": {
            "name": "Price Drop 10%",
            "alert_type": "price_change",
            "conditions": {
                "change_percent": -10.0,
                "timeframe": "1d"
            },
            "notification_channels": ["email", "push"]
        },
        "portfolio_value_threshold": {
            "name": "Portfolio Value Threshold",
            "alert_type": "portfolio_value",
            "conditions": {
                "threshold": 100000,
                "direction": "below"
            },
            "notification_channels": ["email"]
        },
        "dividend_payment": {
            "name": "Dividend Payment",
            "alert_type": "dividend",
            "conditions": {
                "event": "payment_received"
            },
            "notification_channels": ["email", "sms"]
        }
    }
    
    # Report templates (ASIC compliant)
    REPORT_TEMPLATES = {
        "asic_annual_statement": {
            "name": "ASIC Annual Statement",
            "report_type": "annual_statement",
            "sections": [
                "portfolio_summary",
                "transactions",
                "fees_charged",
                "tax_summary",
                "performance"
            ],
            "filters": {},
            "is_asic_compliant": True
        },
        "capital_gains_tax": {
            "name": "Capital Gains Tax Report",
            "report_type": "tax_report",
            "sections": [
                "capital_gains",
                "capital_losses",
                "net_capital_gain",
                "cgt_discount"
            ],
            "filters": {"tax_year": "current"},
            "is_asic_compliant": True
        },
        "franking_credits": {
            "name": "Franking Credits Report",
            "report_type": "tax_report",
            "sections": [
                "franked_dividends",
                "franking_credits",
                "grossed_up_dividends"
            ],
            "filters": {"tax_year": "current"},
            "is_asic_compliant": True
        }
    }
    
    def get_portfolio_template(self, template_key: str) -> Optional[Dict]:
        """Get portfolio template by key"""
        return self.AUSTRALIAN_PORTFOLIO_TEMPLATES.get(template_key)
    
    def get_rebalancing_template(self, template_key: str) -> Optional[Dict]:
        """Get rebalancing template by key"""
        return self.REBALANCING_TEMPLATES.get(template_key)
    
    def get_alert_rule_template(self, template_key: str) -> Optional[Dict]:
        """Get alert rule template by key"""
        return self.ALERT_RULE_TEMPLATES.get(template_key)
    
    def get_report_template(self, template_key: str) -> Optional[Dict]:
        """Get report template by key"""
        return self.REPORT_TEMPLATES.get(template_key)
    
    def list_all_templates(self) -> Dict:
        """List all available templates"""
        return {
            "portfolio_templates": list(self.AUSTRALIAN_PORTFOLIO_TEMPLATES.keys()),
            "rebalancing_templates": list(self.REBALANCING_TEMPLATES.keys()),
            "alert_rule_templates": list(self.ALERT_RULE_TEMPLATES.keys()),
            "report_templates": list(self.REPORT_TEMPLATES.keys())
        }

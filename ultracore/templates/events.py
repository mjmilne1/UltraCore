"""Templates & Presets Events"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal

class TemplateType(Enum):
    """Template types"""
    PORTFOLIO = "portfolio"
    REBALANCING = "rebalancing"
    ALERT_RULE = "alert_rule"
    REPORT = "report"

class PortfolioStrategy(Enum):
    """Portfolio strategies"""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    INCOME = "income"
    GROWTH = "growth"
    SMSF_BALANCED = "smsf_balanced"  # Australian SMSF
    FRANKING_CREDIT_FOCUS = "franking_credit_focus"  # Australian

class RebalancingFrequency(Enum):
    """Rebalancing frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    THRESHOLD_BASED = "threshold_based"

@dataclass
class TemplateCreatedEvent:
    """Template created"""
    template_id: str
    template_name: str
    template_type: TemplateType
    category: str
    configuration: Dict
    is_public: bool
    is_australian_compliant: bool
    created_by: str
    tenant_id: str
    timestamp: datetime

@dataclass
class TemplateUpdatedEvent:
    """Template updated"""
    template_id: str
    template_name: Optional[str]
    configuration: Optional[Dict]
    is_public: Optional[bool]
    updated_by: str
    timestamp: datetime

@dataclass
class TemplateAppliedEvent:
    """Template applied to entity"""
    template_id: str
    applied_to_type: str  # portfolio, alert, etc.
    applied_to_id: str
    user_id: str
    tenant_id: str
    customizations: Optional[Dict]
    timestamp: datetime

@dataclass
class PortfolioTemplateCreatedEvent:
    """Portfolio template created"""
    template_id: str
    template_name: str
    strategy: PortfolioStrategy
    target_allocations: Dict[str, Decimal]  # asset_class -> percentage
    risk_level: int  # 1-10
    min_investment: Decimal
    rebalancing_threshold: Decimal
    is_australian_compliant: bool
    includes_franking_credits: bool
    created_by: str
    timestamp: datetime

@dataclass
class RebalancingTemplateCreatedEvent:
    """Rebalancing template created"""
    template_id: str
    template_name: str
    frequency: RebalancingFrequency
    threshold_percent: Decimal
    min_trade_size: Decimal
    tax_loss_harvesting_enabled: bool
    respect_wash_sale_rules: bool  # Australian 30-day rule
    created_by: str
    timestamp: datetime

@dataclass
class AlertRuleTemplateCreatedEvent:
    """Alert rule template created"""
    template_id: str
    template_name: str
    alert_type: str
    conditions: Dict
    notification_channels: List[str]
    created_by: str
    timestamp: datetime

@dataclass
class ReportTemplateCreatedEvent:
    """Report template created"""
    template_id: str
    template_name: str
    report_type: str
    sections: List[str]
    filters: Dict
    is_asic_compliant: bool
    created_by: str
    timestamp: datetime

@dataclass
class TemplatePublishedEvent:
    """Template published to marketplace"""
    template_id: str
    published_by: str
    price: Optional[Decimal]
    timestamp: datetime

@dataclass
class TemplateDeletedEvent:
    """Template deleted"""
    template_id: str
    deleted_by: str
    timestamp: datetime

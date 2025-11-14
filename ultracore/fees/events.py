"""Fee & Pricing Events - Kafka schemas for billing system"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


class FeeType(str, Enum):
    MANAGEMENT = "management"  # % of AUM annually
    PERFORMANCE = "performance"  # % of gains
    TRANSACTION = "transaction"  # Per transaction
    SUBSCRIPTION = "subscription"  # Monthly/annual subscription
    ADVISORY = "advisory"  # Advisory services
    PLATFORM = "platform"  # Platform usage
    CUSTOM = "custom"  # Custom fee


class BillingFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    PER_TRANSACTION = "per_transaction"


class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class FeeStructureCreated:
    tenant_id: str
    fee_structure_id: str
    name: str
    fee_type: FeeType
    rate: Decimal  # Percentage or fixed amount
    min_fee: Optional[Decimal]
    max_fee: Optional[Decimal]
    frequency: BillingFrequency
    calculation_method: str  # Formula or method name
    applies_to: Dict[str, Any]  # Conditions
    created_by: str
    created_at: datetime


@dataclass
class FeeCharged:
    tenant_id: str
    fee_id: str
    user_id: str
    fee_structure_id: str
    amount: Decimal
    currency: str
    calculation_details: Dict[str, Any]
    period_start: datetime
    period_end: datetime
    charged_at: datetime


@dataclass
class FeeWaived:
    tenant_id: str
    fee_id: str
    user_id: str
    waiver_reason: str
    waived_amount: Decimal
    promotion_id: Optional[str]
    waived_by: str
    waived_at: datetime


@dataclass
class SubscriptionCreated:
    tenant_id: str
    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    monthly_fee: Decimal
    annual_fee: Optional[Decimal]
    features: Dict[str, Any]
    billing_frequency: BillingFrequency
    created_at: datetime


@dataclass
class SubscriptionUpgraded:
    tenant_id: str
    subscription_id: str
    from_tier: SubscriptionTier
    to_tier: SubscriptionTier
    prorated_amount: Decimal
    upgraded_at: datetime


@dataclass
class PromotionCreated:
    tenant_id: str
    promotion_id: str
    name: str
    discount_percentage: Optional[Decimal]
    discount_amount: Optional[Decimal]
    applies_to_tiers: list
    valid_from: datetime
    valid_until: datetime
    created_by: str
    created_at: datetime

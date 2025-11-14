"""Fee Structure Aggregate"""
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Any, List, Optional, Dict
from ultracore.fees.events import *
from ultracore.fees.event_publisher import get_fee_event_publisher

@dataclass
class FeeStructureAggregate:
    tenant_id: str
    fee_structure_id: str
    name: str = ""
    fee_type: FeeType = FeeType.CUSTOM
    rate: Decimal = Decimal("0")
    _events: List[Any] = field(default_factory=list)
    
    def create(self, name: str, fee_type: FeeType, rate: Decimal,
               min_fee: Optional[Decimal], max_fee: Optional[Decimal],
               frequency: BillingFrequency, calculation_method: str,
               applies_to: Dict[str, Any], created_by: str):
        event = FeeStructureCreated(
            tenant_id=self.tenant_id, fee_structure_id=self.fee_structure_id,
            name=name, fee_type=fee_type, rate=rate, min_fee=min_fee,
            max_fee=max_fee, frequency=frequency, calculation_method=calculation_method,
            applies_to=applies_to, created_by=created_by, created_at=datetime.utcnow()
        )
        self._apply(event)
        get_fee_event_publisher().publish_fee_structure_event(event)
    
    def _apply(self, event):
        if isinstance(event, FeeStructureCreated):
            self.name, self.fee_type, self.rate = event.name, event.fee_type, event.rate
        self._events.append(event)

@dataclass
class SubscriptionAggregate:
    tenant_id: str
    subscription_id: str
    user_id: str = ""
    tier: SubscriptionTier = SubscriptionTier.FREE
    _events: List[Any] = field(default_factory=list)
    
    def create(self, user_id: str, tier: SubscriptionTier, monthly_fee: Decimal,
               annual_fee: Optional[Decimal], features: Dict[str, Any],
               billing_frequency: BillingFrequency):
        event = SubscriptionCreated(
            tenant_id=self.tenant_id, subscription_id=self.subscription_id,
            user_id=user_id, tier=tier, monthly_fee=monthly_fee,
            annual_fee=annual_fee, features=features, billing_frequency=billing_frequency,
            created_at=datetime.utcnow()
        )
        self._apply(event)
        get_fee_event_publisher().publish_subscription_event(event)
    
    def upgrade(self, to_tier: SubscriptionTier, prorated_amount: Decimal):
        event = SubscriptionUpgraded(
            tenant_id=self.tenant_id, subscription_id=self.subscription_id,
            from_tier=self.tier, to_tier=to_tier, prorated_amount=prorated_amount,
            upgraded_at=datetime.utcnow()
        )
        self._apply(event)
        get_fee_event_publisher().publish_subscription_event(event)
    
    def _apply(self, event):
        if isinstance(event, SubscriptionCreated):
            self.user_id, self.tier = event.user_id, event.tier
        elif isinstance(event, SubscriptionUpgraded):
            self.tier = event.to_tier
        self._events.append(event)

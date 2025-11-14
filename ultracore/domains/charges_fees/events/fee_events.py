"""
Fee Events
Event schemas for charges and fees management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ultracore.domains.charges_fees.models.fee import FeeType


class FeeAppliedEvent(BaseModel):
    """Event: Fee applied to account or loan"""
    
    fee_id: UUID
    tenant_id: UUID
    
    account_id: Optional[UUID] = None
    loan_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    
    fee_type: FeeType
    fee_name: str
    amount: Decimal
    currency: str = "AUD"
    
    applied_date: date
    charging_rule_id: Optional[UUID] = None
    
    metadata: Optional[Dict[str, Any]] = None


class FeeWaivedEvent(BaseModel):
    """Event: Fee waived"""
    
    fee_id: UUID
    tenant_id: UUID
    
    account_id: Optional[UUID] = None
    loan_id: Optional[UUID] = None
    
    fee_type: FeeType
    fee_name: str
    amount: Decimal
    
    waiver_reason: str
    waived_by: str
    waived_date: date
    
    metadata: Optional[Dict[str, Any]] = None


class FeeRefundedEvent(BaseModel):
    """Event: Fee refunded"""
    
    fee_id: UUID
    tenant_id: UUID
    
    account_id: Optional[UUID] = None
    loan_id: Optional[UUID] = None
    
    fee_type: FeeType
    fee_name: str
    original_amount: Decimal
    refund_amount: Decimal
    
    refund_reason: str
    refunded_by: str
    refunded_date: date
    
    metadata: Optional[Dict[str, Any]] = None


class FeeRevenueRecognizedEvent(BaseModel):
    """Event: Fee revenue recognized in GL"""
    
    fee_id: UUID
    tenant_id: UUID
    
    fee_type: FeeType
    amount: Decimal
    
    gl_entry_id: UUID
    recognition_date: date
    
    metadata: Optional[Dict[str, Any]] = None


class ChargingRuleCreatedEvent(BaseModel):
    """Event: Charging rule created"""
    
    rule_id: UUID
    tenant_id: UUID
    
    rule_name: str
    rule_code: str
    fee_type: FeeType
    
    trigger_type: str
    amount_type: str
    
    created_by: str
    created_at: datetime
    
    metadata: Optional[Dict[str, Any]] = None


class ChargingRuleActivatedEvent(BaseModel):
    """Event: Charging rule activated"""
    
    rule_id: UUID
    tenant_id: UUID
    
    rule_name: str
    activated_by: str
    activated_at: datetime
    
    metadata: Optional[Dict[str, Any]] = None


class ChargingRuleDeactivatedEvent(BaseModel):
    """Event: Charging rule deactivated"""
    
    rule_id: UUID
    tenant_id: UUID
    
    rule_name: str
    deactivated_by: str
    deactivated_at: datetime
    
    metadata: Optional[Dict[str, Any]] = None


class FeeRevenueCalculatedEvent(BaseModel):
    """Event: Fee revenue calculated for period"""
    
    revenue_id: UUID
    tenant_id: UUID
    
    period_start: date
    period_end: date
    
    total_fees_applied: Decimal
    total_fees_waived: Decimal
    total_fees_refunded: Decimal
    net_fee_revenue: Decimal
    
    revenue_by_type: Dict[str, Decimal]
    
    calculated_at: datetime
    
    metadata: Optional[Dict[str, Any]] = None


# Kafka topic names
class FeeTopics:
    """Kafka topics for fee events"""
    
    APPLIED = "ultracore.fees.applied"
    WAIVED = "ultracore.fees.waived"
    REFUNDED = "ultracore.fees.refunded"
    REVENUE = "ultracore.fees.revenue"
    RULES = "ultracore.fees.rules"

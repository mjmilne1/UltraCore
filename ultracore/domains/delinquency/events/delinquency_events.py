"""
Delinquency Events
Event schemas for delinquency management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ultracore.domains.delinquency.models.delinquency_status import (
    DelinquencyBucket,
    RiskLevel,
)


class LoanBecameDelinquentEvent(BaseModel):
    """Event: Loan became delinquent (first missed payment)"""
    
    loan_id: UUID
    tenant_id: UUID
    
    days_past_due: int
    amount_overdue: Decimal
    next_due_date: date
    first_delinquent_date: date
    
    triggered_by: str  # "missed_payment", "payment_reversal", etc.
    
    metadata: Optional[Dict[str, Any]] = None


class DelinquencyBucketChangedEvent(BaseModel):
    """Event: Loan moved to different delinquency bucket"""
    
    loan_id: UUID
    tenant_id: UUID
    
    previous_bucket: DelinquencyBucket
    new_bucket: DelinquencyBucket
    days_past_due: int
    amount_overdue: Decimal
    
    risk_level: RiskLevel
    bucket_entry_date: date
    
    automated_actions: list[Dict[str, Any]] = Field(default_factory=list)
    
    metadata: Optional[Dict[str, Any]] = None


class DelinquencyCuredEvent(BaseModel):
    """Event: Loan delinquency cured (returned to current)"""
    
    loan_id: UUID
    tenant_id: UUID
    
    previous_bucket: DelinquencyBucket
    days_delinquent: int  # Total days spent in delinquency
    total_amount_paid: Decimal
    
    cured_date: date
    cured_by: str  # "full_payment", "payment_plan", etc.
    
    metadata: Optional[Dict[str, Any]] = None


class LoanDefaultedEvent(BaseModel):
    """Event: Loan moved to default status"""
    
    loan_id: UUID
    tenant_id: UUID
    
    days_past_due: int
    amount_overdue: Decimal
    principal_overdue: Decimal
    interest_overdue: Decimal
    fees_overdue: Decimal
    
    defaulted_date: date
    default_reason: str
    
    metadata: Optional[Dict[str, Any]] = None


class LateFeeAppliedEvent(BaseModel):
    """Event: Late fee applied to loan"""
    
    loan_id: UUID
    tenant_id: UUID
    
    fee_amount: Decimal
    fee_reason: str
    days_past_due: int
    current_bucket: DelinquencyBucket
    
    applied_date: date
    
    metadata: Optional[Dict[str, Any]] = None


class PaymentReminderSentEvent(BaseModel):
    """Event: Payment reminder sent to customer"""
    
    loan_id: UUID
    tenant_id: UUID
    customer_id: UUID
    
    reminder_type: str  # "sms", "email", "push", "letter"
    days_past_due: int
    amount_overdue: Decimal
    
    sent_date: datetime
    
    metadata: Optional[Dict[str, Any]] = None


class CollectionNoticeIssuedEvent(BaseModel):
    """Event: Formal collection notice issued"""
    
    loan_id: UUID
    tenant_id: UUID
    customer_id: UUID
    
    notice_type: str  # "first_notice", "final_notice", "legal_notice"
    days_past_due: int
    amount_overdue: Decimal
    
    issued_date: date
    response_deadline: date
    
    metadata: Optional[Dict[str, Any]] = None


class ProvisioningUpdatedEvent(BaseModel):
    """Event: Loan provisioning updated"""
    
    loan_id: UUID
    tenant_id: UUID
    
    previous_provision_amount: Decimal
    new_provision_amount: Decimal
    provision_percentage: Decimal
    
    current_bucket: DelinquencyBucket
    outstanding_balance: Decimal
    
    updated_date: date
    
    metadata: Optional[Dict[str, Any]] = None


class LoanWrittenOffEvent(BaseModel):
    """Event: Loan written off"""
    
    loan_id: UUID
    tenant_id: UUID
    
    write_off_amount: Decimal
    principal_written_off: Decimal
    interest_written_off: Decimal
    fees_written_off: Decimal
    
    days_past_due: int
    write_off_date: date
    write_off_reason: str
    approved_by: str
    
    metadata: Optional[Dict[str, Any]] = None


class PortfolioAtRiskCalculatedEvent(BaseModel):
    """Event: Portfolio at Risk metrics calculated"""
    
    tenant_id: UUID
    calculation_date: date
    
    total_loans: int
    total_outstanding_balance: Decimal
    
    par_1: Decimal
    par_30: Decimal
    par_60: Decimal
    par_90: Decimal
    
    amount_at_risk_30: Decimal
    amount_at_risk_60: Decimal
    amount_at_risk_90: Decimal
    
    total_provisioning_required: Decimal
    
    metadata: Optional[Dict[str, Any]] = None


class DelinquencyStatusUpdatedEvent(BaseModel):
    """Event: Delinquency status updated (daily batch update)"""
    
    loan_id: UUID
    tenant_id: UUID
    
    days_past_due: int
    current_bucket: DelinquencyBucket
    amount_overdue: Decimal
    
    is_delinquent: bool
    consecutive_missed_payments: int
    
    updated_date: date
    
    metadata: Optional[Dict[str, Any]] = None


# Kafka topic names
class DelinquencyTopics:
    """Kafka topics for delinquency events"""
    
    STATUS = "ultracore.delinquency.status"
    BUCKETS = "ultracore.delinquency.buckets"
    ACTIONS = "ultracore.delinquency.actions"
    PORTFOLIO = "ultracore.delinquency.portfolio"
    PROVISIONING = "ultracore.delinquency.provisioning"

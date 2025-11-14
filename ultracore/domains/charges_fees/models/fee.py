"""
Fee Models
Domain models for charges and fees management
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
from enum import Enum


class FeeType(str, Enum):
    """Fee type classification"""
    # Account fees
    MONTHLY_MAINTENANCE = "monthly_maintenance"
    MINIMUM_BALANCE = "minimum_balance"
    DORMANCY = "dormancy"
    ACCOUNT_CLOSURE = "account_closure"
    
    # Transaction fees
    ATM_WITHDRAWAL = "atm_withdrawal"
    OTC_WITHDRAWAL = "otc_withdrawal"
    TRANSFER = "transfer"
    FOREIGN_TRANSACTION = "foreign_transaction"
    
    # Loan fees
    ORIGINATION = "origination"
    LATE_PAYMENT = "late_payment"
    EARLY_REPAYMENT = "early_repayment"
    RESTRUCTURING = "restructuring"
    
    # Service fees
    STATEMENT = "statement"
    CARD_REPLACEMENT = "card_replacement"
    STOP_PAYMENT = "stop_payment"
    RETURNED_PAYMENT = "returned_payment"
    
    # Penalty fees
    OVERDRAFT = "overdraft"
    NSF = "nsf"  # Non-sufficient funds
    
    # Other
    CUSTOM = "custom"


class FeeStatus(str, Enum):
    """Fee status"""
    PENDING = "pending"
    APPLIED = "applied"
    WAIVED = "waived"
    REFUNDED = "refunded"
    REVERSED = "reversed"


class Fee(BaseModel):
    """
    Fee
    
    Represents a charge or fee applied to an account or loan
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    # Identifiers
    fee_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Related entity (account or loan)
    account_id: Optional[UUID] = None
    loan_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    
    # Fee details
    fee_type: FeeType
    fee_name: str
    description: Optional[str] = None
    
    # Amount
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="AUD")
    
    # Status
    status: FeeStatus = Field(default=FeeStatus.PENDING)
    
    # Dates
    applied_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    
    # Waiver
    is_waived: bool = Field(default=False)
    waiver_reason: Optional[str] = None
    waived_by: Optional[str] = None
    waived_date: Optional[date] = None
    
    # Refund
    is_refunded: bool = Field(default=False)
    refund_amount: Decimal = Field(default=Decimal("0.00"))
    refund_reason: Optional[str] = None
    refunded_by: Optional[str] = None
    refunded_date: Optional[date] = None
    
    # Revenue recognition
    revenue_recognized: bool = Field(default=False)
    revenue_recognition_date: Optional[date] = None
    gl_entry_id: Optional[UUID] = None
    
    # Charging rule
    charging_rule_id: Optional[UUID] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def apply(self):
        """Mark fee as applied"""
        self.status = FeeStatus.APPLIED
        self.applied_date = date.today()
        self.updated_at = datetime.utcnow()
    
    def waive(self, reason: str, waived_by: str):
        """Waive the fee"""
        self.status = FeeStatus.WAIVED
        self.is_waived = True
        self.waiver_reason = reason
        self.waived_by = waived_by
        self.waived_date = date.today()
        self.updated_at = datetime.utcnow()
    
    def refund(self, amount: Decimal, reason: str, refunded_by: str):
        """Refund the fee"""
        self.status = FeeStatus.REFUNDED
        self.is_refunded = True
        self.refund_amount = amount
        self.refund_reason = reason
        self.refunded_by = refunded_by
        self.refunded_date = date.today()
        self.updated_at = datetime.utcnow()
    
    def recognize_revenue(self, gl_entry_id: UUID):
        """Mark revenue as recognized"""
        self.revenue_recognized = True
        self.revenue_recognition_date = date.today()
        self.gl_entry_id = gl_entry_id
        self.updated_at = datetime.utcnow()


class TriggerType(str, Enum):
    """Charging rule trigger type"""
    EVENT = "event"  # Triggered by specific event
    SCHEDULE = "schedule"  # Triggered by schedule (monthly, etc.)
    CONDITIONAL = "conditional"  # Triggered by condition
    MANUAL = "manual"  # Manual application


class AmountType(str, Enum):
    """Fee amount calculation type"""
    FIXED = "fixed"  # Fixed amount
    PERCENTAGE = "percentage"  # Percentage of balance/transaction
    TIERED = "tiered"  # Tiered based on volume/balance


class ChargingRule(BaseModel):
    """
    Charging Rule
    
    Defines automated fee charging rules
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    # Identifiers
    rule_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Rule details
    rule_name: str
    rule_code: str  # Unique code for the rule
    description: Optional[str] = None
    
    # Fee type
    fee_type: FeeType
    fee_name: str
    
    # Trigger
    trigger_type: TriggerType
    trigger_event: Optional[str] = None  # Event name (e.g., "PaymentMissed")
    schedule: Optional[str] = None  # Cron expression for scheduled fees
    
    # Amount calculation
    amount_type: AmountType
    fixed_amount: Optional[Decimal] = None
    percentage: Optional[Decimal] = None  # For percentage-based fees
    tiered_amounts: Optional[Dict[str, Decimal]] = None  # For tiered fees
    
    # Conditions
    conditions: Dict[str, Any] = Field(default_factory=dict)
    waiver_conditions: Dict[str, Any] = Field(default_factory=dict)
    
    # Applicability
    applies_to_products: list[str] = Field(default_factory=list)  # Product codes
    applies_to_accounts: list[UUID] = Field(default_factory=list)  # Specific accounts
    
    # Status
    is_active: bool = Field(default=True)
    
    # Limits
    max_fee_amount: Optional[Decimal] = None
    max_fees_per_period: Optional[int] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    
    def activate(self):
        """Activate the charging rule"""
        self.is_active = True
        self.activated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the charging rule"""
        self.is_active = False
        self.deactivated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def calculate_fee_amount(
        self,
        base_amount: Optional[Decimal] = None,
        tier_key: Optional[str] = None
    ) -> Decimal:
        """
        Calculate fee amount based on amount type
        
        Args:
            base_amount: Base amount for percentage calculation
            tier_key: Tier key for tiered fees
        
        Returns:
            Calculated fee amount
        """
        if self.amount_type == AmountType.FIXED:
            amount = self.fixed_amount or Decimal("0.00")
        elif self.amount_type == AmountType.PERCENTAGE:
            if base_amount is None:
                raise ValueError("base_amount required for percentage fees")
            amount = base_amount * (self.percentage or Decimal("0.00")) / 100
        elif self.amount_type == AmountType.TIERED:
            if tier_key is None or self.tiered_amounts is None:
                raise ValueError("tier_key and tiered_amounts required for tiered fees")
            amount = self.tiered_amounts.get(tier_key, Decimal("0.00"))
        else:
            amount = Decimal("0.00")
        
        # Apply max fee limit
        if self.max_fee_amount and amount > self.max_fee_amount:
            amount = self.max_fee_amount
        
        return amount
    
    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if conditions are met
        
        Args:
            context: Context data for condition evaluation
        
        Returns:
            True if conditions are met
        """
        if not self.conditions:
            return True
        
        for key, condition in self.conditions.items():
            value = context.get(key)
            
            if value is None:
                return False
            
            # Simple condition evaluation (can be enhanced)
            if isinstance(condition, str):
                if condition.startswith(">="):
                    threshold = Decimal(condition[2:].strip())
                    if Decimal(str(value)) < threshold:
                        return False
                elif condition.startswith(">"):
                    threshold = Decimal(condition[1:].strip())
                    if Decimal(str(value)) <= threshold:
                        return False
                elif condition.startswith("<="):
                    threshold = Decimal(condition[2:].strip())
                    if Decimal(str(value)) > threshold:
                        return False
                elif condition.startswith("<"):
                    threshold = Decimal(condition[1:].strip())
                    if Decimal(str(value)) >= threshold:
                        return False
                elif condition.startswith("=="):
                    expected = condition[2:].strip()
                    if str(value) != expected:
                        return False
                else:
                    # Exact match
                    if str(value) != condition:
                        return False
        
        return True
    
    def evaluate_waiver_conditions(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if waiver conditions are met
        
        Args:
            context: Context data for waiver evaluation
        
        Returns:
            True if fee should be waived
        """
        if not self.waiver_conditions:
            return False
        
        # Use same logic as evaluate_conditions
        for key, condition in self.waiver_conditions.items():
            value = context.get(key)
            
            if value is None:
                continue
            
            if isinstance(condition, str):
                if condition.startswith(">="):
                    threshold = Decimal(condition[2:].strip())
                    if Decimal(str(value)) >= threshold:
                        return True
                elif condition.startswith(">"):
                    threshold = Decimal(condition[1:].strip())
                    if Decimal(str(value)) > threshold:
                        return True
        
        return False


class FeeRevenue(BaseModel):
    """
    Fee Revenue
    
    Aggregated fee revenue metrics for reporting
    """
    
    # Identifiers
    revenue_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    
    # Period
    period_start: date
    period_end: date
    
    # Totals
    total_fees_applied: Decimal = Field(default=Decimal("0.00"))
    total_fees_waived: Decimal = Field(default=Decimal("0.00"))
    total_fees_refunded: Decimal = Field(default=Decimal("0.00"))
    net_fee_revenue: Decimal = Field(default=Decimal("0.00"))
    
    # Breakdown by fee type
    revenue_by_type: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Breakdown by product
    revenue_by_product: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Counts
    total_fees_count: int = Field(default=0)
    waived_fees_count: int = Field(default=0)
    refunded_fees_count: int = Field(default=0)
    
    # Audit
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_net_revenue(self):
        """Calculate net fee revenue"""
        self.net_fee_revenue = (
            self.total_fees_applied - 
            self.total_fees_waived - 
            self.total_fees_refunded
        )

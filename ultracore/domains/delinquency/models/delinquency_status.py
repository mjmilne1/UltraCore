"""
Delinquency Status Model
Tracks loan delinquency status and bucket classification
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
from enum import Enum


class DelinquencyBucket(str, Enum):
    """Delinquency bucket classification"""
    CURRENT = "current"  # 0 days past due
    BUCKET_1 = "bucket_1"  # 1-30 days past due
    BUCKET_2 = "bucket_2"  # 31-60 days past due
    BUCKET_3 = "bucket_3"  # 61-90 days past due
    BUCKET_4 = "bucket_4"  # 91+ days past due
    DEFAULTED = "defaulted"  # Loan in default
    WRITTEN_OFF = "written_off"  # Loan written off


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DelinquencyStatus(BaseModel):
    """
    Delinquency Status
    
    Tracks the current delinquency status of a loan
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    # Identifiers
    status_id: UUID = Field(default_factory=uuid4)
    loan_id: UUID
    tenant_id: UUID
    
    # Delinquency metrics
    days_past_due: int = Field(default=0, ge=0)
    current_bucket: DelinquencyBucket = Field(default=DelinquencyBucket.CURRENT)
    previous_bucket: Optional[DelinquencyBucket] = None
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    
    # Financial metrics
    amount_overdue: Decimal = Field(default=Decimal("0.00"))
    principal_overdue: Decimal = Field(default=Decimal("0.00"))
    interest_overdue: Decimal = Field(default=Decimal("0.00"))
    fees_overdue: Decimal = Field(default=Decimal("0.00"))
    
    # Dates
    last_payment_date: Optional[date] = None
    next_due_date: Optional[date] = None
    first_delinquent_date: Optional[date] = None  # When loan first became delinquent
    bucket_entry_date: date = Field(default_factory=date.today)  # When entered current bucket
    
    # Status tracking
    is_delinquent: bool = Field(default=False)
    consecutive_missed_payments: int = Field(default=0)
    total_missed_payments: int = Field(default=0)
    
    # Actions taken
    reminders_sent: int = Field(default=0)
    collection_notices_sent: int = Field(default=0)
    late_fees_applied: Decimal = Field(default=Decimal("0.00"))
    
    # ML predictions
    default_probability: Optional[Decimal] = None  # 0-100%
    cure_probability: Optional[Decimal] = None  # 0-100%
    recommended_action: Optional[str] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def update_bucket(self) -> Optional[DelinquencyBucket]:
        """
        Update delinquency bucket based on days past due
        
        Returns:
            New bucket if changed, None otherwise
        """
        old_bucket = self.current_bucket
        
        # Determine new bucket
        if self.days_past_due == 0:
            new_bucket = DelinquencyBucket.CURRENT
        elif self.days_past_due <= 30:
            new_bucket = DelinquencyBucket.BUCKET_1
        elif self.days_past_due <= 60:
            new_bucket = DelinquencyBucket.BUCKET_2
        elif self.days_past_due <= 90:
            new_bucket = DelinquencyBucket.BUCKET_3
        else:
            new_bucket = DelinquencyBucket.BUCKET_4
        
        # Update if changed
        if new_bucket != old_bucket:
            self.previous_bucket = old_bucket
            self.current_bucket = new_bucket
            self.bucket_entry_date = date.today()
            self.update_risk_level()
            return new_bucket
        
        return None
    
    def update_risk_level(self):
        """Update risk level based on bucket"""
        risk_mapping = {
            DelinquencyBucket.CURRENT: RiskLevel.LOW,
            DelinquencyBucket.BUCKET_1: RiskLevel.LOW,
            DelinquencyBucket.BUCKET_2: RiskLevel.MEDIUM,
            DelinquencyBucket.BUCKET_3: RiskLevel.HIGH,
            DelinquencyBucket.BUCKET_4: RiskLevel.CRITICAL,
            DelinquencyBucket.DEFAULTED: RiskLevel.CRITICAL,
            DelinquencyBucket.WRITTEN_OFF: RiskLevel.CRITICAL,
        }
        self.risk_level = risk_mapping.get(self.current_bucket, RiskLevel.LOW)
    
    def mark_delinquent(self):
        """Mark loan as delinquent"""
        if not self.is_delinquent:
            self.is_delinquent = True
            self.first_delinquent_date = date.today()
    
    def mark_current(self):
        """Mark loan as current (delinquency cured)"""
        self.is_delinquent = False
        self.days_past_due = 0
        self.previous_bucket = self.current_bucket
        self.current_bucket = DelinquencyBucket.CURRENT
        self.risk_level = RiskLevel.LOW
        self.amount_overdue = Decimal("0.00")
        self.principal_overdue = Decimal("0.00")
        self.interest_overdue = Decimal("0.00")
        self.fees_overdue = Decimal("0.00")
    
    def get_bucket_display_name(self) -> str:
        """Get human-readable bucket name"""
        display_names = {
            DelinquencyBucket.CURRENT: "Current",
            DelinquencyBucket.BUCKET_1: "1-30 Days Past Due",
            DelinquencyBucket.BUCKET_2: "31-60 Days Past Due",
            DelinquencyBucket.BUCKET_3: "61-90 Days Past Due",
            DelinquencyBucket.BUCKET_4: "91+ Days Past Due",
            DelinquencyBucket.DEFAULTED: "Defaulted",
            DelinquencyBucket.WRITTEN_OFF: "Written Off",
        }
        return display_names.get(self.current_bucket, "Unknown")
    
    def get_days_in_current_bucket(self) -> int:
        """Get number of days in current bucket"""
        if self.bucket_entry_date:
            return (date.today() - self.bucket_entry_date).days
        return 0


class BucketConfiguration(BaseModel):
    """
    Delinquency Bucket Configuration
    
    Defines bucket ranges and automated actions
    """
    
    bucket: DelinquencyBucket
    min_days: int
    max_days: Optional[int]
    risk_level: RiskLevel
    
    # Automated actions
    send_reminder: bool = Field(default=False)
    apply_late_fee: bool = Field(default=False)
    late_fee_amount: Decimal = Field(default=Decimal("0.00"))
    send_collection_notice: bool = Field(default=False)
    escalate_to_collections: bool = Field(default=False)
    
    # Provisioning
    provision_percentage: Decimal = Field(default=Decimal("0.00"))  # % of outstanding balance
    
    # Display
    display_name: str
    description: str


# Default bucket configurations
DEFAULT_BUCKET_CONFIGS = [
    BucketConfiguration(
        bucket=DelinquencyBucket.CURRENT,
        min_days=0,
        max_days=0,
        risk_level=RiskLevel.LOW,
        display_name="Current",
        description="No payments overdue",
        provision_percentage=Decimal("0.00"),
    ),
    BucketConfiguration(
        bucket=DelinquencyBucket.BUCKET_1,
        min_days=1,
        max_days=30,
        risk_level=RiskLevel.LOW,
        display_name="1-30 Days Past Due",
        description="Early stage delinquency",
        send_reminder=True,
        provision_percentage=Decimal("1.00"),
    ),
    BucketConfiguration(
        bucket=DelinquencyBucket.BUCKET_2,
        min_days=31,
        max_days=60,
        risk_level=RiskLevel.MEDIUM,
        display_name="31-60 Days Past Due",
        description="Moderate delinquency",
        send_reminder=True,
        apply_late_fee=True,
        late_fee_amount=Decimal("50.00"),
        provision_percentage=Decimal("5.00"),
    ),
    BucketConfiguration(
        bucket=DelinquencyBucket.BUCKET_3,
        min_days=61,
        max_days=90,
        risk_level=RiskLevel.HIGH,
        display_name="61-90 Days Past Due",
        description="Serious delinquency",
        send_collection_notice=True,
        apply_late_fee=True,
        late_fee_amount=Decimal("100.00"),
        provision_percentage=Decimal("25.00"),
    ),
    BucketConfiguration(
        bucket=DelinquencyBucket.BUCKET_4,
        min_days=91,
        max_days=None,
        risk_level=RiskLevel.CRITICAL,
        display_name="91+ Days Past Due",
        description="Critical delinquency",
        send_collection_notice=True,
        escalate_to_collections=True,
        provision_percentage=Decimal("100.00"),
    ),
]


class PortfolioAtRisk(BaseModel):
    """
    Portfolio at Risk (PAR) Metrics
    
    Calculates portfolio-level delinquency metrics
    """
    
    # Identifiers
    report_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    calculation_date: date = Field(default_factory=date.today)
    
    # Portfolio totals
    total_loans: int = Field(default=0)
    total_outstanding_balance: Decimal = Field(default=Decimal("0.00"))
    
    # PAR metrics (% of portfolio overdue)
    par_1: Decimal = Field(default=Decimal("0.00"))  # 1+ days overdue
    par_30: Decimal = Field(default=Decimal("0.00"))  # 30+ days overdue
    par_60: Decimal = Field(default=Decimal("0.00"))  # 60+ days overdue
    par_90: Decimal = Field(default=Decimal("0.00"))  # 90+ days overdue
    
    # Amount at risk
    amount_at_risk_1: Decimal = Field(default=Decimal("0.00"))
    amount_at_risk_30: Decimal = Field(default=Decimal("0.00"))
    amount_at_risk_60: Decimal = Field(default=Decimal("0.00"))
    amount_at_risk_90: Decimal = Field(default=Decimal("0.00"))
    
    # Loan counts by bucket
    loans_current: int = Field(default=0)
    loans_bucket_1: int = Field(default=0)
    loans_bucket_2: int = Field(default=0)
    loans_bucket_3: int = Field(default=0)
    loans_bucket_4: int = Field(default=0)
    loans_defaulted: int = Field(default=0)
    
    # Provisioning
    total_provisioning_required: Decimal = Field(default=Decimal("0.00"))
    
    def calculate_par(self, total_balance: Decimal, overdue_balance: Decimal) -> Decimal:
        """Calculate PAR percentage"""
        if total_balance == 0:
            return Decimal("0.00")
        return (overdue_balance / total_balance * 100).quantize(Decimal("0.01"))

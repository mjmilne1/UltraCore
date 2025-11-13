"""
Savings Bucket (Goal) Model
Goal-based savings with progress tracking and auto-allocation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from uuid import UUID, uuid4
from datetime import date, datetime
from decimal import Decimal


class GoalType(str, Enum):
    """Savings goal type"""
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    HOME_DEPOSIT = "home_deposit"
    CAR_PURCHASE = "car_purchase"
    EDUCATION = "education"
    WEDDING = "wedding"
    RETIREMENT = "retirement"
    CUSTOM = "custom"


class GoalPriority(str, Enum):
    """Goal priority for allocation"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BucketStatus(str, Enum):
    """Bucket status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"


class SavingsBucket(BaseModel):
    """
    Savings Bucket (Goal)
    
    Goal-based savings with progress tracking, auto-allocation,
    and achievement rewards
    """
    
    # Identifiers
    bucket_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    account_id: UUID  # Parent savings account
    customer_id: UUID
    
    # Goal details
    goal_type: GoalType
    goal_name: str  # e.g., "Hawaii Vacation 2025"
    goal_description: Optional[str] = None
    goal_icon: Optional[str] = None  # Emoji or icon name
    
    # Target
    target_amount: Decimal
    target_date: Optional[date] = None
    currency: str = Field(default="AUD")
    
    # Current progress
    current_balance: Decimal = Field(default=Decimal("0.00"))
    total_allocated: Decimal = Field(default=Decimal("0.00"))
    total_withdrawn: Decimal = Field(default=Decimal("0.00"))
    
    # Progress tracking
    progress_percentage: Decimal = Field(default=Decimal("0.00"))
    estimated_completion_date: Optional[date] = None
    days_to_target: Optional[int] = None
    on_track: bool = Field(default=True)
    
    # Auto-allocation
    auto_allocation_enabled: bool = Field(default=True)
    allocation_percentage: Decimal = Field(default=Decimal("10.00"))  # % of deposits
    priority: GoalPriority = Field(default=GoalPriority.MEDIUM)
    
    # Round-up
    round_up_enabled: bool = Field(default=False)
    round_up_multiplier: int = Field(default=1)  # Round up to nearest $1, $5, $10
    
    # Milestones
    milestones: List[Decimal] = Field(default_factory=list)  # e.g., [25%, 50%, 75%]
    milestones_reached: List[Decimal] = Field(default_factory=list)
    
    # Achievement rewards
    bonus_interest_on_achievement: Decimal = Field(default=Decimal("0.50"))  # 0.5% bonus
    achievement_badge: Optional[str] = None
    
    # Status
    status: BucketStatus = Field(default=BucketStatus.ACTIVE)
    is_active: bool = Field(default=True)
    
    # Notifications
    notify_on_milestone: bool = Field(default=True)
    notify_on_achievement: bool = Field(default=True)
    notify_if_off_track: bool = Field(default=True)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    achieved_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def calculate_progress(self):
        """Calculate progress percentage"""
        if self.target_amount > 0:
            self.progress_percentage = (self.current_balance / self.target_amount) * 100
        else:
            self.progress_percentage = Decimal("0.00")
    
    def check_milestones(self) -> List[Decimal]:
        """Check if any new milestones reached"""
        new_milestones = []
        
        for milestone in self.milestones:
            if milestone not in self.milestones_reached:
                if self.progress_percentage >= milestone:
                    self.milestones_reached.append(milestone)
                    new_milestones.append(milestone)
        
        return new_milestones
    
    def calculate_estimated_completion(self, average_monthly_allocation: Decimal):
        """Calculate estimated completion date based on average allocation"""
        if average_monthly_allocation <= 0:
            self.estimated_completion_date = None
            self.days_to_target = None
            return
        
        remaining_amount = self.target_amount - self.current_balance
        months_remaining = int(remaining_amount / average_monthly_allocation)
        
        from dateutil.relativedelta import relativedelta
        self.estimated_completion_date = date.today() + relativedelta(months=months_remaining)
        self.days_to_target = (self.estimated_completion_date - date.today()).days
        
        # Check if on track
        if self.target_date:
            self.on_track = self.estimated_completion_date <= self.target_date
    
    def allocate(self, amount: Decimal):
        """Allocate funds to bucket"""
        self.current_balance += amount
        self.total_allocated += amount
        self.calculate_progress()
        
        # Check for achievement
        if self.current_balance >= self.target_amount:
            self.achieve()
    
    def withdraw(self, amount: Decimal):
        """Withdraw funds from bucket"""
        if amount > self.current_balance:
            raise ValueError("Insufficient bucket balance")
        
        self.current_balance -= amount
        self.total_withdrawn += amount
        self.calculate_progress()
    
    def achieve(self):
        """Mark goal as achieved"""
        self.status = BucketStatus.ACHIEVED
        self.achieved_at = datetime.utcnow()
        self.progress_percentage = Decimal("100.00")
    
    def pause(self):
        """Pause bucket"""
        self.status = BucketStatus.PAUSED
        self.auto_allocation_enabled = False
    
    def resume(self):
        """Resume bucket"""
        self.status = BucketStatus.ACTIVE
        self.auto_allocation_enabled = True
    
    def cancel(self):
        """Cancel bucket"""
        self.status = BucketStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.is_active = False


class BucketAllocationStrategy(BaseModel):
    """
    Bucket Allocation Strategy
    
    Defines how deposits are allocated across multiple buckets
    """
    
    strategy_id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    
    # Strategy
    allocation_method: str = Field(default="percentage")  # percentage, priority, equal
    
    # Buckets
    buckets: List[SavingsBucket] = Field(default_factory=list)
    
    def calculate_allocation(self, deposit_amount: Decimal) -> dict:
        """
        Calculate allocation across buckets
        
        Returns:
            Dict mapping bucket_id to allocation amount
        """
        allocations = {}
        
        if self.allocation_method == "percentage":
            # Allocate based on percentage
            for bucket in self.buckets:
                if bucket.status == BucketStatus.ACTIVE and bucket.auto_allocation_enabled:
                    allocation = deposit_amount * (bucket.allocation_percentage / 100)
                    allocations[bucket.bucket_id] = allocation
        
        elif self.allocation_method == "priority":
            # Allocate to high priority first
            remaining = deposit_amount
            
            # Sort by priority
            sorted_buckets = sorted(
                [b for b in self.buckets if b.status == BucketStatus.ACTIVE and b.auto_allocation_enabled],
                key=lambda x: (x.priority.value, -x.progress_percentage)
            )
            
            for bucket in sorted_buckets:
                if remaining <= 0:
                    break
                
                # Allocate up to target
                needed = bucket.target_amount - bucket.current_balance
                allocation = min(remaining, needed)
                
                allocations[bucket.bucket_id] = allocation
                remaining -= allocation
        
        elif self.allocation_method == "equal":
            # Equal allocation across active buckets
            active_buckets = [
                b for b in self.buckets
                if b.status == BucketStatus.ACTIVE and b.auto_allocation_enabled
            ]
            
            if active_buckets:
                allocation_per_bucket = deposit_amount / len(active_buckets)
                for bucket in active_buckets:
                    allocations[bucket.bucket_id] = allocation_per_bucket
        
        return allocations

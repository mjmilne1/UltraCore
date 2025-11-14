"""
UltraCore Loan Management - Delinquency Tracker

Delinquency and arrears management:
- Days past due calculation
- Aging bucket classification
- Delinquency status tracking
- Missed payment detection
- Automatic status updates
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal

from ultracore.lending.servicing.loan_account import (
    LoanAccount, LoanStatus
)
from ultracore.lending.servicing.amortization_engine import (
    get_amortization_engine, AmortizationSchedule, ScheduledPayment
)


# ============================================================================
# Delinquency Enums
# ============================================================================

class DelinquencyBucket(str, Enum):
    """Delinquency aging buckets"""
    CURRENT = "CURRENT"  # 0 days
    DPD_1_30 = "DPD_1_30"  # 1-30 days past due
    DPD_31_60 = "DPD_31_60"  # 31-60 days
    DPD_61_90 = "DPD_61_90"  # 61-90 days
    DPD_91_120 = "DPD_91_120"  # 91-120 days
    DPD_121_180 = "DPD_121_180"  # 121-180 days
    DPD_180_PLUS = "DPD_180_PLUS"  # 180+ days
    DEFAULT = "DEFAULT"  # In default status


class DelinquencyRisk(str, Enum):
    """Delinquency risk level"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContactAttemptType(str, Enum):
    """Type of contact attempt"""
    SMS = "SMS"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    LETTER = "LETTER"
    VISIT = "VISIT"


class ContactOutcome(str, Enum):
    """Outcome of contact attempt"""
    NO_ANSWER = "NO_ANSWER"
    ANSWERED = "ANSWERED"
    LEFT_MESSAGE = "LEFT_MESSAGE"
    PROMISE_TO_PAY = "PROMISE_TO_PAY"
    PAYMENT_ARRANGED = "PAYMENT_ARRANGED"
    DISPUTE = "DISPUTE"
    HARDSHIP_REQUEST = "HARDSHIP_REQUEST"
    REFUSED_TO_PAY = "REFUSED_TO_PAY"
    DISCONNECTED = "DISCONNECTED"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class DelinquencyStatus:
    """Current delinquency status of loan"""
    status_id: str
    loan_account_id: str
    
    # Days past due
    days_past_due: int
    
    # Aging bucket
    delinquency_bucket: DelinquencyBucket
    
    # Risk level
    risk_level: DelinquencyRisk
    
    # Amounts
    total_arrears: Decimal
    principal_arrears: Decimal
    interest_arrears: Decimal
    fee_arrears: Decimal
    
    # Missed payments
    missed_payment_count: int
    consecutive_missed: int
    
    # Last payment
    last_payment_date: Optional[date] = None
    last_payment_amount: Optional[Decimal] = None
    
    # Next expected
    next_payment_due_date: Optional[date] = None
    next_payment_amount: Optional[Decimal] = None
    
    # Status change
    delinquent_since: Optional[date] = None
    days_delinquent: int = 0
    
    # Calculated
    as_of_date: date = field(default_factory=date.today)
    
    # Metadata
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MissedPayment:
    """Record of a missed payment"""
    missed_payment_id: str
    loan_account_id: str
    
    # Scheduled payment details
    payment_number: int
    due_date: date
    scheduled_amount: Decimal
    
    # Partial payment
    partial_payment: Decimal = Decimal('0.00')
    remaining_amount: Decimal = Decimal('0.00')
    
    # Status
    resolved: bool = False
    resolved_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContactAttempt:
    """Contact attempt with customer"""
    attempt_id: str
    loan_account_id: str
    
    # Contact details
    contact_date: datetime
    contact_type: ContactAttemptType
    contacted_person: Optional[str] = None
    
    # Outcome
    outcome: ContactOutcome
    notes: Optional[str] = None
    
    # Promise to pay
    promise_to_pay_date: Optional[date] = None
    promise_to_pay_amount: Optional[Decimal] = None
    
    # Follow up
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    
    # Agent
    agent_id: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Delinquency Tracker
# ============================================================================

class DelinquencyTracker:
    """
    Delinquency tracking and aging system
    """
    
    def __init__(self):
        self.delinquency_statuses: Dict[str, DelinquencyStatus] = {}
        self.missed_payments: Dict[str, MissedPayment] = {}
        self.contact_attempts: Dict[str, ContactAttempt] = {}
        self.amortization_engine = get_amortization_engine()
    
    async def update_delinquency_status(
        self,
        loan_account: LoanAccount,
        as_of_date: Optional[date] = None
    ) -> DelinquencyStatus:
        """
        Update delinquency status for loan account
        Calculate days past due, aging bucket, etc.
        """
        
        status_id = f"DEL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        calc_date = as_of_date or date.today()
        
        # Get next payment due date from account
        next_due = loan_account.next_payment_date
        
        # Calculate days past due
        if next_due and calc_date > next_due:
            days_past_due = (calc_date - next_due).days
        else:
            days_past_due = 0
        
        # Determine aging bucket
        bucket = self._determine_aging_bucket(days_past_due)
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            days_past_due,
            loan_account.current_balance.total_arrears
        )
        
        # Count missed payments
        missed_count, consecutive = await self._count_missed_payments(loan_account)
        
        # Get arrears amounts
        balance = loan_account.current_balance
        
        # Determine when became delinquent
        delinquent_since = None
        days_delinquent = 0
        
        if days_past_due > 0:
            if not loan_account.last_payment_date:
                delinquent_since = next_due
            else:
                # Find first missed payment date
                delinquent_since = next_due
            
            days_delinquent = days_past_due
        
        status = DelinquencyStatus(
            status_id=status_id,
            loan_account_id=loan_account.account_id,
            days_past_due=days_past_due,
            delinquency_bucket=bucket,
            risk_level=risk_level,
            total_arrears=balance.total_arrears,
            principal_arrears=balance.principal_in_arrears,
            interest_arrears=balance.interest_in_arrears,
            fee_arrears=balance.fees_in_arrears,
            missed_payment_count=missed_count,
            consecutive_missed=consecutive,
            last_payment_date=loan_account.last_payment_date,
            next_payment_due_date=next_due,
            delinquent_since=delinquent_since,
            days_delinquent=days_delinquent,
            as_of_date=calc_date
        )
        
        self.delinquency_statuses[loan_account.account_id] = status
        
        # Update loan account
        loan_account.days_past_due = days_past_due
        
        # Update status if needed
        if days_past_due > 0 and loan_account.status == LoanStatus.ACTIVE:
            loan_account.status = LoanStatus.DELINQUENT
            loan_account.status_reason = f"{days_past_due} days past due"
        
        if days_past_due > 90 and loan_account.status == LoanStatus.DELINQUENT:
            loan_account.status = LoanStatus.DEFAULT
            loan_account.status_reason = f"{days_past_due} days past due - in default"
        
        return status
    
    def _determine_aging_bucket(self, days_past_due: int) -> DelinquencyBucket:
        """Determine aging bucket based on days past due"""
        
        if days_past_due == 0:
            return DelinquencyBucket.CURRENT
        elif days_past_due <= 30:
            return DelinquencyBucket.DPD_1_30
        elif days_past_due <= 60:
            return DelinquencyBucket.DPD_31_60
        elif days_past_due <= 90:
            return DelinquencyBucket.DPD_61_90
        elif days_past_due <= 120:
            return DelinquencyBucket.DPD_91_120
        elif days_past_due <= 180:
            return DelinquencyBucket.DPD_121_180
        else:
            return DelinquencyBucket.DPD_180_PLUS
    
    def _determine_risk_level(
        self,
        days_past_due: int,
        arrears_amount: Decimal
    ) -> DelinquencyRisk:
        """Determine risk level"""
        
        if days_past_due == 0:
            return DelinquencyRisk.LOW
        elif days_past_due <= 30:
            return DelinquencyRisk.MODERATE
        elif days_past_due <= 90:
            return DelinquencyRisk.HIGH
        else:
            return DelinquencyRisk.CRITICAL
    
    async def _count_missed_payments(
        self,
        loan_account: LoanAccount
    ) -> Tuple[int, int]:
        """
        Count total and consecutive missed payments
        Returns: (total_missed, consecutive_missed)
        """
        
        # Get missed payments for this account
        missed = [
            mp for mp in self.missed_payments.values()
            if mp.loan_account_id == loan_account.account_id and not mp.resolved
        ]
        
        total_missed = len(missed)
        
        # Count consecutive
        if not missed:
            return 0, 0
        
        # Sort by due date
        sorted_missed = sorted(missed, key=lambda x: x.due_date, reverse=True)
        
        consecutive = 1
        for i in range(len(sorted_missed) - 1):
            current = sorted_missed[i]
            next_payment = sorted_missed[i + 1]
            
            # Check if consecutive (roughly 30 days apart for monthly)
            days_diff = (current.due_date - next_payment.due_date).days
            if 25 <= days_diff <= 35:  # Allow for month variations
                consecutive += 1
            else:
                break
        
        return total_missed, consecutive
    
    async def record_missed_payment(
        self,
        loan_account: LoanAccount,
        scheduled_payment: ScheduledPayment
    ) -> MissedPayment:
        """Record a missed payment"""
        
        missed_id = f"MISS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        missed = MissedPayment(
            missed_payment_id=missed_id,
            loan_account_id=loan_account.account_id,
            payment_number=scheduled_payment.payment_number,
            due_date=scheduled_payment.payment_date,
            scheduled_amount=scheduled_payment.payment_amount,
            remaining_amount=scheduled_payment.payment_amount
        )
        
        self.missed_payments[missed_id] = missed
        
        return missed
    
    async def record_contact_attempt(
        self,
        loan_account_id: str,
        contact_type: ContactAttemptType,
        outcome: ContactOutcome,
        agent_id: str,
        notes: Optional[str] = None,
        promise_to_pay_date: Optional[date] = None,
        promise_to_pay_amount: Optional[Decimal] = None
    ) -> ContactAttempt:
        """Record contact attempt with customer"""
        
        attempt_id = f"CNT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        attempt = ContactAttempt(
            attempt_id=attempt_id,
            loan_account_id=loan_account_id,
            contact_date=datetime.now(timezone.utc),
            contact_type=contact_type,
            outcome=outcome,
            notes=notes,
            promise_to_pay_date=promise_to_pay_date,
            promise_to_pay_amount=promise_to_pay_amount,
            agent_id=agent_id
        )
        
        # Set follow up if needed
        if outcome in [
            ContactOutcome.NO_ANSWER,
            ContactOutcome.LEFT_MESSAGE,
            ContactOutcome.PROMISE_TO_PAY
        ]:
            attempt.follow_up_required = True
            if promise_to_pay_date:
                attempt.follow_up_date = promise_to_pay_date
            else:
                attempt.follow_up_date = date.today() + timedelta(days=3)
        
        self.contact_attempts[attempt_id] = attempt
        
        return attempt
    
    async def get_delinquency_status(
        self,
        loan_account_id: str
    ) -> Optional[DelinquencyStatus]:
        """Get current delinquency status"""
        return self.delinquency_statuses.get(loan_account_id)
    
    async def get_delinquent_accounts(
        self,
        min_days_past_due: int = 1,
        bucket: Optional[DelinquencyBucket] = None
    ) -> List[str]:
        """Get list of delinquent account IDs"""
        
        accounts = []
        
        for account_id, status in self.delinquency_statuses.items():
            if status.days_past_due >= min_days_past_due:
                if bucket is None or status.delinquency_bucket == bucket:
                    accounts.append(account_id)
        
        return accounts
    
    async def get_contact_history(
        self,
        loan_account_id: str,
        days: int = 30
    ) -> List[ContactAttempt]:
        """Get contact history for account"""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        attempts = [
            a for a in self.contact_attempts.values()
            if (a.loan_account_id == loan_account_id and
                a.contact_date >= cutoff)
        ]
        
        return sorted(attempts, key=lambda x: x.contact_date, reverse=True)


# ============================================================================
# Global Delinquency Tracker
# ============================================================================

_delinquency_tracker: Optional[DelinquencyTracker] = None

def get_delinquency_tracker() -> DelinquencyTracker:
    """Get the singleton delinquency tracker"""
    global _delinquency_tracker
    if _delinquency_tracker is None:
        _delinquency_tracker = DelinquencyTracker()
    return _delinquency_tracker

"""
UltraCore Loan Management - Payment Processor

Payment processing and allocation:
- Payment receipt
- Payment allocation (fees, interest, principal)
- Overpayment handling
- Partial payment handling
- Payment reversal
- Account reconciliation
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import uuid

from ultracore.lending.servicing.loan_account import (
    LoanAccount, LoanTransaction, LoanTransactionType, LoanStatus
)
from ultracore.lending.servicing.amortization_engine import (
    get_amortization_engine, ScheduledPayment
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Payment Processing Enums
# ============================================================================

class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class PaymentMethod(str, Enum):
    """Payment method"""
    DIRECT_DEBIT = "DIRECT_DEBIT"
    BANK_TRANSFER = "BANK_TRANSFER"
    BPAY = "BPAY"
    CARD = "CARD"
    CASH = "CASH"
    CHEQUE = "CHEQUE"


class PaymentAllocationStrategy(str, Enum):
    """Payment allocation strategy"""
    STANDARD = "STANDARD"  # Fees, penalties, interest, principal
    REGULATORY = "REGULATORY"  # As per regulations
    CUSTOM = "CUSTOM"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PaymentAllocation:
    """How a payment was allocated"""
    fees_paid: Decimal = Decimal('0.00')
    penalties_paid: Decimal = Decimal('0.00')
    interest_arrears_paid: Decimal = Decimal('0.00')
    interest_current_paid: Decimal = Decimal('0.00')
    principal_arrears_paid: Decimal = Decimal('0.00')
    principal_current_paid: Decimal = Decimal('0.00')
    total_allocated: Decimal = Decimal('0.00')
    
    def calculate_total(self):
        """Calculate total allocated"""
        self.total_allocated = (
            self.fees_paid +
            self.penalties_paid +
            self.interest_arrears_paid +
            self.interest_current_paid +
            self.principal_arrears_paid +
            self.principal_current_paid
        )


@dataclass
class Payment:
    """Payment record"""
    payment_id: str
    loan_account_id: str
    payment_date: date
    value_date: date
    payment_amount: Decimal
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    allocation: PaymentAllocation = field(default_factory=PaymentAllocation)
    allocation_strategy: PaymentAllocationStrategy = PaymentAllocationStrategy.STANDARD
    overpayment_amount: Decimal = Decimal('0.00')
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_ids: List[str] = field(default_factory=list)
    reversed: bool = False
    reversal_payment_id: Optional[str] = None
    reversal_reason: Optional[str] = None
    received_by: str = ""
    processed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentPlan:
    """Payment arrangement for delinquent accounts"""
    plan_id: str
    loan_account_id: str
    plan_start_date: date
    plan_end_date: date
    scheduled_payments: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    completed: bool = False
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Payment Processor
# ============================================================================

class PaymentProcessor:
    """Payment processing engine"""
    
    def __init__(self):
        self.payments: Dict[str, Payment] = {}
        self.payment_plans: Dict[str, PaymentPlan] = {}
        self.audit_store = get_audit_store()
        self.amortization_engine = get_amortization_engine()
    
    async def receive_payment(
        self,
        loan_account: LoanAccount,
        payment_amount: Decimal,
        payment_date: date,
        payment_method: PaymentMethod,
        payment_reference: Optional[str] = None,
        received_by: str = "SYSTEM"
    ) -> Payment:
        """Receive and process a payment"""
        
        payment_id = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        payment = Payment(
            payment_id=payment_id,
            loan_account_id=loan_account.account_id,
            payment_date=payment_date,
            value_date=payment_date,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            received_by=received_by,
            status=PaymentStatus.PROCESSING
        )
        
        await self._allocate_payment(payment, loan_account)
        await self._create_payment_transactions(payment, loan_account)
        await self._update_account_after_payment(payment, loan_account)
        
        payment.status = PaymentStatus.COMPLETED
        payment.processed_at = datetime.now(timezone.utc)
        
        self.payments[payment_id] = payment
        
        await self.audit_store.log_event(
            event_type=AuditEventType.TRANSACTION_SETTLED,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='loan_payment',
            resource_id=payment_id,
            action='payment_received',
            description=f"Payment received: ${payment_amount}",
            user_id=received_by,
            metadata={
                'loan_account_id': loan_account.account_id,
                'amount': str(payment_amount),
                'method': payment_method.value,
                'allocation': {
                    'fees': str(payment.allocation.fees_paid),
                    'interest': str(payment.allocation.interest_current_paid + payment.allocation.interest_arrears_paid),
                    'principal': str(payment.allocation.principal_current_paid + payment.allocation.principal_arrears_paid)
                }
            },
            regulatory_relevant=True
        )
        
        return payment
    
    async def _allocate_payment(self, payment: Payment, loan_account: LoanAccount):
        """Allocate payment to fees, interest, principal"""
        
        remaining = payment.payment_amount
        allocation = payment.allocation
        balance = loan_account.current_balance
        
        # Standard allocation order:
        # 1. Fees in arrears
        if remaining > 0 and balance.fees_in_arrears > 0:
            amount = min(remaining, balance.fees_in_arrears)
            allocation.fees_paid = amount
            remaining -= amount
        
        # 2. Penalties
        if remaining > 0 and balance.penalties_outstanding > 0:
            amount = min(remaining, balance.penalties_outstanding)
            allocation.penalties_paid = amount
            remaining -= amount
        
        # 3. Interest in arrears
        if remaining > 0 and balance.interest_in_arrears > 0:
            amount = min(remaining, balance.interest_in_arrears)
            allocation.interest_arrears_paid = amount
            remaining -= amount
        
        # 4. Principal in arrears
        if remaining > 0 and balance.principal_in_arrears > 0:
            amount = min(remaining, balance.principal_in_arrears)
            allocation.principal_arrears_paid = amount
            remaining -= amount
        
        # 5. Current interest accrued
        if remaining > 0 and balance.interest_accrued > 0:
            amount = min(remaining, balance.interest_accrued)
            allocation.interest_current_paid = amount
            remaining -= amount
        
        # 6. Current principal
        if remaining > 0 and balance.principal_outstanding > 0:
            amount = min(remaining, balance.principal_outstanding)
            allocation.principal_current_paid = amount
            remaining -= amount
        
        # 7. Overpayment
        if remaining > 0:
            payment.overpayment_amount = remaining
        
        allocation.calculate_total()
    
    async def _create_payment_transactions(self, payment: Payment, loan_account: LoanAccount):
        """Create loan transactions for payment"""
        
        allocation = payment.allocation
        
        if allocation.fees_paid > 0:
            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            transaction = LoanTransaction(
                transaction_id=txn_id,
                loan_account_id=loan_account.account_id,
                transaction_type=LoanTransactionType.FEE_PAYMENT,
                transaction_date=payment.payment_date,
                value_date=payment.value_date,
                amount=allocation.fees_paid,
                fee_portion=allocation.fees_paid,
                description="Fee payment",
                external_reference=payment.payment_id,
                created_by=payment.received_by
            )
            loan_account.add_transaction(transaction)
            payment.transaction_ids.append(txn_id)
        
        if allocation.penalties_paid > 0:
            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            transaction = LoanTransaction(
                transaction_id=txn_id,
                loan_account_id=loan_account.account_id,
                transaction_type=LoanTransactionType.PENALTY_PAYMENT,
                transaction_date=payment.payment_date,
                value_date=payment.value_date,
                amount=allocation.penalties_paid,
                penalty_portion=allocation.penalties_paid,
                description="Penalty payment",
                external_reference=payment.payment_id,
                created_by=payment.received_by
            )
            loan_account.add_transaction(transaction)
            payment.transaction_ids.append(txn_id)
        
        total_interest = allocation.interest_arrears_paid + allocation.interest_current_paid
        if total_interest > 0:
            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            transaction = LoanTransaction(
                transaction_id=txn_id,
                loan_account_id=loan_account.account_id,
                transaction_type=LoanTransactionType.INTEREST_PAYMENT,
                transaction_date=payment.payment_date,
                value_date=payment.value_date,
                amount=total_interest,
                interest_portion=total_interest,
                description="Interest payment",
                external_reference=payment.payment_id,
                created_by=payment.received_by
            )
            loan_account.add_transaction(transaction)
            payment.transaction_ids.append(txn_id)
        
        total_principal = allocation.principal_arrears_paid + allocation.principal_current_paid
        if total_principal > 0:
            txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            transaction = LoanTransaction(
                transaction_id=txn_id,
                loan_account_id=loan_account.account_id,
                transaction_type=LoanTransactionType.PRINCIPAL_PAYMENT,
                transaction_date=payment.payment_date,
                value_date=payment.value_date,
                amount=total_principal,
                principal_portion=total_principal,
                description="Principal payment",
                external_reference=payment.payment_id,
                created_by=payment.received_by
            )
            loan_account.add_transaction(transaction)
            payment.transaction_ids.append(txn_id)
    
    async def _update_account_after_payment(self, payment: Payment, loan_account: LoanAccount):
        """Update loan account balances after payment"""
        
        allocation = payment.allocation
        balance = loan_account.current_balance
        
        balance.fees_in_arrears -= allocation.fees_paid
        balance.penalties_outstanding -= allocation.penalties_paid
        balance.interest_in_arrears -= allocation.interest_arrears_paid
        balance.interest_accrued -= allocation.interest_current_paid
        balance.principal_in_arrears -= allocation.principal_arrears_paid
        balance.principal_outstanding -= allocation.principal_current_paid
        
        balance.update_total()
        
        loan_account.last_payment_date = payment.payment_date
        
        if balance.total_outstanding <= Decimal('0.01'):
            loan_account.status = LoanStatus.PAID_OFF
            loan_account.closed_date = payment.payment_date
        
        elif balance.total_arrears == 0 and loan_account.status == LoanStatus.DELINQUENT:
            loan_account.status = LoanStatus.ACTIVE
            loan_account.days_past_due = 0
    
    async def process_extra_payment(
        self,
        loan_account: LoanAccount,
        extra_amount: Decimal,
        payment_date: date,
        received_by: str = "SYSTEM"
    ) -> Payment:
        """Process extra payment (beyond scheduled)"""
        
        payment = await self.receive_payment(
            loan_account,
            extra_amount,
            payment_date,
            PaymentMethod.BANK_TRANSFER,
            payment_reference="Extra Payment",
            received_by=received_by
        )
        
        return payment
    
    async def reverse_payment(
        self,
        payment_id: str,
        reversal_reason: str,
        reversed_by: str
    ) -> Payment:
        """Reverse a payment (e.g., dishonored direct debit)"""
        
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.reversed:
            raise ValueError("Payment already reversed")
        
        reversal_id = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        reversal = Payment(
            payment_id=reversal_id,
            loan_account_id=payment.loan_account_id,
            payment_date=date.today(),
            value_date=date.today(),
            payment_amount=-payment.payment_amount,
            payment_method=payment.payment_method,
            payment_reference=f"Reversal of {payment_id}",
            received_by=reversed_by,
            status=PaymentStatus.COMPLETED
        )
        
        payment.reversed = True
        payment.reversal_payment_id = reversal_id
        payment.reversal_reason = reversal_reason
        
        self.payments[reversal_id] = reversal
        
        return reversal
    
    async def create_payment_plan(
        self,
        loan_account: LoanAccount,
        plan_start_date: date,
        monthly_payment: Decimal,
        number_of_payments: int,
        created_by: str
    ) -> PaymentPlan:
        """Create payment plan for delinquent account"""
        
        plan_id = f"PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        scheduled_payments = []
        payment_date = plan_start_date
        
        for i in range(number_of_payments):
            scheduled_payments.append({
                'payment_number': i + 1,
                'payment_date': payment_date.isoformat(),
                'amount': str(monthly_payment),
                'paid': False
            })
            
            if payment_date.month == 12:
                payment_date = payment_date.replace(year=payment_date.year + 1, month=1)
            else:
                payment_date = payment_date.replace(month=payment_date.month + 1)
        
        plan_end_date = payment_date
        
        plan = PaymentPlan(
            plan_id=plan_id,
            loan_account_id=loan_account.account_id,
            plan_start_date=plan_start_date,
            plan_end_date=plan_end_date,
            scheduled_payments=scheduled_payments,
            created_by=created_by
        )
        
        self.payment_plans[plan_id] = plan
        return plan
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        return self.payments.get(payment_id)
    
    async def get_payments_for_account(
        self,
        loan_account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Payment]:
        """Get all payments for an account"""
        
        payments = [
            p for p in self.payments.values()
            if p.loan_account_id == loan_account_id
        ]
        
        if start_date:
            payments = [p for p in payments if p.payment_date >= start_date]
        
        if end_date:
            payments = [p for p in payments if p.payment_date <= end_date]
        
        return sorted(payments, key=lambda x: x.payment_date)


_payment_processor: Optional[PaymentProcessor] = None

def get_payment_processor() -> PaymentProcessor:
    """Get the singleton payment processor"""
    global _payment_processor
    if _payment_processor is None:
        _payment_processor = PaymentProcessor()
    return _payment_processor

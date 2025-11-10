"""
Loan Servicing Engine - Complete Lifecycle Management
Handles: Payments, Amortization, Interest, Collections, Defaults
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import math

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.domains.account.aggregate import AccountAggregate
from ultracore.ledger.general_ledger import ledger


class PaymentFrequency(str, Enum):
    MONTHLY = 'MONTHLY'
    FORTNIGHTLY = 'FORTNIGHTLY'
    WEEKLY = 'WEEKLY'


class PaymentStatus(str, Enum):
    SCHEDULED = 'SCHEDULED'
    PAID = 'PAID'
    LATE = 'LATE'
    MISSED = 'MISSED'
    PARTIAL = 'PARTIAL'


class LoanStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    CURRENT = 'CURRENT'
    LATE = 'LATE'
    DEFAULT = 'DEFAULT'
    PAID_OFF = 'PAID_OFF'
    CHARGED_OFF = 'CHARGED_OFF'


class AmortizationSchedule:
    """Calculate loan amortization schedule"""
    
    @staticmethod
    def generate_schedule(
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
        frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    ) -> List[Dict]:
        """
        Generate complete amortization schedule
        
        Uses: Monthly compound interest formula
        M = P * [r(1+r)^n] / [(1+r)^n - 1]
        """
        
        # Convert annual rate to period rate
        if frequency == PaymentFrequency.MONTHLY:
            periods = term_months
            period_rate = annual_rate / 12 / 100
        elif frequency == PaymentFrequency.FORTNIGHTLY:
            periods = term_months * 2
            period_rate = annual_rate / 26 / 100
        else:  # WEEKLY
            periods = term_months * 4
            period_rate = annual_rate / 52 / 100
        
        # Calculate payment amount
        if period_rate == 0:
            payment = principal / periods
        else:
            payment = principal * (period_rate * pow(1 + period_rate, periods)) / (pow(1 + period_rate, periods) - 1)
        
        schedule = []
        remaining_balance = principal
        
        for period in range(1, int(periods) + 1):
            # Calculate interest for this period
            interest_payment = remaining_balance * period_rate
            principal_payment = payment - interest_payment
            remaining_balance -= principal_payment
            
            # Ensure last payment zeros out the balance
            if period == periods:
                principal_payment += remaining_balance
                remaining_balance = Decimal('0')
            
            schedule.append({
                'period': period,
                'payment_date': (datetime.utcnow() + timedelta(days=30 * period)).strftime('%Y-%m-%d'),
                'payment_amount': float(round(payment, 2)),
                'principal': float(round(principal_payment, 2)),
                'interest': float(round(interest_payment, 2)),
                'remaining_balance': float(round(max(remaining_balance, 0), 2)),
                'status': PaymentStatus.SCHEDULED.value
            })
        
        return schedule


class LoanServicing:
    """Complete loan servicing and lifecycle management"""
    
    def __init__(self, loan_id: str):
        self.loan_id = loan_id
        self.principal: Decimal = Decimal('0')
        self.interest_rate: Decimal = Decimal('0')
        self.term_months: int = 0
        self.remaining_balance: Decimal = Decimal('0')
        self.total_interest_paid: Decimal = Decimal('0')
        self.total_principal_paid: Decimal = Decimal('0')
        self.payment_schedule: List[Dict] = []
        self.payment_history: List[Dict] = []
        self.days_past_due: int = 0
        self.loan_status: LoanStatus = LoanStatus.ACTIVE
    
    async def setup_servicing(
        self,
        principal: Decimal,
        interest_rate: Decimal,
        term_months: int,
        frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    ):
        """Setup loan servicing after approval"""
        store = get_event_store()
        
        # Generate amortization schedule
        schedule = AmortizationSchedule.generate_schedule(
            principal=principal,
            annual_rate=interest_rate,
            term_months=term_months,
            frequency=frequency
        )
        
        event_data = {
            'loan_id': self.loan_id,
            'principal': str(principal),
            'interest_rate': str(interest_rate),
            'term_months': term_months,
            'payment_frequency': frequency.value,
            'payment_schedule': schedule,
            'first_payment_date': schedule[0]['payment_date'],
            'servicing_started': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='LoanServicing',
            event_type='ServicingSetup',
            event_data=event_data,
            user_id='servicing_system'
        )
        
        self.principal = principal
        self.interest_rate = interest_rate
        self.term_months = term_months
        self.remaining_balance = principal
        self.payment_schedule = schedule
        self.loan_status = LoanStatus.CURRENT
    
    async def process_payment(
        self,
        payment_amount: Decimal,
        account_id: str,
        payment_date: str = None
    ):
        """
        Process loan payment
        
        Allocation order:
        1. Late fees
        2. Accrued interest
        3. Principal
        """
        store = get_event_store()
        
        if payment_date is None:
            payment_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Find next scheduled payment
        next_payment = None
        for payment in self.payment_schedule:
            if payment['status'] == PaymentStatus.SCHEDULED.value:
                next_payment = payment
                break
        
        if not next_payment:
            raise ValueError('No scheduled payments remaining')
        
        # Allocate payment
        remaining_payment = payment_amount
        late_fee_paid = Decimal('0')
        interest_paid = Decimal(str(next_payment['interest']))
        principal_paid = Decimal('0')
        
        # Check for late fees
        scheduled_date = datetime.strptime(next_payment['payment_date'], '%Y-%m-%d')
        actual_date = datetime.strptime(payment_date, '%Y-%m-%d')
        days_late = max(0, (actual_date - scheduled_date).days)
        
        if days_late > 0:
            late_fee = self._calculate_late_fee(days_late)
            late_fee_paid = min(late_fee, remaining_payment)
            remaining_payment -= late_fee_paid
        
        # Allocate to interest
        if remaining_payment >= interest_paid:
            remaining_payment -= interest_paid
        else:
            interest_paid = remaining_payment
            remaining_payment = Decimal('0')
        
        # Allocate to principal
        scheduled_principal = Decimal(str(next_payment['principal']))
        if remaining_payment > 0:
            principal_paid = min(remaining_payment, scheduled_principal)
            remaining_payment -= principal_paid
        
        # Update balances
        self.total_interest_paid += interest_paid
        self.total_principal_paid += principal_paid
        self.remaining_balance -= principal_paid
        
        # Determine payment status
        total_allocated = late_fee_paid + interest_paid + principal_paid
        expected_payment = Decimal(str(next_payment['payment_amount']))
        
        if total_allocated >= expected_payment:
            payment_status = PaymentStatus.PAID
        else:
            payment_status = PaymentStatus.PARTIAL
        
        event_data = {
            'loan_id': self.loan_id,
            'payment_date': payment_date,
            'payment_amount': str(payment_amount),
            'late_fee_paid': str(late_fee_paid),
            'interest_paid': str(interest_paid),
            'principal_paid': str(principal_paid),
            'remaining_balance': str(self.remaining_balance),
            'payment_status': payment_status.value,
            'days_late': days_late,
            'period': next_payment['period']
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='LoanServicing',
            event_type='PaymentProcessed',
            event_data=event_data,
            user_id='servicing_system'
        )
        
        # Update payment schedule
        next_payment['status'] = payment_status.value
        self.payment_history.append(event_data)
        
        # Debit customer account
        account = AccountAggregate(account_id)
        await account.load_from_events()
        await account.withdraw(
            amount=payment_amount,
            description=f'Loan payment - {self.loan_id}',
            reference=self.loan_id
        )
        
        # Post to general ledger
        # DR: Customer Deposits (liability decrease)
        # CR: Customer Loans (asset decrease)
        # DR: Cash
        # CR: Interest Income
        await ledger.post_journal_entry(
            entry_id=f'JE-LOAN-PMT-{self.loan_id}-{datetime.utcnow().timestamp()}',
            date=datetime.utcnow().isoformat(),
            description=f'Loan payment received',
            reference=self.loan_id,
            debits=[
                {'account': '2000', 'amount': float(payment_amount)},  # Customer deposits
                {'account': '1000', 'amount': float(interest_paid)}    # Cash for interest
            ],
            credits=[
                {'account': '1100', 'amount': float(principal_paid)},  # Customer loans
                {'account': '4000', 'amount': float(interest_paid)}    # Interest income
            ],
            posted_by='servicing_system'
        )
        
        # Check if loan is paid off
        if self.remaining_balance <= Decimal('0.01'):
            await self.payoff_loan()
        
        return event_data
    
    def _calculate_late_fee(self, days_late: int) -> Decimal:
        """Calculate late fee"""
        # Australian standard:  +  per month after first month
        if days_late <= 30:
            return Decimal('20.00')
        else:
            months_late = math.ceil(days_late / 30)
            return Decimal('20.00') + (Decimal('7.00') * (months_late - 1))
    
    async def payoff_loan(self):
        """Mark loan as paid off"""
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'payoff_date': datetime.utcnow().isoformat(),
            'total_interest_paid': str(self.total_interest_paid),
            'total_principal_paid': str(self.total_principal_paid),
            'final_balance': str(self.remaining_balance)
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='LoanServicing',
            event_type='LoanPaidOff',
            event_data=event_data,
            user_id='servicing_system'
        )
        
        self.loan_status = LoanStatus.PAID_OFF
    
    async def calculate_early_payoff(self) -> Dict:
        """Calculate early payoff amount"""
        # Simple interest method (no prepayment penalty in Australia typically)
        return {
            'remaining_principal': str(self.remaining_balance),
            'accrued_interest': '0.00',  # Simplified
            'total_payoff_amount': str(self.remaining_balance),
            'savings': str(self._calculate_remaining_interest()),
            'as_of_date': datetime.utcnow().strftime('%Y-%m-%d')
        }
    
    def _calculate_remaining_interest(self) -> Decimal:
        """Calculate total remaining interest"""
        total_remaining = sum(
            Decimal(str(p['interest'])) for p in self.payment_schedule
            if p['status'] == PaymentStatus.SCHEDULED.value
        )
        return total_remaining
    
    async def mark_default(self, reason: str):
        """Mark loan as default"""
        store = get_event_store()
        
        event_data = {
            'loan_id': self.loan_id,
            'default_date': datetime.utcnow().isoformat(),
            'days_past_due': self.days_past_due,
            'outstanding_balance': str(self.remaining_balance),
            'reason': reason
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='LoanServicing',
            event_type='LoanDefaulted',
            event_data=event_data,
            user_id='collections_system'
        )
        
        self.loan_status = LoanStatus.DEFAULT
    
    async def charge_off(self, recovery_amount: Decimal = Decimal('0')):
        """Charge off bad debt"""
        store = get_event_store()
        
        loss_amount = self.remaining_balance - recovery_amount
        
        event_data = {
            'loan_id': self.loan_id,
            'charge_off_date': datetime.utcnow().isoformat(),
            'outstanding_balance': str(self.remaining_balance),
            'recovery_amount': str(recovery_amount),
            'loss_amount': str(loss_amount)
        }
        
        await store.append(
            aggregate_id=self.loan_id,
            aggregate_type='LoanServicing',
            event_type='LoanChargedOff',
            event_data=event_data,
            user_id='collections_system'
        )
        
        # Post to general ledger
        # DR: Loan Loss Provision
        # CR: Customer Loans
        await ledger.post_journal_entry(
            entry_id=f'JE-CHARGEOFF-{self.loan_id}',
            date=datetime.utcnow().isoformat(),
            description=f'Loan charge-off',
            reference=self.loan_id,
            debits=[{'account': '5200', 'amount': float(loss_amount)}],   # Loan loss provision
            credits=[{'account': '1100', 'amount': float(loss_amount)}],  # Customer loans
            posted_by='collections_system'
        )
        
        self.loan_status = LoanStatus.CHARGED_OFF
        self.remaining_balance = Decimal('0')
    
    async def load_from_events(self):
        """Rebuild servicing state from events"""
        store = get_event_store()
        events = await store.get_events(self.loan_id)
        
        for event in events:
            if event.event_type == 'ServicingSetup':
                self.principal = Decimal(event.event_data['principal'])
                self.interest_rate = Decimal(event.event_data['interest_rate'])
                self.term_months = event.event_data['term_months']
                self.remaining_balance = self.principal
                self.payment_schedule = event.event_data['payment_schedule']
                self.loan_status = LoanStatus.CURRENT
            elif event.event_type == 'PaymentProcessed':
                self.total_interest_paid += Decimal(event.event_data['interest_paid'])
                self.total_principal_paid += Decimal(event.event_data['principal_paid'])
                self.remaining_balance = Decimal(event.event_data['remaining_balance'])
                self.payment_history.append(event.event_data)
            elif event.event_type == 'LoanPaidOff':
                self.loan_status = LoanStatus.PAID_OFF
            elif event.event_type == 'LoanDefaulted':
                self.loan_status = LoanStatus.DEFAULT
            elif event.event_type == 'LoanChargedOff':
                self.loan_status = LoanStatus.CHARGED_OFF
                self.remaining_balance = Decimal('0')

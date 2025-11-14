"""Recurring Deposit Domain Service - Event-Sourced"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from dateutil.relativedelta import relativedelta
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    RecurringDepositApplicationSubmittedEvent,
    RecurringDepositApprovedEvent,
    RecurringDepositActivatedEvent
)
from ..models import (
    RecurringDepositAccount,
    RecurringDepositApplication,
    RecurringDepositProduct,
    RecurringDepositStatus,
    DepositSchedule,
    DepositInstallment,
    InstallmentStatus
)


class RecurringDepositService:
    """
    Event-sourced Recurring Deposit service.
    
    All state changes flow through Kafka events.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
    
    async def submit_application(
        self,
        customer_id: str,
        product: RecurringDepositProduct,
        monthly_deposit_amount: Decimal,
        term_months: int,
        source_account_id: str,
        debit_day_of_month: int,
        maturity_instruction: str,
        submitted_by: str,
        **kwargs
    ) -> RecurringDepositApplication:
        """
        Submit recurring deposit application.
        
        Publishes to Kafka: RecurringDepositApplicationSubmittedEvent
        """
        # Validate
        if monthly_deposit_amount < product.min_monthly_deposit:
            raise ValueError(f"Minimum monthly deposit: {product.min_monthly_deposit}")
        
        if term_months not in range(product.min_term_months, product.max_term_months + 1):
            raise ValueError(f"Term must be between {product.min_term_months}-{product.max_term_months} months")
        
        # Calculate interest rate
        interest_rate = self._get_interest_rate(product, monthly_deposit_amount, term_months)
        
        # Create application
        application_id = f"RD-APP-{uuid.uuid4().hex[:12].upper()}"
        application = RecurringDepositApplication(
            application_id=application_id,
            customer_id=customer_id,
            product_id=product.product_id,
            monthly_deposit_amount=monthly_deposit_amount,
            term_months=term_months,
            deposit_frequency=product.deposit_frequency,
            interest_rate_annual=interest_rate,
            source_account_id=source_account_id,
            debit_day_of_month=debit_day_of_month,
            maturity_instruction=maturity_instruction,
            submitted_by=submitted_by,
            submitted_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        # Publish event to Kafka
        event = RecurringDepositApplicationSubmittedEvent(
            aggregate_id=application_id,
            account_id=application_id,
            customer_id=customer_id,
            product_id=product.product_id,
            application_id=application_id,
            monthly_deposit_amount=monthly_deposit_amount,
            term_months=term_months,
            deposit_frequency=product.deposit_frequency.value,
            interest_rate_annual=interest_rate,
            interest_calculation_method=product.interest_calculation_method,
            maturity_instruction=maturity_instruction,
            source_account_id=source_account_id,
            debit_day_of_month=debit_day_of_month,
            submitted_by=submitted_by,
            submitted_at=application.submitted_at,
            channel=kwargs.get("channel", "web")
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return application
    
    async def approve_application(
        self,
        application_id: str,
        approved_by: str,
        approval_notes: Optional[str] = None
    ) -> None:
        """Approve RD application (maker-checker)."""
        # Load application
        application = await self._load_application(application_id)
        
        # Calculate dates
        activation_date = date.today()
        maturity_date = activation_date + relativedelta(months=application.term_months)
        first_deposit_due = self._calculate_first_deposit_date(
            activation_date,
            application.debit_day_of_month
        )
        
        # Publish approval event
        event = RecurringDepositApprovedEvent(
            aggregate_id=application_id,
            account_id=application_id,
            customer_id=application.customer_id,
            product_id=application.product_id,
            application_id=application_id,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc),
            approval_notes=approval_notes,
            monthly_deposit_amount=application.monthly_deposit_amount,
            term_months=application.term_months,
            interest_rate_annual=application.interest_rate_annual,
            maturity_date=maturity_date,
            first_deposit_due_date=first_deposit_due
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
    
    async def activate_account(
        self,
        application_id: str,
        activation_date: date,
        mandate_reference: str
    ) -> RecurringDepositAccount:
        """
        Activate RD account.
        
        Publishes: RecurringDepositActivatedEvent
        """
        application = await self._load_application(application_id)
        
        # Generate account
        account_id = f"RD-{uuid.uuid4().hex[:12].upper()}"
        account_number = f"RD{datetime.now(timezone.utc).strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate maturity date
        maturity_date = activation_date + relativedelta(months=application.term_months)
        
        # Calculate expected values
        total_principal = application.monthly_deposit_amount * application.term_months
        expected_interest = self._calculate_total_interest_rd(
            application.monthly_deposit_amount,
            application.interest_rate_annual,
            application.term_months
        )
        expected_maturity = total_principal + expected_interest
        
        # Publish activation event
        event = RecurringDepositActivatedEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=application.customer_id,
            product_id=application.product_id,
            monthly_deposit_amount=application.monthly_deposit_amount,
            activation_date=activation_date,
            maturity_date=maturity_date,
            term_months=application.term_months,
            total_deposits_expected=application.term_months,
            interest_rate_annual=application.interest_rate_annual,
            total_principal_expected=total_principal,
            expected_interest=expected_interest,
            expected_maturity_value=expected_maturity,
            source_account_id=application.source_account_id,
            debit_day_of_month=application.debit_day_of_month,
            mandate_reference=mandate_reference,
            mandate_status="active",
            first_deposit_due_date=self._calculate_first_deposit_date(
                activation_date,
                application.debit_day_of_month
            ),
            certificate_number=account_number
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        account = await self._reconstruct_account(account_id)
        return account
    
    async def get_account(self, account_id: str) -> RecurringDepositAccount:
        """Reconstruct account from events."""
        return await self._reconstruct_account(account_id)
    
    async def generate_deposit_schedule(
        self,
        account: RecurringDepositAccount
    ) -> DepositSchedule:
        """Generate complete deposit schedule."""
        installments = []
        current_date = account.start_date
        
        for i in range(account.total_deposits_expected):
            due_date = self._calculate_deposit_date(
                current_date,
                account.debit_day_of_month,
                i
            )
            
            installment = DepositInstallment(
                installment_number=i + 1,
                due_date=due_date,
                deposit_amount=account.monthly_deposit_amount,
                status=InstallmentStatus.PENDING
            )
            installments.append(installment)
        
        schedule = DepositSchedule(
            account_id=account.account_id,
            start_date=account.start_date,
            maturity_date=account.maturity_date,
            monthly_deposit_amount=account.monthly_deposit_amount,
            total_installments=account.total_deposits_expected,
            installments=installments
        )
        
        return schedule
    
    # Private helpers
    
    def _get_interest_rate(
        self,
        product: RecurringDepositProduct,
        amount: Decimal,
        term_months: int
    ) -> Decimal:
        """Get interest rate from slabs."""
        for slab in product.interest_rate_slabs:
            if term_months >= slab.get("min_term", 0):
                return Decimal(str(slab["interest_rate"]))
        return Decimal("5.5")  # Default
    
    def _calculate_first_deposit_date(
        self,
        activation_date: date,
        debit_day: int
    ) -> date:
        """Calculate first deposit due date."""
        if activation_date.day <= debit_day:
            # First deposit this month
            return activation_date.replace(day=debit_day)
        else:
            # First deposit next month
            next_month = activation_date + relativedelta(months=1)
            return next_month.replace(day=debit_day)
    
    def _calculate_deposit_date(
        self,
        start_date: date,
        debit_day: int,
        installment_index: int
    ) -> date:
        """Calculate deposit date for installment."""
        target_date = start_date + relativedelta(months=installment_index)
        return target_date.replace(day=min(debit_day, 28))
    
    def _calculate_total_interest_rd(
        self,
        monthly_deposit: Decimal,
        rate_annual: Decimal,
        term_months: int
    ) -> Decimal:
        """
        Calculate total interest for recurring deposit.
        
        Formula: Interest = P * n * (n + 1) / (2 * 12) * (r / 100)
        Where:
        - P = monthly deposit
        - n = number of months
        - r = annual interest rate
        """
        n = Decimal(term_months)
        r = rate_annual / Decimal("100")
        
        interest = monthly_deposit * n * (n + Decimal("1")) / (Decimal("2") * Decimal("12")) * r
        return interest
    
    async def _load_application(self, application_id: str) -> RecurringDepositApplication:
        """Load from events."""
        # Placeholder
        raise NotImplementedError()
    
    async def _reconstruct_account(self, account_id: str) -> RecurringDepositAccount:
        """Reconstruct from events."""
        # Placeholder
        raise NotImplementedError()

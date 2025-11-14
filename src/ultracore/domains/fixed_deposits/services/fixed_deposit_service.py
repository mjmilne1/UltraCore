"""Fixed Deposit Domain Service - Event-Sourced"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    FixedDepositApplicationSubmittedEvent,
    FixedDepositApprovedEvent,
    FixedDepositActivatedEvent,
    FixedDepositCreatedEvent
)
from ..models import (
    FixedDepositAccount,
    FixedDepositApplication,
    FixedDepositProduct,
    FixedDepositStatus
)


class FixedDepositService:
    """
    Event-sourced Fixed Deposit service.
    
    All state changes flow through Kafka events.
    Account state is reconstructed from event stream.
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
        product: FixedDepositProduct,
        deposit_amount: Decimal,
        term_months: int,
        source_account_id: str,
        maturity_instruction: str,
        submitted_by: str,
        **kwargs
    ) -> FixedDepositApplication:
        """
        Submit fixed deposit application.
        
        Publishes to Kafka: FixedDepositApplicationSubmittedEvent
        """
        # Validate
        if deposit_amount < product.min_deposit_amount:
            raise ValueError(f"Minimum deposit: {product.min_deposit_amount}")
        
        if term_months not in range(product.min_term_months, product.max_term_months + 1):
            raise ValueError(f"Term must be between {product.min_term_months} and {product.max_term_months} months")
        
        # Calculate interest rate (from slabs)
        interest_rate = self._get_interest_rate(product, deposit_amount, term_months)
        
        # Create application
        application_id = f"FD-APP-{uuid.uuid4().hex[:12].upper()}"
        application = FixedDepositApplication(
            application_id=application_id,
            customer_id=customer_id,
            product_id=product.product_id,
            deposit_amount=deposit_amount,
            term_months=term_months,
            interest_rate_annual=interest_rate,
            interest_calculation_method=product.interest_calculation_method,
            maturity_instruction=maturity_instruction,
            submitted_by=submitted_by,
            submitted_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        # Publish event to Kafka
        event = FixedDepositApplicationSubmittedEvent(
            aggregate_id=application_id,
            account_id=application_id,
            customer_id=customer_id,
            product_id=product.product_id,
            application_id=application_id,
            deposit_amount=deposit_amount,
            term_months=term_months,
            interest_rate_annual=interest_rate,
            interest_calculation_method=product.interest_calculation_method.value,
            maturity_instruction=maturity_instruction,
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
        """
        Approve fixed deposit application (maker-checker).
        
        Publishes to Kafka: FixedDepositApprovedEvent
        """
        # Load application from events
        application = await self._load_application(application_id)
        
        if application.status != FixedDepositStatus.SUBMITTED:
            raise ValueError(f"Application {application_id} not in submitted status")
        
        # Calculate maturity date
        maturity_date = self._calculate_maturity_date(
            date.today(),
            application.term_months
        )
        
        # Publish approval event
        event = FixedDepositApprovedEvent(
            aggregate_id=application_id,
            account_id=application_id,
            customer_id=application.customer_id,
            product_id=application.product_id,
            application_id=application_id,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc),
            approval_notes=approval_notes,
            deposit_amount=application.deposit_amount,
            term_months=application.term_months,
            interest_rate_annual=application.interest_rate_annual,
            maturity_date=maturity_date
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
    
    async def activate_account(
        self,
        application_id: str,
        activation_date: date,
        source_account_id: str,
        certificate_number: Optional[str] = None
    ) -> FixedDepositAccount:
        """
        Activate fixed deposit account.
        
        Publishes to Kafka:
        - FixedDepositActivatedEvent
        - Accounting events (debit source, credit FD liability)
        """
        # Load approved application
        application = await self._load_application(application_id)
        
        if application.status != FixedDepositStatus.APPROVED:
            raise ValueError(f"Application {application_id} not approved")
        
        # Generate account number
        account_id = f"FD-{uuid.uuid4().hex[:12].upper()}"
        account_number = f"FD{datetime.now(timezone.utc).strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate maturity date
        maturity_date = self._calculate_maturity_date(activation_date, application.term_months)
        
        # Calculate expected interest
        expected_interest = self._calculate_total_interest(
            application.deposit_amount,
            application.interest_rate_annual,
            application.term_months,
            application.interest_calculation_method
        )
        
        # Publish activation event
        event = FixedDepositActivatedEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=application.customer_id,
            product_id=application.product_id,
            deposit_amount=application.deposit_amount,
            activation_date=activation_date,
            maturity_date=maturity_date,
            term_months=application.term_months,
            interest_rate_annual=application.interest_rate_annual,
            interest_calculation_method=application.interest_calculation_method.value,
            expected_interest=expected_interest,
            expected_maturity_value=application.deposit_amount + expected_interest,
            source_account_id=source_account_id,
            source_account_type="savings",
            certificate_number=certificate_number or account_number,
            certificate_issued=True
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Create account aggregate from events
        account = await self._reconstruct_account(account_id)
        return account
    
    async def get_account(self, account_id: str) -> FixedDepositAccount:
        """
        Reconstruct account state from event stream.
        
        This is event sourcing in action!
        """
        return await self._reconstruct_account(account_id)
    
    # Private helpers
    
    def _get_interest_rate(
        self,
        product: FixedDepositProduct,
        amount: Decimal,
        term_months: int
    ) -> Decimal:
        """Get interest rate from product slabs."""
        # Simplified: return highest applicable rate
        for slab in product.interest_rate_slabs:
            if amount >= slab.get("min_amount", 0) and term_months >= slab.get("min_term", 0):
                return Decimal(str(slab["interest_rate"]))
        
        return Decimal("5.0")  # Default rate
    
    def _calculate_maturity_date(self, start_date: date, term_months: int) -> date:
        """Calculate maturity date."""
        # Simple calculation (in production, handle month-end, holidays, etc.)
        year = start_date.year + (start_date.month + term_months - 1) // 12
        month = (start_date.month + term_months - 1) % 12 + 1
        day = start_date.day
        
        return date(year, month, min(day, 28))  # Simplified
    
    def _calculate_total_interest(
        self,
        principal: Decimal,
        rate_annual: Decimal,
        term_months: int,
        method: str
    ) -> Decimal:
        """Calculate total interest."""
        # Simplified calculation
        if method == "simple":
            return principal * rate_annual / Decimal("100") * Decimal(term_months) / Decimal("12")
        else:
            # Compound calculation
            n = 12  # Monthly compounding
            rate = rate_annual / Decimal("100") / Decimal(n)
            periods = Decimal(term_months)
            amount = principal * (Decimal("1") + rate) ** periods
            return amount - principal
    
    async def _load_application(self, application_id: str) -> FixedDepositApplication:
        """Load application from events."""
        events = await self.event_store.get_events(application_id)
        # Reconstruct application state from events
        # (Implementation depends on your event store)
        # For now, placeholder
        raise NotImplementedError("Event reconstruction not yet implemented")
    
    async def _reconstruct_account(self, account_id: str) -> FixedDepositAccount:
        """Reconstruct account from event stream (event sourcing)."""
        events = await self.event_store.get_events(account_id)
        # Replay events to build current state
        # (Implementation depends on your event store)
        raise NotImplementedError("Event reconstruction not yet implemented")

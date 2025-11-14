"""Loan Restructuring Service - Event-Sourced, NCCP Compliant"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from dateutil.relativedelta import relativedelta
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    HardshipApplicationSubmittedEvent,
    HardshipApplicationApprovedEvent,
    PaymentHolidayGrantedEvent,
    TermExtensionAppliedEvent,
    RestructuringCompletedEvent
)
from ..models import (
    LoanRestructuring,
    HardshipApplication,
    PaymentHoliday,
    TermExtension,
    RestructuringPlan,
    HardshipReason,
    ReliefType,
    RestructuringStatus
)


class LoanRestructuringService:
    """
    Event-sourced Loan Restructuring service.
    
    Australian NCCP Section 72: Hardship variations.
    
    All state changes flow through Kafka events.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
    
    async def submit_hardship_application(
        self,
        loan_id: str,
        customer_id: str,
        hardship_reason: HardshipReason,
        hardship_description: str,
        financial_situation: dict,
        requested_relief: List[ReliefType],
        **kwargs
    ) -> HardshipApplication:
        """
        Submit hardship application under NCCP Section 72.
        
        Publishes: HardshipApplicationSubmittedEvent to Kafka
        
        Triggers:
        - Assessment workflow
        - Financial counselling offer (mandatory)
        - ASIC notification
        - Anya empathetic support
        """
        
        application_id = f"HARD-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate disposable income
        income = Decimal(str(financial_situation.get("income_monthly", 0)))
        expenses = Decimal(str(financial_situation.get("expenses_monthly", 0)))
        other_debts = Decimal(str(financial_situation.get("other_debts_monthly", 0)))
        disposable = income - expenses - other_debts
        
        # Create application
        application = HardshipApplication(
            application_id=application_id,
            loan_id=loan_id,
            customer_id=customer_id,
            hardship_reason=hardship_reason,
            hardship_description=hardship_description,
            financial_impact_description=kwargs.get("financial_impact", ""),
            current_income_monthly=income,
            essential_expenses_monthly=expenses,
            other_debts_monthly=other_debts,
            disposable_income_monthly=disposable,
            current_payment_amount=Decimal(str(kwargs.get("current_payment", 0))),
            current_arrears_amount=Decimal(str(kwargs.get("arrears", 0))),
            days_in_arrears=kwargs.get("days_in_arrears", 0),
            requested_relief_types=requested_relief,
            submitted_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        # Publish event
        event = HardshipApplicationSubmittedEvent(
            aggregate_id=application_id,
            loan_id=loan_id,
            customer_id=customer_id,
            application_id=application_id,
            hardship_reason=hardship_reason.value,
            hardship_description=hardship_description,
            financial_impact_description=kwargs.get("financial_impact", ""),
            current_income_monthly=income,
            essential_expenses_monthly=expenses,
            other_debts_monthly=other_debts,
            disposable_income_monthly=disposable,
            current_payment_amount=application.current_payment_amount,
            current_arrears_amount=application.current_arrears_amount,
            days_in_arrears=application.days_in_arrears,
            requested_relief_type=[r.value for r in requested_relief],
            submitted_by=kwargs.get("submitted_by", "customer"),
            submitted_at=application.submitted_at,
            submission_channel=kwargs.get("channel", "web")
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return application
    
    async def grant_payment_holiday(
        self,
        loan_id: str,
        customer_id: str,
        duration_months: int,
        holiday_type: str = "hardship",
        **kwargs
    ) -> PaymentHoliday:
        """
        Grant payment holiday.
        
        Publishes: PaymentHolidayGrantedEvent
        
        Common hardship relief in Australia.
        """
        
        # Calculate holiday details
        start_date = date.today()
        end_date = start_date + relativedelta(months=duration_months)
        
        # Load loan details (would come from loan service)
        current_payment = Decimal(str(kwargs.get("current_payment", 500)))
        payments_deferred = duration_months
        deferred_amount = current_payment * payments_deferred
        
        # Interest during holiday (still accrues)
        interest_rate = Decimal(str(kwargs.get("interest_rate", 5.0))) / Decimal("100")
        loan_balance = Decimal(str(kwargs.get("loan_balance", 100000)))
        monthly_interest = loan_balance * interest_rate / Decimal("12")
        interest_during_holiday = monthly_interest * duration_months
        
        # Term extension
        original_maturity = kwargs.get("original_maturity", date.today() + relativedelta(years=5))
        new_maturity = original_maturity + relativedelta(months=duration_months)
        
        # Resumption payment
        resumption_payment = current_payment  # Usually same as before
        
        holiday = PaymentHoliday(
            loan_id=loan_id,
            customer_id=customer_id,
            holiday_type=holiday_type,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            payments_deferred=payments_deferred,
            deferred_amount=deferred_amount,
            interest_during_holiday=interest_during_holiday,
            interest_capitalized=True,
            original_maturity_date=original_maturity,
            new_maturity_date=new_maturity,
            term_extension_months=duration_months,
            resumption_payment_amount=resumption_payment,
            resumption_date=end_date
        )
        
        # Publish event
        event = PaymentHolidayGrantedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            holiday_type=holiday_type,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            payments_deferred=payments_deferred,
            deferred_amount=deferred_amount,
            interest_during_holiday=interest_during_holiday,
            interest_capitalized=True,
            original_maturity_date=original_maturity,
            new_maturity_date=new_maturity,
            term_extension_months=duration_months,
            resumption_payment_amount=resumption_payment,
            resumption_date=end_date,
            granted_by=kwargs.get("granted_by", "system"),
            granted_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return holiday
    
    async def get_restructuring(self, restructuring_id: str) -> LoanRestructuring:
        """Reconstruct restructuring from events."""
        return await self._reconstruct_restructuring(restructuring_id)
    
    async def _reconstruct_restructuring(self, restructuring_id: str) -> LoanRestructuring:
        """Reconstruct from events."""
        # Placeholder
        raise NotImplementedError("Event replay not implemented")

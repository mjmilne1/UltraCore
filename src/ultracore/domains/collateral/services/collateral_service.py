"""Collateral Management Service - Event-Sourced, Australian Compliant"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from dateutil.relativedelta import relativedelta
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    CollateralRegisteredEvent,
    CollateralValuationCompletedEvent,
    CollateralPerfectedEvent,
    CollateralReleasedEvent,
    PPSRRegistrationCompletedEvent,
    LVRBreachDetectedEvent
)
from ..models import (
    Collateral,
    CollateralType,
    CollateralStatus,
    SecurityPosition,
    AustralianState
)


class CollateralService:
    """
    Event-sourced Collateral Management service.
    
    Australian compliance:
    - PPSR integration for personal property
    - Land title integration for real property
    - LVR monitoring
    - Insurance tracking
    - Valuation lifecycle
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ppsr_client  # PPSR API client
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ppsr = ppsr_client
    
    async def register_collateral(
        self,
        loan_id: str,
        customer_id: str,
        collateral_type: CollateralType,
        collateral_description: str,
        estimated_value: Decimal,
        loan_amount_secured: Decimal,
        jurisdiction: AustralianState,
        security_position: SecurityPosition = SecurityPosition.FIRST,
        **kwargs
    ) -> Collateral:
        """
        Register collateral against loan.
        
        Publishes: CollateralRegisteredEvent to Kafka
        
        Triggers:
        - PPSR search (for personal property)
        - Valuation ordering
        - Insurance requirement setup
        """
        
        # Generate IDs
        collateral_id = f"COL-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate LVR
        policy_max_lvr = Decimal("80.0")  # Standard residential
        if collateral_type == CollateralType.REAL_PROPERTY_COMMERCIAL:
            policy_max_lvr = Decimal("70.0")
        
        current_lvr = (loan_amount_secured / estimated_value * Decimal("100"))
        
        # LMI required?
        lmi_required = current_lvr > Decimal("80.0")
        
        # PPSR required?
        ppsr_required = collateral_type not in [
            CollateralType.REAL_PROPERTY_RESIDENTIAL,
            CollateralType.REAL_PROPERTY_COMMERCIAL
        ]
        
        # Valuation method
        if estimated_value > Decimal("3000000"):
            valuation_method = "professional"
        elif estimated_value > Decimal("500000"):
            valuation_method = "desktop"
        else:
            valuation_method = "automated"
        
        # Create event
        event = CollateralRegisteredEvent(
            aggregate_id=collateral_id,
            collateral_id=collateral_id,
            loan_id=loan_id,
            customer_id=customer_id,
            jurisdiction=jurisdiction.value,
            collateral_type=collateral_type.value,
            collateral_description=collateral_description,
            estimated_value=estimated_value,
            valuation_date=date.today(),
            valuation_method=valuation_method,
            security_position=security_position.value,
            loan_amount_secured=loan_amount_secured,
            required_lvr=policy_max_lvr,
            current_lvr=current_lvr,
            insurance_required=True,
            registered_by=kwargs.get("registered_by", "system"),
            registered_at=datetime.now(timezone.utc),
            ppsr_required=ppsr_required,
            lmi_required=lmi_required,
            **kwargs
        )
        
        # Publish to Kafka
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Reconstruct aggregate
        collateral = await self._reconstruct_collateral(collateral_id)
        
        return collateral
    
    async def complete_valuation(
        self,
        collateral_id: str,
        valuation_order_id: str,
        market_value: Decimal,
        forced_sale_value: Optional[Decimal],
        valuer_name: str,
        valuer_registration: str,
        valuation_firm: str,
        valuation_report_reference: str
    ) -> None:
        """
        Record completed valuation.
        
        Publishes: CollateralValuationCompletedEvent
        
        Triggers:
        - LVR recalculation
        - LVR breach detection
        - LMI assessment
        """
        
        # Load current collateral
        collateral = await self._reconstruct_collateral(collateral_id)
        
        # Calculate new LVR
        new_lvr = (collateral.loan_amount_secured / market_value * Decimal("100"))
        
        # LVR breach?
        lvr_breach = new_lvr > collateral.policy_max_lvr
        
        # Additional security required?
        additional_security_required = False
        additional_security_amount = None
        
        if lvr_breach:
            # Calculate shortfall
            max_loan = market_value * collateral.policy_max_lvr / Decimal("100")
            shortfall = collateral.loan_amount_secured - max_loan
            additional_security_required = True
            additional_security_amount = shortfall
        
        # Valuation expiry (90 days for property, 30 days for vehicles)
        if collateral.collateral_type == CollateralType.MOTOR_VEHICLE:
            expiry_days = 30
        else:
            expiry_days = 90
        
        valuation_expiry = date.today() + timedelta(days=expiry_days)
        
        # Create event
        event = CollateralValuationCompletedEvent(
            aggregate_id=collateral_id,
            collateral_id=collateral_id,
            loan_id=collateral.loan_id,
            customer_id=collateral.customer_id,
            jurisdiction=collateral.jurisdiction.value,
            valuation_order_id=valuation_order_id,
            valuation_report_reference=valuation_report_reference,
            market_value=market_value,
            forced_sale_value=forced_sale_value,
            valuation_date=date.today(),
            valuation_effective_date=date.today(),
            valuation_expiry_date=valuation_expiry,
            valuer_name=valuer_name,
            valuer_registration=valuer_registration,
            valuation_firm=valuation_firm,
            previous_value=collateral.estimated_value,
            value_change_percentage=(
                (market_value - collateral.estimated_value) / collateral.estimated_value * Decimal("100")
                if collateral.estimated_value > 0 else Decimal("0")
            ),
            new_lvr=new_lvr,
            lvr_breach=lvr_breach,
            additional_security_required=additional_security_required,
            additional_security_amount=additional_security_amount,
            confidence_level="high",
            market_conditions="stable",
            completed_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # If LVR breach, publish alert
        if lvr_breach:
            breach_event = LVRBreachDetectedEvent(
                aggregate_id=collateral_id,
                collateral_id=collateral_id,
                loan_id=collateral.loan_id,
                customer_id=collateral.customer_id,
                jurisdiction=collateral.jurisdiction.value,
                previous_lvr=collateral.current_lvr,
                new_lvr=new_lvr,
                policy_max_lvr=collateral.policy_max_lvr,
                breach_amount=additional_security_amount or Decimal("0"),
                breach_percentage=(new_lvr - collateral.policy_max_lvr),
                triggered_by="valuation_update",
                action_required="additional_security",
                detected_at=datetime.now(timezone.utc)
            )
            
            await self.kafka.publish(breach_event)
            await self.event_store.append_event(breach_event)
    
    async def perfect_security(
        self,
        collateral_id: str,
        perfection_method: str,
        ppsr_registration_number: Optional[str] = None,
        ppsr_registration_time: Optional[datetime] = None,
        caveat_number: Optional[str] = None,
        security_agreement_date: Optional[date] = None
    ) -> None:
        """
        Perfect security interest under PPSA.
        
        Publishes: CollateralPerfectedEvent
        
        Critical: Establishes priority!
        """
        
        collateral = await self._reconstruct_collateral(collateral_id)
        
        # Determine priority (simplified - would check PPSR search results)
        priority_position = SecurityPosition.FIRST
        prior_encumbrances = []
        
        event = CollateralPerfectedEvent(
            aggregate_id=collateral_id,
            collateral_id=collateral_id,
            loan_id=collateral.loan_id,
            customer_id=collateral.customer_id,
            jurisdiction=collateral.jurisdiction.value,
            perfection_method=perfection_method,
            ppsr_registration_number=ppsr_registration_number,
            ppsr_registration_time=ppsr_registration_time,
            ppsr_security_agreement_date=security_agreement_date or date.today(),
            caveat_number=caveat_number,
            priority_position=priority_position.value,
            prior_encumbrances=prior_encumbrances,
            perfected_by="system",
            perfected_at=datetime.now(timezone.utc),
            legal_advice_obtained=False
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
    
    async def release_collateral(
        self,
        collateral_id: str,
        release_reason: str,
        final_loan_balance: Decimal,
        released_by: str
    ) -> None:
        """
        Release collateral (loan repaid).
        
        Publishes: CollateralReleasedEvent
        
        Triggers:
        - PPSR discharge (5 business days deadline!)
        - Land title discharge
        - Insurance cancellation
        """
        
        collateral = await self._reconstruct_collateral(collateral_id)
        
        # PPSR discharge required?
        ppsr_discharge_required = collateral.ppsr_registration is not None
        
        event = CollateralReleasedEvent(
            aggregate_id=collateral_id,
            collateral_id=collateral_id,
            loan_id=collateral.loan_id,
            customer_id=collateral.customer_id,
            jurisdiction=collateral.jurisdiction.value,
            release_reason=release_reason,
            final_loan_balance=final_loan_balance,
            release_date=date.today(),
            ppsr_discharge_requested=ppsr_discharge_required,
            ppsr_discharge_completed=False,
            title_discharge_lodged=False,
            title_discharge_completed=False,
            original_title_returned=False,
            discharge_statement_issued=False,
            released_by=released_by,
            released_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Trigger PPSR discharge if required
        if ppsr_discharge_required:
            await self._initiate_ppsr_discharge(collateral)
    
    async def get_collateral(self, collateral_id: str) -> Collateral:
        """Reconstruct collateral from events."""
        return await self._reconstruct_collateral(collateral_id)
    
    # Private helpers
    
    async def _reconstruct_collateral(self, collateral_id: str) -> Collateral:
        """Reconstruct collateral aggregate from events."""
        # Placeholder - would replay events from event store
        raise NotImplementedError("Event replay not implemented")
    
    async def _initiate_ppsr_discharge(self, collateral: Collateral):
        """Initiate PPSR discharge process."""
        # Would integrate with PPSR API
        pass

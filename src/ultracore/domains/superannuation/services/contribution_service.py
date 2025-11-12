"""Contribution Service - SMSF Contributions"""
from typing import Dict
from decimal import Decimal
from datetime import date
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import ConcessionalContributionReceivedEvent, NonConcessionalContributionReceivedEvent
from ..models import ContributionType


class ContributionService:
    """
    SMSF contribution processing service.
    
    Features:
    - Concessional contributions (15% tax)
    - Non-concessional contributions (0% tax)
    - Cap monitoring and alerts
    - Unused cap carry-forward
    - ATO reporting
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
    
    async def make_contribution(
        self,
        smsf_id: str,
        member_id: str,
        amount: Decimal,
        contribution_type: ContributionType,
        financial_year: str = "2024-25",
        **kwargs
    ) -> Dict:
        """
        Process SMSF contribution.
        
        Applies contributions tax:
        - Concessional: 15% (before-tax)
        - Non-concessional: 0% (after-tax)
        
        Monitors caps and alerts if exceeded.
        """
        
        contribution_id = f"CONT-{uuid.uuid4().hex[:12].upper()}"
        
        if contribution_type in [ContributionType.CONCESSIONAL, ContributionType.EMPLOYER, 
                                 ContributionType.SALARY_SACRIFICE, ContributionType.PERSONAL_DEDUCTIBLE]:
            # Concessional contribution
            result = await self._process_concessional(
                contribution_id=contribution_id,
                smsf_id=smsf_id,
                member_id=member_id,
                amount=amount,
                contribution_type=contribution_type,
                financial_year=financial_year,
                **kwargs
            )
        else:
            # Non-concessional contribution
            result = await self._process_non_concessional(
                contribution_id=contribution_id,
                smsf_id=smsf_id,
                member_id=member_id,
                amount=amount,
                contribution_type=contribution_type,
                financial_year=financial_year,
                **kwargs
            )
        
        return result
    
    async def _process_concessional(
        self,
        contribution_id: str,
        smsf_id: str,
        member_id: str,
        amount: Decimal,
        contribution_type: ContributionType,
        financial_year: str,
        **kwargs
    ) -> Dict:
        """Process concessional contribution (15% tax)."""
        
        # Calculate tax
        contributions_tax = amount * Decimal("0.15")
        division_293_tax = Decimal("0.00")  # Would check if income > $250K
        net_contribution = amount - contributions_tax - division_293_tax
        
        # Check caps (mock YTD for now)
        ytd_concessional = Decimal("15000")  # Would fetch from events
        concessional_cap = Decimal("30000")
        new_ytd = ytd_concessional + amount
        
        cap_exceeded = new_ytd > concessional_cap
        excess_amount = max(Decimal("0"), new_ytd - concessional_cap)
        
        # Publish event
        event = ConcessionalContributionReceivedEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            contribution_id=contribution_id,
            member_id=member_id,
            amount=amount,
            contribution_type=contribution_type.value,
            source_description=kwargs.get("source_description", "Employer contribution"),
            contributions_tax=contributions_tax,
            division_293_tax=division_293_tax,
            net_contribution=net_contribution,
            contribution_year=financial_year,
            year_to_date_concessional=new_ytd,
            concessional_cap=concessional_cap,
            cap_exceeded=cap_exceeded,
            excess_amount=excess_amount,
            received_date=date.today(),
            ledger_entry_id=f"LE-{uuid.uuid4().hex[:8]}"
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        result = {
            "success": True,
            "contribution_id": contribution_id,
            "contribution_type": "concessional",
            "gross_amount": float(amount),
            "contributions_tax": float(contributions_tax),
            "net_contribution": float(net_contribution),
            "cap_status": {
                "ytd_contributions": float(new_ytd),
                "annual_cap": float(concessional_cap),
                "remaining": float(concessional_cap - new_ytd),
                "cap_exceeded": cap_exceeded
            }
        }
        
        if cap_exceeded:
            result["warning"] = f"?? Concessional cap exceeded by ${float(excess_amount):,.2f}"
            result["action_required"] = "Contact accountant - excess taxed at marginal rate"
        else:
            result["message"] = "? Contribution processed successfully"
        
        return result
    
    async def _process_non_concessional(
        self,
        contribution_id: str,
        smsf_id: str,
        member_id: str,
        amount: Decimal,
        contribution_type: ContributionType,
        financial_year: str,
        **kwargs
    ) -> Dict:
        """Process non-concessional contribution (0% tax)."""
        
        # No tax on non-concessional
        net_contribution = amount
        
        # Check caps
        ytd_non_concessional = Decimal("50000")  # Mock
        non_concessional_cap = Decimal("120000")
        bring_forward_cap = Decimal("360000")
        
        new_ytd = ytd_non_concessional + amount
        
        # Check if bring-forward triggered
        bring_forward_triggered = new_ytd > non_concessional_cap
        applicable_cap = bring_forward_cap if bring_forward_triggered else non_concessional_cap
        
        cap_exceeded = new_ytd > applicable_cap
        excess_amount = max(Decimal("0"), new_ytd - applicable_cap)
        
        # Publish event
        event = NonConcessionalContributionReceivedEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            contribution_id=contribution_id,
            member_id=member_id,
            amount=amount,
            contribution_type=contribution_type.value,
            contributions_tax=Decimal("0.00"),
            contribution_year=financial_year,
            year_to_date_non_concessional=new_ytd,
            non_concessional_cap=non_concessional_cap,
            bring_forward_triggered=bring_forward_triggered,
            bring_forward_cap=bring_forward_cap,
            cap_exceeded=cap_exceeded,
            excess_amount=excess_amount,
            total_super_balance=Decimal("500000"),  # Mock
            tsb_limit=Decimal("1900000"),
            received_date=date.today()
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        result = {
            "success": True,
            "contribution_id": contribution_id,
            "contribution_type": "non_concessional",
            "amount": float(amount),
            "tax": 0.00,
            "net_contribution": float(net_contribution),
            "cap_status": {
                "ytd_contributions": float(new_ytd),
                "annual_cap": float(non_concessional_cap),
                "bring_forward_triggered": bring_forward_triggered,
                "applicable_cap": float(applicable_cap),
                "remaining": float(applicable_cap - new_ytd),
                "cap_exceeded": cap_exceeded
            }
        }
        
        if bring_forward_triggered and not cap_exceeded:
            result["info"] = f"?? Bring-forward triggered - 3-year cap of ${float(bring_forward_cap):,.0f} applies"
        
        if cap_exceeded:
            result["warning"] = f"?? Non-concessional cap exceeded by ${float(excess_amount):,.2f}"
            result["action_required"] = "Excess contributions taxed at 47% or can be withdrawn"
        else:
            result["message"] = "? Contribution processed (no tax on after-tax contributions)"
        
        return result

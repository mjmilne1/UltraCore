"""Pension Service - SMSF Pension Management"""
from typing import Dict
from decimal import Decimal
from datetime import date
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import PensionCommencedEvent, PensionPaymentMadeEvent
from ..models import PensionType, MinimumPension


class PensionService:
    """
    SMSF pension (retirement income) service.
    
    Features:
    - Pension commencement (condition of release)
    - Account-based pensions
    - TTR (Transition to Retirement)
    - Minimum drawdown monitoring
    - 0% tax in pension phase! ??
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
    
    async def commence_pension(
        self,
        smsf_id: str,
        member_id: str,
        member_age: int,
        opening_balance: Decimal,
        pension_type: PensionType = PensionType.ACCOUNT_BASED,
        payment_frequency: str = "monthly",
        **kwargs
    ) -> Dict:
        """
        Commence pension (retirement income stream).
        
        Conditions of Release:
        - Age 60+ and retired
        - Age 65+ (regardless)
        - TTR: Age 60+ still working
        
        Amazing Benefits:
        - 0% tax on earnings in pension phase!
        - Tax-free payments if 60+
        """
        
        pension_id = f"PEN-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate minimum drawdown
        minimum_percentage = MinimumPension.get_minimum_for_age(member_age)
        minimum_annual = opening_balance * minimum_percentage
        
        # Calculate payment amount
        if payment_frequency == "monthly":
            payment_amount = minimum_annual / 12
        elif payment_frequency == "quarterly":
            payment_amount = minimum_annual / 4
        else:  # annually
            payment_amount = minimum_annual
        
        # TTR maximum (10% of balance)
        maximum_annual = opening_balance * Decimal("0.10") if pension_type == PensionType.TTR else None
        
        # Tax components (simplified)
        tax_free_component = opening_balance * Decimal("0.70")  # Mock
        taxable_component = opening_balance * Decimal("0.30")
        
        # Publish event
        event = PensionCommencedEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            pension_id=pension_id,
            member_id=member_id,
            pension_type=pension_type.value,
            opening_balance=opening_balance,
            member_age=member_age,
            minimum_percentage=minimum_percentage,
            minimum_annual_payment=minimum_annual,
            payment_frequency=payment_frequency,
            payment_amount=payment_amount,
            tax_free_component=tax_free_component,
            taxable_component=taxable_component,
            transfer_balance_cap=Decimal("1900000"),
            transfer_balance_account_credit=opening_balance,
            commencement_date=date.today(),
            financial_year=self._get_financial_year()
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "pension_id": pension_id,
            "pension_type": pension_type.value,
            "opening_balance": float(opening_balance),
            "tax_benefits": {
                "earnings_tax": "0% in pension phase! ??",
                "payment_tax": "Tax-free if 60+" if member_age >= 60 else "Taxable component taxed",
                "savings": "Huge tax savings vs accumulation phase (15% tax)"
            },
            "minimum_drawdown": {
                "age": member_age,
                "percentage": float(minimum_percentage * 100),
                "annual_minimum": float(minimum_annual),
                "payment_frequency": payment_frequency,
                "payment_amount": float(payment_amount)
            },
            "maximum_drawdown": {
                "annual_maximum": float(maximum_annual) if maximum_annual else "No limit",
                "restriction": "10% for TTR" if pension_type == PensionType.TTR else "No restriction"
            },
            "next_steps": [
                "Set up automatic pension payments",
                f"Review minimum drawdown annually (currently {float(minimum_percentage * 100):.0f}%)",
                "Monitor pension balance",
                "Adjust payments as needed (above minimum)"
            ],
            "message": f"?? Pension commenced! Enjoy 0% tax on earnings!"
        }
    
    async def make_pension_payment(
        self,
        pension_id: str,
        smsf_id: str,
        member_id: str,
        payment_amount: Decimal,
        destination_account_id: str,
        **kwargs
    ) -> Dict:
        """
        Make pension payment to member.
        
        Payments are tax-free if member is 60+.
        Must meet minimum annual payment.
        """
        
        payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        
        # Mock YTD and minimum
        ytd_payments = Decimal("20000")
        minimum_required = Decimal("32000")
        new_ytd = ytd_payments + payment_amount
        minimum_met = new_ytd >= minimum_required
        
        # Tax (usually $0 if 60+)
        tax_withheld = Decimal("0.00")
        
        # Publish event
        event = PensionPaymentMadeEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            pension_id=pension_id,
            member_id=member_id,
            payment_id=payment_id,
            payment_amount=payment_amount,
            payment_date=date.today(),
            financial_year=self._get_financial_year(),
            ytd_payments=new_ytd,
            minimum_payment_required=minimum_required,
            minimum_met=minimum_met,
            tax_withheld=tax_withheld,
            destination_account_id=destination_account_id
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "payment_id": payment_id,
            "payment_amount": float(payment_amount),
            "tax_withheld": float(tax_withheld),
            "net_payment": float(payment_amount - tax_withheld),
            "ytd_status": {
                "ytd_payments": float(new_ytd),
                "minimum_required": float(minimum_required),
                "remaining": float(max(Decimal("0"), minimum_required - new_ytd)),
                "minimum_met": minimum_met,
                "percentage_of_minimum": float((new_ytd / minimum_required) * 100) if minimum_required > 0 else 0
            },
            "message": "? Pension payment processed (tax-free!)" if tax_withheld == 0 else "? Pension payment processed"
        }
    
    def _get_financial_year(self) -> str:
        """Get current financial year (July 1 - June 30)."""
        today = date.today()
        if today.month >= 7:
            return f"{today.year}-{str(today.year + 1)[-2:]}"
        else:
            return f"{today.year - 1}-{str(today.year)[-2:]}"

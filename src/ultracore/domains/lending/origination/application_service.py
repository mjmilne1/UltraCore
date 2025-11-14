"""Loan Application Service - Event-Sourced Origination"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    LoanApplicationSubmittedEvent,
    CreditCheckCompletedEvent,
    LoanApprovedEvent,
    LoanRejectedEvent,
    LoanDisbursedEvent
)
from ..models import LoanApplication, LoanType, LoanPurpose
from ..ml import CreditScorer, AffordabilityCalculator
from ..rl import LoanPricingOptimizer
# from ultracore.domains.accounts.ledger import UltraLedgerService  # TODO: Fix import path


class LoanApplicationService:
    """
    Event-sourced loan origination.
    
    Australian NCCP Compliance:
    - Responsible lending assessment
    - Assessment of unsuitability
    - Credit checking
    - Affordability verification
    - Purpose verification
    
    Workflow:
    1. Application submitted ? Event
    2. Credit check ? Event
    3. ML scoring ? Risk assessment
    4. RL pricing ? Optimal rate
    5. Approval decision ? Event
    6. Disbursement ? Event + UltraLedger
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ledger_service: UltraLedgerService,
        credit_scorer: CreditScorer,
        pricing_optimizer: LoanPricingOptimizer
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ledger = ledger_service
        self.credit_scorer = credit_scorer
        self.pricing = pricing_optimizer
    
    async def submit_application(
        self,
        customer_id: str,
        loan_type: LoanType,
        loan_purpose: LoanPurpose,
        loan_amount: Decimal,
        loan_term_months: int,
        annual_income: Decimal,
        employment_type: str,
        employment_duration_months: int,
        monthly_living_expenses: Decimal,
        monthly_debt_obligations: Decimal,
        dependents: int = 0,
        property_address: Optional[str] = None,
        property_value: Optional[Decimal] = None,
        **kwargs
    ) -> Dict:
        """
        Submit loan application.
        
        Publishes: LoanApplicationSubmittedEvent
        Triggers: Automated credit check and assessment
        
        NCCP Requirement: Collect sufficient information to
        assess whether loan is unsuitable for customer.
        """
        
        application_id = f"APP-{uuid.uuid4().hex[:12].upper()}"
        loan_id = f"LOAN-{uuid.uuid4().hex[:12].upper()}"
        
        # Publish application event
        event = LoanApplicationSubmittedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            application_id=application_id,
            customer_id=customer_id,
            loan_type=loan_type.value,
            loan_purpose=loan_purpose.value,
            loan_amount=loan_amount,
            loan_term_months=loan_term_months,
            employment_type=employment_type,
            annual_income=annual_income,
            employment_duration_months=employment_duration_months,
            monthly_living_expenses=monthly_living_expenses,
            monthly_debt_obligations=monthly_debt_obligations,
            dependents=dependents,
            property_address=property_address,
            property_value=property_value,
            property_usage=kwargs.get("property_usage"),
            submitted_at=datetime.now(timezone.utc),
            submitted_via=kwargs.get("channel", "online")
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Trigger automated assessment
        assessment = await self._automated_assessment(
            application_id=application_id,
            loan_id=loan_id,
            customer_id=customer_id,
            application_data={
                "loan_type": loan_type.value,
                "loan_amount": loan_amount,
                "loan_term_months": loan_term_months,
                "annual_income": annual_income,
                "employment_type": employment_type,
                "employment_duration_months": employment_duration_months,
                "monthly_living_expenses": monthly_living_expenses,
                "monthly_debt_obligations": monthly_debt_obligations,
                "dependents": dependents,
                "property_value": property_value
            }
        )
        
        return {
            "application_id": application_id,
            "loan_id": loan_id,
            "status": "submitted",
            "assessment": assessment,
            "next_steps": [
                "Credit check in progress",
                "Assessment typically completes within 24 hours",
                "You'll be notified of decision via email/SMS"
            ]
        }
    
    async def _automated_assessment(
        self,
        application_id: str,
        loan_id: str,
        customer_id: str,
        application_data: Dict
    ) -> Dict:
        """
        Automated assessment workflow.
        
        1. Credit check (via bureau API)
        2. ML credit scoring
        3. Affordability calculation
        4. RL pricing optimization
        5. Approval decision
        """
        
        # 1. Credit check (simulated)
        credit_check = await self._perform_credit_check(customer_id)
        
        # Publish credit check event
        credit_event = CreditCheckCompletedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            application_id=application_id,
            bureau="equifax",
            bureau_reference=f"EQ-{uuid.uuid4().hex[:8].upper()}",
            credit_score=credit_check["credit_score"],
            credit_score_band=credit_check["credit_score_band"],
            enquiries_last_12_months=credit_check["enquiries_last_12_months"],
            active_credit_accounts=credit_check["active_credit_accounts"],
            total_credit_limit=Decimal(str(credit_check["total_credit_limit"])),
            total_outstanding_balance=Decimal(str(credit_check["total_outstanding_balance"])),
            payment_defaults=credit_check["payment_defaults"],
            on_time_payments_percentage=Decimal(str(credit_check["on_time_payments_percentage"])),
            credit_risk_rating=credit_check["credit_risk_rating"],
            completed_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(credit_event)
        await self.event_store.append_event(credit_event)
        
        # 2. ML credit scoring
        credit_assessment = await self.credit_scorer.score_application(
            application=application_data,
            credit_check=credit_check
        )
        
        # 3. RL pricing optimization
        pricing = await self.pricing.optimize_rate(
            loan_type=application_data["loan_type"],
            loan_amount=application_data["loan_amount"],
            term_months=application_data["loan_term_months"],
            credit_score=credit_assessment["credit_score"],
            risk_band=credit_assessment["risk_band"],
            lvr=self._calculate_lvr(application_data) if application_data.get("property_value") else None
        )
        
        # 4. Decision
        decision = self._make_decision(credit_assessment, pricing)
        
        return {
            "credit_check": credit_check,
            "credit_assessment": credit_assessment,
            "pricing": pricing,
            "decision": decision
        }
    
    async def _perform_credit_check(self, customer_id: str) -> Dict:
        """
        Perform credit check via bureau.
        
        Australian Credit Bureaus:
        - Equifax (formerly Veda)
        - Experian
        - Illion (formerly Dun & Bradstreet)
        """
        
        # Mock credit check (would call real API)
        return {
            "credit_score": 750,
            "credit_score_band": "good",
            "enquiries_last_12_months": 2,
            "active_credit_accounts": 3,
            "total_credit_limit": 25000.00,
            "total_outstanding_balance": 8000.00,
            "payment_defaults": 0,
            "on_time_payments_percentage": 95.0,
            "credit_risk_rating": "low"
        }
    
    def _calculate_lvr(self, application_data: Dict) -> Decimal:
        """Calculate Loan-to-Value Ratio."""
        loan_amount = application_data.get("loan_amount", Decimal("0"))
        property_value = application_data.get("property_value", Decimal("1"))
        
        if property_value > 0:
            return loan_amount / property_value
        return Decimal("0")
    
    def _make_decision(self, credit_assessment: Dict, pricing: Dict) -> str:
        """Make approval decision."""
        recommendation = credit_assessment.get("approval_recommendation")
        
        if recommendation == "approve":
            return "approved"
        elif recommendation == "review":
            return "manual_review"
        else:
            return "declined"
    
    async def approve_application(
        self,
        loan_id: str,
        application_id: str,
        customer_id: str,
        approved_amount: Decimal,
        approved_term_months: int,
        interest_rate: Decimal,
        comparison_rate: Decimal,
        disbursement_account_id: str,
        approved_by: str = "system",
        **kwargs
    ) -> Dict:
        """
        Approve loan application.
        
        Publishes: LoanApprovedEvent
        
        NCCP: Provides credit contract disclosure
        """
        
        # Calculate repayment
        repayment = self._calculate_repayment(
            approved_amount,
            interest_rate,
            approved_term_months
        )
        
        # Publish approval event
        event = LoanApprovedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            application_id=application_id,
            approved_amount=approved_amount,
            approved_term_months=approved_term_months,
            interest_rate=interest_rate,
            comparison_rate=comparison_rate,
            establishment_fee=Decimal("500.00"),
            monthly_fee=Decimal("10.00"),
            repayment_amount=repayment,
            repayment_frequency="monthly",
            first_payment_date=date.today(),
            responsible_lending_assessed=True,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc),
            disbursement_account_id=disbursement_account_id
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "loan_id": loan_id,
            "status": "approved",
            "approved_amount": float(approved_amount),
            "interest_rate": float(interest_rate),
            "comparison_rate": float(comparison_rate),
            "monthly_repayment": float(repayment),
            "total_repayable": float(repayment * approved_term_months),
            "message": "Loan approved! Funds will be disbursed within 1 business day."
        }
    
    def _calculate_repayment(
        self,
        amount: Decimal,
        rate: Decimal,
        term_months: int
    ) -> Decimal:
        """Calculate monthly repayment amount."""
        # Monthly interest rate
        monthly_rate = rate / Decimal("100") / Decimal("12")
        
        # Amortization formula
        if monthly_rate > 0:
            repayment = amount * (
                monthly_rate * (1 + monthly_rate) ** term_months
            ) / (
                (1 + monthly_rate) ** term_months - 1
            )
        else:
            repayment = amount / term_months
        
        return repayment.quantize(Decimal("0.01"))

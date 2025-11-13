"""SMSF Service - Establishment and Management"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date, datetime
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import SMSFEstablishedEvent, MemberAddedEvent
from ..models import SMSF, TrusteeType
# from ultracore.domains.accounts.services import AccountService  # TODO: Fix import path


class SMSFService:
    """
    SMSF establishment and management service.
    
    Features:
    - SMSF establishment (trust deed, ABN, TFN)
    - Member management (add, remove)
    - Trustee appointments
    - Investment strategy
    - ATO registration
    - Compliance monitoring
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        account_service: AccountService
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.accounts = account_service
    
    async def establish_smsf(
        self,
        fund_name: str,
        trustee_type: TrusteeType,
        members: List[Dict],
        investment_strategy: str = "balanced",
        risk_tolerance: str = "medium",
        **kwargs
    ) -> Dict:
        """
        Establish new SMSF.
        
        Steps:
        1. Validate member count (max 6)
        2. Generate ABN/TFN (mock for now)
        3. Create trust deed
        4. Register with ATO
        5. Open bank accounts
        6. Add members
        7. Create investment strategy
        
        Returns SMSF details and setup checklist.
        """
        
        # Validate
        if len(members) > 6:
            raise ValueError("SMSF cannot have more than 6 members")
        
        if len(members) < 1:
            raise ValueError("SMSF must have at least 1 member")
        
        # Generate IDs
        smsf_id = f"SMSF-{uuid.uuid4().hex[:12].upper()}"
        abn = self._generate_abn()
        tfn = self._generate_tfn()
        
        # Create operating account
        operating_account = await self.accounts.create_account(
            customer_id=smsf_id,
            account_name=f"{fund_name} - Operating Account",
            account_type="transactional"
        )
        
        # Publish event
        event = SMSFEstablishedEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            fund_name=fund_name,
            abn=abn,
            tfn=tfn,
            trustee_type=trustee_type.value,
            member_ids=[m["member_id"] for m in members],
            investment_strategy=investment_strategy,
            risk_tolerance=risk_tolerance,
            establishment_date=date.today(),
            established_by=kwargs.get("established_by", "system")
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Add members
        for member_data in members:
            await self.add_member(
                smsf_id=smsf_id,
                member_data=member_data
            )
        
        return {
            "success": True,
            "smsf_id": smsf_id,
            "fund_name": fund_name,
            "abn": abn,
            "trustee_type": trustee_type.value,
            "member_count": len(members),
            "operating_account_id": operating_account["account_id"],
            "setup_checklist": {
                "trust_deed": "Execute trust deed with all trustees",
                "ato_registration": "Register with ATO (ABN/TFN obtained)",
                "bank_account": f"Opened: {operating_account['account_number']}",
                "investment_strategy": "Create written investment strategy",
                "insurance": "Consider insurance for members",
                "auditor": "Appoint SMSF auditor",
                "annual_return": "Lodge annual return by October 31"
            },
            "next_steps": [
                "Execute trust deed",
                "Transfer initial contributions",
                "Invest according to strategy",
                "Arrange annual audit",
                "Lodge annual return"
            ],
            "important_dates": {
                "annual_return_due": "October 31 each year",
                "audit_required": "Before lodging annual return",
                "financial_year_end": "June 30"
            },
            "message": f"?? SMSF '{fund_name}' established successfully!"
        }
    
    async def add_member(
        self,
        smsf_id: str,
        member_data: Dict
    ) -> Dict:
        """
        Add member to SMSF.
        
        Member becomes trustee (individual structure)
        or director (corporate trustee).
        """
        
        member_id = member_data.get("member_id", f"MEM-{uuid.uuid4().hex[:8].upper()}")
        
        # Create accumulation account
        acc_account = await self.accounts.create_account(
            customer_id=member_data["customer_id"],
            account_name=f"SMSF Accumulation - {member_data['first_name']} {member_data['last_name']}",
            account_type="savings"
        )
        
        # Publish event
        event = MemberAddedEvent(
            aggregate_id=smsf_id,
            smsf_id=smsf_id,
            member_id=member_id,
            customer_id=member_data["customer_id"],
            first_name=member_data["first_name"],
            last_name=member_data["last_name"],
            date_of_birth=member_data["date_of_birth"],
            tfn=member_data["tfn"],
            join_date=date.today(),
            member_type=member_data.get("member_type", "adult"),
            accumulation_account_id=acc_account["account_id"],
            opening_balance=member_data.get("opening_balance", Decimal("0"))
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "member_id": member_id,
            "accumulation_account_id": acc_account["account_id"],
            "message": f"Member {member_data['first_name']} {member_data['last_name']} added successfully"
        }
    
    def _generate_abn(self) -> str:
        """Generate ABN (mock)."""
        import random
        return f"{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)} {random.randint(100,999)}"
    
    def _generate_tfn(self) -> str:
        """Generate TFN (mock, encrypted in production)."""
        import random
        return f"{random.randint(100,999)} {random.randint(100,999)} {random.randint(100,999)}"

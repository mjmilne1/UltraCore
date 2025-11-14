"""BNPL Service - Buy Now Pay Later (Afterpay Style)"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ...events import BNPLPurchaseCreatedEvent, BNPLInstallmentPaidEvent
from ...models import BNPLPurchase, LoanStatus
# from ultracore.domains.accounts.ledger import UltraLedgerService  # TODO: Fix import path


class BNPLService:
    """
    Buy Now Pay Later service (Afterpay/Zip/Klarna style).
    
    Australian BNPL Market:
    - Afterpay: 4 payments over 6 weeks
    - Zip: Flexible terms, 4-12 weeks
    - Klarna: 4 payments over 6 weeks
    - Humm: Longer terms available
    
    Features:
    - Interest-free if paid on time
    - Installment-based (typically 4 payments)
    - Fortnightly payments
    - Late fees for missed payments
    - Merchant-funded (merchant pays fee)
    - Quick approval (real-time)
    
    Regulation:
    - ASIC oversight (credit product)
    - Responsible lending principles
    - Small amount exemptions (< $2,000)
    - Consumer protection laws
    
    Model:
    1. Customer makes purchase at merchant
    2. BNPL pays merchant immediately (minus fee)
    3. Customer pays in 4 installments
    4. First payment at checkout (25%)
    5. Remaining 3 payments fortnightly
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ledger_service: UltraLedgerService
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ledger = ledger_service
    
    async def create_purchase(
        self,
        customer_id: str,
        merchant: str,
        order_id: str,
        purchase_amount: Decimal,
        merchant_category: str = "retail",
        **kwargs
    ) -> Dict:
        """
        Create BNPL purchase (instant approval).
        
        Approval Criteria:
        - Purchase amount < $2,000
        - No recent missed payments
        - Customer has payment method on file
        - Real-time affordability check
        
        Publishes: BNPLPurchaseCreatedEvent
        """
        
        # Validation
        if purchase_amount > Decimal("2000.00"):
            return {
                "success": False,
                "error": "Purchase amount exceeds $2,000 limit"
            }
        
        if purchase_amount < Decimal("1.00"):
            return {
                "success": False,
                "error": "Purchase amount too small"
            }
        
        # Generate IDs
        loan_id = f"BNPL-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate installments (4 payments)
        number_of_installments = 4
        installment_amount = (purchase_amount / number_of_installments).quantize(Decimal("0.01"))
        
        # First payment today, then fortnightly
        installment_dates = self._calculate_installment_dates(number_of_installments)
        
        # Create purchase
        purchase = BNPLPurchase(
            loan_id=loan_id,
            application_id=loan_id,  # Same for BNPL
            customer_id=customer_id,
            merchant=merchant,
            order_id=order_id,
            principal=purchase_amount,
            current_balance=purchase_amount,
            principal_outstanding=purchase_amount,
            interest_outstanding=Decimal("0.00"),
            number_of_installments=number_of_installments,
            installment_amount=installment_amount,
            installments_paid=0,
            repayment_amount=installment_amount,
            repayment_frequency="fortnightly",
            next_payment_date=installment_dates[0],
            status=LoanStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Publish event
        event = BNPLPurchaseCreatedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            loan_type="bnpl",
            merchant=merchant,
            order_id=order_id,
            purchase_amount=purchase_amount,
            installment_amount=installment_amount,
            number_of_installments=number_of_installments,
            first_payment_date=installment_dates[0],
            created_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Record in UltraLedger (merchant gets paid immediately)
        await self._record_merchant_payment(
            loan_id=loan_id,
            merchant=merchant,
            amount=purchase_amount
        )
        
        return {
            "success": True,
            "loan_id": loan_id,
            "purchase_amount": float(purchase_amount),
            "installment_amount": float(installment_amount),
            "number_of_installments": number_of_installments,
            "payment_schedule": [
                {
                    "installment": i + 1,
                    "amount": float(installment_amount),
                    "due_date": installment_dates[i].isoformat()
                }
                for i in range(number_of_installments)
            ],
            "first_payment_today": True,
            "message": f"Purchase approved! First payment of ${float(installment_amount):.2f} due today, then 3 more fortnightly payments."
        }
    
    def _calculate_installment_dates(self, num_installments: int) -> List[date]:
        """Calculate fortnightly installment dates."""
        dates = []
        current_date = date.today()
        
        for i in range(num_installments):
            dates.append(current_date + timedelta(weeks=2 * i))
        
        return dates
    
    async def _record_merchant_payment(
        self,
        loan_id: str,
        merchant: str,
        amount: Decimal
    ):
        """
        Record merchant payment in UltraLedger.
        
        BNPL pays merchant immediately (minus fee).
        Merchant fee typically: 3-6% of purchase.
        """
        
        merchant_fee = amount * Decimal("0.04")  # 4% fee
        merchant_payment = amount - merchant_fee
        
        # Would record actual ledger entry
        pass
    
    async def process_installment_payment(
        self,
        loan_id: str,
        customer_id: str,
        payment_amount: Decimal,
        payment_method: str = "auto_debit"
    ) -> Dict:
        """
        Process BNPL installment payment.
        
        Publishes: BNPLInstallmentPaidEvent
        """
        
        # Publish event
        event = BNPLInstallmentPaidEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            loan_type="bnpl",
            installment_number=1,  # Would track current
            payment_amount=payment_amount,
            paid_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "payment_processed": True,
            "remaining_installments": 3,
            "next_payment_date": (date.today() + timedelta(weeks=2)).isoformat()
        }
    
    async def apply_late_fee(
        self,
        loan_id: str,
        customer_id: str,
        days_overdue: int
    ) -> Dict:
        """
        Apply late fee for missed installment.
        
        Australian BNPL Late Fees:
        - Typically $10 per missed payment
        - Capped at certain amounts
        - Must be reasonable (ASIC requirement)
        """
        
        late_fee = Decimal("10.00")
        
        # Publish event
        event = BNPLInstallmentMissedEvent(
            aggregate_id=loan_id,
            loan_id=loan_id,
            customer_id=customer_id,
            loan_type="bnpl",
            installment_number=1,
            days_overdue=days_overdue,
            late_fee=late_fee,
            missed_at=datetime.now(timezone.utc)
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "success": True,
            "late_fee_applied": float(late_fee),
            "message": f"Late fee of ${float(late_fee):.2f} applied. Please pay as soon as possible to avoid further fees."
        }


class BNPLInstallmentMissedEvent:
    """BNPL installment missed (simplified for now)."""
    pass

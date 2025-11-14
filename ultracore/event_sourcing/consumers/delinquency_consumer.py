"""
Delinquency Event Consumer
Processes payment events and updates delinquency status in real-time
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging
import asyncio

from ultracore.event_sourcing.consumers.base_consumer import BaseEventConsumer
from ultracore.domains.delinquency.models.delinquency_status import (
    DelinquencyStatus,
    DelinquencyBucket,
)
from ultracore.domains.delinquency.services.delinquency_service import DelinquencyService
from ultracore.domains.delinquency.events.event_producer import DelinquencyEventProducer
from ultracore.domains.delinquency.events.delinquency_events import (
    LoanBecameDelinquentEvent,
    DelinquencyBucketChangedEvent,
    DelinquencyCuredEvent,
    LateFeeAppliedEvent,
    PaymentReminderSentEvent,
)

logger = logging.getLogger(__name__)


class DelinquencyConsumer(BaseEventConsumer):
    """
    Delinquency Event Consumer
    
    Listens to payment events and loan events, automatically:
    - Calculates days past due
    - Updates delinquency buckets
    - Triggers automated actions (fees, reminders, notices)
    - Publishes delinquency events to Kafka
    
    This enables real-time delinquency tracking across the platform.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "delinquency-consumer-group"
    ):
        # Subscribe to payment and loan topics
        topics = [
            "ultracore.loans.payments",  # Payment events
            "ultracore.loans.lifecycle",  # Loan lifecycle events
        ]
        
        super().__init__(
            topics=topics,
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )
        
        self.delinquency_service = DelinquencyService()
        self.event_producer = DelinquencyEventProducer(bootstrap_servers)
        
        # In-memory cache of delinquency statuses
        # In production, this would be backed by database
        self.delinquency_statuses: Dict[UUID, DelinquencyStatus] = {}
        
        logger.info("✓ Delinquency consumer initialized")
    
    async def process_event(self, event: Dict[str, Any]) -> bool:
        """
        Process incoming event
        
        Args:
            event: Event data
        
        Returns:
            True if processed successfully
        """
        event_type = event.get("event_type")
        
        try:
            if event_type == "PaymentReceived":
                await self._handle_payment_received(event)
            elif event_type == "PaymentMissed":
                await self._handle_payment_missed(event)
            elif event_type == "LoanDisbursed":
                await self._handle_loan_disbursed(event)
            elif event_type == "PaymentDue":
                await self._handle_payment_due(event)
            else:
                logger.debug(f"Ignoring event type: {event_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}", exc_info=True)
            return False
    
    async def _handle_payment_received(self, event: Dict[str, Any]):
        """Handle payment received event"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        payment_amount = Decimal(str(event_data.get("amount", "0.00")))
        
        logger.info(f"Payment received for loan {loan_id}: ${payment_amount}")
        
        # Get or create delinquency status
        status = self._get_or_create_status(loan_id, tenant_id)
        
        # Update status with payment
        changes = self.delinquency_service.update_delinquency_status(
            status=status,
            payment_received=payment_amount
        )
        
        # Publish events based on changes
        if changes["became_current"]:
            # Delinquency cured!
            await self._publish_delinquency_cured(
                status, payment_amount, user_id, event["event_id"]
            )
        elif changes["bucket_changed"]:
            # Bucket improved (e.g., from Bucket 3 to Bucket 2)
            await self._publish_bucket_changed(
                status, changes, user_id, event["event_id"]
            )
    
    async def _handle_payment_missed(self, event: Dict[str, Any]):
        """Handle payment missed event"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        logger.warning(f"Payment missed for loan {loan_id}")
        
        # Get or create delinquency status
        status = self._get_or_create_status(loan_id, tenant_id)
        
        # Increment missed payments
        status.consecutive_missed_payments += 1
        status.total_missed_payments += 1
        
        # Update amount overdue
        missed_amount = Decimal(str(event_data.get("amount_due", "0.00")))
        status.amount_overdue += missed_amount
        
        # Update status
        changes = self.delinquency_service.update_delinquency_status(status)
        
        # Publish events
        if changes["became_delinquent"]:
            await self._publish_became_delinquent(
                status, user_id, event["event_id"]
            )
        
        if changes["bucket_changed"]:
            await self._publish_bucket_changed(
                status, changes, user_id, event["event_id"]
            )
            
            # Execute automated actions
            await self._execute_automated_actions(
                status, changes["actions_required"], user_id, event["event_id"]
            )
    
    async def _handle_loan_disbursed(self, event: Dict[str, Any]):
        """Handle loan disbursed event - create initial delinquency status"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        
        logger.info(f"Creating delinquency status for new loan {loan_id}")
        
        # Create initial status
        status = DelinquencyStatus(
            loan_id=loan_id,
            tenant_id=tenant_id,
            current_bucket=DelinquencyBucket.CURRENT,
            is_delinquent=False,
        )
        
        self.delinquency_statuses[loan_id] = status
    
    async def _handle_payment_due(self, event: Dict[str, Any]):
        """Handle payment due event - update next due date"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        
        due_date_str = event_data.get("due_date")
        if due_date_str:
            due_date = datetime.fromisoformat(due_date_str).date()
            
            status = self._get_or_create_status(loan_id, tenant_id)
            status.next_due_date = due_date
            
            logger.info(f"Updated next due date for loan {loan_id}: {due_date}")
    
    def _get_or_create_status(
        self,
        loan_id: UUID,
        tenant_id: UUID
    ) -> DelinquencyStatus:
        """Get existing status or create new one"""
        if loan_id not in self.delinquency_statuses:
            self.delinquency_statuses[loan_id] = DelinquencyStatus(
                loan_id=loan_id,
                tenant_id=tenant_id,
            )
        return self.delinquency_statuses[loan_id]
    
    async def _publish_became_delinquent(
        self,
        status: DelinquencyStatus,
        user_id: str,
        causation_id: str
    ):
        """Publish LoanBecameDelinquent event"""
        event = LoanBecameDelinquentEvent(
            loan_id=status.loan_id,
            tenant_id=status.tenant_id,
            days_past_due=status.days_past_due,
            amount_overdue=status.amount_overdue,
            next_due_date=status.next_due_date,
            first_delinquent_date=status.first_delinquent_date,
            triggered_by="missed_payment",
        )
        
        await self.event_producer.publish_loan_became_delinquent(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        logger.warning(f"✗ Loan {status.loan_id} became delinquent")
    
    async def _publish_delinquency_cured(
        self,
        status: DelinquencyStatus,
        amount_paid: Decimal,
        user_id: str,
        causation_id: str
    ):
        """Publish DelinquencyCured event"""
        days_delinquent = 0
        if status.first_delinquent_date:
            days_delinquent = (date.today() - status.first_delinquent_date).days
        
        event = DelinquencyCuredEvent(
            loan_id=status.loan_id,
            tenant_id=status.tenant_id,
            previous_bucket=status.previous_bucket or DelinquencyBucket.CURRENT,
            days_delinquent=days_delinquent,
            total_amount_paid=amount_paid,
            cured_date=date.today(),
            cured_by="full_payment",
        )
        
        await self.event_producer.publish_delinquency_cured(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        logger.info(f"✓ Loan {status.loan_id} delinquency cured")
    
    async def _publish_bucket_changed(
        self,
        status: DelinquencyStatus,
        changes: Dict[str, Any],
        user_id: str,
        causation_id: str
    ):
        """Publish DelinquencyBucketChanged event"""
        event = DelinquencyBucketChangedEvent(
            loan_id=status.loan_id,
            tenant_id=status.tenant_id,
            previous_bucket=changes["old_bucket"],
            new_bucket=changes["new_bucket"],
            days_past_due=status.days_past_due,
            amount_overdue=status.amount_overdue,
            risk_level=status.risk_level,
            bucket_entry_date=status.bucket_entry_date,
            automated_actions=changes.get("actions_required", []),
        )
        
        await self.event_producer.publish_bucket_changed(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        logger.info(
            f"Loan {status.loan_id} bucket changed: "
            f"{changes['old_bucket']} → {changes['new_bucket']}"
        )
    
    async def _execute_automated_actions(
        self,
        status: DelinquencyStatus,
        actions: list[Dict[str, Any]],
        user_id: str,
        causation_id: str
    ):
        """Execute automated actions based on bucket rules"""
        for action in actions:
            action_type = action["type"]
            
            if action_type == "send_reminder":
                await self._send_reminder(status, user_id, causation_id)
            elif action_type == "apply_late_fee":
                await self._apply_late_fee(
                    status, action["amount"], user_id, causation_id
                )
            elif action_type == "send_collection_notice":
                logger.info(f"TODO: Send collection notice for loan {status.loan_id}")
            elif action_type == "escalate_to_collections":
                logger.info(f"TODO: Escalate loan {status.loan_id} to collections")
            elif action_type == "update_provisioning":
                logger.info(f"TODO: Update provisioning for loan {status.loan_id}")
    
    async def _send_reminder(
        self,
        status: DelinquencyStatus,
        user_id: str,
        causation_id: str
    ):
        """Send payment reminder"""
        event = PaymentReminderSentEvent(
            loan_id=status.loan_id,
            tenant_id=status.tenant_id,
            customer_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: Get from loan
            reminder_type="email",
            days_past_due=status.days_past_due,
            amount_overdue=status.amount_overdue,
            sent_date=datetime.utcnow(),
        )
        
        await self.event_producer.publish_reminder_sent(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        status.reminders_sent += 1
        logger.info(f"✉ Payment reminder sent for loan {status.loan_id}")
    
    async def _apply_late_fee(
        self,
        status: DelinquencyStatus,
        fee_amount: Decimal,
        user_id: str,
        causation_id: str
    ):
        """Apply late fee"""
        event = LateFeeAppliedEvent(
            loan_id=status.loan_id,
            tenant_id=status.tenant_id,
            fee_amount=fee_amount,
            fee_reason=f"Late fee for {status.current_bucket}",
            days_past_due=status.days_past_due,
            current_bucket=status.current_bucket,
            applied_date=date.today(),
        )
        
        await self.event_producer.publish_late_fee_applied(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        status.late_fees_applied += fee_amount
        status.fees_overdue += fee_amount
        status.amount_overdue += fee_amount
        
        logger.info(f"💰 Late fee ${fee_amount} applied to loan {status.loan_id}")
    
    def close(self):
        """Close consumer and producer"""
        super().close()
        self.event_producer.close()


# ============================================================================
# Convenience function to start consumer
# ============================================================================

def start_delinquency_consumer(bootstrap_servers: str = "localhost:9092"):
    """Start delinquency consumer"""
    consumer = DelinquencyConsumer(bootstrap_servers=bootstrap_servers)
    consumer.start()
    return consumer

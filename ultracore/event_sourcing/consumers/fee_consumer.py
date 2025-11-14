"""
Fee Event Consumer
Processes events and applies fees in real-time
"""

from typing import Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging

from ultracore.event_sourcing.consumers.base_consumer import BaseEventConsumer
from ultracore.domains.charges_fees.models.fee import Fee, FeeType
from ultracore.domains.charges_fees.services.fee_service import FeeService
from ultracore.domains.charges_fees.events.event_producer import FeeEventProducer
from ultracore.domains.charges_fees.events.fee_events import (
    FeeAppliedEvent,
    FeeWaivedEvent,
)

logger = logging.getLogger(__name__)


class FeeConsumer(BaseEventConsumer):
    """
    Fee Event Consumer
    
    Listens to various events and automatically applies fees based on
    charging rules. Enables real-time fee application across the platform.
    
    Consumes events from:
    - Payment events (missed payments, late payments)
    - Transaction events (ATM withdrawals, transfers)
    - Account events (overdrafts, dormancy)
    - Loan events (disbursement, early repayment)
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "fee-consumer-group"
    ):
        # Subscribe to relevant topics
        topics = [
            "ultracore.loans.payments",  # Payment events
            "ultracore.accounts.transactions",  # Transaction events
            "ultracore.accounts.lifecycle",  # Account lifecycle
            "ultracore.loans.lifecycle",  # Loan lifecycle
            "ultracore.delinquency.buckets",  # Delinquency bucket changes
        ]
        
        super().__init__(
            topics=topics,
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )
        
        self.fee_service = FeeService()
        self.event_producer = FeeEventProducer(bootstrap_servers)
        
        # In-memory fee storage (in production, use database)
        self.fees: Dict[UUID, Fee] = {}
        
        logger.info("✓ Fee consumer initialized")
    
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
            if event_type == "PaymentMissed":
                await self._handle_payment_missed(event)
            elif event_type == "ATMWithdrawal":
                await self._handle_atm_withdrawal(event)
            elif event_type == "AccountOverdrawn":
                await self._handle_account_overdrawn(event)
            elif event_type == "LoanDisbursed":
                await self._handle_loan_disbursed(event)
            elif event_type == "DelinquencyBucketChanged":
                await self._handle_bucket_changed(event)
            else:
                logger.debug(f"Ignoring event type: {event_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}", exc_info=True)
            return False
    
    async def _handle_payment_missed(self, event: Dict[str, Any]):
        """Handle payment missed event - apply late fee"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        logger.info(f"Payment missed for loan {loan_id}")
        
        # Build context for fee evaluation
        context = {
            "loan_id": loan_id,
            "customer_id": event_data.get("customer_id"),
            "days_past_due": event_data.get("days_past_due", 1),
            "amount_due": event_data.get("amount_due"),
        }
        
        # Evaluate fees
        fees = self.fee_service.evaluate_fee_for_event(
            event_type="PaymentMissed",
            context=context,
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        # Apply fees
        for fee in fees:
            result = self.fee_service.apply_fee(fee)
            
            if result["success"]:
                # Store fee
                self.fees[fee.fee_id] = fee
                
                # Publish FeeApplied event
                await self._publish_fee_applied(fee, user_id, event["event_id"])
    
    async def _handle_atm_withdrawal(self, event: Dict[str, Any]):
        """Handle ATM withdrawal - apply withdrawal fee if applicable"""
        event_data = event.get("event_data", {})
        account_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        logger.info(f"ATM withdrawal for account {account_id}")
        
        # Build context
        context = {
            "account_id": account_id,
            "customer_id": event_data.get("customer_id"),
            "atm_network": event_data.get("atm_network", "own_bank"),
            "free_withdrawals_used": event_data.get("free_withdrawals_used", 0),
            "withdrawal_amount": event_data.get("amount"),
        }
        
        # Evaluate fees
        fees = self.fee_service.evaluate_fee_for_event(
            event_type="ATMWithdrawal",
            context=context,
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        # Apply fees
        for fee in fees:
            result = self.fee_service.apply_fee(fee)
            
            if result["success"]:
                self.fees[fee.fee_id] = fee
                await self._publish_fee_applied(fee, user_id, event["event_id"])
    
    async def _handle_account_overdrawn(self, event: Dict[str, Any]):
        """Handle account overdraft - apply overdraft fee"""
        event_data = event.get("event_data", {})
        account_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        logger.warning(f"Account overdrawn: {account_id}")
        
        # Build context
        context = {
            "account_id": account_id,
            "customer_id": event_data.get("customer_id"),
            "overdraft_amount": event_data.get("overdraft_amount"),
            "current_balance": event_data.get("current_balance"),
        }
        
        # Evaluate fees
        fees = self.fee_service.evaluate_fee_for_event(
            event_type="AccountOverdrawn",
            context=context,
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        # Apply fees
        for fee in fees:
            result = self.fee_service.apply_fee(fee)
            
            if result["success"]:
                self.fees[fee.fee_id] = fee
                await self._publish_fee_applied(fee, user_id, event["event_id"])
    
    async def _handle_loan_disbursed(self, event: Dict[str, Any]):
        """Handle loan disbursement - apply origination fee if applicable"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        tenant_id = UUID(event["tenant_id"])
        user_id = event["user_id"]
        
        logger.info(f"Loan disbursed: {loan_id}")
        
        # Build context
        context = {
            "loan_id": loan_id,
            "customer_id": event_data.get("customer_id"),
            "principal_amount": event_data.get("principal_amount"),
            "base_amount": event_data.get("principal_amount"),  # For percentage fees
        }
        
        # Evaluate fees
        fees = self.fee_service.evaluate_fee_for_event(
            event_type="LoanDisbursed",
            context=context,
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        # Apply fees
        for fee in fees:
            result = self.fee_service.apply_fee(fee)
            
            if result["success"]:
                self.fees[fee.fee_id] = fee
                await self._publish_fee_applied(fee, user_id, event["event_id"])
    
    async def _handle_bucket_changed(self, event: Dict[str, Any]):
        """Handle delinquency bucket change - may trigger additional fees"""
        event_data = event.get("event_data", {})
        loan_id = UUID(event["aggregate_id"])
        
        logger.info(f"Delinquency bucket changed for loan {loan_id}")
        
        # Note: Late fees are already handled by PaymentMissed event
        # This is for any additional bucket-specific fees
        # (e.g., collection fees for Bucket 3+)
    
    async def _publish_fee_applied(
        self,
        fee: Fee,
        user_id: str,
        causation_id: str
    ):
        """Publish FeeApplied event"""
        event = FeeAppliedEvent(
            fee_id=fee.fee_id,
            tenant_id=fee.tenant_id,
            account_id=fee.account_id,
            loan_id=fee.loan_id,
            customer_id=fee.customer_id,
            fee_type=fee.fee_type,
            fee_name=fee.fee_name,
            amount=fee.amount,
            currency=fee.currency,
            applied_date=fee.applied_date,
            charging_rule_id=fee.charging_rule_id,
        )
        
        await self.event_producer.publish_fee_applied(
            event=event,
            user_id=user_id,
            causation_id=causation_id,
        )
        
        logger.info(f"✓ Fee applied: {fee.fee_name} ${fee.amount}")
    
    def close(self):
        """Close consumer and producer"""
        super().close()
        self.event_producer.close()


# ============================================================================
# Convenience function to start consumer
# ============================================================================

def start_fee_consumer(bootstrap_servers: str = "localhost:9092"):
    """Start fee consumer"""
    consumer = FeeConsumer(bootstrap_servers=bootstrap_servers)
    consumer.start()
    return consumer

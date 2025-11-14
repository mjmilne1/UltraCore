"""
Savings Phase 2 Event Consumer
Processes recurring deposits, standing orders, and bucket allocations
"""

from typing import Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import logging

from ultracore.event_sourcing.consumers.base_consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class SavingsPhase2Consumer(BaseEventConsumer):
    """
    Savings Phase 2 Event Consumer
    
    Processes events for:
    - Recurring deposits (automated deposits)
    - Standing orders (automated transfers)
    - Savings buckets (auto-allocation)
    
    Enables real-time, automated savings features
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "savings-phase2-consumer-group"
    ):
        # Subscribe to Phase 2 topics
        topics = [
            "ultracore.savings.recurring_deposits",
            "ultracore.savings.standing_orders",
            "ultracore.savings.buckets",
            "ultracore.savings.scheduled_tasks",
            "ultracore.savings.transactions",  # Listen for deposits to trigger allocation
        ]
        
        super().__init__(
            topics=topics,
            group_id=group_id,
            bootstrap_servers=bootstrap_servers
        )
        
        # In-memory storage (in production, use database)
        self.recurring_deposits = {}
        self.standing_orders = {}
        self.savings_buckets = {}
        
        logger.info("✓ Savings Phase 2 consumer initialized")
    
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
            # Recurring Deposit Events
            if event_type == "RecurringDepositDue":
                await self._handle_recurring_deposit_due(event)
            elif event_type == "RecurringDepositMissed":
                await self._handle_recurring_deposit_missed(event)
            elif event_type == "RecurringDepositMatured":
                await self._handle_recurring_deposit_matured(event)
            
            # Standing Order Events
            elif event_type == "StandingOrderDue":
                await self._handle_standing_order_due(event)
            elif event_type == "StandingOrderFailed":
                await self._handle_standing_order_failed(event)
            
            # Savings Bucket Events
            elif event_type == "DepositReceived":
                await self._handle_deposit_received(event)
            elif event_type == "BucketMilestoneReached":
                await self._handle_bucket_milestone_reached(event)
            elif event_type == "BucketGoalAchieved":
                await self._handle_bucket_goal_achieved(event)
            
            else:
                logger.debug(f"Ignoring event type: {event_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}", exc_info=True)
            return False
    
    # ========================================================================
    # Recurring Deposit Handlers
    # ========================================================================
    
    async def _handle_recurring_deposit_due(self, event: Dict[str, Any]):
        """
        Handle recurring deposit due event
        
        Automatically execute the deposit
        """
        event_data = event.get("event_data", {})
        rd_id = UUID(event["aggregate_id"])
        account_id = UUID(event_data.get("account_id"))
        amount = Decimal(event_data.get("amount"))
        due_date = event_data.get("due_date")
        
        logger.info(f"Recurring deposit due: RD={rd_id}, Amount=${amount}")
        
        # Execute deposit
        result = await self._execute_recurring_deposit(
            rd_id=rd_id,
            account_id=account_id,
            amount=amount,
            due_date=due_date
        )
        
        if result["success"]:
            logger.info(f"✓ Recurring deposit executed: ${amount}")
            
            # Publish RecurringDepositExecuted event
            await self._publish_event(
                topic="ultracore.savings.recurring_deposits",
                event_type="RecurringDepositExecuted",
                aggregate_id=str(rd_id),
                event_data={
                    "account_id": str(account_id),
                    "amount": str(amount),
                    "executed_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            logger.warning(f"✗ Recurring deposit failed: {result['reason']}")
            
            # Publish RecurringDepositFailed event
            await self._publish_event(
                topic="ultracore.savings.recurring_deposits",
                event_type="RecurringDepositFailed",
                aggregate_id=str(rd_id),
                event_data={
                    "account_id": str(account_id),
                    "amount": str(amount),
                    "failure_reason": result["reason"],
                }
            )
    
    async def _execute_recurring_deposit(
        self,
        rd_id: UUID,
        account_id: UUID,
        amount: Decimal,
        due_date: str
    ) -> Dict[str, Any]:
        """Execute recurring deposit"""
        # In production, this would:
        # 1. Debit source account (or external payment method)
        # 2. Credit recurring deposit account
        # 3. Update recurring deposit record
        # 4. Calculate interest accrual
        
        # Simulated execution
        logger.info(f"Executing recurring deposit: ${amount} to account {account_id}")
        
        return {
            "success": True,
            "amount": amount,
            "transaction_id": UUID("00000000-0000-0000-0000-000000000000"),
        }
    
    async def _handle_recurring_deposit_missed(self, event: Dict[str, Any]):
        """Handle missed recurring deposit"""
        event_data = event.get("event_data", {})
        rd_id = UUID(event["aggregate_id"])
        
        logger.warning(f"Recurring deposit missed: RD={rd_id}")
        
        # Send notification to customer
        await self._send_notification(
            customer_id=event_data.get("customer_id"),
            notification_type="recurring_deposit_missed",
            message=f"Your recurring deposit of ${event_data.get('amount')} was missed. "
                   f"Please ensure sufficient funds are available."
        )
    
    async def _handle_recurring_deposit_matured(self, event: Dict[str, Any]):
        """Handle recurring deposit maturity"""
        event_data = event.get("event_data", {})
        rd_id = UUID(event["aggregate_id"])
        maturity_amount = Decimal(event_data.get("maturity_amount"))
        maturity_action = event_data.get("maturity_action")
        
        logger.info(f"Recurring deposit matured: RD={rd_id}, Amount=${maturity_amount}")
        
        # Execute maturity action
        if maturity_action == "auto_renew":
            await self._auto_renew_recurring_deposit(rd_id)
        elif maturity_action == "transfer_to_savings":
            await self._transfer_maturity_to_savings(rd_id, maturity_amount)
        elif maturity_action == "payout":
            await self._payout_maturity(rd_id, maturity_amount)
        
        # Send notification
        await self._send_notification(
            customer_id=event_data.get("customer_id"),
            notification_type="recurring_deposit_matured",
            message=f"Your recurring deposit has matured! "
                   f"Maturity amount: ${maturity_amount}"
        )
    
    # ========================================================================
    # Standing Order Handlers
    # ========================================================================
    
    async def _handle_standing_order_due(self, event: Dict[str, Any]):
        """
        Handle standing order due event
        
        Automatically execute the transfer
        """
        event_data = event.get("event_data", {})
        so_id = UUID(event["aggregate_id"])
        from_account_id = UUID(event_data.get("from_account_id"))
        to_account_id = event_data.get("to_account_id")
        amount = Decimal(event_data.get("amount"))
        transfer_type = event_data.get("transfer_type")
        
        logger.info(f"Standing order due: SO={so_id}, Amount=${amount}")
        
        # Check balance before execution
        balance = await self._get_account_balance(from_account_id)
        
        if balance < amount:
            logger.warning(f"Insufficient funds for standing order: Balance=${balance}, Required=${amount}")
            
            # Publish StandingOrderFailed event
            await self._publish_event(
                topic="ultracore.savings.standing_orders",
                event_type="StandingOrderFailed",
                aggregate_id=str(so_id),
                event_data={
                    "from_account_id": str(from_account_id),
                    "amount": str(amount),
                    "failure_reason": "insufficient_funds",
                }
            )
            return
        
        # Execute transfer
        result = await self._execute_standing_order(
            so_id=so_id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            transfer_type=transfer_type
        )
        
        if result["success"]:
            logger.info(f"✓ Standing order executed: ${amount}")
            
            # Publish StandingOrderExecuted event
            await self._publish_event(
                topic="ultracore.savings.standing_orders",
                event_type="StandingOrderExecuted",
                aggregate_id=str(so_id),
                event_data={
                    "from_account_id": str(from_account_id),
                    "to_account_id": to_account_id,
                    "amount": str(amount),
                    "executed_at": datetime.utcnow().isoformat(),
                    "transaction_id": str(result["transaction_id"]),
                }
            )
        else:
            logger.warning(f"✗ Standing order failed: {result['reason']}")
            
            # Publish StandingOrderFailed event
            await self._publish_event(
                topic="ultracore.savings.standing_orders",
                event_type="StandingOrderFailed",
                aggregate_id=str(so_id),
                event_data={
                    "from_account_id": str(from_account_id),
                    "amount": str(amount),
                    "failure_reason": result["reason"],
                }
            )
    
    async def _execute_standing_order(
        self,
        so_id: UUID,
        from_account_id: UUID,
        to_account_id: str,
        amount: Decimal,
        transfer_type: str
    ) -> Dict[str, Any]:
        """Execute standing order transfer"""
        # In production, this would:
        # 1. Debit from_account
        # 2. Credit to_account (or initiate external transfer)
        # 3. Update standing order record
        # 4. Generate transaction records
        
        # Simulated execution
        logger.info(f"Executing standing order: ${amount} from {from_account_id} to {to_account_id}")
        
        return {
            "success": True,
            "amount": amount,
            "transaction_id": UUID("00000000-0000-0000-0000-000000000001"),
        }
    
    async def _handle_standing_order_failed(self, event: Dict[str, Any]):
        """Handle failed standing order with retry logic"""
        event_data = event.get("event_data", {})
        so_id = UUID(event["aggregate_id"])
        failure_reason = event_data.get("failure_reason")
        
        logger.warning(f"Standing order failed: SO={so_id}, Reason={failure_reason}")
        
        # Check if should retry
        should_retry = event_data.get("should_retry", False)
        
        if should_retry:
            # Schedule retry
            await self._schedule_standing_order_retry(so_id)
        else:
            # Send failure notification
            await self._send_notification(
                customer_id=event_data.get("customer_id"),
                notification_type="standing_order_failed",
                message=f"Your standing order failed: {failure_reason}"
            )
    
    # ========================================================================
    # Savings Bucket Handlers
    # ========================================================================
    
    async def _handle_deposit_received(self, event: Dict[str, Any]):
        """
        Handle deposit received event
        
        Automatically allocate to savings buckets
        """
        event_data = event.get("event_data", {})
        account_id = UUID(event_data.get("account_id"))
        amount = Decimal(event_data.get("amount"))
        
        logger.info(f"Deposit received: Account={account_id}, Amount=${amount}")
        
        # Get active buckets for this account
        buckets = await self._get_active_buckets(account_id)
        
        if not buckets:
            logger.debug("No active buckets for auto-allocation")
            return
        
        # Calculate allocation
        allocations = await self._calculate_bucket_allocation(buckets, amount)
        
        # Execute allocations
        for bucket_id, allocation_amount in allocations.items():
            await self._allocate_to_bucket(bucket_id, allocation_amount)
            
            # Publish BucketAllocated event
            await self._publish_event(
                topic="ultracore.savings.buckets",
                event_type="BucketAllocated",
                aggregate_id=str(bucket_id),
                event_data={
                    "account_id": str(account_id),
                    "amount": str(allocation_amount),
                    "allocated_at": datetime.utcnow().isoformat(),
                }
            )
        
        logger.info(f"✓ Allocated ${sum(allocations.values())} across {len(allocations)} buckets")
    
    async def _handle_bucket_milestone_reached(self, event: Dict[str, Any]):
        """Handle bucket milestone reached"""
        event_data = event.get("event_data", {})
        bucket_id = UUID(event["aggregate_id"])
        milestone = Decimal(event_data.get("milestone"))
        
        logger.info(f"Bucket milestone reached: Bucket={bucket_id}, Milestone={milestone}%")
        
        # Send celebration notification
        await self._send_notification(
            customer_id=event_data.get("customer_id"),
            notification_type="bucket_milestone_reached",
            message=f"🎉 You've reached {milestone}% of your {event_data.get('goal_name')} goal!"
        )
    
    async def _handle_bucket_goal_achieved(self, event: Dict[str, Any]):
        """Handle bucket goal achieved"""
        event_data = event.get("event_data", {})
        bucket_id = UUID(event["aggregate_id"])
        goal_name = event_data.get("goal_name")
        final_amount = Decimal(event_data.get("final_amount"))
        
        logger.info(f"Bucket goal achieved: Bucket={bucket_id}, Goal={goal_name}, Amount=${final_amount}")
        
        # Apply bonus interest
        bonus_interest = final_amount * (Decimal(event_data.get("bonus_interest_rate", "0.5")) / 100)
        await self._apply_bonus_interest(bucket_id, bonus_interest)
        
        # Send achievement notification
        await self._send_notification(
            customer_id=event_data.get("customer_id"),
            notification_type="bucket_goal_achieved",
            message=f"🎊 Congratulations! You've achieved your {goal_name} goal of ${final_amount}! "
                   f"Bonus interest of ${bonus_interest} has been credited."
        )
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    async def _get_account_balance(self, account_id: UUID) -> Decimal:
        """Get account balance"""
        # In production, query from database
        return Decimal("1000.00")  # Simulated
    
    async def _get_active_buckets(self, account_id: UUID) -> list:
        """Get active buckets for account"""
        # In production, query from database
        return []  # Simulated
    
    async def _calculate_bucket_allocation(self, buckets: list, amount: Decimal) -> dict:
        """Calculate allocation across buckets"""
        # In production, use BucketAllocationStrategy
        return {}  # Simulated
    
    async def _allocate_to_bucket(self, bucket_id: UUID, amount: Decimal):
        """Allocate funds to bucket"""
        # In production, update bucket balance in database
        logger.info(f"Allocated ${amount} to bucket {bucket_id}")
    
    async def _apply_bonus_interest(self, bucket_id: UUID, amount: Decimal):
        """Apply bonus interest to bucket"""
        # In production, credit bonus interest to bucket
        logger.info(f"Applied bonus interest ${amount} to bucket {bucket_id}")
    
    async def _send_notification(self, customer_id: str, notification_type: str, message: str):
        """Send notification to customer"""
        # In production, integrate with notification service
        logger.info(f"Notification [{notification_type}]: {message}")
    
    async def _publish_event(self, topic: str, event_type: str, aggregate_id: str, event_data: dict):
        """Publish event to Kafka"""
        # In production, use event producer
        logger.info(f"Publishing event: {event_type} to {topic}")
    
    async def _auto_renew_recurring_deposit(self, rd_id: UUID):
        """Auto-renew recurring deposit"""
        logger.info(f"Auto-renewing recurring deposit: {rd_id}")
    
    async def _transfer_maturity_to_savings(self, rd_id: UUID, amount: Decimal):
        """Transfer maturity amount to savings account"""
        logger.info(f"Transferring ${amount} to savings account")
    
    async def _payout_maturity(self, rd_id: UUID, amount: Decimal):
        """Payout maturity amount"""
        logger.info(f"Paying out ${amount}")
    
    async def _schedule_standing_order_retry(self, so_id: UUID):
        """Schedule standing order retry"""
        logger.info(f"Scheduling retry for standing order: {so_id}")


# ============================================================================
# Convenience function to start consumer
# ============================================================================

def start_savings_phase2_consumer(bootstrap_servers: str = "localhost:9092"):
    """Start Savings Phase 2 consumer"""
    consumer = SavingsPhase2Consumer(bootstrap_servers=bootstrap_servers)
    consumer.start()
    return consumer

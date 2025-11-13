"""
Kafka Events for Additional Modules
Shares, COB, Configuration Management
"""

from typing import Any, Optional
from datetime import date, datetime
from decimal import Decimal


class AdditionalModulesKafkaProducer:
    """
    Kafka Producer for Additional Modules
    
    Publishes events for:
    - Share accounts and products
    - COB processing
    - Configuration management
    """
    
    def __init__(self, kafka_client=None):
        self.kafka_client = kafka_client
        
        # Topic names
        self.SHARE_PRODUCT_EVENTS = "share-product-events"
        self.SHARE_ACCOUNT_EVENTS = "share-account-events"
        self.SHARE_TRANSACTION_EVENTS = "share-transaction-events"
        self.DIVIDEND_EVENTS = "dividend-events"
        self.COB_EVENTS = "cob-events"
        self.COB_TASK_EVENTS = "cob-task-events"
        self.CONFIG_EVENTS = "config-events"
        self.FEATURE_FLAG_EVENTS = "feature-flag-events"
        
    # ========================================================================
    # SHARE PRODUCT EVENTS
    # ========================================================================
    
    def publish_share_product_created(
        self,
        product_id: str,
        product_code: str,
        product_name: str,
        product_type: str,
        nominal_price: Decimal
    ):
        """Publish share product created event"""
        event = {
            "event_type": "share_product_created",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "product_id": product_id,
            "product_code": product_code,
            "product_name": product_name,
            "product_type": product_type,
            "nominal_price": str(nominal_price)
        }
        self._publish(self.SHARE_PRODUCT_EVENTS, product_id, event)
        
    def publish_share_product_updated(
        self,
        product_id: str,
        product_code: str,
        updated_fields: dict
    ):
        """Publish share product updated event"""
        event = {
            "event_type": "share_product_updated",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "product_id": product_id,
            "product_code": product_code,
            "updated_fields": updated_fields
        }
        self._publish(self.SHARE_PRODUCT_EVENTS, product_id, event)
        
    # ========================================================================
    # SHARE ACCOUNT EVENTS
    # ========================================================================
    
    def publish_share_account_created(
        self,
        account_id: str,
        account_number: str,
        client_id: str,
        product_id: str,
        num_shares: int
    ):
        """Publish share account created event"""
        event = {
            "event_type": "share_account_created",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "account_number": account_number,
            "client_id": client_id,
            "product_id": product_id,
            "num_shares": num_shares
        }
        self._publish(self.SHARE_ACCOUNT_EVENTS, account_id, event)
        
    def publish_shares_purchased(
        self,
        account_id: str,
        num_shares: int,
        price_per_share: Decimal
    ):
        """Publish shares purchased event"""
        event = {
            "event_type": "shares_purchased",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "num_shares": num_shares,
            "price_per_share": str(price_per_share),
            "total_amount": str(num_shares * price_per_share)
        }
        self._publish(self.SHARE_TRANSACTION_EVENTS, account_id, event)
        
    def publish_shares_redeemed(
        self,
        account_id: str,
        num_shares: int,
        redemption_price: Decimal
    ):
        """Publish shares redeemed event"""
        event = {
            "event_type": "shares_redeemed",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "num_shares": num_shares,
            "redemption_price": str(redemption_price),
            "total_amount": str(num_shares * redemption_price)
        }
        self._publish(self.SHARE_TRANSACTION_EVENTS, account_id, event)
        
    def publish_shares_transferred(
        self,
        from_account_id: str,
        to_account_id: str,
        num_shares: int,
        transfer_price: Decimal
    ):
        """Publish shares transferred event"""
        event = {
            "event_type": "shares_transferred",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "num_shares": num_shares,
            "transfer_price": str(transfer_price)
        }
        self._publish(self.SHARE_TRANSACTION_EVENTS, from_account_id, event)
        
    # ========================================================================
    # DIVIDEND EVENTS
    # ========================================================================
    
    def publish_dividend_declared(
        self,
        dividend_id: str,
        product_id: str,
        amount_per_share: Decimal,
        total_amount: Decimal
    ):
        """Publish dividend declared event"""
        event = {
            "event_type": "dividend_declared",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "dividend_id": dividend_id,
            "product_id": product_id,
            "amount_per_share": str(amount_per_share),
            "total_amount": str(total_amount)
        }
        self._publish(self.DIVIDEND_EVENTS, dividend_id, event)
        
    def publish_dividends_paid(
        self,
        dividend_id: str,
        num_shareholders: int,
        total_paid: Decimal
    ):
        """Publish dividends paid event"""
        event = {
            "event_type": "dividends_paid",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "dividend_id": dividend_id,
            "num_shareholders": num_shareholders,
            "total_paid": str(total_paid)
        }
        self._publish(self.DIVIDEND_EVENTS, dividend_id, event)
        
    # ========================================================================
    # COB EVENTS
    # ========================================================================
    
    def publish_cob_started(
        self,
        run_id: str,
        business_date: date
    ):
        """Publish COB started event"""
        event = {
            "event_type": "cob_started",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "business_date": business_date.isoformat()
        }
        self._publish(self.COB_EVENTS, run_id, event)
        
    def publish_cob_completed(
        self,
        run_id: str,
        business_date: date,
        status: str,
        completed_tasks: int,
        failed_tasks: int
    ):
        """Publish COB completed event"""
        event = {
            "event_type": "cob_completed",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "business_date": business_date.isoformat(),
            "status": status,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks
        }
        self._publish(self.COB_EVENTS, run_id, event)
        
    def publish_cob_failed(
        self,
        run_id: str,
        business_date: date,
        error_message: str
    ):
        """Publish COB failed event"""
        event = {
            "event_type": "cob_failed",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "business_date": business_date.isoformat(),
            "error_message": error_message
        }
        self._publish(self.COB_EVENTS, run_id, event)
        
    def publish_cob_task_started(
        self,
        execution_id: str,
        run_id: str,
        task_id: str,
        task_type: str
    ):
        """Publish COB task started event"""
        event = {
            "event_type": "cob_task_started",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "run_id": run_id,
            "task_id": task_id,
            "task_type": task_type
        }
        self._publish(self.COB_TASK_EVENTS, execution_id, event)
        
    def publish_cob_task_completed(
        self,
        execution_id: str,
        run_id: str,
        task_id: str,
        records_processed: int,
        duration_seconds: float
    ):
        """Publish COB task completed event"""
        event = {
            "event_type": "cob_task_completed",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "run_id": run_id,
            "task_id": task_id,
            "records_processed": records_processed,
            "duration_seconds": duration_seconds
        }
        self._publish(self.COB_TASK_EVENTS, execution_id, event)
        
    # ========================================================================
    # CONFIGURATION EVENTS
    # ========================================================================
    
    def publish_config_created(
        self,
        config_id: str,
        config_key: str,
        config_value: Any,
        environment: str
    ):
        """Publish configuration created event"""
        event = {
            "event_type": "config_created",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "config_id": config_id,
            "config_key": config_key,
            "config_value": str(config_value),
            "environment": environment
        }
        self._publish(self.CONFIG_EVENTS, config_id, event)
        
    def publish_config_updated(
        self,
        config_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        environment: str
    ):
        """Publish configuration updated event"""
        event = {
            "event_type": "config_updated",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "config_id": config_id,
            "config_key": config_key,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "environment": environment
        }
        self._publish(self.CONFIG_EVENTS, config_id, event)
        
    def publish_config_audit(
        self,
        audit_id: str,
        config_key: str,
        action: str,
        changed_by: str
    ):
        """Publish configuration audit event"""
        event = {
            "event_type": "config_audit",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "audit_id": audit_id,
            "config_key": config_key,
            "action": action,
            "changed_by": changed_by
        }
        self._publish(self.CONFIG_EVENTS, audit_id, event)
        
    # ========================================================================
    # FEATURE FLAG EVENTS
    # ========================================================================
    
    def publish_feature_flag_created(
        self,
        flag_id: str,
        flag_key: str,
        is_enabled: bool,
        rollout_percentage: int
    ):
        """Publish feature flag created event"""
        event = {
            "event_type": "feature_flag_created",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "flag_id": flag_id,
            "flag_key": flag_key,
            "is_enabled": is_enabled,
            "rollout_percentage": rollout_percentage
        }
        self._publish(self.FEATURE_FLAG_EVENTS, flag_id, event)
        
    def publish_feature_flag_updated(
        self,
        flag_id: str,
        flag_key: str,
        is_enabled: bool,
        rollout_percentage: int
    ):
        """Publish feature flag updated event"""
        event = {
            "event_type": "feature_flag_updated",
            "event_id": self._generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "flag_id": flag_id,
            "flag_key": flag_key,
            "is_enabled": is_enabled,
            "rollout_percentage": rollout_percentage
        }
        self._publish(self.FEATURE_FLAG_EVENTS, flag_id, event)
        
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _publish(self, topic: str, key: str, event: dict):
        """Publish event to Kafka"""
        if self.kafka_client:
            self.kafka_client.produce(topic, key, event)
        else:
            # Log event (for testing without Kafka)
            print(f"[KAFKA] Topic: {topic}, Key: {key}, Event: {event['event_type']}")
            
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return f"EVT-{uuid.uuid4().hex[:16].upper()}"

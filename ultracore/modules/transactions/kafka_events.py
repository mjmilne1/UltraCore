"""
Transaction Kafka Events
Complete event streaming for order lifecycle
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TransactionEventType(str, Enum):
    # Order Events
    ORDER_CREATED = "order_created"
    ORDER_VALIDATED = "order_validated"
    ORDER_REJECTED = "order_rejected"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACKNOWLEDGED = "order_acknowledged"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_EXPIRED = "order_expired"
    
    # Trade Events
    TRADE_MATCHED = "trade_matched"
    TRADE_EXECUTED = "trade_executed"
    TRADE_CONFIRMED = "trade_confirmed"
    TRADE_FAILED = "trade_failed"
    
    # Settlement Events
    SETTLEMENT_PENDING = "settlement_pending"
    SETTLEMENT_IN_PROGRESS = "settlement_in_progress"
    SETTLEMENT_COMPLETED = "settlement_completed"
    SETTLEMENT_FAILED = "settlement_failed"
    
    # Cash Events
    CASH_RESERVED = "cash_reserved"
    CASH_RELEASED = "cash_released"
    CASH_DEBITED = "cash_debited"
    CASH_CREDITED = "cash_credited"
    
    # Risk Events
    RISK_CHECK_PASSED = "risk_check_passed"
    RISK_CHECK_FAILED = "risk_check_failed"
    FRAUD_DETECTED = "fraud_detected"
    
    # Compliance Events
    COMPLIANCE_CHECK_PASSED = "compliance_check_passed"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"

class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class TimeInForce(str, Enum):
    DAY = "day"              # Good for day
    GTC = "gtc"              # Good till cancelled
    IOC = "ioc"              # Immediate or cancel
    FOK = "fok"              # Fill or kill

class TransactionKafkaProducer:
    """
    Extended Kafka producer for transaction events
    Integrates with main Kafka system
    """
    
    def __init__(self):
        from ultracore.streaming.kafka_events import kafka_producer
        self.kafka = kafka_producer
        
        # Transaction-specific topics
        self.topics = {
            "transactions.orders": "Order lifecycle events",
            "transactions.trades": "Trade execution events",
            "transactions.settlement": "Settlement events",
            "transactions.cash": "Cash movement events",
            "transactions.risk": "Risk check events",
            "transactions.compliance": "Compliance events"
        }
    
    async def produce_order_event(
        self,
        event_type: TransactionEventType,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Produce order event"""
        
        event = await self.kafka.produce(
            topic="transactions.orders",
            event_type=event_type,
            data=order_data,
            key=order_data.get("order_id")
        )
        
        return event
    
    async def produce_trade_event(
        self,
        event_type: TransactionEventType,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Produce trade event"""
        
        event = await self.kafka.produce(
            topic="transactions.trades",
            event_type=event_type,
            data=trade_data,
            key=trade_data.get("trade_id")
        )
        
        return event
    
    async def produce_settlement_event(
        self,
        event_type: TransactionEventType,
        settlement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Produce settlement event"""
        
        event = await self.kafka.produce(
            topic="transactions.settlement",
            event_type=event_type,
            data=settlement_data,
            key=settlement_data.get("settlement_id")
        )
        
        return event
    
    async def produce_cash_event(
        self,
        event_type: TransactionEventType,
        cash_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Produce cash event"""
        
        event = await self.kafka.produce(
            topic="transactions.cash",
            event_type=event_type,
            data=cash_data,
            key=cash_data.get("client_id")
        )
        
        return event
    
    async def produce_risk_event(
        self,
        event_type: TransactionEventType,
        risk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Produce risk event"""
        
        event = await self.kafka.produce(
            topic="transactions.risk",
            event_type=event_type,
            data=risk_data,
            key=risk_data.get("order_id")
        )
        
        return event
    
    def subscribe_to_orders(self, callback):
        """Subscribe to order events"""
        self.kafka.subscribe("transactions.orders", callback)
    
    def subscribe_to_trades(self, callback):
        """Subscribe to trade events"""
        self.kafka.subscribe("transactions.trades", callback)
    
    def subscribe_to_settlement(self, callback):
        """Subscribe to settlement events"""
        self.kafka.subscribe("transactions.settlement", callback)

# Global instance
transaction_kafka = TransactionKafkaProducer()

"""
Cash Management Kafka Events
Event streaming for cash transactions
"""

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum
import json

class CashEventType(str, Enum):
    """Cash event types"""
    ACCOUNT_CREATED = "cash.account.created"
    DEPOSIT_INITIATED = "cash.deposit.initiated"
    DEPOSIT_COMPLETED = "cash.deposit.completed"
    DEPOSIT_FAILED = "cash.deposit.failed"
    WITHDRAWAL_INITIATED = "cash.withdrawal.initiated"
    WITHDRAWAL_COMPLETED = "cash.withdrawal.completed"
    WITHDRAWAL_FAILED = "cash.withdrawal.failed"
    BALANCE_RESERVED = "cash.balance.reserved"
    BALANCE_RELEASED = "cash.balance.released"
    INTEREST_CREDITED = "cash.interest.credited"
    FEE_DEBITED = "cash.fee.debited"
    TRANSFER_INITIATED = "cash.transfer.initiated"
    TRANSFER_COMPLETED = "cash.transfer.completed"
    RECONCILIATION_STARTED = "cash.reconciliation.started"
    RECONCILIATION_COMPLETED = "cash.reconciliation.completed"
    FRAUD_DETECTED = "cash.fraud.detected"
    LIMIT_EXCEEDED = "cash.limit.exceeded"

class CashKafkaProducer:
    """
    Kafka producer for cash events
    
    Publishes all cash events to Kafka topics for:
    - Event sourcing
    - Real-time processing
    - Analytics
    - Compliance monitoring
    - Fraud detection
    """
    
    def __init__(self):
        self.events_published = []
        
    def publish_account_created(
        self,
        account_id: str,
        client_id: str,
        account_type: str,
        currency: str
    ):
        """Publish account created event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.ACCOUNT_CREATED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "client_id": client_id,
            "account_type": account_type,
            "currency": currency,
            "metadata": {
                "source": "cash_account_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-accounts", event)
        
    def publish_deposit_initiated(
        self,
        account_id: str,
        transaction_id: str,
        amount: float,
        payment_method: str,
        reference: str
    ):
        """Publish deposit initiated event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.DEPOSIT_INITIATED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "payment_method": payment_method,
            "reference": reference,
            "status": "pending",
            "metadata": {
                "source": "cash_transaction_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-transactions", event)
        
    def publish_deposit_completed(
        self,
        account_id: str,
        transaction_id: str,
        amount: float,
        final_balance: float
    ):
        """Publish deposit completed event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.DEPOSIT_COMPLETED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "final_balance": final_balance,
            "status": "completed",
            "metadata": {
                "source": "cash_transaction_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-transactions", event)
        
    def publish_withdrawal_initiated(
        self,
        account_id: str,
        transaction_id: str,
        amount: float,
        payment_method: str,
        destination: str
    ):
        """Publish withdrawal initiated event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.WITHDRAWAL_INITIATED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "payment_method": payment_method,
            "destination": destination,
            "status": "pending",
            "metadata": {
                "source": "cash_transaction_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-transactions", event)
        
    def publish_withdrawal_completed(
        self,
        account_id: str,
        transaction_id: str,
        amount: float,
        final_balance: float
    ):
        """Publish withdrawal completed event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.WITHDRAWAL_COMPLETED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "final_balance": final_balance,
            "status": "completed",
            "metadata": {
                "source": "cash_transaction_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-transactions", event)
        
    def publish_balance_reserved(
        self,
        account_id: str,
        reservation_id: str,
        amount: float,
        reason: str
    ):
        """Publish balance reserved event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.BALANCE_RESERVED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "reservation_id": reservation_id,
            "amount": amount,
            "reason": reason,
            "metadata": {
                "source": "cash_account_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-balances", event)
        
    def publish_balance_released(
        self,
        account_id: str,
        reservation_id: str,
        amount: float
    ):
        """Publish balance released event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.BALANCE_RELEASED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "reservation_id": reservation_id,
            "amount": amount,
            "metadata": {
                "source": "cash_account_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-balances", event)
        
    def publish_interest_credited(
        self,
        account_id: str,
        amount: float,
        interest_rate: float,
        period_start: str,
        period_end: str
    ):
        """Publish interest credited event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.INTEREST_CREDITED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "amount": amount,
            "interest_rate": interest_rate,
            "period_start": period_start,
            "period_end": period_end,
            "metadata": {
                "source": "cash_interest_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-interest", event)
        
    def publish_fee_debited(
        self,
        account_id: str,
        fee_id: str,
        amount: float,
        fee_type: str,
        description: str
    ):
        """Publish fee debited event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.FEE_DEBITED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "fee_id": fee_id,
            "amount": amount,
            "fee_type": fee_type,
            "description": description,
            "metadata": {
                "source": "cash_fee_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-fees", event)
        
    def publish_fraud_detected(
        self,
        account_id: str,
        transaction_id: str,
        fraud_score: float,
        reasons: List[str]
    ):
        """Publish fraud detected event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.FRAUD_DETECTED,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "transaction_id": transaction_id,
            "fraud_score": fraud_score,
            "reasons": reasons,
            "severity": "high" if fraud_score > 0.8 else "medium",
            "metadata": {
                "source": "cash_fraud_detector",
                "version": "1.0"
            }
        }
        
        self._publish("cash-fraud", event)
        
    def publish_reconciliation_completed(
        self,
        reconciliation_id: str,
        accounts_reconciled: int,
        discrepancies_found: int,
        total_amount: float
    ):
        """Publish reconciliation completed event"""
        
        event = {
            "event_id": f"evt_{datetime.utcnow().timestamp()}",
            "event_type": CashEventType.RECONCILIATION_COMPLETED,
            "timestamp": datetime.utcnow().isoformat(),
            "reconciliation_id": reconciliation_id,
            "accounts_reconciled": accounts_reconciled,
            "discrepancies_found": discrepancies_found,
            "total_amount": total_amount,
            "metadata": {
                "source": "cash_reconciliation_service",
                "version": "1.0"
            }
        }
        
        self._publish("cash-reconciliation", event)
        
    def _publish(self, topic: str, event: Dict[str, Any]):
        """Publish event to Kafka topic"""
        
        # In production, this would publish to actual Kafka
        # For now, store in memory
        self.events_published.append({
            "topic": topic,
            "event": event
        })
        
        print(f"📤 Published to {topic}: {event['event_type']}")

# Global Kafka producer
cash_kafka_producer = CashKafkaProducer()

"""
Investor Management Kafka Events
Event sourcing for loan transfers and investor operations
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json


class InvestorEventType(str, Enum):
    """Investor management event types"""
    
    # Investor events
    INVESTOR_CREATED = "investor.created"
    INVESTOR_UPDATED = "investor.updated"
    INVESTOR_KYC_VERIFIED = "investor.kyc.verified"
    INVESTOR_AML_VERIFIED = "investor.aml.verified"
    INVESTOR_SUSPENDED = "investor.suspended"
    INVESTOR_ACTIVATED = "investor.activated"
    
    # Transfer events
    TRANSFER_INITIATED = "transfer.initiated"
    TRANSFER_APPROVED = "transfer.approved"
    TRANSFER_REJECTED = "transfer.rejected"
    TRANSFER_SETTLEMENT_STARTED = "transfer.settlement.started"
    TRANSFER_SETTLEMENT_COMPLETED = "transfer.settlement.completed"
    TRANSFER_ACTIVATED = "transfer.activated"
    TRANSFER_COMPLETED = "transfer.completed"
    TRANSFER_CANCELLED = "transfer.cancelled"
    TRANSFER_FAILED = "transfer.failed"
    
    # Ownership events
    LOAN_OWNERSHIP_TRANSFERRED = "loan.ownership.transferred"
    LOAN_OWNERSHIP_PARTIAL_TRANSFERRED = "loan.ownership.partial_transferred"
    LOAN_BOUGHT_BACK = "loan.bought_back"
    
    # Payment routing events
    PAYMENT_ROUTING_ACTIVATED = "payment.routing.activated"
    PAYMENT_ROUTING_UPDATED = "payment.routing.updated"
    PAYMENT_ROUTING_TERMINATED = "payment.routing.terminated"
    PAYMENT_ROUTED_TO_INVESTOR = "payment.routed.to_investor"
    
    # Portfolio events
    PORTFOLIO_UPDATED = "portfolio.updated"
    PORTFOLIO_REBALANCED = "portfolio.rebalanced"
    
    # Securitization events
    SECURITIZATION_POOL_CREATED = "securitization.pool.created"
    LOAN_ADDED_TO_POOL = "loan.added.to_pool"
    SECURITIZATION_POOL_CLOSED = "securitization.pool.closed"
    
    # AI/ML events
    INVESTOR_MATCHED = "investor.matched"
    PRICING_RECOMMENDED = "pricing.recommended"
    RISK_ASSESSED = "risk.assessed"
    FRAUD_DETECTED = "fraud.detected"


class InvestorKafkaProducer:
    """
    Kafka producer for investor management events
    
    Publishes all investor and transfer events to Kafka topics for:
    - Event sourcing (complete audit trail)
    - Real-time processing
    - Analytics and reporting
    - Compliance monitoring
    - AI/ML model training
    """
    
    def __init__(self):
        self.events_published = []
        self.kafka_bootstrap_servers = "localhost:9092"
        
    def _publish(self, topic: str, event: Dict[str, Any]):
        """
        Publish event to Kafka topic
        
        In production, this would use kafka-python or confluent-kafka
        For now, we simulate by storing events
        """
        event_record = {
            "topic": topic,
            "event": event,
            "published_at": datetime.now(timezone.utc).isoformat()
        }
        self.events_published.append(event_record)
        
        # In production:
        # from kafka import KafkaProducer
        # producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        # producer.send(topic, json.dumps(event).encode('utf-8'))
        
    def publish_investor_created(
        self,
        investor_id: str,
        external_id: str,
        investor_name: str,
        investor_type: str,
        created_by: str
    ):
        """Publish investor created event"""
        
        event = {
            "event_id": f"evt_inv_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.INVESTOR_CREATED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "investor_id": investor_id,
            "external_id": external_id,
            "investor_name": investor_name,
            "investor_type": investor_type,
            "created_by": created_by,
            "metadata": {
                "source": "investor_management_service",
                "version": "1.0",
                "correlation_id": f"corr_{datetime.now(timezone.utc).timestamp()}"
            }
        }
        
        self._publish("investor-events", event)
        
    def publish_transfer_initiated(
        self,
        transfer_id: str,
        loan_id: str,
        from_investor_id: Optional[str],
        to_investor_id: str,
        transfer_type: str,
        outstanding_principal: Decimal,
        purchase_price: Decimal,
        purchase_price_ratio: Decimal,
        settlement_date: date,
        created_by: str
    ):
        """Publish transfer initiated event"""
        
        event = {
            "event_id": f"evt_trf_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.TRANSFER_INITIATED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transfer_id": transfer_id,
            "loan_id": loan_id,
            "from_investor_id": from_investor_id,
            "to_investor_id": to_investor_id,
            "transfer_type": transfer_type,
            "outstanding_principal": str(outstanding_principal),
            "purchase_price": str(purchase_price),
            "purchase_price_ratio": str(purchase_price_ratio),
            "settlement_date": settlement_date.isoformat(),
            "created_by": created_by,
            "metadata": {
                "source": "investor_management_service",
                "version": "1.0",
                "correlation_id": f"corr_{datetime.now(timezone.utc).timestamp()}"
            }
        }
        
        self._publish("transfer-events", event)
        
    def publish_transfer_approved(
        self,
        transfer_id: str,
        loan_id: str,
        to_investor_id: str,
        approved_by: str
    ):
        """Publish transfer approved event"""
        
        event = {
            "event_id": f"evt_trf_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.TRANSFER_APPROVED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transfer_id": transfer_id,
            "loan_id": loan_id,
            "to_investor_id": to_investor_id,
            "approved_by": approved_by,
            "metadata": {
                "source": "investor_management_service",
                "version": "1.0"
            }
        }
        
        self._publish("transfer-events", event)
        
    def publish_loan_ownership_transferred(
        self,
        loan_id: str,
        transfer_id: str,
        from_owner: Optional[str],
        to_owner: str,
        transfer_percentage: Decimal,
        effective_date: date
    ):
        """Publish loan ownership transferred event"""
        
        event = {
            "event_id": f"evt_own_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.LOAN_OWNERSHIP_TRANSFERRED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loan_id": loan_id,
            "transfer_id": transfer_id,
            "from_owner": from_owner or "ORIGINATOR",
            "to_owner": to_owner,
            "transfer_percentage": str(transfer_percentage),
            "effective_date": effective_date.isoformat(),
            "metadata": {
                "source": "investor_management_service",
                "version": "1.0"
            }
        }
        
        self._publish("ownership-events", event)
        
    def publish_payment_routing_activated(
        self,
        routing_id: str,
        loan_id: str,
        investor_id: str,
        transfer_id: str,
        routing_percentage: Decimal,
        effective_from: date
    ):
        """Publish payment routing activated event"""
        
        event = {
            "event_id": f"evt_rte_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.PAYMENT_ROUTING_ACTIVATED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "routing_id": routing_id,
            "loan_id": loan_id,
            "investor_id": investor_id,
            "transfer_id": transfer_id,
            "routing_percentage": str(routing_percentage),
            "effective_from": effective_from.isoformat(),
            "metadata": {
                "source": "investor_management_service",
                "version": "1.0"
            }
        }
        
        self._publish("payment-routing-events", event)
        
    def publish_payment_routed_to_investor(
        self,
        payment_id: str,
        loan_id: str,
        investor_id: str,
        amount: Decimal,
        payment_type: str,
        routing_percentage: Decimal
    ):
        """Publish payment routed to investor event"""
        
        event = {
            "event_id": f"evt_pay_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.PAYMENT_ROUTED_TO_INVESTOR,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payment_id": payment_id,
            "loan_id": loan_id,
            "investor_id": investor_id,
            "amount": str(amount),
            "payment_type": payment_type,
            "routing_percentage": str(routing_percentage),
            "metadata": {
                "source": "payment_routing_service",
                "version": "1.0"
            }
        }
        
        self._publish("payment-routing-events", event)
        
    def publish_investor_matched(
        self,
        loan_id: str,
        matched_investors: list,
        match_score: float,
        algorithm: str
    ):
        """Publish AI investor matching event"""
        
        event = {
            "event_id": f"evt_ai_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.INVESTOR_MATCHED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loan_id": loan_id,
            "matched_investors": matched_investors,
            "match_score": match_score,
            "algorithm": algorithm,
            "metadata": {
                "source": "ai_matching_service",
                "version": "1.0"
            }
        }
        
        self._publish("ai-events", event)
        
    def publish_pricing_recommended(
        self,
        loan_id: str,
        recommended_price_ratio: Decimal,
        confidence_score: float,
        model_version: str
    ):
        """Publish AI pricing recommendation event"""
        
        event = {
            "event_id": f"evt_ai_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.PRICING_RECOMMENDED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loan_id": loan_id,
            "recommended_price_ratio": str(recommended_price_ratio),
            "confidence_score": confidence_score,
            "model_version": model_version,
            "metadata": {
                "source": "ai_pricing_service",
                "version": "1.0"
            }
        }
        
        self._publish("ai-events", event)
        
    def publish_securitization_pool_created(
        self,
        pool_id: str,
        pool_name: str,
        spv_investor_id: str,
        created_by: str
    ):
        """Publish securitization pool created event"""
        
        event = {
            "event_id": f"evt_sec_{datetime.now(timezone.utc).timestamp()}",
            "event_type": InvestorEventType.SECURITIZATION_POOL_CREATED,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pool_id": pool_id,
            "pool_name": pool_name,
            "spv_investor_id": spv_investor_id,
            "created_by": created_by,
            "metadata": {
                "source": "securitization_service",
                "version": "1.0"
            }
        }
        
        self._publish("securitization-events", event)
        
    def get_event_stream(self, topic: Optional[str] = None) -> list:
        """Get published events for testing/debugging"""
        if topic:
            return [e for e in self.events_published if e["topic"] == topic]
        return self.events_published


# Kafka Topics Configuration
KAFKA_TOPICS = {
    "investor-events": {
        "partitions": 3,
        "replication_factor": 3,
        "retention_ms": 31536000000,  # 1 year
        "description": "Investor lifecycle events"
    },
    "transfer-events": {
        "partitions": 6,
        "replication_factor": 3,
        "retention_ms": 31536000000,  # 1 year
        "description": "Loan transfer events"
    },
    "ownership-events": {
        "partitions": 6,
        "replication_factor": 3,
        "retention_ms": -1,  # Infinite retention (event sourcing)
        "description": "Loan ownership changes"
    },
    "payment-routing-events": {
        "partitions": 12,
        "replication_factor": 3,
        "retention_ms": 7776000000,  # 90 days
        "description": "Payment routing events"
    },
    "ai-events": {
        "partitions": 3,
        "replication_factor": 2,
        "retention_ms": 2592000000,  # 30 days
        "description": "AI/ML events (matching, pricing, risk)"
    },
    "securitization-events": {
        "partitions": 2,
        "replication_factor": 3,
        "retention_ms": 31536000000,  # 1 year
        "description": "Securitization pool events"
    }
}

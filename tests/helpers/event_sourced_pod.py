"""
Event-Sourced Investment Pod for E2E Testing.

Wraps the Investment Pod aggregate with event publishing capabilities.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import uuid4


class EventSourcedPod:
    """
    Investment Pod with event sourcing.
    
    Publishes events to Kafka for all state changes.
    """
    
    def __init__(self, kafka_producer, tenant_id: str = "ultrawealth", user_id: str = None):
        self.kafka_producer = kafka_producer
        self.tenant_id = tenant_id
        self.user_id = user_id or f"user_{uuid4().hex[:8]}"
        self.pod_id = None
        self.status = None
        self.correlation_id = str(uuid4())
    
    async def create_pod(
        self,
        goal_type: str,
        target_amount: str,
        target_date: str,
        initial_deposit: str,
        monthly_contribution: str,
        risk_tolerance: str
    ) -> str:
        """
        Create Investment Pod and publish PodCreated event.
        
        Returns:
            pod_id
        """
        self.pod_id = f"pod_{uuid4().hex[:12]}"
        self.status = "created"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodCreated",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "goal_type": goal_type,
                "target_amount": target_amount,
                "target_date": target_date,
                "initial_deposit": initial_deposit,
                "monthly_contribution": monthly_contribution,
                "risk_tolerance": risk_tolerance
            },
            correlation_id=self.correlation_id,
            causation_id=None
        )
        
        return self.pod_id
    
    async def optimize_pod(
        self,
        allocation: Dict[str, float],
        expected_return: float,
        sharpe_ratio: float
    ):
        """Optimize Pod and publish PodOptimized event."""
        self.status = "optimized"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodOptimized",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "allocation": allocation,
                "expected_return": expected_return,
                "sharpe_ratio": sharpe_ratio
            },
            correlation_id=self.correlation_id
        )
    
    async def fund_pod(self, funded_amount: str):
        """Fund Pod and publish PodFunded event."""
        self.status = "funded"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodFunded",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "funded_amount": funded_amount
            },
            correlation_id=self.correlation_id
        )
    
    async def activate_pod(self):
        """Activate Pod and publish PodActivated event."""
        self.status = "active"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodActivated",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={},
            correlation_id=self.correlation_id
        )
    
    async def make_contribution(self, amount: str):
        """Make contribution and publish ContributionMade event."""
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="ContributionMade",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "amount": amount,
                "contribution_date": datetime.utcnow().isoformat()
            },
            correlation_id=self.correlation_id
        )
    
    async def rebalance_pod(self, new_allocation: Dict[str, float]):
        """Rebalance Pod and publish PodRebalanced event."""
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodRebalanced",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "new_allocation": new_allocation,
                "rebalance_date": datetime.utcnow().isoformat()
            },
            correlation_id=self.correlation_id
        )
    
    async def trigger_circuit_breaker(self, drawdown_pct: float):
        """Trigger circuit breaker and publish CircuitBreakerTriggered event."""
        self.status = "defensive"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="CircuitBreakerTriggered",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "drawdown_pct": drawdown_pct,
                "trigger_date": datetime.utcnow().isoformat()
            },
            correlation_id=self.correlation_id
        )
    
    async def achieve_goal(self, final_value: str):
        """Mark goal as achieved and publish GoalAchieved event."""
        self.status = "achieved"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="GoalAchieved",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "final_value": final_value,
                "achievement_date": datetime.utcnow().isoformat()
            },
            correlation_id=self.correlation_id
        )
    
    async def close_pod(self):
        """Close Pod and publish PodClosed event."""
        self.status = "closed"
        
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodClosed",
            aggregate_type="InvestmentPod",
            aggregate_id=self.pod_id,
            event_data={
                "close_date": datetime.utcnow().isoformat()
            },
            correlation_id=self.correlation_id
        )

"""
Event-Driven UltraOptimiser Integration.

Listens to Pod events and triggers optimization automatically.
"""

from typing import Dict, Any, Optional
import asyncio


class EventDrivenOptimiser:
    """
    Event-driven UltraOptimiser that responds to Pod events.
    
    Listens for PodCreated and PodRebalanced events and triggers optimization.
    """
    
    def __init__(self, kafka_producer, ultraoptimiser_adapter):
        self.kafka_producer = kafka_producer
        self.ultraoptimiser_adapter = ultraoptimiser_adapter
        self.optimizations_triggered = []
    
    async def handle_pod_created(self, event: Dict[str, Any]):
        """
        Handle PodCreated event by triggering optimization.
        
        Args:
            event: PodCreated event
        """
        pod_id = event.get("aggregate_id")
        event_data = event.get("event_data", {})
        
        # Extract Pod parameters
        goal_type = event_data.get("goal_type")
        target_amount = float(event_data.get("target_amount", "0"))
        risk_tolerance = event_data.get("risk_tolerance", "moderate")
        
        # Map risk tolerance to risk budget (0-1)
        risk_budget_map = {
            "conservative": 0.3,
            "moderate": 0.5,
            "aggressive": 0.8
        }
        risk_budget = risk_budget_map.get(risk_tolerance, 0.5)
        
        # Trigger optimization with correct parameters
        result = await self.ultraoptimiser_adapter.optimize(
            universe=["VAS", "VGS", "VAF", "VGE", "VGAD", "VAP"],
            risk_budget=risk_budget,
            current_holdings={},
            available_cash=target_amount,
            constraints={
                "max_etfs": 6,
                "min_weight": 0.05,
                "max_weight": 0.40
            }
        )
        
        # Record optimization
        self.optimizations_triggered.append({
            "pod_id": pod_id,
            "event_type": "PodCreated",
            "result": result
        })
        
        # Publish PodOptimized event
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodOptimized",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "allocation": result.get("optimal_weights", {}),
                "expected_return": result.get("expected_return", 0.0),
                "sharpe_ratio": result.get("sharpe_ratio", 0.0)
            },
            correlation_id=event.get("correlation_id")
        )
    
    async def handle_glide_path_adjustment(self, event: Dict[str, Any]):
        """
        Handle glide path adjustment by triggering optimization with new risk level.
        
        Args:
            event: GlidePathAdjusted event
        """
        pod_id = event.get("aggregate_id")
        event_data = event.get("event_data", {})
        
        # Extract new risk parameters
        new_risk_tolerance = event_data.get("new_risk_tolerance", "moderate")
        new_equity_allocation = event_data.get("new_equity_allocation", 0.6)
        
        # Map risk tolerance to risk budget
        risk_budget_map = {
            "conservative": 0.3,
            "moderate": 0.5,
            "aggressive": 0.8
        }
        risk_budget = risk_budget_map.get(new_risk_tolerance, 0.5)
        
        # Trigger optimization with adjusted risk
        result = await self.ultraoptimiser_adapter.optimize(
            universe=["VAS", "VGS", "VAF", "VGE", "VGAD", "VAP"],
            risk_budget=risk_budget,
            current_holdings={},
            available_cash=100000.0,
            constraints={
                "max_etfs": 6,
                "min_weight": 0.05,
                "max_weight": 0.40
            }
        )
        
        # Record optimization
        self.optimizations_triggered.append({
            "pod_id": pod_id,
            "event_type": "GlidePathAdjusted",
            "result": result
        })
        
        # Publish PodRebalanced event
        await self.kafka_producer.publish_event(
            topic="ultracore.investment_pods.events",
            event_type="PodRebalanced",
            aggregate_type="InvestmentPod",
            aggregate_id=pod_id,
            event_data={
                "new_allocation": result.get("optimal_weights", {}),
                "reason": "glide_path_adjustment"
            },
            correlation_id=event.get("correlation_id")
        )
    
    async def process_events(self, events: list):
        """
        Process a list of events and trigger optimizations.
        
        Args:
            events: List of events to process
        """
        for event in events:
            event_type = event.get("event_type")
            
            if event_type == "PodCreated":
                await self.handle_pod_created(event)
            elif event_type == "GlidePathAdjusted":
                await self.handle_glide_path_adjustment(event)
    
    def get_optimizations_for_pod(self, pod_id: str) -> list:
        """
        Get all optimizations triggered for a specific Pod.
        
        Args:
            pod_id: Pod ID
        
        Returns:
            List of optimization records
        """
        return [
            opt for opt in self.optimizations_triggered
            if opt["pod_id"] == pod_id
        ]

"""
Aggregate Reconstruction from Event Streams.

Provides utilities to rebuild aggregate state from event streams for testing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal


class AggregateReconstructor:
    """
    Reconstruct aggregate state from event streams.
    
    Used in E2E tests to verify event sourcing correctness.
    """
    
    @staticmethod
    def reconstruct_investment_pod(events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Reconstruct Investment Pod state from events.
        
        Args:
            events: List of events in chronological order
        
        Returns:
            Pod state dictionary or None if no events
        """
        if not events:
            return None
        
        # Initialize empty state
        pod_state = {
            "pod_id": None,
            "status": None,
            "goal_type": None,
            "target_amount": None,
            "target_date": None,
            "current_value": Decimal("0"),
            "initial_deposit": None,
            "monthly_contribution": None,
            "risk_tolerance": None,
            "allocation": {},
            "expected_return": None,
            "sharpe_ratio": None,
            "circuit_breaker_triggered": False,
            "goal_achieved": False,
            "created_at": None,
            "updated_at": None
        }
        
        # Apply events in order
        for event in events:
            event_type = event.get("event_type")
            event_data = event.get("event_data", {})
            
            if event_type == "PodCreated":
                pod_state["pod_id"] = event.get("aggregate_id")
                pod_state["status"] = "created"
                pod_state["goal_type"] = event_data.get("goal_type")
                pod_state["target_amount"] = Decimal(str(event_data.get("target_amount", "0")))
                pod_state["target_date"] = event_data.get("target_date")
                pod_state["initial_deposit"] = Decimal(str(event_data.get("initial_deposit", "0")))
                pod_state["monthly_contribution"] = Decimal(str(event_data.get("monthly_contribution", "0")))
                pod_state["risk_tolerance"] = event_data.get("risk_tolerance")
                pod_state["current_value"] = pod_state["initial_deposit"]
                pod_state["created_at"] = event.get("timestamp")
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "PodOptimized":
                pod_state["status"] = "optimized"
                pod_state["allocation"] = event_data.get("allocation", {})
                pod_state["expected_return"] = Decimal(str(event_data.get("expected_return", "0")))
                pod_state["sharpe_ratio"] = Decimal(str(event_data.get("sharpe_ratio", "0")))
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "PodFunded":
                pod_state["status"] = "funded"
                pod_state["current_value"] = Decimal(str(event_data.get("funded_amount", "0")))
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "PodActivated":
                pod_state["status"] = "active"
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "ContributionMade":
                contribution = Decimal(str(event_data.get("amount", "0")))
                pod_state["current_value"] += contribution
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "PodRebalanced":
                pod_state["allocation"] = event_data.get("new_allocation", {})
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "CircuitBreakerTriggered":
                pod_state["circuit_breaker_triggered"] = True
                pod_state["status"] = "defensive"
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "GoalAchieved":
                pod_state["goal_achieved"] = True
                pod_state["status"] = "achieved"
                pod_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "PodClosed":
                pod_state["status"] = "closed"
                pod_state["updated_at"] = event.get("timestamp")
        
        return pod_state
    
    @staticmethod
    def reconstruct_account(events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Reconstruct Account state from events.
        
        Args:
            events: List of events in chronological order
        
        Returns:
            Account state dictionary or None if no events
        """
        if not events:
            return None
        
        account_state = {
            "account_id": None,
            "user_id": None,
            "tenant_id": None,
            "balance": Decimal("0"),
            "status": None,
            "created_at": None,
            "updated_at": None
        }
        
        for event in events:
            event_type = event.get("event_type")
            event_data = event.get("event_data", {})
            
            if event_type == "AccountCreated":
                account_state["account_id"] = event.get("aggregate_id")
                account_state["user_id"] = event_data.get("user_id")
                account_state["tenant_id"] = event_data.get("tenant_id")
                account_state["status"] = "active"
                account_state["created_at"] = event.get("timestamp")
                account_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "FundsDeposited":
                amount = Decimal(str(event_data.get("amount", "0")))
                account_state["balance"] += amount
                account_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "FundsWithdrawn":
                amount = Decimal(str(event_data.get("amount", "0")))
                account_state["balance"] -= amount
                account_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "AccountFrozen":
                account_state["status"] = "frozen"
                account_state["updated_at"] = event.get("timestamp")
            
            elif event_type == "AccountClosed":
                account_state["status"] = "closed"
                account_state["updated_at"] = event.get("timestamp")
        
        return account_state
    
    @staticmethod
    def get_aggregate_version(events: List[Dict[str, Any]]) -> int:
        """
        Get aggregate version (event count).
        
        Args:
            events: List of events
        
        Returns:
            Number of events (version)
        """
        return len(events)
    
    @staticmethod
    def get_correlation_chain(events: List[Dict[str, Any]], correlation_id: str) -> List[Dict[str, Any]]:
        """
        Get all events in a correlation chain.
        
        Args:
            events: List of all events
            correlation_id: Correlation ID to filter by
        
        Returns:
            List of events with matching correlation_id
        """
        return [
            event for event in events
            if event.get("correlation_id") == correlation_id
        ]

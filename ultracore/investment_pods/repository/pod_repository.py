"""
Pod Repository with Multi-Tenancy Support
Tenant-aware data access layer
"""

from typing import List, Optional, Dict
from decimal import Decimal
from datetime import date

from ..aggregates.pod_aggregate import PodAggregate
from ..events import PodStatus, GoalType


class PodRepository:
    """
    Repository for Pod aggregates with tenant isolation
    
    All queries are automatically filtered by tenant_id
    """
    
    def __init__(self, event_store=None):
        """
        Initialize repository
        
        Args:
            event_store: Event store for event sourcing (optional for now)
        """
        self.event_store = event_store
        self._pods: Dict[str, PodAggregate] = {}  # In-memory for demo
    
    def save(self, pod: PodAggregate) -> None:
        """
        Save Pod aggregate
        
        Publishes uncommitted events to Kafka
        """
        # Publish events
        events = pod.get_uncommitted_events()
        if self.event_store:
            for event in events:
                self.event_store.append(event)
        
        # Save to repository
        self._pods[pod.pod_id] = pod
        
        # Mark events as committed
        pod.mark_events_committed()
    
    def get_by_id(self, pod_id: str, tenant_id: str) -> Optional[PodAggregate]:
        """
        Get Pod by ID with tenant check
        
        Args:
            pod_id: Pod identifier
            tenant_id: Tenant identifier
        
        Returns:
            Pod aggregate or None
        
        Raises:
            ValueError: If Pod belongs to different tenant
        """
        pod = self._pods.get(pod_id)
        
        if pod is None:
            return None
        
        # Tenant isolation check
        if pod.tenant_id != tenant_id:
            raise ValueError(f"Pod {pod_id} does not belong to tenant {tenant_id}")
        
        return pod
    
    def get_by_client(self, client_id: str, tenant_id: str) -> List[PodAggregate]:
        """
        Get all Pods for a client within a tenant
        
        Args:
            client_id: Client identifier
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        return [
            pod for pod in self._pods.values()
            if pod.client_id == client_id and pod.tenant_id == tenant_id
        ]
    
    def get_by_tenant(self, tenant_id: str) -> List[PodAggregate]:
        """
        Get all Pods for a tenant
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        return [
            pod for pod in self._pods.values()
            if pod.tenant_id == tenant_id
        ]
    
    def get_by_status(self, status: PodStatus, tenant_id: str) -> List[PodAggregate]:
        """
        Get Pods by status within a tenant
        
        Args:
            status: Pod status
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        return [
            pod for pod in self._pods.values()
            if pod.status == status and pod.tenant_id == tenant_id
        ]
    
    def get_by_goal_type(self, goal_type: GoalType, tenant_id: str) -> List[PodAggregate]:
        """
        Get Pods by goal type within a tenant
        
        Args:
            goal_type: Goal type
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        return [
            pod for pod in self._pods.values()
            if pod.goal_type == goal_type and pod.tenant_id == tenant_id
        ]
    
    def get_active_pods(self, tenant_id: str) -> List[PodAggregate]:
        """
        Get all active Pods for a tenant
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of active Pod aggregates
        """
        return self.get_by_status(PodStatus.ACTIVE, tenant_id)
    
    def get_pods_requiring_glide_path(self, tenant_id: str) -> List[PodAggregate]:
        """
        Get Pods that need glide path transition
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        today = date.today()
        return [
            pod for pod in self.get_active_pods(tenant_id)
            if pod.glide_path_enabled and pod.next_glide_path_date and pod.next_glide_path_date <= today
        ]
    
    def get_pods_requiring_rebalance(self, tenant_id: str) -> List[PodAggregate]:
        """
        Get Pods that need rebalancing
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of Pod aggregates
        """
        # In production, check actual drift from market prices
        return []
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict:
        """
        Get aggregate metrics for a tenant
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Dict with tenant-level metrics
        """
        pods = self.get_by_tenant(tenant_id)
        
        if not pods:
            return {
                "total_pods": 0,
                "total_clients": 0,
                "total_aum": Decimal("0"),
                "average_pod_size": Decimal("0"),
                "average_return": Decimal("0"),
            }
        
        total_aum = sum(pod.current_value for pod in pods)
        total_clients = len(set(pod.client_id for pod in pods))
        avg_return = sum(pod.total_return for pod in pods) / len(pods)
        
        return {
            "total_pods": len(pods),
            "total_clients": total_clients,
            "total_aum": total_aum,
            "average_pod_size": total_aum / len(pods),
            "average_return": avg_return,
            "pods_by_status": {
                "active": len([p for p in pods if p.status == PodStatus.ACTIVE]),
                "completed": len([p for p in pods if p.status == PodStatus.COMPLETED]),
                "paused": len([p for p in pods if p.status == PodStatus.PAUSED]),
            },
            "pods_by_goal_type": {
                "first_home": len([p for p in pods if p.goal_type == GoalType.FIRST_HOME]),
                "retirement": len([p for p in pods if p.goal_type == GoalType.RETIREMENT]),
                "wealth_accumulation": len([p for p in pods if p.goal_type == GoalType.WEALTH_ACCUMULATION]),
            }
        }

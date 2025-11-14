"""
Investment Pods Repository.

Database operations for Investment Pods.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from ..models.investment_pods import (
    InvestmentPodDB,
    PodTransactionDB,
    PodAllocationDB,
    PodPerformanceDB,
)
from ...domains.wealth.models.investment_pod import InvestmentPod


class InvestmentPodRepository:
    """Repository for Investment Pod database operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create_pod(self, pod: InvestmentPod) -> InvestmentPodDB:
        """
        Create new investment pod in database.
        
        Args:
            pod: Investment pod domain model
            
        Returns:
            Database model
        """
        db_pod = InvestmentPodDB(
            pod_id=pod.pod_id,
            tenant_id=pod.tenant_id,
            user_id=pod.user_id,
            goal_type=pod.goal_type.value,
            goal_name=pod.goal_name,
            target_amount=pod.target_amount,
            target_date=pod.target_date,
            initial_deposit=pod.initial_deposit,
            monthly_contribution=pod.monthly_contribution,
            current_value=pod.current_value,
            risk_tolerance=pod.risk_tolerance.value,
            target_allocation=pod.target_allocation,
            current_allocation=pod.current_allocation,
            status=pod.status.value,
            created_at=pod.created_at,
            updated_at=pod.updated_at,
            funded_at=pod.funded_at,
            activated_at=pod.activated_at,
            closed_at=pod.closed_at
        )
        
        self.session.add(db_pod)
        self.session.commit()
        self.session.refresh(db_pod)
        
        return db_pod
    
    def get_pod(self, pod_id: str) -> Optional[InvestmentPodDB]:
        """
        Get pod by ID.
        
        Args:
            pod_id: Pod ID
            
        Returns:
            Database model or None
        """
        return self.session.query(InvestmentPodDB).filter(
            InvestmentPodDB.pod_id == pod_id
        ).first()
    
    def list_pods(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        goal_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[InvestmentPodDB]:
        """
        List pods with filters.
        
        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID filter
            status: Optional status filter
            goal_type: Optional goal type filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of database models
        """
        query = self.session.query(InvestmentPodDB).filter(
            InvestmentPodDB.tenant_id == tenant_id
        )
        
        if user_id:
            query = query.filter(InvestmentPodDB.user_id == user_id)
        
        if status:
            query = query.filter(InvestmentPodDB.status == status)
        
        if goal_type:
            query = query.filter(InvestmentPodDB.goal_type == goal_type)
        
        return query.order_by(desc(InvestmentPodDB.created_at)).limit(limit).offset(offset).all()
    
    def update_pod(self, pod: InvestmentPod) -> InvestmentPodDB:
        """
        Update existing pod.
        
        Args:
            pod: Investment pod domain model
            
        Returns:
            Updated database model
        """
        db_pod = self.get_pod(pod.pod_id)
        
        if not db_pod:
            raise ValueError(f"Pod {pod.pod_id} not found")
        
        # Update fields
        db_pod.goal_name = pod.goal_name
        db_pod.target_amount = pod.target_amount
        db_pod.target_date = pod.target_date
        db_pod.monthly_contribution = pod.monthly_contribution
        db_pod.current_value = pod.current_value
        db_pod.risk_tolerance = pod.risk_tolerance.value
        db_pod.target_allocation = pod.target_allocation
        db_pod.current_allocation = pod.current_allocation
        db_pod.status = pod.status.value
        db_pod.updated_at = datetime.utcnow()
        db_pod.funded_at = pod.funded_at
        db_pod.activated_at = pod.activated_at
        db_pod.closed_at = pod.closed_at
        
        self.session.commit()
        self.session.refresh(db_pod)
        
        return db_pod
    
    def delete_pod(self, pod_id: str) -> bool:
        """
        Delete pod.
        
        Args:
            pod_id: Pod ID
            
        Returns:
            True if deleted, False if not found
        """
        db_pod = self.get_pod(pod_id)
        
        if not db_pod:
            return False
        
        self.session.delete(db_pod)
        self.session.commit()
        
        return True
    
    def create_transaction(
        self,
        pod_id: str,
        transaction_type: str,
        amount: Decimal,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> PodTransactionDB:
        """
        Create pod transaction.
        
        Args:
            pod_id: Pod ID
            transaction_type: Transaction type
            amount: Transaction amount
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            Database model
        """
        db_transaction = PodTransactionDB(
            transaction_id=str(uuid4()),
            pod_id=pod_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            metadata=metadata,
            created_at=datetime.utcnow()
        )
        
        self.session.add(db_transaction)
        self.session.commit()
        self.session.refresh(db_transaction)
        
        return db_transaction
    
    def list_transactions(
        self,
        pod_id: str,
        transaction_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PodTransactionDB]:
        """
        List pod transactions.
        
        Args:
            pod_id: Pod ID
            transaction_type: Optional transaction type filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of database models
        """
        query = self.session.query(PodTransactionDB).filter(
            PodTransactionDB.pod_id == pod_id
        )
        
        if transaction_type:
            query = query.filter(PodTransactionDB.transaction_type == transaction_type)
        
        return query.order_by(desc(PodTransactionDB.created_at)).limit(limit).offset(offset).all()
    
    def create_performance_snapshot(
        self,
        pod_id: str,
        current_value: Decimal,
        total_contributions: Decimal,
        total_withdrawals: Decimal,
        total_return: Decimal,
        total_return_pct: Decimal,
        volatility: Optional[Decimal] = None,
        sharpe_ratio: Optional[Decimal] = None,
        max_drawdown: Optional[Decimal] = None
    ) -> PodPerformanceDB:
        """
        Create performance snapshot.
        
        Args:
            pod_id: Pod ID
            current_value: Current value
            total_contributions: Total contributions
            total_withdrawals: Total withdrawals
            total_return: Total return
            total_return_pct: Total return percentage
            volatility: Optional volatility
            sharpe_ratio: Optional Sharpe ratio
            max_drawdown: Optional max drawdown
            
        Returns:
            Database model
        """
        db_performance = PodPerformanceDB(
            performance_id=str(uuid4()),
            pod_id=pod_id,
            current_value=current_value,
            total_contributions=total_contributions,
            total_withdrawals=total_withdrawals,
            total_return=total_return,
            total_return_pct=total_return_pct,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            snapshot_date=datetime.utcnow()
        )
        
        self.session.add(db_performance)
        self.session.commit()
        self.session.refresh(db_performance)
        
        return db_performance
    
    def get_performance_history(
        self,
        pod_id: str,
        limit: int = 100
    ) -> List[PodPerformanceDB]:
        """
        Get performance history.
        
        Args:
            pod_id: Pod ID
            limit: Maximum number of results
            
        Returns:
            List of database models
        """
        return self.session.query(PodPerformanceDB).filter(
            PodPerformanceDB.pod_id == pod_id
        ).order_by(desc(PodPerformanceDB.snapshot_date)).limit(limit).all()

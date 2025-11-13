"""
Investor Management Service
Core business logic for investor operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import uuid

from .models import (
    Investor, InvestorType, InvestorStatus,
    CreateInvestorRequest
)
from .kafka_events import InvestorKafkaProducer


class InvestorService:
    """
    Investor Management Service
    
    Handles:
    - Investor onboarding
    - KYC/AML verification
    - Investor profile management
    - Portfolio tracking
    """
    
    def __init__(self):
        self.investors: Dict[str, Investor] = {}
        self.kafka_producer = InvestorKafkaProducer()
        
    def create_investor(
        self,
        request: CreateInvestorRequest
    ) -> Investor:
        """
        Create a new investor
        
        Args:
            request: Investor creation request
            
        Returns:
            Created investor
        """
        
        # Generate investor ID
        investor_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
        
        # Create investor
        investor = Investor(
            investor_id=investor_id,
            external_id=request.external_id,
            investor_name=request.investor_name,
            investor_type=request.investor_type,
            email=request.email,
            phone=request.phone,
            country=request.country,
            created_by=request.created_by,
            status=InvestorStatus.UNDER_REVIEW  # Requires KYC/AML
        )
        
        # Store investor
        self.investors[investor_id] = investor
        
        # Publish event
        self.kafka_producer.publish_investor_created(
            investor_id=investor_id,
            external_id=request.external_id,
            investor_name=request.investor_name,
            investor_type=request.investor_type.value,
            created_by=request.created_by
        )
        
        return investor
        
    def verify_kyc(
        self,
        investor_id: str,
        verified_by: str
    ) -> Investor:
        """
        Mark investor as KYC verified
        
        Args:
            investor_id: Investor ID
            verified_by: User who verified
            
        Returns:
            Updated investor
        """
        
        investor = self.investors.get(investor_id)
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        investor.kyc_verified = True
        investor.kyc_verification_date = datetime.now(timezone.utc)
        investor.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        self.kafka_producer.publish_investor_created(
            investor_id=investor_id,
            external_id=investor.external_id,
            investor_name=investor.investor_name,
            investor_type=investor.investor_type.value,
            created_by=verified_by
        )
        
        # If both KYC and AML verified, activate
        if investor.kyc_verified and investor.aml_verified:
            investor.status = InvestorStatus.ACTIVE
        
        return investor
        
    def verify_aml(
        self,
        investor_id: str,
        verified_by: str
    ) -> Investor:
        """
        Mark investor as AML verified
        
        Args:
            investor_id: Investor ID
            verified_by: User who verified
            
        Returns:
            Updated investor
        """
        
        investor = self.investors.get(investor_id)
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        investor.aml_verified = True
        investor.aml_verification_date = datetime.now(timezone.utc)
        investor.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        self.kafka_producer.publish_investor_created(
            investor_id=investor_id,
            external_id=investor.external_id,
            investor_name=investor.investor_name,
            investor_type=investor.investor_type.value,
            created_by=verified_by
        )
        
        # If both KYC and AML verified, activate
        if investor.kyc_verified and investor.aml_verified:
            investor.status = InvestorStatus.ACTIVE
        
        return investor
        
    def get_investor(
        self,
        investor_id: str
    ) -> Optional[Investor]:
        """Get investor by ID"""
        return self.investors.get(investor_id)
        
    def get_investor_by_external_id(
        self,
        external_id: str
    ) -> Optional[Investor]:
        """Get investor by external ID"""
        for investor in self.investors.values():
            if investor.external_id == external_id:
                return investor
        return None
        
    def list_investors(
        self,
        status: Optional[InvestorStatus] = None,
        investor_type: Optional[InvestorType] = None
    ) -> List[Investor]:
        """
        List investors with optional filters
        
        Args:
            status: Filter by status
            investor_type: Filter by type
            
        Returns:
            List of investors
        """
        
        investors = list(self.investors.values())
        
        if status:
            investors = [i for i in investors if i.status == status]
            
        if investor_type:
            investors = [i for i in investors if i.investor_type == investor_type]
            
        return investors
        
    def update_investor_portfolio(
        self,
        investor_id: str,
        total_investments: Decimal,
        active_loans: int,
        total_returns: Decimal
    ) -> Investor:
        """
        Update investor portfolio aggregates
        
        Args:
            investor_id: Investor ID
            total_investments: Total amount invested
            active_loans: Number of active loans
            total_returns: Total returns earned
            
        Returns:
            Updated investor
        """
        
        investor = self.investors.get(investor_id)
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        investor.total_investments = total_investments
        investor.active_loans = active_loans
        investor.total_returns = total_returns
        investor.updated_at = datetime.now(timezone.utc)
        
        return investor
        
    def suspend_investor(
        self,
        investor_id: str,
        reason: str,
        suspended_by: str
    ) -> Investor:
        """
        Suspend investor account
        
        Args:
            investor_id: Investor ID
            reason: Suspension reason
            suspended_by: User who suspended
            
        Returns:
            Updated investor
        """
        
        investor = self.investors.get(investor_id)
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        investor.status = InvestorStatus.SUSPENDED
        investor.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        self.kafka_producer._publish("investor-events", {
            "event_type": "investor.suspended",
            "investor_id": investor_id,
            "reason": reason,
            "suspended_by": suspended_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return investor
        
    def activate_investor(
        self,
        investor_id: str,
        activated_by: str
    ) -> Investor:
        """
        Activate investor account
        
        Args:
            investor_id: Investor ID
            activated_by: User who activated
            
        Returns:
            Updated investor
        """
        
        investor = self.investors.get(investor_id)
        if not investor:
            raise ValueError(f"Investor {investor_id} not found")
        
        # Verify KYC/AML before activation
        if not investor.kyc_verified or not investor.aml_verified:
            raise ValueError("Investor must be KYC and AML verified before activation")
        
        investor.status = InvestorStatus.ACTIVE
        investor.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        self.kafka_producer._publish("investor-events", {
            "event_type": "investor.activated",
            "investor_id": investor_id,
            "activated_by": activated_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return investor

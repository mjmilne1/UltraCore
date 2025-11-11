"""
Customer Repository

Specialized repository for customer operations:
- Customer search by email, mobile, ABN
- KYC status queries
- Risk assessment queries
- Customer relationship management
"""

from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ultracore.database.repositories.base import BaseRepository
from ultracore.database.models.customers import (
    Customer,
    CustomerRelationship,
    CustomerTypeEnum,
    CustomerStatusEnum,
    RiskRatingEnum
)


class CustomerRepository(BaseRepository[Customer]):
    """Customer-specific repository"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(Customer, session, tenant_id)
    
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        query = select(Customer).where(
            and_(
                Customer.email == email,
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_mobile(self, mobile: str) -> Optional[Customer]:
        """Find customer by mobile number"""
        query = select(Customer).where(
            and_(
                Customer.mobile == mobile,
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_abn(self, abn: str) -> Optional[Customer]:
        """Find business customer by ABN"""
        query = select(Customer).where(
            and_(
                Customer.abn == abn,
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def search(
        self,
        search_term: str,
        customer_type: Optional[CustomerTypeEnum] = None,
        status: Optional[CustomerStatusEnum] = None,
        limit: int = 50
    ) -> List[Customer]:
        """
        Search customers by name, email, or mobile
        
        Uses ILIKE for case-insensitive search
        """
        query = select(Customer).where(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None),
                or_(
                    Customer.first_name.ilike(f"%{search_term}%"),
                    Customer.last_name.ilike(f"%{search_term}%"),
                    Customer.business_name.ilike(f"%{search_term}%"),
                    Customer.email.ilike(f"%{search_term}%"),
                    Customer.mobile.ilike(f"%{search_term}%")
                )
            )
        )
        
        if customer_type:
            query = query.where(Customer.customer_type == customer_type)
        
        if status:
            query = query.where(Customer.status == status)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_high_risk_customers(self) -> List[Customer]:
        """Get customers with high risk rating"""
        query = select(Customer).where(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None),
                Customer.risk_rating.in_([RiskRatingEnum.HIGH, RiskRatingEnum.CRITICAL])
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_kyc_pending(self) -> List[Customer]:
        """Get customers with pending KYC verification"""
        from ultracore.database.models.customers import KYCStatusEnum
        
        query = select(Customer).where(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.deleted_at.is_(None),
                Customer.kyc_status.in_([
                    KYCStatusEnum.NOT_STARTED,
                    KYCStatusEnum.IN_PROGRESS
                ])
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class CustomerRelationshipRepository(BaseRepository[CustomerRelationship]):
    """Customer relationship repository (for graph sync)"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(CustomerRelationship, session, tenant_id)
    
    async def get_relationships(
        self,
        customer_id: str,
        relationship_type: Optional[str] = None
    ) -> List[CustomerRelationship]:
        """Get all relationships for a customer"""
        query = select(CustomerRelationship).where(
            and_(
                CustomerRelationship.tenant_id == self.tenant_id,
                or_(
                    CustomerRelationship.from_customer_id == customer_id,
                    CustomerRelationship.to_customer_id == customer_id
                ),
                CustomerRelationship.is_active == True
            )
        )
        
        if relationship_type:
            query = query.where(
                CustomerRelationship.relationship_type == relationship_type
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

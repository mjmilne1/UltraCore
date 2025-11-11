"""
Loan Repository

Specialized repository for loan operations:
- Loan queries by customer
- Payment history
- Delinquency tracking
- Portfolio analytics
"""

from typing import List, Optional
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from decimal import Decimal

from ultracore.database.repositories.base import BaseRepository
from ultracore.database.models.loans import (
    Loan,
    LoanPayment,
    LoanPaymentSchedule,
    LoanCollateral,
    LoanTypeEnum,
    LoanStatusEnum,
    PaymentStatusEnum
)


class LoanRepository(BaseRepository[Loan]):
    """Loan-specific repository"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(Loan, session, tenant_id)
    
    async def get_by_loan_number(self, loan_number: str) -> Optional[Loan]:
        """Get loan by loan number"""
        query = select(Loan).where(
            and_(
                Loan.loan_number == loan_number,
                Loan.tenant_id == self.tenant_id,
                Loan.deleted_at.is_(None)
            )
        ).options(
            selectinload(Loan.payment_schedule),
            selectinload(Loan.collateral_items)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_customer_loans(
        self,
        customer_id: str,
        loan_type: Optional[LoanTypeEnum] = None,
        status: Optional[LoanStatusEnum] = None
    ) -> List[Loan]:
        """Get all loans for a customer"""
        query = select(Loan).where(
            and_(
                Loan.customer_id == customer_id,
                Loan.tenant_id == self.tenant_id,
                Loan.deleted_at.is_(None)
            )
        ).options(
            selectinload(Loan.payment_schedule)
        )
        
        if loan_type:
            query = query.where(Loan.loan_type == loan_type)
        
        if status:
            query = query.where(Loan.status == status)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_loans(
        self,
        loan_type: Optional[LoanTypeEnum] = None
    ) -> List[Loan]:
        """Get all active loans"""
        query = select(Loan).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE,
                Loan.deleted_at.is_(None)
            )
        )
        
        if loan_type:
            query = query.where(Loan.loan_type == loan_type)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_delinquent_loans(
        self,
        days_past_due: int = 30
    ) -> List[Loan]:
        """Get loans that are delinquent"""
        query = select(Loan).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE,
                Loan.days_past_due >= days_past_due,
                Loan.deleted_at.is_(None)
            )
        ).order_by(desc(Loan.days_past_due))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_maturing_loans(
        self,
        days_ahead: int = 30
    ) -> List[Loan]:
        """Get loans maturing within specified days"""
        from datetime import timedelta
        
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(Loan).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE,
                Loan.maturity_date <= cutoff_date,
                Loan.deleted_at.is_(None)
            )
        ).order_by(Loan.maturity_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_portfolio_metrics(self) -> dict:
        """Get portfolio-wide metrics"""
        
        # Total outstanding
        outstanding_query = select(
            func.sum(Loan.current_balance)
        ).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status.in_([LoanStatusEnum.ACTIVE, LoanStatusEnum.DEFAULT])
            )
        )
        
        # Number of active loans
        count_query = select(func.count(Loan.id)).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE
            )
        )
        
        # Delinquent balance
        delinquent_query = select(
            func.sum(Loan.current_balance)
        ).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE,
                Loan.days_past_due > 0
            )
        )
        
        # Average interest rate
        avg_rate_query = select(
            func.avg(Loan.interest_rate)
        ).where(
            and_(
                Loan.tenant_id == self.tenant_id,
                Loan.status == LoanStatusEnum.ACTIVE
            )
        )
        
        outstanding_result = await self.session.execute(outstanding_query)
        count_result = await self.session.execute(count_query)
        delinquent_result = await self.session.execute(delinquent_query)
        avg_rate_result = await self.session.execute(avg_rate_query)
        
        total_outstanding = float(outstanding_result.scalar_one() or 0)
        delinquent_balance = float(delinquent_result.scalar_one() or 0)
        
        return {
            'total_outstanding': total_outstanding,
            'active_loan_count': count_result.scalar_one(),
            'delinquent_balance': delinquent_balance,
            'delinquency_rate': (delinquent_balance / total_outstanding * 100) if total_outstanding > 0 else 0,
            'average_interest_rate': float(avg_rate_result.scalar_one() or 0)
        }


class LoanPaymentRepository(BaseRepository[LoanPayment]):
    """Loan payment repository"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(LoanPayment, session, tenant_id)
    
    async def get_loan_payments(
        self,
        loan_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[PaymentStatusEnum] = None
    ) -> List[LoanPayment]:
        """Get payments for a loan"""
        query = select(LoanPayment).where(
            and_(
                LoanPayment.loan_id == loan_id,
                LoanPayment.tenant_id == self.tenant_id
            )
        )
        
        if start_date:
            query = query.where(LoanPayment.payment_date >= start_date)
        
        if end_date:
            query = query.where(LoanPayment.payment_date <= end_date)
        
        if status:
            query = query.where(LoanPayment.status == status)
        
        query = query.order_by(LoanPayment.payment_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_upcoming_payments(
        self,
        days_ahead: int = 7
    ) -> List[LoanPayment]:
        """Get upcoming scheduled payments"""
        from datetime import timedelta
        
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(LoanPayment).where(
            and_(
                LoanPayment.tenant_id == self.tenant_id,
                LoanPayment.status == PaymentStatusEnum.SCHEDULED,
                LoanPayment.due_date <= cutoff_date
            )
        ).order_by(LoanPayment.due_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_missed_payments(self) -> List[LoanPayment]:
        """Get missed payments"""
        query = select(LoanPayment).where(
            and_(
                LoanPayment.tenant_id == self.tenant_id,
                LoanPayment.status == PaymentStatusEnum.MISSED,
                LoanPayment.due_date < date.today()
            )
        ).order_by(LoanPayment.due_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

"""
Account Repository

Specialized repository for account operations:
- Account queries by customer
- Balance queries
- Transaction history
- Account statement generation
"""

from typing import List, Optional
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, date

from ultracore.database.repositories.base import BaseRepository
from ultracore.database.models.accounts import (
    Account,
    AccountBalance,
    Transaction,
    AccountTypeEnum,
    AccountStatusEnum,
    TransactionTypeEnum
)


class AccountRepository(BaseRepository[Account]):
    """Account-specific repository"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(Account, session, tenant_id)
    
    async def get_by_account_number(
        self,
        account_number: str
    ) -> Optional[Account]:
        """Get account by account number"""
        query = select(Account).where(
            and_(
                Account.account_number == account_number,
                Account.tenant_id == self.tenant_id,
                Account.deleted_at.is_(None)
            )
        ).options(
            selectinload(Account.balances)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_customer_accounts(
        self,
        customer_id: str,
        account_type: Optional[AccountTypeEnum] = None,
        status: Optional[AccountStatusEnum] = None
    ) -> List[Account]:
        """Get all accounts for a customer"""
        query = select(Account).where(
            and_(
                Account.customer_id == customer_id,
                Account.tenant_id == self.tenant_id,
                Account.deleted_at.is_(None)
            )
        ).options(
            selectinload(Account.balances)
        )
        
        if account_type:
            query = query.where(Account.account_type == account_type)
        
        if status:
            query = query.where(Account.status == status)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_total_balance(
        self,
        customer_id: str,
        account_types: Optional[List[AccountTypeEnum]] = None
    ) -> float:
        """Get total balance across accounts"""
        query = select(func.sum(AccountBalance.ledger_balance)).join(
            Account
        ).where(
            and_(
                Account.customer_id == customer_id,
                Account.tenant_id == self.tenant_id,
                Account.deleted_at.is_(None)
            )
        )
        
        if account_types:
            query = query.where(Account.account_type.in_(account_types))
        
        result = await self.session.execute(query)
        return result.scalar_one() or 0.0


class TransactionRepository(BaseRepository[Transaction]):
    """Transaction-specific repository"""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(Transaction, session, tenant_id)
    
    async def get_account_transactions(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionTypeEnum] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for an account"""
        query = select(Transaction).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.tenant_id == self.tenant_id
            )
        )
        
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        
        query = query.order_by(desc(Transaction.transaction_date))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_transaction_summary(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """Get transaction summary for period"""
        
        # Total credits
        credits_query = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.tenant_id == self.tenant_id,
                Transaction.transaction_type.in_([
                    TransactionTypeEnum.DEPOSIT,
                    TransactionTypeEnum.INTEREST
                ]),
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        
        # Total debits
        debits_query = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.tenant_id == self.tenant_id,
                Transaction.transaction_type.in_([
                    TransactionTypeEnum.WITHDRAWAL,
                    TransactionTypeEnum.FEE
                ]),
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        
        # Transaction count
        count_query = select(func.count(Transaction.id)).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.tenant_id == self.tenant_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        
        credits_result = await self.session.execute(credits_query)
        debits_result = await self.session.execute(debits_query)
        count_result = await self.session.execute(count_query)
        
        return {
            'total_credits': float(credits_result.scalar_one() or 0),
            'total_debits': float(debits_result.scalar_one() or 0),
            'transaction_count': count_result.scalar_one()
        }

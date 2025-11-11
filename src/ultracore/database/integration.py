"""
Database Integration Layer

Bridges between repositories (database layer) and existing managers (business logic):
- Converts between domain models and database models
- Provides persistence hooks for managers
- Maintains backward compatibility
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from decimal import Decimal
import uuid

from ultracore.database.repositories import (
    CustomerRepository,
    AccountRepository,
    TransactionRepository,
    LoanRepository,
    LoanPaymentRepository
)
from ultracore.database.models import (
    Customer as DBCustomer,
    Account as DBAccount,
    Transaction as DBTransaction,
    Loan as DBLoan,
    LoanPayment as DBLoanPayment,
    CustomerTypeEnum,
    AccountTypeEnum,
    TransactionTypeEnum,
    LoanTypeEnum,
    LoanStatusEnum
)

# Import existing domain models
from ultracore.customers.core.customer_models import Customer, CustomerType
from ultracore.accounts.core.account_models import Account, AccountType, Transaction, TransactionType
from ultracore.lending.loan_models import Loan, LoanStatus


class DatabaseIntegration:
    """
    Integration layer between domain models and database models
    
    Features:
    - Bidirectional conversion (domain ↔ database)
    - Persistence operations
    - Caching coordination
    - Event sourcing coordination
    """
    
    def __init__(self, session: AsyncSession, tenant_id: str = "DEFAULT"):
        self.session = session
        self.tenant_id = tenant_id
        
        # Initialize repositories
        self.customer_repo = CustomerRepository(session, tenant_id)
        self.account_repo = AccountRepository(session, tenant_id)
        self.transaction_repo = TransactionRepository(session, tenant_id)
        self.loan_repo = LoanRepository(session, tenant_id)
        self.payment_repo = LoanPaymentRepository(session, tenant_id)
    
    # ========================================================================
    # CUSTOMER CONVERSION
    # ========================================================================
    
    def domain_to_db_customer(self, customer: Customer) -> DBCustomer:
        """Convert domain Customer to database Customer"""
        
        db_customer = DBCustomer(
            id=uuid.UUID(customer.customer_id) if customer.customer_id else uuid.uuid4(),
            customer_id=customer.customer_id,
            tenant_id=self.tenant_id,
            customer_type=CustomerTypeEnum[customer.customer_type.name],
            status=customer.status.name,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            date_of_birth=customer.date_of_birth,
            business_name=customer.business_name,
            business_registration=customer.business_registration,
            abn=customer.abn,
            acn=customer.acn,
            email=customer.email,
            mobile=customer.mobile,
            phone=customer.phone,
            street_address=customer.street_address,
            suburb=customer.suburb,
            city=customer.city,
            state=customer.state,
            postal_code=customer.postal_code,
            country=customer.country,
            risk_rating=customer.risk_rating.name if customer.risk_rating else "MEDIUM",
            kyc_status=customer.kyc_status.name if customer.kyc_status else "NOT_STARTED",
            is_pep=customer.is_pep,
            created_by="SYSTEM"
        )
        
        return db_customer
    
    def db_to_domain_customer(self, db_customer: DBCustomer) -> Customer:
        """Convert database Customer to domain Customer"""
        
        customer = Customer(
            customer_type=CustomerType[db_customer.customer_type.name],
            first_name=db_customer.first_name,
            middle_name=db_customer.middle_name,
            last_name=db_customer.last_name,
            date_of_birth=db_customer.date_of_birth,
            email=db_customer.email,
            mobile=db_customer.mobile,
            phone=db_customer.phone
        )
        
        # Set additional fields
        customer.customer_id = db_customer.customer_id
        customer.business_name = db_customer.business_name
        customer.abn = db_customer.abn
        customer.street_address = db_customer.street_address
        customer.city = db_customer.city
        customer.state = db_customer.state
        customer.postal_code = db_customer.postal_code
        
        return customer
    
    async def persist_customer(self, customer: Customer, created_by: str = "SYSTEM") -> str:
        """Persist domain customer to database"""
        
        db_customer = self.domain_to_db_customer(customer)
        db_customer = await self.customer_repo.create(db_customer, created_by)
        await self.session.commit()
        
        return db_customer.customer_id
    
    async def load_customer(self, customer_id: str) -> Optional[Customer]:
        """Load customer from database"""
        
        db_customer = await self.customer_repo.get_by_business_id(customer_id)
        if not db_customer:
            return None
        
        return self.db_to_domain_customer(db_customer)
    
    # ========================================================================
    # ACCOUNT CONVERSION
    # ========================================================================
    
    def domain_to_db_account(self, account: Account) -> DBAccount:
        """Convert domain Account to database Account"""
        
        db_account = DBAccount(
            id=uuid.UUID(account.account_id) if account.account_id else uuid.uuid4(),
            account_id=account.account_id,
            account_number=account.account_number,
            tenant_id=self.tenant_id,
            customer_id=uuid.UUID(account.customer_id),
            account_type=AccountTypeEnum[account.account_type.name],
            status=account.status.name,
            currency=account.currency,
            interest_bearing=account.interest_bearing,
            current_interest_rate=account.current_interest_rate.annual_rate if account.current_interest_rate else None,
            maturity_date=account.maturity_date,
            opened_date=account.opened_date,
            closed_date=account.closed_date,
            created_by="SYSTEM"
        )
        
        return db_account
    
    def db_to_domain_account(self, db_account: DBAccount) -> Account:
        """Convert database Account to domain Account"""
        
        from ultracore.accounts.core.account_models import AccountBalance
        
        account = Account(
            customer_id=str(db_account.customer_id),
            account_type=AccountType[db_account.account_type.name],
            currency=db_account.currency,
            opened_by="SYSTEM"
        )
        
        # Set additional fields
        account.account_id = db_account.account_id
        account.account_number = db_account.account_number
        account.opened_date = db_account.opened_date
        
        # Set balance if available
        if db_account.balances:
            account.balance = AccountBalance(
                ledger_balance=Decimal(str(db_account.balances.ledger_balance)),
                available_balance=Decimal(str(db_account.balances.available_balance)),
                pending_credits=Decimal(str(db_account.balances.pending_credits)),
                pending_debits=Decimal(str(db_account.balances.pending_debits)),
                held_amount=Decimal(str(db_account.balances.held_amount))
            )
        
        return account
    
    async def persist_account(self, account: Account, created_by: str = "SYSTEM") -> str:
        """Persist domain account to database"""
        
        db_account = self.domain_to_db_account(account)
        db_account = await self.account_repo.create(db_account, created_by)
        
        # Create balance record
        from ultracore.database.models import AccountBalance as DBAccountBalance
        db_balance = DBAccountBalance(
            tenant_id=self.tenant_id,
            account_id=db_account.id,
            ledger_balance=account.balance.ledger_balance,
            available_balance=account.balance.available_balance,
            pending_credits=account.balance.pending_credits,
            pending_debits=account.balance.pending_debits,
            held_amount=account.balance.held_amount,
            last_balance_update=datetime.utcnow(),
            created_by=created_by
        )
        
        self.session.add(db_balance)
        await self.session.commit()
        
        return db_account.account_id
    
    async def load_account(self, account_id: str) -> Optional[Account]:
        """Load account from database"""
        
        db_account = await self.account_repo.get_by_business_id(account_id, 'account_id')
        if not db_account:
            return None
        
        return self.db_to_domain_account(db_account)
    
    # ========================================================================
    # TRANSACTION CONVERSION
    # ========================================================================
    
    async def persist_transaction(
        self,
        transaction: Transaction,
        created_by: str = "SYSTEM"
    ) -> str:
        """Persist domain transaction to database"""
        
        db_transaction = DBTransaction(
            tenant_id=self.tenant_id,
            transaction_id=transaction.transaction_id,
            account_id=uuid.UUID(transaction.account_id),
            transaction_type=TransactionTypeEnum[transaction.transaction_type.name],
            status=transaction.status.name,
            amount=transaction.amount,
            currency=transaction.currency,
            balance_before=transaction.balance_before,
            balance_after=transaction.balance_after,
            description=transaction.description,
            reference=transaction.reference,
            related_account_id=transaction.related_account_id,
            related_transaction_id=transaction.related_transaction_id,
            transaction_date=transaction.transaction_date,
            value_date=transaction.value_date,
            posted_date=transaction.posted_date,
            created_by=created_by
        )
        
        db_transaction = await self.transaction_repo.create(db_transaction, created_by)
        await self.session.commit()
        
        return db_transaction.transaction_id
    
    # ========================================================================
    # LOAN CONVERSION
    # ========================================================================
    
    def domain_to_db_loan(self, loan: Loan) -> DBLoan:
        """Convert domain Loan to database Loan"""
        
        db_loan = DBLoan(
            tenant_id=self.tenant_id,
            loan_id=loan.loan_id,
            loan_number=loan.loan_id,  # Use same for now
            customer_id=uuid.UUID(loan.customer_id),
            loan_type=LoanTypeEnum[loan.loan_type.name],
            status=LoanStatusEnum[loan.status.name],
            requested_amount=loan.requested_amount,
            approved_amount=loan.approved_amount,
            current_balance=loan.current_balance,
            principal_balance=loan.principal_balance,
            interest_balance=loan.interest_balance,
            fees_balance=loan.fees_balance,
            currency=loan.currency,
            interest_rate=loan.interest_rate,
            term_months=loan.term_months,
            monthly_payment=loan.monthly_payment,
            application_date=loan.created_at,
            approved_at=loan.approved_at,
            disbursement_date=loan.disbursement_date,
            first_payment_date=loan.first_payment_date,
            maturity_date=loan.maturity_date,
            payments_made=loan.payments_made,
            payments_remaining=loan.payments_remaining,
            next_payment_date=loan.next_payment_date,
            next_payment_amount=loan.next_payment_amount,
            purpose=loan.purpose,
            created_by="SYSTEM"
        )
        
        return db_loan
    
    async def persist_loan(self, loan: Loan, created_by: str = "SYSTEM") -> str:
        """Persist domain loan to database"""
        
        db_loan = self.domain_to_db_loan(loan)
        db_loan = await self.loan_repo.create(db_loan, created_by)
        await self.session.commit()
        
        return db_loan.loan_id


def get_db_integration(session: AsyncSession, tenant_id: str = "DEFAULT") -> DatabaseIntegration:
    """Factory function to get database integration"""
    return DatabaseIntegration(session, tenant_id)

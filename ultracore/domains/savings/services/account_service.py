"""
Account Lifecycle Service
Manages savings account creation, activation, transactions, and closure
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Tuple
from uuid import UUID, uuid4

from ultracore.domains.savings.models.savings_account import (
    SavingsAccount,
    AccountStatus,
)
from ultracore.domains.savings.models.savings_product import SavingsProduct
from ultracore.domains.savings.models.transaction import (
    SavingsTransaction,
    TransactionType,
    TransactionStatus,
)


class AccountService:
    """
    Savings Account Lifecycle Management
    
    Handles all account operations with Australian compliance:
    - Account opening with PDS acceptance
    - TFN collection and validation
    - Deposits and withdrawals
    - Balance management
    - Dormancy tracking
    - Account closure
    """
    
    @staticmethod
    def create_account(
        client_id: UUID,
        product: SavingsProduct,
        account_name: str,
        bsb: str,
        account_number: str,
        tenant_id: UUID,
        initial_deposit: Decimal = Decimal("0.00"),
        tfn: Optional[str] = None,
        tfn_exemption: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> SavingsAccount:
        """
        Create a new savings account
        
        Args:
            client_id: Customer ID
            product: Savings product
            account_name: Name for the account
            bsb: Australian BSB number
            account_number: Account number
            tenant_id: Tenant ID
            initial_deposit: Opening deposit amount
            tfn: Tax File Number (optional)
            tfn_exemption: TFN exemption category (optional)
            created_by: User who created the account
        
        Returns:
            New SavingsAccount instance
        
        Raises:
            ValueError: If initial deposit is below minimum or other validation fails
        """
        # Validate minimum opening balance
        if initial_deposit < product.minimum_opening_balance:
            raise ValueError(
                f"Initial deposit ${initial_deposit} is below minimum "
                f"opening balance ${product.minimum_opening_balance}"
            )
        
        # Calculate withholding tax rate
        withholding_tax_rate = Decimal("47.00") if not (tfn or tfn_exemption) else Decimal("0.00")
        
        # Create account
        account = SavingsAccount(
            client_id=client_id,
            product_id=product.product_id,
            tenant_id=tenant_id,
            account_number=account_number,
            bsb=bsb,
            account_name=account_name,
            account_type=product.product_type,
            balance=initial_deposit,
            available_balance=initial_deposit,
            interest_rate=product.base_interest_rate,
            bonus_interest_rate=product.bonus_interest_rate,
            tfn=tfn,
            tfn_exemption=tfn_exemption,
            withholding_tax_rate=withholding_tax_rate,
            status=AccountStatus.PENDING_APPROVAL,
            created_by=created_by,
        )
        
        return account
    
    @staticmethod
    def approve_account(
        account: SavingsAccount,
        approved_by: UUID
    ) -> SavingsAccount:
        """
        Approve a pending account
        
        Implements maker-checker workflow for account opening.
        """
        if account.status != AccountStatus.PENDING_APPROVAL:
            raise ValueError(f"Account is not pending approval (status: {account.status})")
        
        account.status = AccountStatus.ACTIVE
        account.approved_date = datetime.utcnow()
        account.activated_date = datetime.utcnow()
        account.updated_by = approved_by
        account.updated_at = datetime.utcnow()
        
        return account
    
    @staticmethod
    def make_deposit(
        account: SavingsAccount,
        amount: Decimal,
        source: str,
        reference: str,
        description: str,
        tenant_id: UUID,
        created_by: Optional[UUID] = None
    ) -> Tuple[SavingsAccount, SavingsTransaction]:
        """
        Make a deposit to the account
        
        Args:
            account: Savings account
            amount: Deposit amount
            source: Source of funds
            reference: Transaction reference
            description: Transaction description
            tenant_id: Tenant ID
            created_by: User making the deposit
        
        Returns:
            (updated_account, transaction)
        
        Raises:
            ValueError: If deposit is not allowed
        """
        # Validate deposit
        can_deposit, reason = account.can_deposit(amount)
        if not can_deposit:
            raise ValueError(reason)
        
        # Update balances
        balance_before = account.balance
        account.balance += amount
        account.available_balance += amount
        account.last_transaction_date = datetime.utcnow()
        account.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = SavingsTransaction(
            account_id=account.account_id,
            tenant_id=tenant_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=account.balance,
            status=TransactionStatus.COMPLETED,
            reference_number=reference,
            description=description,
            source_account=source,
            created_by=created_by,
            processed_by=created_by,
            processed_at=datetime.utcnow(),
        )
        
        return account, transaction
    
    @staticmethod
    def make_withdrawal(
        account: SavingsAccount,
        amount: Decimal,
        destination: str,
        reference: str,
        description: str,
        tenant_id: UUID,
        created_by: Optional[UUID] = None
    ) -> Tuple[SavingsAccount, SavingsTransaction]:
        """
        Make a withdrawal from the account
        
        Args:
            account: Savings account
            amount: Withdrawal amount
            destination: Destination of funds
            reference: Transaction reference
            description: Transaction description
            tenant_id: Tenant ID
            created_by: User making the withdrawal
        
        Returns:
            (updated_account, transaction)
        
        Raises:
            ValueError: If withdrawal is not allowed
        """
        # Validate withdrawal
        can_withdraw, reason = account.can_withdraw(amount)
        if not can_withdraw:
            raise ValueError(reason)
        
        # Update balances
        balance_before = account.balance
        account.balance -= amount
        account.available_balance -= amount
        account.last_transaction_date = datetime.utcnow()
        account.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = SavingsTransaction(
            account_id=account.account_id,
            tenant_id=tenant_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=-amount,  # Negative for withdrawals
            balance_before=balance_before,
            balance_after=account.balance,
            status=TransactionStatus.COMPLETED,
            reference_number=reference,
            description=description,
            destination_account=destination,
            created_by=created_by,
            processed_by=created_by,
            processed_at=datetime.utcnow(),
        )
        
        return account, transaction
    
    @staticmethod
    def post_interest(
        account: SavingsAccount,
        gross_interest: Decimal,
        withholding_tax: Decimal,
        reference: str,
        tenant_id: UUID
    ) -> Tuple[SavingsAccount, SavingsTransaction, Optional[SavingsTransaction]]:
        """
        Post accrued interest to account
        
        Args:
            account: Savings account
            gross_interest: Gross interest amount
            withholding_tax: Withholding tax amount
            reference: Transaction reference
            tenant_id: Tenant ID
        
        Returns:
            (updated_account, interest_transaction, tax_transaction)
        """
        net_interest = gross_interest - withholding_tax
        
        # Update account
        balance_before = account.balance
        account.balance += net_interest
        account.available_balance += net_interest
        account.ytd_interest_earned += gross_interest
        account.ytd_withholding_tax += withholding_tax
        account.accrued_interest = Decimal("0.00")  # Reset accrued interest
        account.last_interest_date = date.today()
        account.updated_at = datetime.utcnow()
        
        # Create interest posting transaction
        interest_transaction = SavingsTransaction(
            account_id=account.account_id,
            tenant_id=tenant_id,
            transaction_type=TransactionType.INTEREST_POSTING,
            amount=net_interest,
            balance_before=balance_before,
            balance_after=account.balance,
            status=TransactionStatus.COMPLETED,
            reference_number=reference,
            description=f"Interest posting (gross: ${gross_interest}, tax: ${withholding_tax})",
        )
        
        # Create withholding tax transaction if applicable
        tax_transaction = None
        if withholding_tax > Decimal("0.00"):
            tax_transaction = SavingsTransaction(
                account_id=account.account_id,
                tenant_id=tenant_id,
                transaction_type=TransactionType.WITHHOLDING_TAX,
                amount=-withholding_tax,
                balance_before=balance_before,
                balance_after=balance_before,  # Tax doesn't affect balance (already deducted)
                status=TransactionStatus.COMPLETED,
                reference_number=f"{reference}-TAX",
                description=f"Withholding tax @ {account.withholding_tax_rate}%",
                related_transaction_id=interest_transaction.transaction_id,
            )
        
        return account, interest_transaction, tax_transaction
    
    @staticmethod
    def charge_fee(
        account: SavingsAccount,
        fee_amount: Decimal,
        fee_description: str,
        reference: str,
        tenant_id: UUID
    ) -> Tuple[SavingsAccount, SavingsTransaction]:
        """
        Charge a fee to the account
        
        Args:
            account: Savings account
            fee_amount: Fee amount
            fee_description: Description of the fee
            reference: Transaction reference
            tenant_id: Tenant ID
        
        Returns:
            (updated_account, transaction)
        """
        if fee_amount <= Decimal("0.00"):
            raise ValueError("Fee amount must be positive")
        
        # Update balances
        balance_before = account.balance
        account.balance -= fee_amount
        account.available_balance -= fee_amount
        account.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = SavingsTransaction(
            account_id=account.account_id,
            tenant_id=tenant_id,
            transaction_type=TransactionType.FEE_CHARGE,
            amount=-fee_amount,
            balance_before=balance_before,
            balance_after=account.balance,
            status=TransactionStatus.COMPLETED,
            reference_number=reference,
            description=fee_description,
        )
        
        return account, transaction
    
    @staticmethod
    def close_account(
        account: SavingsAccount,
        closure_reason: str,
        closed_by: UUID
    ) -> SavingsAccount:
        """
        Close a savings account
        
        Args:
            account: Savings account
            closure_reason: Reason for closure
            closed_by: User closing the account
        
        Returns:
            Updated account
        
        Raises:
            ValueError: If account cannot be closed
        """
        if account.status == AccountStatus.CLOSED:
            raise ValueError("Account is already closed")
        
        if account.balance != Decimal("0.00"):
            raise ValueError(
                f"Account has non-zero balance (${account.balance}). "
                "Please withdraw all funds before closing."
            )
        
        account.status = AccountStatus.CLOSED
        account.closure_date = datetime.utcnow()
        account.updated_by = closed_by
        account.updated_at = datetime.utcnow()
        
        return account
    
    @staticmethod
    def update_tfn(
        account: SavingsAccount,
        tfn: str,
        updated_by: UUID
    ) -> SavingsAccount:
        """
        Update TFN for account
        
        This will change withholding tax rate from 47% to 0%.
        """
        account.tfn = tfn
        account.tfn_exemption = None
        account.update_withholding_tax_rate()
        account.updated_by = updated_by
        account.updated_at = datetime.utcnow()
        
        return account
    
    @staticmethod
    def check_dormancy(
        account: SavingsAccount,
        dormancy_period_days: int = 365
    ) -> bool:
        """
        Check if account should be marked as dormant
        
        Returns: True if account should be marked dormant
        """
        if account.status == AccountStatus.DORMANT:
            return False
        
        if account.is_dormant(dormancy_period_days):
            account.status = AccountStatus.DORMANT
            account.dormancy_date = datetime.utcnow()
            account.updated_at = datetime.utcnow()
            return True
        
        return False

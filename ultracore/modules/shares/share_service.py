"""
Share Service
Manages share products, accounts, transactions, and dividends
"""

from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
import uuid

from .models import (
    ShareProduct, ShareAccount, ShareTransaction, DividendDeclaration, DividendPayment,
    CreateShareProductRequest, CreateShareAccountRequest, PurchaseSharesRequest,
    RedeemSharesRequest, DeclareDividendRequest, TransferSharesRequest,
    ShareProductType, ShareAccountStatus, ShareTransactionType, DividendStatus
)


class ShareService:
    """
    Share Service
    
    Manages:
    - Share products
    - Share accounts
    - Share transactions (purchase, sale, redemption, transfer)
    - Dividend declarations and payments
    """
    
    def __init__(self, kafka_producer=None):
        self.products: Dict[str, ShareProduct] = {}
        self.accounts: Dict[str, ShareAccount] = {}
        self.transactions: Dict[str, ShareTransaction] = {}
        self.dividends: Dict[str, DividendDeclaration] = {}
        self.kafka_producer = kafka_producer
        
    # ========================================================================
    # SHARE PRODUCTS
    # ========================================================================
    
    def create_product(
        self,
        request: CreateShareProductRequest
    ) -> ShareProduct:
        """Create a new share product"""
        product_id = f"SPROD-{uuid.uuid4().hex[:12].upper()}"
        
        product = ShareProduct(
            product_id=product_id,
            product_code=request.product_code,
            product_name=request.product_name,
            product_type=request.product_type,
            description=request.description,
            nominal_price=request.nominal_price,
            minimum_shares=request.minimum_shares,
            dividend_rate=request.dividend_rate,
            is_active=True,
            available_from=date.today(),
            created_by=request.created_by
        )
        
        self.products[product_id] = product
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_share_product_created(
                product_id, request.product_code, request.product_name,
                request.product_type.value, request.nominal_price
            )
        
        return product
        
    def get_product(self, product_id: str) -> Optional[ShareProduct]:
        """Get share product by ID"""
        return self.products.get(product_id)
        
    def list_active_products(self) -> List[ShareProduct]:
        """List all active share products"""
        return [p for p in self.products.values() if p.is_active]
        
    # ========================================================================
    # SHARE ACCOUNTS
    # ========================================================================
    
    def create_account(
        self,
        request: CreateShareAccountRequest
    ) -> ShareAccount:
        """Create a new share account with initial purchase"""
        account_id = f"SACC-{uuid.uuid4().hex[:12].upper()}"
        account_number = f"SA-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        product = self.products.get(request.product_id)
        if not product:
            raise ValueError(f"Product {request.product_id} not found")
        
        # Validate minimum shares
        if request.num_shares < product.minimum_shares:
            raise ValueError(f"Minimum {product.minimum_shares} shares required")
        
        # Calculate values
        total_amount = request.num_shares * request.price_per_share
        total_nominal_value = request.num_shares * product.nominal_price
        
        account = ShareAccount(
            account_id=account_id,
            account_number=account_number,
            client_id=request.client_id,
            shareholder_name="",  # Would be fetched from client service
            product_id=request.product_id,
            product_code=product.product_code,
            product_name=product.product_name,
            total_shares=request.num_shares,
            shares_purchased=request.num_shares,
            nominal_value_per_share=product.nominal_price,
            total_nominal_value=total_nominal_value,
            total_amount_paid=total_amount,
            average_purchase_price=request.price_per_share,
            status=ShareAccountStatus.ACTIVE,
            account_opened_date=date.today(),
            created_by=request.created_by
        )
        
        self.accounts[account_id] = account
        
        # Create initial purchase transaction
        self._create_transaction(
            account_id=account_id,
            transaction_type=ShareTransactionType.PURCHASE,
            num_shares=request.num_shares,
            price_per_share=request.price_per_share,
            created_by=request.created_by
        )
        
        # Update product issued shares
        product.total_shares_issued += request.num_shares
        product.total_shares_outstanding += request.num_shares
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_share_account_created(
                account_id, account_number, request.client_id,
                request.product_id, request.num_shares
            )
        
        return account
        
    def get_account(self, account_id: str) -> Optional[ShareAccount]:
        """Get share account by ID"""
        return self.accounts.get(account_id)
        
    def list_accounts_by_client(self, client_id: str) -> List[ShareAccount]:
        """List all share accounts for a client"""
        return [a for a in self.accounts.values() if a.client_id == client_id]
        
    # ========================================================================
    # SHARE TRANSACTIONS
    # ========================================================================
    
    def purchase_shares(
        self,
        request: PurchaseSharesRequest
    ) -> ShareTransaction:
        """Purchase additional shares"""
        account = self.accounts.get(request.account_id)
        if not account:
            raise ValueError(f"Account {request.account_id} not found")
        
        if account.status != ShareAccountStatus.ACTIVE:
            raise ValueError(f"Account is not active")
        
        # Create transaction
        transaction = self._create_transaction(
            account_id=request.account_id,
            transaction_type=ShareTransactionType.PURCHASE,
            num_shares=request.num_shares,
            price_per_share=request.price_per_share,
            transaction_date=request.transaction_date,
            created_by=request.created_by
        )
        
        # Update account
        account.total_shares += request.num_shares
        account.shares_purchased += request.num_shares
        account.total_amount_paid += transaction.total_amount
        account.average_purchase_price = account.total_amount_paid / account.total_shares
        account.total_nominal_value = account.total_shares * account.nominal_value_per_share
        account.updated_at = datetime.now(timezone.utc)
        
        # Update product
        product = self.products.get(account.product_id)
        if product:
            product.total_shares_issued += request.num_shares
            product.total_shares_outstanding += request.num_shares
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_shares_purchased(
                request.account_id, request.num_shares, request.price_per_share
            )
        
        return transaction
        
    def redeem_shares(
        self,
        request: RedeemSharesRequest
    ) -> ShareTransaction:
        """Redeem shares"""
        account = self.accounts.get(request.account_id)
        if not account:
            raise ValueError(f"Account {request.account_id} not found")
        
        product = self.products.get(account.product_id)
        if not product or not product.is_redeemable:
            raise ValueError("Shares are not redeemable")
        
        if account.total_shares < request.num_shares:
            raise ValueError("Insufficient shares")
        
        if account.is_locked:
            raise ValueError("Account is locked")
        
        # Create transaction
        transaction = self._create_transaction(
            account_id=request.account_id,
            transaction_type=ShareTransactionType.REDEMPTION,
            num_shares=request.num_shares,
            price_per_share=request.redemption_price,
            transaction_date=request.transaction_date,
            created_by=request.created_by
        )
        
        # Update account
        account.total_shares -= request.num_shares
        account.shares_redeemed += request.num_shares
        account.total_nominal_value = account.total_shares * account.nominal_value_per_share
        account.updated_at = datetime.now(timezone.utc)
        
        # Close account if no shares remaining
        if account.total_shares == 0:
            account.status = ShareAccountStatus.CLOSED
            account.account_closed_date = date.today()
        
        # Update product
        if product:
            product.total_shares_outstanding -= request.num_shares
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_shares_redeemed(
                request.account_id, request.num_shares, request.redemption_price
            )
        
        return transaction
        
    def transfer_shares(
        self,
        request: TransferSharesRequest
    ) -> tuple[ShareTransaction, ShareTransaction]:
        """Transfer shares between accounts"""
        from_account = self.accounts.get(request.from_account_id)
        to_account = self.accounts.get(request.to_account_id)
        
        if not from_account or not to_account:
            raise ValueError("Invalid account IDs")
        
        if from_account.product_id != to_account.product_id:
            raise ValueError("Accounts must be for same product")
        
        if from_account.total_shares < request.num_shares:
            raise ValueError("Insufficient shares")
        
        if from_account.is_locked:
            raise ValueError("From account is locked")
        
        # Create transfer-out transaction
        txn_out = self._create_transaction(
            account_id=request.from_account_id,
            transaction_type=ShareTransactionType.TRANSFER,
            num_shares=-request.num_shares,  # Negative for outgoing
            price_per_share=request.transfer_price,
            transaction_date=request.transaction_date,
            created_by=request.created_by
        )
        txn_out.transfer_to_account_id = request.to_account_id
        
        # Create transfer-in transaction
        txn_in = self._create_transaction(
            account_id=request.to_account_id,
            transaction_type=ShareTransactionType.TRANSFER,
            num_shares=request.num_shares,
            price_per_share=request.transfer_price,
            transaction_date=request.transaction_date,
            created_by=request.created_by
        )
        txn_in.transfer_from_account_id = request.from_account_id
        
        # Update from account
        from_account.total_shares -= request.num_shares
        from_account.shares_transferred_out += request.num_shares
        from_account.total_nominal_value = from_account.total_shares * from_account.nominal_value_per_share
        from_account.updated_at = datetime.now(timezone.utc)
        
        # Update to account
        to_account.total_shares += request.num_shares
        to_account.shares_transferred_in += request.num_shares
        to_account.total_nominal_value = to_account.total_shares * to_account.nominal_value_per_share
        to_account.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_shares_transferred(
                request.from_account_id, request.to_account_id,
                request.num_shares, request.transfer_price
            )
        
        return (txn_out, txn_in)
        
    def _create_transaction(
        self,
        account_id: str,
        transaction_type: ShareTransactionType,
        num_shares: int,
        price_per_share: Decimal,
        transaction_date: Optional[date] = None,
        created_by: str = "system"
    ) -> ShareTransaction:
        """Create a share transaction"""
        transaction_id = f"STXN-{uuid.uuid4().hex[:12].upper()}"
        
        total_amount = abs(num_shares) * price_per_share
        
        transaction = ShareTransaction(
            transaction_id=transaction_id,
            account_id=account_id,
            transaction_type=transaction_type,
            transaction_date=transaction_date or date.today(),
            num_shares=num_shares,
            price_per_share=price_per_share,
            total_amount=total_amount,
            created_by=created_by
        )
        
        self.transactions[transaction_id] = transaction
        
        return transaction
        
    # ========================================================================
    # DIVIDENDS
    # ========================================================================
    
    def declare_dividend(
        self,
        request: DeclareDividendRequest
    ) -> DividendDeclaration:
        """Declare dividend for a share product"""
        product = self.products.get(request.product_id)
        if not product:
            raise ValueError(f"Product {request.product_id} not found")
        
        dividend_id = f"DIV-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate total dividend amount
        total_amount = request.dividend_amount_per_share * product.total_shares_outstanding
        
        dividend = DividendDeclaration(
            dividend_id=dividend_id,
            product_id=request.product_id,
            dividend_amount_per_share=request.dividend_amount_per_share,
            total_dividend_amount=total_amount,
            declaration_date=date.today(),
            record_date=request.record_date,
            payment_date=request.payment_date,
            status=DividendStatus.DECLARED,
            created_by=request.created_by
        )
        
        self.dividends[dividend_id] = dividend
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_dividend_declared(
                dividend_id, request.product_id,
                request.dividend_amount_per_share, total_amount
            )
        
        return dividend
        
    def pay_dividends(
        self,
        dividend_id: str,
        approved_by: str
    ) -> List[DividendPayment]:
        """Pay dividends to all eligible shareholders"""
        dividend = self.dividends.get(dividend_id)
        if not dividend:
            raise ValueError(f"Dividend {dividend_id} not found")
        
        if dividend.status != DividendStatus.DECLARED:
            raise ValueError("Dividend must be in DECLARED status")
        
        # Approve dividend
        dividend.status = DividendStatus.APPROVED
        dividend.approved_by = approved_by
        dividend.approved_at = datetime.now(timezone.utc)
        
        # Get all accounts for this product
        eligible_accounts = [
            a for a in self.accounts.values()
            if a.product_id == dividend.product_id and a.total_shares > 0
        ]
        
        payments = []
        total_paid = Decimal("0")
        
        for account in eligible_accounts:
            payment_id = f"DPAY-{uuid.uuid4().hex[:12].upper()}"
            
            total_amount = account.total_shares * dividend.dividend_amount_per_share
            withholding_tax = total_amount * Decimal("0.30")  # 30% withholding tax
            net_amount = total_amount - withholding_tax
            
            payment = DividendPayment(
                payment_id=payment_id,
                dividend_id=dividend_id,
                account_id=account.account_id,
                num_shares=account.total_shares,
                amount_per_share=dividend.dividend_amount_per_share,
                total_amount=total_amount,
                withholding_tax=withholding_tax,
                net_amount=net_amount,
                payment_date=dividend.payment_date
            )
            
            payments.append(payment)
            
            # Update account
            account.total_dividends_paid += total_amount
            account.updated_at = datetime.now(timezone.utc)
            
            total_paid += total_amount
        
        # Update dividend
        dividend.status = DividendStatus.PAID
        dividend.total_paid = total_paid
        dividend.num_shareholders_paid = len(payments)
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_dividends_paid(
                dividend_id, len(payments), total_paid
            )
        
        return payments

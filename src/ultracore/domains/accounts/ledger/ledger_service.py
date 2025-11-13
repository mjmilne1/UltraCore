"""UltraLedger Service - Bitemporal Event-Sourced Ledger"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from ultracore.ledger.ultraledger import UltraLedger
from ultracore.ledger.models import (
    LedgerEntry,
    LedgerAccount,
    TransactionTime,
    ValidTime
)


class UltraLedgerService:
    """
    Integration with UltraLedger - Bitemporal Event-Sourced Ledger.
    
    UltraLedger Features:
    - Double-entry bookkeeping
    - Bitemporal data model (transaction time + valid time)
    - Immutable audit trail
    - Point-in-time balance queries
    - Corrections without deletion
    - Regulatory compliance (APRA, ASIC, AUSTRAC)
    
    Account Structure in UltraLedger:
    
    Chart of Accounts:
    1000 - Assets
      1100 - Current Assets
        1110 - Customer Transactional Accounts
        1120 - Customer Savings Accounts
        1130 - Customer Term Deposits
      1200 - Fixed Assets
    
    2000 - Liabilities
      2100 - Customer Deposits (contra-asset)
      2200 - Borrowings
    
    3000 - Equity
      3100 - Share Capital
      3200 - Retained Earnings
    
    4000 - Income
      4100 - Interest Income
      4200 - Fee Income
    
    5000 - Expenses
      5100 - Interest Expense
      5200 - Operating Expenses
    """
    
    def __init__(self, ultraledger: UltraLedger):
        self.ledger = ultraledger
    
    async def create_account(
        self,
        account_id: str,
        customer_id: str,
        account_type: str,
        account_name: str,
        bsb: str,
        account_number: str,
        currency: str = "AUD"
    ) -> LedgerAccount:
        """
        Create ledger account for banking account.
        
        Creates two ledger accounts:
        1. Asset account (bank's perspective): Customer Account Receivable
        2. Liability account: Customer Deposit Payable
        
        This is because customer deposits are liabilities to the bank!
        """
        
        # Determine ledger account code
        if account_type == "transactional":
            asset_code = "1110"  # Customer Transactional Accounts
        elif account_type == "savings":
            asset_code = "1120"  # Customer Savings Accounts
        elif account_type == "term_deposit":
            asset_code = "1130"  # Customer Term Deposits
        else:
            asset_code = "1110"
        
        liability_code = "2100"  # Customer Deposits
        
        # Create asset account (bank's view of customer funds)
        asset_account = await self.ledger.create_account(
            account_code=f"{asset_code}-{account_id}",
            account_name=f"{account_name} (Asset)",
            account_type="asset",
            currency=currency,
            metadata={
                "account_id": account_id,
                "customer_id": customer_id,
                "bsb": bsb,
                "account_number": account_number,
                "banking_account_type": account_type
            }
        )
        
        # Create liability account (bank's obligation to customer)
        liability_account = await self.ledger.create_account(
            account_code=f"{liability_code}-{account_id}",
            account_name=f"{account_name} (Liability)",
            account_type="liability",
            currency=currency,
            metadata={
                "account_id": account_id,
                "customer_id": customer_id,
                "contra_account": asset_account.account_code
            }
        )
        
        return asset_account
    
    async def record_deposit(
        self,
        account_id: str,
        amount: Decimal,
        description: str,
        transaction_time: Optional[datetime] = None,
        valid_time: Optional[datetime] = None,
        source_account: Optional[str] = None,
        reference: Optional[str] = None
    ) -> LedgerEntry:
        """
        Record deposit to customer account.
        
        Double-entry:
        - DEBIT: Cash/Source Account (asset increases)
        - CREDIT: Customer Deposit Account (liability increases)
        
        Customer sees their balance increase.
        Bank sees liability increase (owes customer more).
        """
        
        transaction_time = transaction_time or datetime.now(timezone.utc)
        valid_time = valid_time or transaction_time
        
        entry_id = f"DEP-{uuid.uuid4().hex[:12].upper()}"
        
        # Get account codes
        asset_account = f"1110-{account_id}"  # Simplified
        liability_account = f"2100-{account_id}"
        
        # Source of funds
        if source_account:
            debit_account = source_account
        else:
            debit_account = "1000-CASH"  # Cash account
        
        # Create ledger entry
        entry = await self.ledger.create_entry(
            entry_id=entry_id,
            transaction_date=transaction_time,
            valid_date=valid_time,
            description=description,
            reference=reference,
            lines=[
                {
                    "account_code": debit_account,
                    "debit": amount,
                    "credit": Decimal("0.00"),
                    "description": f"Deposit to {account_id}"
                },
                {
                    "account_code": liability_account,
                    "debit": Decimal("0.00"),
                    "credit": amount,
                    "description": f"Customer deposit credited"
                }
            ],
            metadata={
                "account_id": account_id,
                "transaction_type": "deposit",
                "amount": str(amount)
            }
        )
        
        return entry
    
    async def record_withdrawal(
        self,
        account_id: str,
        amount: Decimal,
        description: str,
        transaction_time: Optional[datetime] = None,
        valid_time: Optional[datetime] = None,
        destination_account: Optional[str] = None,
        reference: Optional[str] = None
    ) -> LedgerEntry:
        """
        Record withdrawal from customer account.
        
        Double-entry:
        - DEBIT: Customer Deposit Account (liability decreases)
        - CREDIT: Cash/Destination Account (asset decreases)
        
        Customer sees their balance decrease.
        Bank sees liability decrease (owes customer less).
        """
        
        transaction_time = transaction_time or datetime.now(timezone.utc)
        valid_time = valid_time or transaction_time
        
        entry_id = f"WDL-{uuid.uuid4().hex[:12].upper()}"
        
        liability_account = f"2100-{account_id}"
        
        if destination_account:
            credit_account = destination_account
        else:
            credit_account = "1000-CASH"
        
        entry = await self.ledger.create_entry(
            entry_id=entry_id,
            transaction_date=transaction_time,
            valid_date=valid_time,
            description=description,
            reference=reference,
            lines=[
                {
                    "account_code": liability_account,
                    "debit": amount,
                    "credit": Decimal("0.00"),
                    "description": f"Withdrawal from {account_id}"
                },
                {
                    "account_code": credit_account,
                    "debit": Decimal("0.00"),
                    "credit": amount,
                    "description": f"Cash withdrawn"
                }
            ],
            metadata={
                "account_id": account_id,
                "transaction_type": "withdrawal",
                "amount": str(amount)
            }
        )
        
        return entry
    
    async def record_transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        description: str,
        transaction_time: Optional[datetime] = None,
        valid_time: Optional[datetime] = None,
        reference: Optional[str] = None
    ) -> LedgerEntry:
        """
        Record transfer between accounts.
        
        Double-entry (simplified view):
        - DEBIT: To Account (liability increases)
        - CREDIT: From Account (liability decreases)
        """
        
        transaction_time = transaction_time or datetime.now(timezone.utc)
        valid_time = valid_time or transaction_time
        
        entry_id = f"TRF-{uuid.uuid4().hex[:12].upper()}"
        
        from_liability = f"2100-{from_account_id}"
        to_liability = f"2100-{to_account_id}"
        
        entry = await self.ledger.create_entry(
            entry_id=entry_id,
            transaction_date=transaction_time,
            valid_date=valid_time,
            description=description,
            reference=reference,
            lines=[
                {
                    "account_code": from_liability,
                    "debit": amount,
                    "credit": Decimal("0.00"),
                    "description": f"Transfer from {from_account_id}"
                },
                {
                    "account_code": to_liability,
                    "debit": Decimal("0.00"),
                    "credit": amount,
                    "description": f"Transfer to {to_account_id}"
                }
            ],
            metadata={
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "transaction_type": "transfer",
                "amount": str(amount)
            }
        )
        
        return entry
    
    async def get_balance(
        self,
        account_id: str,
        as_of_transaction_time: Optional[datetime] = None,
        as_of_valid_time: Optional[datetime] = None
    ) -> Decimal:
        """
        Get account balance at specific point in time.
        
        Bitemporal querying:
        - transaction_time: When we knew about transactions
        - valid_time: When transactions were effective
        
        This allows for corrections, backdating, and audit queries.
        """
        
        liability_account = f"2100-{account_id}"
        
        balance = await self.ledger.get_account_balance(
            account_code=liability_account,
            as_of_transaction_time=as_of_transaction_time,
            as_of_valid_time=as_of_valid_time
        )
        
        # Liability accounts have credit balance
        # Customer sees this as positive balance
        return balance.credit_balance - balance.debit_balance
    
    async def get_transaction_history(
        self,
        account_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LedgerEntry]:
        """Get transaction history for account."""
        
        liability_account = f"2100-{account_id}"
        
        entries = await self.ledger.get_account_entries(
            account_code=liability_account,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
        
        return entries

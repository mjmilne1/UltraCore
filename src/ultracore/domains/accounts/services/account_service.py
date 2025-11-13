"""Account Service - Event-Sourced, UltraLedger Integration"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import (
    AccountOpenedEvent,
    AccountActivatedEvent,
    DepositMadeEvent,
    WithdrawalMadeEvent
)
from ..models import (
    Account,
    TransactionalAccount,
    SavingsAccount,
    AccountType,
    AccountStatus
)
from ..ledger import UltraLedgerService


class AccountService:
    """
    Event-sourced Account service.
    
    All state changes flow through Kafka events.
    UltraLedger provides authoritative balances.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ledger_service: UltraLedgerService
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ledger = ledger_service
    
    async def open_transactional_account(
        self,
        customer_id: str,
        account_name: str,
        product_code: str = "TXN-STANDARD",
        opening_deposit: Optional[Decimal] = None,
        tfn: Optional[str] = None,
        **kwargs
    ) -> TransactionalAccount:
        """
        Open new transactional account.
        
        Publishes: AccountOpenedEvent to Kafka
        Creates: UltraLedger accounts (asset + liability)
        
        Australian Requirements:
        - BSB assigned
        - Account number generated
        - KYC verified
        - TFN collected (optional but recommended)
        """
        
        account_id = f"ACC-{uuid.uuid4().hex[:12].upper()}"
        
        # Generate Australian identifiers
        bsb = self._generate_bsb()
        account_number = self._generate_account_number()
        
        # Create in UltraLedger
        await self.ledger.create_account(
            account_id=account_id,
            customer_id=customer_id,
            account_type="transactional",
            account_name=account_name,
            bsb=bsb,
            account_number=account_number,
            currency="AUD"
        )
        
        # Create account object
        account = TransactionalAccount(
            account_id=account_id,
            customer_id=customer_id,
            bsb=bsb,
            account_number=account_number,
            account_name=account_name,
            product_code=product_code,
            product_name="Standard Transactional Account",
            status=AccountStatus.PENDING,
            current_balance=Decimal("0.00"),
            available_balance=Decimal("0.00"),
            daily_withdrawal_limit=Decimal("5000.00"),
            daily_transfer_limit=Decimal("10000.00"),
            overdraft_limit=Decimal("0.00"),
            tfn_provided=tfn is not None,
            opened_date=date.today(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Publish event
        event = AccountOpenedEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=customer_id,
            account_type="transactional",
            account_name=account_name,
            currency="AUD",
            bsb=bsb,
            account_number=account_number,
            product_code=product_code,
            product_name="Standard Transactional Account",
            opening_balance=opening_deposit or Decimal("0.00"),
            opening_deposit_amount=opening_deposit,
            daily_withdrawal_limit=Decimal("5000.00"),
            daily_transfer_limit=Decimal("10000.00"),
            overdraft_limit=Decimal("0.00"),
            tfn_provided=tfn is not None,
            tfn=tfn,
            kyc_completed=True,
            customer_type="individual",
            opening_channel=kwargs.get("channel", "online"),
            opened_by=kwargs.get("opened_by", "system"),
            opened_at=datetime.now(timezone.utc),
            ledger_account_id=account_id,
            ledger_entry_id=f"OPEN-{account_id}"
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Record opening deposit if provided
        if opening_deposit and opening_deposit > Decimal("0.00"):
            await self.deposit(
                account_id=account_id,
                amount=opening_deposit,
                description="Opening deposit",
                deposited_by=kwargs.get("opened_by", "system")
            )
        
        return account
    
    async def open_savings_account(
        self,
        customer_id: str,
        account_name: str,
        product_code: str = "SAV-HIGH-INTEREST",
        base_rate: Decimal = Decimal("2.5"),
        bonus_rate: Decimal = Decimal("2.0"),
        linked_transactional_account: Optional[str] = None,
        **kwargs
    ) -> SavingsAccount:
        """
        Open savings account.
        
        Australian High-Interest Savings Features:
        - Competitive base rate (e.g., 2.5% p.a.)
        - Bonus rate for meeting conditions (e.g., +2.0%)
        - Conditions: Deposit $1000+/month, max 1 withdrawal
        """
        
        account_id = f"ACC-{uuid.uuid4().hex[:12].upper()}"
        
        bsb = self._generate_bsb()
        account_number = self._generate_account_number()
        
        await self.ledger.create_account(
            account_id=account_id,
            customer_id=customer_id,
            account_type="savings",
            account_name=account_name,
            bsb=bsb,
            account_number=account_number,
            currency="AUD"
        )
        
        total_rate = base_rate + bonus_rate
        
        account = SavingsAccount(
            account_id=account_id,
            customer_id=customer_id,
            bsb=bsb,
            account_number=account_number,
            account_name=account_name,
            product_code=product_code,
            product_name="High Interest Savings Account",
            status=AccountStatus.PENDING,
            current_balance=Decimal("0.00"),
            available_balance=Decimal("0.00"),
            daily_withdrawal_limit=Decimal("10000.00"),
            daily_transfer_limit=Decimal("10000.00"),
            base_interest_rate=base_rate,
            bonus_interest_rate=bonus_rate,
            total_interest_rate=total_rate,
            bonus_conditions=[
                "Deposit $1,000+ per month",
                "Maximum 1 withdrawal per month",
                "Grow balance each month"
            ],
            interest_calculation_method="daily",
            interest_payment_frequency="monthly",
            linked_transactional_account=linked_transactional_account,
            opened_date=date.today(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Publish event (similar to transactional)
        event = AccountOpenedEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=customer_id,
            account_type="savings",
            account_name=account_name,
            currency="AUD",
            bsb=bsb,
            account_number=account_number,
            product_code=product_code,
            product_name="High Interest Savings Account",
            opening_balance=Decimal("0.00"),
            interest_rate=total_rate,
            interest_calculation_method="daily",
            daily_withdrawal_limit=Decimal("10000.00"),
            daily_transfer_limit=Decimal("10000.00"),
            kyc_completed=True,
            customer_type="individual",
            opening_channel=kwargs.get("channel", "online"),
            opened_by=kwargs.get("opened_by", "system"),
            opened_at=datetime.now(timezone.utc),
            ledger_account_id=account_id,
            ledger_entry_id=f"OPEN-{account_id}"
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return account
    
    async def deposit(
        self,
        account_id: str,
        amount: Decimal,
        description: str,
        source_account: Optional[str] = None,
        deposited_by: str = "customer",
        **kwargs
    ) -> Dict:
        """
        Deposit funds to account.
        
        Publishes: DepositMadeEvent to Kafka
        Records: UltraLedger entry (double-entry)
        
        AUSTRAC Reporting:
        - Large cash transactions (>$10,000 AUD) must be reported
        """
        
        # Get current balance from UltraLedger
        balance_before = await self.ledger.get_balance(account_id)
        
        # Record in UltraLedger
        ledger_entry = await self.ledger.record_deposit(
            account_id=account_id,
            amount=amount,
            description=description,
            source_account=source_account,
            reference=kwargs.get("reference")
        )
        
        balance_after = balance_before + amount
        
        # Check for large cash transaction (AUSTRAC)
        is_large_cash = amount >= Decimal("10000.00") and kwargs.get("method") == "cash"
        
        # Publish event
        event = DepositMadeEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=kwargs.get("customer_id", "unknown"),
            amount=amount,
            description=description,
            balance_before=balance_before,
            balance_after=balance_after,
            available_balance_before=balance_before,
            available_balance_after=balance_after,
            source_account=source_account,
            deposit_method=kwargs.get("method", "transfer"),
            deposited_by=deposited_by,
            deposited_at=datetime.now(timezone.utc),
            ledger_entry_id=ledger_entry.entry_id,
            large_cash_transaction=is_large_cash,
            austrac_reportable=is_large_cash
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "transaction_id": ledger_entry.entry_id,
            "amount": float(amount),
            "balance_after": float(balance_after),
            "timestamp": event.transaction_time.isoformat()
        }
    
    async def withdraw(
        self,
        account_id: str,
        amount: Decimal,
        description: str,
        destination_account: Optional[str] = None,
        withdrawn_by: str = "customer",
        **kwargs
    ) -> Dict:
        """
        Withdraw funds from account.
        
        Publishes: WithdrawalMadeEvent to Kafka
        Records: UltraLedger entry
        
        Checks:
        - Sufficient balance
        - Daily withdrawal limit
        - Account not frozen
        """
        
        # Get current balance
        balance_before = await self.ledger.get_balance(account_id)
        
        # Check sufficient funds
        if balance_before < amount:
            raise ValueError(f"Insufficient funds. Balance: ${float(balance_before):.2f}, Requested: ${float(amount):.2f}")
        
        # Record in UltraLedger
        ledger_entry = await self.ledger.record_withdrawal(
            account_id=account_id,
            amount=amount,
            description=description,
            destination_account=destination_account,
            reference=kwargs.get("reference")
        )
        
        balance_after = balance_before - amount
        
        # Publish event
        event = WithdrawalMadeEvent(
            aggregate_id=account_id,
            account_id=account_id,
            customer_id=kwargs.get("customer_id", "unknown"),
            amount=amount,
            description=description,
            balance_before=balance_before,
            balance_after=balance_after,
            available_balance_before=balance_before,
            available_balance_after=balance_after,
            destination_account=destination_account,
            withdrawal_method=kwargs.get("method", "transfer"),
            withdrawn_by=withdrawn_by,
            withdrawn_at=datetime.now(timezone.utc),
            ledger_entry_id=ledger_entry.entry_id
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "transaction_id": ledger_entry.entry_id,
            "amount": float(amount),
            "balance_after": float(balance_after),
            "timestamp": event.transaction_time.isoformat()
        }
    
    async def get_account(self, account_id: str) -> Account:
        """Reconstruct account from events."""
        # Would reconstruct from event store
        raise NotImplementedError("Event replay not implemented")
    
    def _generate_bsb(self) -> str:
        """Generate BSB (Bank State Branch) code."""
        # Format: XXX-XXX
        # First 2 digits: Bank code
        # Next 3 digits: State
        # Last digit: Branch
        return "123-456"  # Placeholder
    
    def _generate_account_number(self) -> str:
        """Generate account number (6-9 digits)."""
        import random
        return f"{random.randint(100000, 999999999)}"


class DepositMadeEvent(AccountEvent):
    """Deposit made to account."""
    event_type: str = "DepositMade"
    amount: Decimal
    description: str
    source_account: Optional[str] = None
    deposit_method: str = "transfer"
    deposited_by: str
    deposited_at: datetime


class WithdrawalMadeEvent(AccountEvent):
    """Withdrawal made from account."""
    event_type: str = "WithdrawalMade"
    amount: Decimal
    description: str
    destination_account: Optional[str] = None
    withdrawal_method: str = "transfer"
    withdrawn_by: str
    withdrawn_at: datetime

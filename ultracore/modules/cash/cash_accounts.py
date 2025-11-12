"""
Cash Management Account (CMA) Module - Event Sourced
Complete cash account management with event sourcing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
import uuid

class AccountType(str, Enum):
    """Cash account types"""
    OPERATING = "operating"
    SETTLEMENT = "settlement"
    CUSTODY = "custody"
    TRUST = "trust"
    INTEREST_BEARING = "interest_bearing"

class TransactionType(str, Enum):
    """Cash transaction types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    INTEREST_CREDIT = "interest_credit"
    FEE_DEBIT = "fee_debit"
    TRADE_SETTLEMENT = "trade_settlement"
    DIVIDEND = "dividend"
    REVERSAL = "reversal"

class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class PaymentMethod(str, Enum):
    """Payment methods"""
    NPP = "npp"  # New Payments Platform (instant)
    BPAY = "bpay"
    DIRECT_CREDIT = "direct_credit"
    DIRECT_DEBIT = "direct_debit"
    INTERNAL_TRANSFER = "internal_transfer"
    CARD = "card"

# ============================================================================
# EVENT SOURCING - CASH ACCOUNT EVENTS
# ============================================================================

class CashAccountEvent:
    """Base class for cash account events"""
    
    def __init__(self, account_id: str, event_id: str = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.account_id = account_id
        self.timestamp = datetime.utcnow()
        self.event_type = self.__class__.__name__

class AccountCreatedEvent(CashAccountEvent):
    """Account created event"""
    
    def __init__(
        self,
        account_id: str,
        client_id: str,
        account_type: AccountType,
        currency: str,
        interest_rate: float
    ):
        super().__init__(account_id)
        self.client_id = client_id
        self.account_type = account_type
        self.currency = currency
        self.interest_rate = interest_rate

class DepositInitiatedEvent(CashAccountEvent):
    """Deposit initiated event"""
    
    def __init__(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        reference: str
    ):
        super().__init__(account_id)
        self.transaction_id = transaction_id
        self.amount = amount
        self.payment_method = payment_method
        self.reference = reference

class DepositCompletedEvent(CashAccountEvent):
    """Deposit completed event"""
    
    def __init__(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal
    ):
        super().__init__(account_id)
        self.transaction_id = transaction_id
        self.amount = amount

class WithdrawalInitiatedEvent(CashAccountEvent):
    """Withdrawal initiated event"""
    
    def __init__(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        destination: str
    ):
        super().__init__(account_id)
        self.transaction_id = transaction_id
        self.amount = amount
        self.payment_method = payment_method
        self.destination = destination

class WithdrawalCompletedEvent(CashAccountEvent):
    """Withdrawal completed event"""
    
    def __init__(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal
    ):
        super().__init__(account_id)
        self.transaction_id = transaction_id
        self.amount = amount

class BalanceReservedEvent(CashAccountEvent):
    """Balance reserved event (for trade settlement)"""
    
    def __init__(
        self,
        account_id: str,
        reservation_id: str,
        amount: Decimal,
        reason: str
    ):
        super().__init__(account_id)
        self.reservation_id = reservation_id
        self.amount = amount
        self.reason = reason

class BalanceReleasedEvent(CashAccountEvent):
    """Balance released event"""
    
    def __init__(
        self,
        account_id: str,
        reservation_id: str,
        amount: Decimal
    ):
        super().__init__(account_id)
        self.reservation_id = reservation_id
        self.amount = amount

class InterestCreditedEvent(CashAccountEvent):
    """Interest credited event"""
    
    def __init__(
        self,
        account_id: str,
        amount: Decimal,
        period_start: datetime,
        period_end: datetime,
        interest_rate: float
    ):
        super().__init__(account_id)
        self.amount = amount
        self.period_start = period_start
        self.period_end = period_end
        self.interest_rate = interest_rate

class FeeDebitedEvent(CashAccountEvent):
    """Fee debited event"""
    
    def __init__(
        self,
        account_id: str,
        fee_id: str,
        amount: Decimal,
        fee_type: str,
        description: str
    ):
        super().__init__(account_id)
        self.fee_id = fee_id
        self.amount = amount
        self.fee_type = fee_type
        self.description = description

# ============================================================================
# CASH ACCOUNT - EVENT SOURCED
# ============================================================================

class CashAccount:
    """
    Event-Sourced Cash Management Account
    
    All state changes are recorded as events.
    Current state is rebuilt from event history.
    """
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.version = 0
        
        # Event store
        self.events: List[CashAccountEvent] = []
        
        # Current state (derived from events)
        self.client_id = None
        self.account_type = None
        self.currency = None
        self.interest_rate = 0.0
        
        # Balances
        self.available_balance = Decimal("0.00")
        self.ledger_balance = Decimal("0.00")
        self.reserved_balance = Decimal("0.00")
        
        # Metadata
        self.created_at = None
        self.is_active = True
        
    def apply_event(self, event: CashAccountEvent):
        """Apply an event to update state"""
        
        if isinstance(event, AccountCreatedEvent):
            self.client_id = event.client_id
            self.account_type = event.account_type
            self.currency = event.currency
            self.interest_rate = event.interest_rate
            self.created_at = event.timestamp
            
        elif isinstance(event, DepositCompletedEvent):
            self.available_balance += event.amount
            self.ledger_balance += event.amount
            
        elif isinstance(event, WithdrawalCompletedEvent):
            self.available_balance -= event.amount
            self.ledger_balance -= event.amount
            
        elif isinstance(event, BalanceReservedEvent):
            self.available_balance -= event.amount
            self.reserved_balance += event.amount
            
        elif isinstance(event, BalanceReleasedEvent):
            self.available_balance += event.amount
            self.reserved_balance -= event.amount
            
        elif isinstance(event, InterestCreditedEvent):
            self.available_balance += event.amount
            self.ledger_balance += event.amount
            
        elif isinstance(event, FeeDebitedEvent):
            self.available_balance -= event.amount
            self.ledger_balance -= event.amount
        
        # Add event to history
        self.events.append(event)
        self.version += 1
    
    def get_balance_snapshot(self) -> Dict[str, Any]:
        """Get current balance snapshot"""
        
        return {
            "account_id": self.account_id,
            "available_balance": float(self.available_balance),
            "ledger_balance": float(self.ledger_balance),
            "reserved_balance": float(self.reserved_balance),
            "currency": self.currency,
            "as_of": datetime.utcnow().isoformat()
        }
    
    def rebuild_from_events(self, events: List[CashAccountEvent]):
        """Rebuild state from event history"""
        
        for event in sorted(events, key=lambda e: e.timestamp):
            self.apply_event(event)

# ============================================================================
# CASH ACCOUNT SERVICE
# ============================================================================

class CashAccountService:
    """
    Cash Account Service
    
    Manages cash accounts with:
    - Event sourcing
    - CQRS pattern
    - Event streaming to Kafka
    """
    
    def __init__(self):
        self.accounts: Dict[str, CashAccount] = {}
        self.event_store: List[CashAccountEvent] = []
        
    def create_account(
        self,
        client_id: str,
        account_type: AccountType,
        currency: str = "AUD",
        interest_rate: float = 0.0
    ) -> CashAccount:
        """Create a new cash account"""
        
        account_id = f"CMA-{len(self.accounts) + 1:08d}"
        
        # Create event
        event = AccountCreatedEvent(
            account_id=account_id,
            client_id=client_id,
            account_type=account_type,
            currency=currency,
            interest_rate=interest_rate
        )
        
        # Create account and apply event
        account = CashAccount(account_id)
        account.apply_event(event)
        
        # Store account
        self.accounts[account_id] = account
        self.event_store.append(event)
        
        return account
    
    def initiate_deposit(
        self,
        account_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        reference: str
    ) -> str:
        """Initiate a deposit"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        transaction_id = f"DEP-{uuid.uuid4().hex[:12].upper()}"
        
        # Create event
        event = DepositInitiatedEvent(
            account_id=account_id,
            transaction_id=transaction_id,
            amount=amount,
            payment_method=payment_method,
            reference=reference
        )
        
        account.apply_event(event)
        self.event_store.append(event)
        
        return transaction_id
    
    def complete_deposit(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal
    ):
        """Complete a deposit"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Create event
        event = DepositCompletedEvent(
            account_id=account_id,
            transaction_id=transaction_id,
            amount=amount
        )
        
        account.apply_event(event)
        self.event_store.append(event)
    
    def initiate_withdrawal(
        self,
        account_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        destination: str
    ) -> str:
        """Initiate a withdrawal"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Check sufficient balance
        if account.available_balance < amount:
            raise ValueError("Insufficient funds")
        
        transaction_id = f"WDR-{uuid.uuid4().hex[:12].upper()}"
        
        # Create event
        event = WithdrawalInitiatedEvent(
            account_id=account_id,
            transaction_id=transaction_id,
            amount=amount,
            payment_method=payment_method,
            destination=destination
        )
        
        account.apply_event(event)
        self.event_store.append(event)
        
        return transaction_id
    
    def complete_withdrawal(
        self,
        account_id: str,
        transaction_id: str,
        amount: Decimal
    ):
        """Complete a withdrawal"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Create event
        event = WithdrawalCompletedEvent(
            account_id=account_id,
            transaction_id=transaction_id,
            amount=amount
        )
        
        account.apply_event(event)
        self.event_store.append(event)
    
    def reserve_balance(
        self,
        account_id: str,
        amount: Decimal,
        reason: str
    ) -> str:
        """Reserve balance for pending operation (e.g., trade settlement)"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if account.available_balance < amount:
            raise ValueError("Insufficient available balance")
        
        reservation_id = f"RES-{uuid.uuid4().hex[:12].upper()}"
        
        # Create event
        event = BalanceReservedEvent(
            account_id=account_id,
            reservation_id=reservation_id,
            amount=amount,
            reason=reason
        )
        
        account.apply_event(event)
        self.event_store.append(event)
        
        return reservation_id
    
    def release_balance(
        self,
        account_id: str,
        reservation_id: str,
        amount: Decimal
    ):
        """Release reserved balance"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Create event
        event = BalanceReleasedEvent(
            account_id=account_id,
            reservation_id=reservation_id,
            amount=amount
        )
        
        account.apply_event(event)
        self.event_store.append(event)
    
    def credit_interest(
        self,
        account_id: str,
        period_start: datetime,
        period_end: datetime
    ):
        """Credit interest to account"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Calculate interest
        days = (period_end - period_start).days
        interest_amount = account.ledger_balance * Decimal(str(account.interest_rate)) * Decimal(days) / Decimal(365) / Decimal(100)
        interest_amount = interest_amount.quantize(Decimal("0.01"))
        
        if interest_amount > 0:
            # Create event
            event = InterestCreditedEvent(
                account_id=account_id,
                amount=interest_amount,
                period_start=period_start,
                period_end=period_end,
                interest_rate=account.interest_rate
            )
            
            account.apply_event(event)
            self.event_store.append(event)
    
    def debit_fee(
        self,
        account_id: str,
        amount: Decimal,
        fee_type: str,
        description: str
    ) -> str:
        """Debit fee from account"""
        
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if account.available_balance < amount:
            raise ValueError("Insufficient funds for fee")
        
        fee_id = f"FEE-{uuid.uuid4().hex[:12].upper()}"
        
        # Create event
        event = FeeDebitedEvent(
            account_id=account_id,
            fee_id=fee_id,
            amount=amount,
            fee_type=fee_type,
            description=description
        )
        
        account.apply_event(event)
        self.event_store.append(event)
        
        return fee_id
    
    def get_account(self, account_id: str) -> Optional[CashAccount]:
        """Get account by ID"""
        return self.accounts.get(account_id)
    
    def get_account_history(self, account_id: str) -> List[CashAccountEvent]:
        """Get complete event history for account"""
        return [e for e in self.event_store if e.account_id == account_id]

# Global service instance
cash_account_service = CashAccountService()

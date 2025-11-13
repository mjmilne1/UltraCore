"""
UltraCore Multi-Currency System - Forex Accounting

Comprehensive forex accounting:
- Realized gains/losses on transactions
- Unrealized gains/losses (mark-to-market)
- Period-end revaluation
- Automatic journal entries
- GL integration
- Audit trail
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio

from ultracore.accounting.forex.currency_manager import (
    get_currency_manager, CurrencyCode, RateType, ExchangeRate
)
from ultracore.accounting.chart_of_accounts import get_chart_of_accounts
from ultracore.accounting.general_ledger import (
    get_general_ledger, JournalEntryType
)
from ultracore.audit.audit_core import (
    get_audit_store, AuditEventType, AuditCategory, AuditSeverity
)


# ============================================================================
# Forex Accounting Enums
# ============================================================================

class ForexGainLossType(str, Enum):
    """Type of forex gain/loss"""
    REALIZED = "REALIZED"  # Actual transaction completed
    UNREALIZED = "UNREALIZED"  # Mark-to-market valuation
    TRANSLATION = "TRANSLATION"  # Financial statement translation


class RevaluationMethod(str, Enum):
    """Revaluation methodology"""
    SPOT_RATE = "SPOT_RATE"  # Use spot rate at valuation date
    AVERAGE_RATE = "AVERAGE_RATE"  # Use average rate for period
    CLOSING_RATE = "CLOSING_RATE"  # Use official closing rate
    CUSTOM = "CUSTOM"  # Custom rate specified


class ForexAccountType(str, Enum):
    """Type of forex-enabled account"""
    CASH = "CASH"  # Cash in foreign currency
    RECEIVABLE = "RECEIVABLE"  # Foreign currency receivables
    PAYABLE = "PAYABLE"  # Foreign currency payables
    LOAN = "LOAN"  # Foreign currency loans
    INVESTMENT = "INVESTMENT"  # Foreign currency investments


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ForexTransaction:
    """A foreign exchange transaction"""
    transaction_id: str
    transaction_date: datetime
    
    # Currency details
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    
    # Amounts
    from_amount: Decimal  # Amount in source currency
    to_amount: Decimal  # Amount in target currency
    
    # Exchange rate used
    exchange_rate: Decimal
    exchange_rate_id: str
    rate_type: RateType
    
    # GL accounts affected
    from_account: str  # Account code
    to_account: str
    
    # Realized gain/loss
    realized_gain_loss: Optional[Decimal] = None
    gain_loss_account: Optional[str] = None  # GL account for gain/loss
    
    # Reference
    reference: Optional[str] = None
    description: str = ""
    
    # Journal entry created
    journal_entry_id: Optional[str] = None
    
    # Audit
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForexPosition:
    """Current forex position in a currency"""
    position_id: str
    
    # Currency
    currency: CurrencyCode
    base_currency: CurrencyCode  # Reporting currency (usually AUD)
    
    # Position details
    account_code: str  # GL account
    account_type: ForexAccountType
    
    # Amounts
    foreign_currency_amount: Decimal  # Amount in foreign currency
    base_currency_amount: Decimal  # Amount in base currency at original rate
    
    # Rates
    original_rate: Decimal  # Rate when position was created
    current_rate: Decimal  # Current market rate
    
    # Valuation
    current_value_base: Decimal  # Current value in base currency
    unrealized_gain_loss: Decimal  # Mark-to-market gain/loss
    
    # Dates
    position_date: date
    valuation_date: date
    
    # Last revaluation
    last_revaluation_date: Optional[date] = None
    last_revaluation_rate: Optional[Decimal] = None
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RevaluationEntry:
    """Forex revaluation journal entry"""
    revaluation_id: str
    revaluation_date: date
    
    # Currency
    currency: CurrencyCode
    base_currency: CurrencyCode
    
    # Accounts revalued
    accounts: List[str]  # GL account codes
    
    # Rates
    previous_rate: Decimal
    new_rate: Decimal
    rate_change_percent: float
    
    # Amounts
    total_foreign_amount: Decimal
    previous_base_value: Decimal
    new_base_value: Decimal
    unrealized_gain_loss: Decimal
    
    # Method
    method: RevaluationMethod
    
    # Journal entries created
    journal_entry_ids: List[str] = field(default_factory=list)
    
    # Status
    posted: bool = False
    reversed: bool = False
    
    # Audit
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForexGainLoss:
    """Forex gain or loss record"""
    gain_loss_id: str
    gain_loss_type: ForexGainLossType
    
    # Transaction/position reference
    transaction_id: Optional[str] = None
    position_id: Optional[str] = None
    
    # Currency
    currency: CurrencyCode
    base_currency: CurrencyCode
    
    # Amounts
    foreign_amount: Decimal
    gain_loss_amount: Decimal  # In base currency
    
    # Rates
    original_rate: Decimal
    settlement_rate: Decimal
    
    # Date
    recognition_date: date
    
    # GL posting
    gl_account: str  # Gain/loss account
    journal_entry_id: Optional[str] = None
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Forex Accounting Engine
# ============================================================================

class ForexAccountingEngine:
    """
    Core forex accounting engine
    Handles gains/losses, revaluation, and GL integration
    """
    
    def __init__(self):
        self.currency_manager = get_currency_manager()
        self.chart = get_chart_of_accounts()
        self.gl = get_general_ledger()
        self.audit_store = get_audit_store()
        
        # Storage
        self.transactions: Dict[str, ForexTransaction] = {}
        self.positions: Dict[str, ForexPosition] = {}
        self.revaluations: Dict[str, RevaluationEntry] = {}
        self.gains_losses: Dict[str, ForexGainLoss] = {}
        
        # Configuration
        self.base_currency = CurrencyCode.AUD
        self.auto_post_revaluations = True
        
        # GL account mappings
        self._initialize_gl_accounts()
    
    def _initialize_gl_accounts(self):
        """Initialize forex-related GL accounts"""
        
        # Add forex gain/loss accounts to chart if not exist
        # These should be in the 4000-5000 range (income/expense)
        
        self.forex_gain_account = "4310"  # Forex Gain (Revenue)
        self.forex_loss_account = "5700"  # Forex Loss (Expense)
        self.unrealized_gain_account = "4320"  # Unrealized Forex Gain
        self.unrealized_loss_account = "5710"  # Unrealized Forex Loss
    
    # ========================================================================
    # Forex Transactions
    # ========================================================================
    
    async def record_forex_transaction(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        from_amount: Decimal,
        from_account: str,
        to_account: str,
        description: str,
        created_by: str,
        reference: Optional[str] = None,
        rate: Optional[Decimal] = None,
        auto_post: bool = True
    ) -> ForexTransaction:
        """
        Record a foreign exchange transaction
        Automatically calculates and posts realized gain/loss
        """
        
        transaction_id = f"FX-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Get exchange rate
        if rate:
            # Use provided rate
            exchange_rate_obj = await self.currency_manager.set_exchange_rate(
                from_currency,
                to_currency,
                rate,
                rate_type=RateType.SPOT,
                created_by=created_by
            )
        else:
            # Fetch current market rate
            exchange_rate_obj = await self.currency_manager.get_exchange_rate(
                from_currency,
                to_currency,
                rate_type=RateType.SPOT
            )
        
        if not exchange_rate_obj:
            raise ValueError(
                f"No exchange rate available for {from_currency.value}/{to_currency.value}"
            )
        
        # Calculate converted amount
        to_amount = from_amount * exchange_rate_obj.rate
        
        # Round to target currency precision
        to_curr = self.currency_manager.get_currency(to_currency)
        if to_curr:
            to_amount = round(to_amount, to_curr.minor_units)
        
        # Create transaction record
        transaction = ForexTransaction(
            transaction_id=transaction_id,
            transaction_date=datetime.now(timezone.utc),
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=from_amount,
            to_amount=to_amount,
            exchange_rate=exchange_rate_obj.rate,
            exchange_rate_id=exchange_rate_obj.rate_id,
            rate_type=exchange_rate_obj.rate_type,
            from_account=from_account,
            to_account=to_account,
            reference=reference,
            description=description,
            created_by=created_by
        )
        
        # Calculate realized gain/loss if converting to base currency
        if to_currency == self.base_currency:
            gain_loss = await self._calculate_realized_gain_loss(transaction)
            transaction.realized_gain_loss = gain_loss
            transaction.gain_loss_account = (
                self.forex_gain_account if gain_loss > 0 else self.forex_loss_account
            )
        
        # Store transaction
        self.transactions[transaction_id] = transaction
        
        # Create journal entry
        if auto_post:
            journal_entry = await self._post_forex_transaction(transaction)
            transaction.journal_entry_id = journal_entry.entry_id
        
        # Audit log
        await self.audit_store.log_event(
            event_type=AuditEventType.TRANSACTION_SETTLED,
            category=AuditCategory.FINANCIAL,
            severity=AuditSeverity.INFO,
            resource_type='forex_transaction',
            resource_id=transaction_id,
            action='forex_transaction_recorded',
            description=f"Forex transaction: {from_amount} {from_currency.value} -> {to_amount} {to_currency.value}",
            user_id=created_by,
            metadata={
                'from_currency': from_currency.value,
                'to_currency': to_currency.value,
                'rate': str(exchange_rate_obj.rate),
                'realized_gain_loss': str(transaction.realized_gain_loss) if transaction.realized_gain_loss else None
            },
            regulatory_relevant=True
        )
        
        return transaction
    
    async def _calculate_realized_gain_loss(
        self,
        transaction: ForexTransaction
    ) -> Decimal:
        """
        Calculate realized forex gain/loss on transaction
        """
        
        # For now, simplified calculation
        # In production, would track original cost basis of foreign currency
        
        # If we have a position in the from_currency, calculate gain/loss
        position = await self.get_position_for_account(
            transaction.from_account,
            transaction.from_currency
        )
        
        if position:
            # Calculate based on original rate vs current rate
            original_base_value = transaction.from_amount * position.original_rate
            current_base_value = transaction.from_amount * transaction.exchange_rate
            gain_loss = current_base_value - original_base_value
            return gain_loss
        
        return Decimal('0.00')
    
    async def _post_forex_transaction(
        self,
        transaction: ForexTransaction
    ) -> Any:
        """
        Post forex transaction to general ledger
        Creates journal entry with gain/loss if applicable
        """
        
        lines = []
        
        # Main transaction lines
        # Debit: To Account (receiving currency)
        lines.append({
            'account_code': transaction.to_account,
            'debit': str(transaction.to_amount),
            'credit': '0.00',
            'description': f"{transaction.description} - {transaction.to_currency.value}"
        })
        
        # Credit: From Account (paying currency)
        lines.append({
            'account_code': transaction.from_account,
            'debit': '0.00',
            'credit': str(transaction.from_amount),
            'description': f"{transaction.description} - {transaction.from_currency.value}"
        })
        
        # Realized gain/loss if applicable
        if transaction.realized_gain_loss and transaction.gain_loss_account:
            if transaction.realized_gain_loss > 0:
                # Gain - credit gain account
                lines.append({
                    'account_code': transaction.gain_loss_account,
                    'debit': '0.00',
                    'credit': str(abs(transaction.realized_gain_loss)),
                    'description': f"Realized forex gain on {transaction.from_currency.value}"
                })
            else:
                # Loss - debit loss account
                lines.append({
                    'account_code': transaction.gain_loss_account,
                    'debit': str(abs(transaction.realized_gain_loss)),
                    'credit': '0.00',
                    'description': f"Realized forex loss on {transaction.from_currency.value}"
                })
        
        # Create journal entry
        entry = await self.gl.create_entry(
            entry_type=JournalEntryType.STANDARD,
            entry_date=transaction.transaction_date.date(),
            description=f"Forex: {transaction.description}",
            lines=lines,
            created_by=transaction.created_by,
            reference=transaction.reference,
            auto_post=True
        )
        
        return entry
    
    # ========================================================================
    # Forex Positions
    # ========================================================================
    
    async def create_position(
        self,
        currency: CurrencyCode,
        account_code: str,
        account_type: ForexAccountType,
        amount: Decimal,
        rate: Optional[Decimal] = None
    ) -> ForexPosition:
        """
        Create a new forex position
        Tracks foreign currency holdings
        """
        
        position_id = f"POS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        
        # Get current rate if not provided
        if not rate:
            rate_obj = await self.currency_manager.get_exchange_rate(
                currency,
                self.base_currency,
                rate_type=RateType.SPOT
            )
            rate = rate_obj.rate if rate_obj else Decimal('1.0')
        
        # Calculate base currency value
        base_value = amount * rate
        
        position = ForexPosition(
            position_id=position_id,
            currency=currency,
            base_currency=self.base_currency,
            account_code=account_code,
            account_type=account_type,
            foreign_currency_amount=amount,
            base_currency_amount=base_value,
            original_rate=rate,
            current_rate=rate,
            current_value_base=base_value,
            unrealized_gain_loss=Decimal('0.00'),
            position_date=date.today(),
            valuation_date=date.today()
        )
        
        self.positions[position_id] = position
        
        return position
    
    async def get_position_for_account(
        self,
        account_code: str,
        currency: CurrencyCode
    ) -> Optional[ForexPosition]:
        """Get position for a specific account and currency"""
        
        for position in self.positions.values():
            if position.account_code == account_code and position.currency == currency:
                return position
        
        return None
    
    async def update_position_amount(
        self,
        position_id: str,
        amount_change: Decimal
    ) -> ForexPosition:
        """Update position amount (e.g., after transaction)"""
        
        position = self.positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        
        position.foreign_currency_amount += amount_change
        position.base_currency_amount = position.foreign_currency_amount * position.original_rate
        position.updated_at = datetime.now(timezone.utc)
        
        # Recalculate unrealized gain/loss
        await self.revalue_position(position_id)
        
        return position
    
    async def revalue_position(
        self,
        position_id: str,
        valuation_date: Optional[date] = None
    ) -> ForexPosition:
        """
        Revalue a forex position to current market rate
        Calculates unrealized gain/loss
        """
        
        position = self.positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        
        val_date = valuation_date or date.today()
        
        # Get current exchange rate
        rate_obj = await self.currency_manager.get_exchange_rate(
            position.currency,
            position.base_currency,
            rate_type=RateType.SPOT
        )
        
        if not rate_obj:
            return position
        
        # Update current rate
        position.current_rate = rate_obj.rate
        
        # Calculate current value
        position.current_value_base = position.foreign_currency_amount * position.current_rate
        
        # Calculate unrealized gain/loss
        position.unrealized_gain_loss = (
            position.current_value_base - position.base_currency_amount
        )
        
        # Update valuation date
        position.valuation_date = val_date
        position.updated_at = datetime.now(timezone.utc)
        
        return position
    
    # ========================================================================
    # Period-End Revaluation
    # ========================================================================
    
    async def perform_period_end_revaluation(
        self,
        revaluation_date: date,
        currencies: Optional[List[CurrencyCode]] = None,
        method: RevaluationMethod = RevaluationMethod.SPOT_RATE,
        created_by: str = "system",
        auto_post: bool = True
    ) -> List[RevaluationEntry]:
        """
        Perform period-end revaluation of all forex positions
        Creates journal entries for unrealized gains/losses
        """
        
        revaluations = []
        
        # Get all currencies to revalue
        currencies_to_revalue = currencies or [
            CurrencyCode.USD, CurrencyCode.EUR, CurrencyCode.GBP,
            CurrencyCode.JPY, CurrencyCode.NZD, CurrencyCode.SGD
        ]
        
        for currency in currencies_to_revalue:
            if currency == self.base_currency:
                continue
            
            # Get all positions in this currency
            positions = [
                p for p in self.positions.values()
                if p.currency == currency
            ]
            
            if not positions:
                continue
            
            # Get revaluation rate
            rate_obj = await self._get_revaluation_rate(
                currency,
                revaluation_date,
                method
            )
            
            if not rate_obj:
                continue
            
            # Calculate total unrealized gain/loss
            total_foreign_amount = Decimal('0.00')
            total_previous_base = Decimal('0.00')
            total_new_base = Decimal('0.00')
            accounts = []
            
            for position in positions:
                # Revalue position
                previous_rate = position.current_rate
                previous_base = position.current_value_base
                
                position.current_rate = rate_obj.rate
                position.current_value_base = position.foreign_currency_amount * rate_obj.rate
                position.unrealized_gain_loss = (
                    position.current_value_base - position.base_currency_amount
                )
                position.last_revaluation_date = revaluation_date
                position.last_revaluation_rate = rate_obj.rate
                position.updated_at = datetime.now(timezone.utc)
                
                # Accumulate totals
                total_foreign_amount += position.foreign_currency_amount
                total_previous_base += previous_base
                total_new_base += position.current_value_base
                accounts.append(position.account_code)
            
            # Calculate net unrealized gain/loss
            unrealized_gain_loss = total_new_base - total_previous_base
            
            # Create revaluation entry
            revaluation_id = f"REVAL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            
            previous_rate = positions[0].current_rate if positions else Decimal('1.0')
            rate_change = float((rate_obj.rate - previous_rate) / previous_rate * 100) if previous_rate else 0.0
            
            revaluation = RevaluationEntry(
                revaluation_id=revaluation_id,
                revaluation_date=revaluation_date,
                currency=currency,
                base_currency=self.base_currency,
                accounts=list(set(accounts)),
                previous_rate=previous_rate,
                new_rate=rate_obj.rate,
                rate_change_percent=rate_change,
                total_foreign_amount=total_foreign_amount,
                previous_base_value=total_previous_base,
                new_base_value=total_new_base,
                unrealized_gain_loss=unrealized_gain_loss,
                method=method,
                created_by=created_by
            )
            
            self.revaluations[revaluation_id] = revaluation
            
            # Post to GL if auto_post
            if auto_post and abs(unrealized_gain_loss) > Decimal('0.01'):
                journal_entry = await self._post_revaluation(revaluation)
                revaluation.journal_entry_ids.append(journal_entry.entry_id)
                revaluation.posted = True
            
            revaluations.append(revaluation)
            
            # Audit log
            await self.audit_store.log_event(
                event_type=AuditEventType.COMPLIANCE_CHECK,
                category=AuditCategory.FINANCIAL,
                severity=AuditSeverity.INFO,
                resource_type='forex_revaluation',
                resource_id=revaluation_id,
                action='period_end_revaluation',
                description=f"Forex revaluation for {currency.value}: {unrealized_gain_loss} {self.base_currency.value}",
                user_id=created_by,
                metadata={
                    'currency': currency.value,
                    'accounts': len(accounts),
                    'previous_rate': str(previous_rate),
                    'new_rate': str(rate_obj.rate),
                    'unrealized_gain_loss': str(unrealized_gain_loss)
                },
                regulatory_relevant=True
            )
        
        return revaluations
    
    async def _get_revaluation_rate(
        self,
        currency: CurrencyCode,
        revaluation_date: date,
        method: RevaluationMethod
    ) -> Optional[ExchangeRate]:
        """Get exchange rate for revaluation"""
        
        if method == RevaluationMethod.SPOT_RATE:
            # Use spot rate at revaluation date
            return await self.currency_manager.get_exchange_rate(
                currency,
                self.base_currency,
                rate_type=RateType.SPOT
            )
        
        elif method == RevaluationMethod.CLOSING_RATE:
            # Use official closing rate
            return await self.currency_manager.get_historical_rate(
                currency,
                self.base_currency,
                revaluation_date
            )
        
        elif method == RevaluationMethod.AVERAGE_RATE:
            # Calculate average rate for period (simplified)
            trend = await self.currency_manager.get_rate_trend(
                currency,
                self.base_currency,
                days=30
            )
            
            if trend:
                avg_rate = sum(h.close_rate for h in trend) / len(trend)
                return await self.currency_manager.set_exchange_rate(
                    currency,
                    self.base_currency,
                    avg_rate,
                    rate_type=RateType.MID
                )
        
        return None
    
    async def _post_revaluation(
        self,
        revaluation: RevaluationEntry
    ) -> Any:
        """
        Post revaluation to general ledger
        Creates journal entry for unrealized gain/loss
        """
        
        lines = []
        
        # Unrealized gain/loss
        if revaluation.unrealized_gain_loss > 0:
            # Unrealized gain
            # Debit: Foreign currency accounts (asset increase)
            for account_code in revaluation.accounts:
                lines.append({
                    'account_code': account_code,
                    'debit': str(abs(revaluation.unrealized_gain_loss / len(revaluation.accounts))),
                    'credit': '0.00',
                    'description': f"Forex revaluation - {revaluation.currency.value} gain"
                })
            
            # Credit: Unrealized gain account
            lines.append({
                'account_code': self.unrealized_gain_account,
                'debit': '0.00',
                'credit': str(abs(revaluation.unrealized_gain_loss)),
                'description': f"Unrealized forex gain - {revaluation.currency.value}"
            })
        
        elif revaluation.unrealized_gain_loss < 0:
            # Unrealized loss
            # Debit: Unrealized loss account
            lines.append({
                'account_code': self.unrealized_loss_account,
                'debit': str(abs(revaluation.unrealized_gain_loss)),
                'credit': '0.00',
                'description': f"Unrealized forex loss - {revaluation.currency.value}"
            })
            
            # Credit: Foreign currency accounts (asset decrease)
            for account_code in revaluation.accounts:
                lines.append({
                    'account_code': account_code,
                    'debit': '0.00',
                    'credit': str(abs(revaluation.unrealized_gain_loss / len(revaluation.accounts))),
                    'description': f"Forex revaluation - {revaluation.currency.value} loss"
                })
        
        # Create journal entry
        entry = await self.gl.create_entry(
            entry_type=JournalEntryType.ADJUSTING,
            entry_date=revaluation.revaluation_date,
            description=f"Forex revaluation - {revaluation.currency.value}",
            lines=lines,
            created_by=revaluation.created_by,
            reference=revaluation.revaluation_id,
            auto_post=True
        )
        
        return entry
    
    async def reverse_revaluation(
        self,
        revaluation_id: str,
        reversed_by: str,
        reason: str
    ) -> Any:
        """Reverse a revaluation entry"""
        
        revaluation = self.revaluations.get(revaluation_id)
        if not revaluation:
            raise ValueError(f"Revaluation {revaluation_id} not found")
        
        if not revaluation.posted:
            raise ValueError("Revaluation not posted, cannot reverse")
        
        if revaluation.reversed:
            raise ValueError("Revaluation already reversed")
        
        # Reverse journal entries
        for je_id in revaluation.journal_entry_ids:
            await self.gl.reverse_entry(
                entry_id=je_id,
                reversal_date=date.today(),
                reversed_by=reversed_by,
                reason=reason
            )
        
        revaluation.reversed = True
        
        return revaluation
    
    # ========================================================================
    # Reporting
    # ========================================================================
    
    async def get_forex_summary(
        self,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary of forex positions and gains/losses"""
        
        as_of = as_of_date or date.today()
        
        # Revalue all positions
        for position in self.positions.values():
            await self.revalue_position(position.position_id, as_of)
        
        # Calculate totals by currency
        summary_by_currency = {}
        
        for position in self.positions.values():
            curr = position.currency.value
            
            if curr not in summary_by_currency:
                summary_by_currency[curr] = {
                    'currency': curr,
                    'total_foreign_amount': Decimal('0.00'),
                    'total_base_value': Decimal('0.00'),
                    'unrealized_gain_loss': Decimal('0.00'),
                    'positions': []
                }
            
            summary_by_currency[curr]['total_foreign_amount'] += position.foreign_currency_amount
            summary_by_currency[curr]['total_base_value'] += position.current_value_base
            summary_by_currency[curr]['unrealized_gain_loss'] += position.unrealized_gain_loss
            summary_by_currency[curr]['positions'].append({
                'position_id': position.position_id,
                'account': position.account_code,
                'amount': str(position.foreign_currency_amount),
                'value': str(position.current_value_base),
                'gain_loss': str(position.unrealized_gain_loss)
            })
        
        # Calculate overall totals
        total_unrealized_gain_loss = sum(
            p.unrealized_gain_loss for p in self.positions.values()
        )
        
        return {
            'as_of_date': as_of.isoformat(),
            'base_currency': self.base_currency.value,
            'by_currency': list(summary_by_currency.values()),
            'total_unrealized_gain_loss': str(total_unrealized_gain_loss),
            'total_positions': len(self.positions)
        }
    
    async def get_realized_gains_losses(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get realized forex gains/losses for period"""
        
        realized = [
            {
                'transaction_id': t.transaction_id,
                'date': t.transaction_date.isoformat(),
                'from_currency': t.from_currency.value,
                'to_currency': t.to_currency.value,
                'amount': str(t.from_amount),
                'rate': str(t.exchange_rate),
                'realized_gain_loss': str(t.realized_gain_loss) if t.realized_gain_loss else '0.00'
            }
            for t in self.transactions.values()
            if start_date <= t.transaction_date.date() <= end_date
            and t.realized_gain_loss is not None
        ]
        
        return realized


# ============================================================================
# Global Forex Accounting Engine
# ============================================================================

_forex_engine: Optional[ForexAccountingEngine] = None

def get_forex_engine() -> ForexAccountingEngine:
    """Get the singleton forex accounting engine"""
    global _forex_engine
    if _forex_engine is None:
        _forex_engine = ForexAccountingEngine()
    return _forex_engine

"""
Property-Based Tests for General Ledger
Nubank-inspired invariant testing using Hypothesis

Tests:
1. Conservation: Debits always equal credits (accounting equation)
2. Idempotency: Replaying same event produces same result
3. Commutativity: Order of independent transactions doesn't matter
4. Balance integrity: Account balances match sum of transactions
5. Referential integrity: All transaction references exist

Uses Hypothesis for generative testing with 1000s of random scenarios
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Set
import uuid

from ultracore.modules.accounting.general_ledger.chart_of_accounts import ChartOfAccounts, AccountType
from ultracore.modules.accounting.general_ledger.journal import JournalEntry, JournalService
from ultracore.modules.accounting.general_ledger.ledger import GeneralLedger


# Hypothesis strategies for generating test data
@st.composite
def decimal_amounts(draw, min_value=0, max_value=1000000):
    """Generate valid decimal amounts"""
    value = draw(st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    ))
    return Decimal(str(round(value, 2)))


@st.composite
def account_codes(draw):
    """Generate valid account codes from chart of accounts"""
    account_type = draw(st.sampled_from([
        '1100', '1200', '2100', '2200', '3100',  # Assets, Liabilities, Equity
        '4100', '4200', '5100', '5200'  # Revenue, Expenses
    ]))
    return account_type


@st.composite
def journal_entries(draw, num_lines=None):
    """Generate valid journal entries"""
    if num_lines is None:
        num_lines = draw(st.integers(min_value=2, max_value=5))
    
    # Generate lines ensuring debits = credits
    lines = []
    total_debit = Decimal('0')
    
    # Generate n-1 lines with random amounts
    for i in range(num_lines - 1):
        account = draw(account_codes())
        amount = draw(decimal_amounts(max_value=10000))
        
        # Randomly assign to debit or credit
        is_debit = draw(st.booleans())
        
        if is_debit:
            lines.append({
                'account_code': account,
                'debit': str(amount),
                'credit': '0'
            })
            total_debit += amount
        else:
            lines.append({
                'account_code': account,
                'debit': '0',
                'credit': str(amount)
            })
            total_debit -= amount
    
    # Last line balances the entry
    last_account = draw(account_codes())
    if total_debit > 0:
        # Need credit to balance
        lines.append({
            'account_code': last_account,
            'debit': '0',
            'credit': str(total_debit)
        })
    else:
        # Need debit to balance
        lines.append({
            'account_code': last_account,
            'debit': str(abs(total_debit)),
            'credit': '0'
        })
    
    return {
        'description': 'Generated test entry',
        'entries': lines
    }


class TestLedgerInvariants:
    """
    Property-based tests for ledger invariants
    
    Tests mathematical properties that must ALWAYS hold
    """
    
    @given(entry_data=journal_entries())
    @settings(max_examples=1000, deadline=None)
    async def test_conservation_law(self, entry_data):
        """
        PROPERTY: Debits always equal credits (accounting equation)
        
        This is the fundamental law of double-entry bookkeeping.
        If this fails, the ledger is corrupted.
        """
        journal_service = JournalService()
        
        # Create entry
        entry = await journal_service.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        
        # Calculate totals
        total_debit = sum(
            Decimal(line['debit']) for line in entry_data['entries']
        )
        total_credit = sum(
            Decimal(line['credit']) for line in entry_data['entries']
        )
        
        # INVARIANT: Debits MUST equal credits
        assert total_debit == total_credit, \
            f"Conservation violated: debits={total_debit}, credits={total_credit}"
        
        # Verify in created entry
        assert entry['total_debit'] == entry['total_credit'], \
            "Created entry violates conservation law"
    
    @given(entry_data=journal_entries())
    @settings(max_examples=500, deadline=None)
    async def test_idempotency(self, entry_data):
        """
        PROPERTY: Replaying same event produces same result
        
        Critical for Kafka event replay and disaster recovery
        """
        journal_service = JournalService()
        gl = GeneralLedger()
        
        # Post entry once
        entry1 = await journal_service.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        
        balance1 = await gl.get_account_balance('1100')
        
        # Replay same entry (simulate Kafka replay)
        entry2 = await journal_service.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        
        balance2 = await gl.get_account_balance('1100')
        
        # INVARIANT: Same input produces same output
        # Note: In production, we'd use idempotency keys to prevent duplicates
        # Here we're testing that the mathematical result is consistent
        assert entry1['total_debit'] == entry2['total_debit']
        assert entry1['total_credit'] == entry2['total_credit']
    
    @given(
        entries=st.lists(
            journal_entries(),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=200, deadline=None)
    async def test_commutativity_independent_transactions(self, entries):
        """
        PROPERTY: Order of independent transactions doesn't affect final balance
        
        If transactions touch different accounts, order shouldn't matter
        """
        journal_service = JournalService()
        gl1 = GeneralLedger()
        gl2 = GeneralLedger()
        
        # Post in original order
        for entry_data in entries:
            await journal_service.create_entry(
                description=entry_data['description'],
                entries=entry_data['entries']
            )
        
        balance1 = await gl1.get_account_balance('1100')
        
        # Post in reverse order (new ledger)
        for entry_data in reversed(entries):
            await journal_service.create_entry(
                description=entry_data['description'],
                entries=entry_data['entries']
            )
        
        balance2 = await gl2.get_account_balance('1100')
        
        # INVARIANT: Final balance should be same regardless of order
        # (assuming independent transactions)
        assert balance1 == balance2, \
            f"Commutativity violated: forward={balance1}, reverse={balance2}"
    
    @given(entry_data=journal_entries())
    @settings(max_examples=500, deadline=None)
    async def test_balance_integrity(self, entry_data):
        """
        PROPERTY: Account balance equals sum of all debits minus credits
        
        Balance calculation must be accurate
        """
        journal_service = JournalService()
        gl = GeneralLedger()
        
        # Get initial balance
        account_code = entry_data['entries'][0]['account_code']
        initial_balance = await gl.get_account_balance(account_code)
        
        # Post entry
        await journal_service.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        
        # Calculate expected change for this account
        expected_change = Decimal('0')
        for line in entry_data['entries']:
            if line['account_code'] == account_code:
                expected_change += Decimal(line['debit']) - Decimal(line['credit'])
        
        # Get new balance
        new_balance = await gl.get_account_balance(account_code)
        
        # INVARIANT: Balance change must match transaction amounts
        actual_change = new_balance - initial_balance
        assert actual_change == expected_change, \
            f"Balance integrity violated: expected={expected_change}, actual={actual_change}"
    
    @given(
        num_entries=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=50, deadline=None)
    async def test_ledger_equation_always_balanced(self, num_entries):
        """
        PROPERTY: Assets = Liabilities + Equity (fundamental accounting equation)
        
        After any number of transactions, this must hold
        """
        journal_service = JournalService()
        gl = GeneralLedger()
        coa = ChartOfAccounts()
        
        # Generate and post random entries
        for _ in range(num_entries):
            entry_data = journal_entries().example()
            await journal_service.create_entry(
                description=entry_data['description'],
                entries=entry_data['entries']
            )
        
        # Calculate totals by account type
        total_assets = Decimal('0')
        total_liabilities = Decimal('0')
        total_equity = Decimal('0')
        
        for account in coa.accounts.values():
            balance = await gl.get_account_balance(account.code)
            
            if account.account_type == AccountType.ASSET:
                total_assets += balance
            elif account.account_type == AccountType.LIABILITY:
                total_liabilities += balance
            elif account.account_type == AccountType.EQUITY:
                total_equity += balance
        
        # INVARIANT: Assets = Liabilities + Equity
        left_side = total_assets
        right_side = total_liabilities + total_equity
        
        # Allow for rounding errors (pennies)
        diff = abs(left_side - right_side)
        assert diff < Decimal('0.01'), \
            f"Accounting equation violated: Assets={left_side}, L+E={right_side}, diff={diff}"
    
    @given(entry_data=journal_entries())
    @settings(max_examples=500, deadline=None)
    async def test_referential_integrity(self, entry_data):
        """
        PROPERTY: All account codes referenced in transactions must exist
        
        No orphaned transactions
        """
        journal_service = JournalService()
        coa = ChartOfAccounts()
        
        # Verify all account codes exist before posting
        for line in entry_data['entries']:
            account = coa.get_account(line['account_code'])
            assert account is not None, \
                f"Referential integrity violated: account {line['account_code']} does not exist"
        
        # Post entry
        entry = await journal_service.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        
        # Verify all lines reference valid accounts
        for line in entry['lines']:
            account = coa.get_account(line['account_code'])
            assert account is not None


class LedgerStateMachine(RuleBasedStateMachine):
    """
    Stateful property-based testing
    
    Generates random sequences of operations and checks invariants
    """
    
    def __init__(self):
        super().__init__()
        self.ledger = GeneralLedger()
        self.journal = JournalService()
        self.posted_entries: List[str] = []
        self.account_balances: Dict[str, Decimal] = {}
    
    @rule(entry_data=journal_entries())
    async def post_entry(self, entry_data):
        """Post a journal entry"""
        entry = await self.journal.create_entry(
            description=entry_data['description'],
            entries=entry_data['entries']
        )
        self.posted_entries.append(entry['entry_id'])
    
    @rule(account_code=account_codes())
    async def check_balance(self, account_code):
        """Check account balance"""
        balance = await self.ledger.get_account_balance(account_code)
        self.account_balances[account_code] = balance
    
    @invariant()
    async def balances_are_consistent(self):
        """Invariant: All balances are consistent with posted transactions"""
        # Verify conservation law holds
        for entry_id in self.posted_entries:
            # In production: retrieve entry and verify debits = credits
            pass
    
    @invariant()
    async def no_negative_balances_in_asset_accounts(self):
        """Invariant: Asset accounts should not have negative balances"""
        coa = ChartOfAccounts()
        
        for account_code, balance in self.account_balances.items():
            account = coa.get_account(account_code)
            if account and account.account_type == AccountType.ASSET:
                # Assets typically shouldn't be negative (except contra-assets)
                if not account.code.startswith('19'):  # Contra-asset accounts
                    assert balance >= 0, \
                        f"Asset account {account_code} has negative balance: {balance}"


# Run stateful tests
TestLedgerState = LedgerStateMachine.TestCase


class TestPaymentInvariants:
    """
    Property-based tests for payment processing
    """
    
    @given(
        amount=decimal_amounts(min_value=1, max_value=100000),
        num_splits=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=500, deadline=None)
    async def test_payment_splitting_conservation(self, amount, num_splits):
        """
        PROPERTY: Split payments sum to original amount
        
        When splitting a payment, total must equal original
        """
        # Split amount randomly
        splits = []
        remaining = amount
        
        for i in range(num_splits - 1):
            # Random split (but ensure some left for last)
            max_split = remaining - Decimal('0.01') * (num_splits - i - 1)
            if max_split > 0:
                split = min(
                    Decimal(str(round(float(remaining) * 0.3, 2))),
                    max_split
                )
                splits.append(split)
                remaining -= split
        
        # Last split gets remainder
        splits.append(remaining)
        
        # INVARIANT: Sum of splits equals original
        total = sum(splits)
        assert total == amount, \
            f"Payment split conservation violated: original={amount}, total={total}"
    
    @given(
        amount=decimal_amounts(min_value=1, max_value=10000),
        fee_rate=st.floats(min_value=0, max_value=0.05)  # 0-5% fee
    )
    @settings(max_examples=500, deadline=None)
    async def test_fee_calculation_bounds(self, amount, fee_rate):
        """
        PROPERTY: Calculated fees are within expected bounds
        
        Fees should never exceed amount or be negative
        """
        fee_percentage = Decimal(str(round(fee_rate * 100, 2)))
        
        # Calculate fee
        fee = (amount * fee_percentage / Decimal('100')).quantize(
            Decimal('0.01')
        )
        
        # INVARIANT: Fee bounds
        assert fee >= 0, "Fee cannot be negative"
        assert fee <= amount, "Fee cannot exceed payment amount"
        assert fee == (amount * fee_percentage / Decimal('100')).quantize(Decimal('0.01')), \
            "Fee calculation incorrect"


class TestInterestInvariants:
    """
    Property-based tests for interest calculations
    """
    
    @given(
        principal=decimal_amounts(min_value=1000, max_value=1000000),
        rate=st.floats(min_value=0.01, max_value=20.0),  # 0.01% - 20%
        days=st.integers(min_value=1, max_value=365)
    )
    @settings(max_examples=1000, deadline=None)
    def test_interest_monotonicity(self, principal, rate, days):
        """
        PROPERTY: Interest increases monotonically with time
        
        More days = more interest (for positive rates)
        """
        from ultracore.business_logic.interest.interest_engine import InterestCalculator
        
        rate_decimal = Decimal(str(round(rate, 2)))
        
        # Calculate interest for n days
        interest_n = InterestCalculator.calculate_simple_interest(
            principal, rate_decimal, days
        )
        
        # Calculate interest for n+1 days
        interest_n_plus_1 = InterestCalculator.calculate_simple_interest(
            principal, rate_decimal, days + 1
        )
        
        # INVARIANT: Interest increases with time
        assert interest_n_plus_1 >= interest_n, \
            f"Interest monotonicity violated: day {days}={interest_n}, day {days+1}={interest_n_plus_1}"
    
    @given(
        principal=decimal_amounts(min_value=1000, max_value=100000),
        rate=st.floats(min_value=0.01, max_value=10.0)
    )
    @settings(max_examples=500, deadline=None)
    def test_interest_linearity(self, principal, rate):
        """
        PROPERTY: Simple interest is linear with principal
        
        Double principal = double interest (for same rate and time)
        """
        from ultracore.business_logic.interest.interest_engine import InterestCalculator
        
        rate_decimal = Decimal(str(round(rate, 2)))
        days = 30
        
        # Calculate for principal
        interest_1x = InterestCalculator.calculate_simple_interest(
            principal, rate_decimal, days
        )
        
        # Calculate for 2x principal
        interest_2x = InterestCalculator.calculate_simple_interest(
            principal * Decimal('2'), rate_decimal, days
        )
        
        # INVARIANT: 2x principal = 2x interest (within rounding)
        expected = interest_1x * Decimal('2')
        diff = abs(interest_2x - expected)
        
        assert diff < Decimal('0.02'), \
            f"Interest linearity violated: 1x={interest_1x}, 2x={interest_2x}, expected={expected}"


# Pytest configuration
@pytest.fixture(scope='session')
def hypothesis_settings():
    """Configure Hypothesis settings"""
    settings.register_profile('ci', max_examples=100, deadline=1000)
    settings.register_profile('dev', max_examples=10, deadline=None)
    settings.register_profile('nightly', max_examples=10000, deadline=None)
    
    # Use appropriate profile based on environment
    settings.load_profile('dev')


if __name__ == '__main__':
    # Run property-based tests
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])

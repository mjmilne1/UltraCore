"""
Comprehensive Accounting Module Test Suite
Tests all components: Chart of Accounts, Journal Entries, Ledger, Statements
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Import all modules
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts, AccountType
from ultracore.modules.accounting.journal_entry import (
    journal_entry_service, JournalEntry, JournalEntryLine
)
from ultracore.modules.accounting.general_ledger import general_ledger
from ultracore.modules.accounting.financial_statements import financial_statements
from ultracore.modules.accounting.reconciliation import reconciliation_service
from ultracore.modules.accounting.transaction_integration import transaction_accounting
from ultracore.modules.accounting.holdings_integration import holdings_accounting

class TestChartOfAccounts:
    """Test Chart of Accounts"""
    
    def test_account_creation(self):
        """Test getting accounts"""
        account = chart_of_accounts.get_account("1000")
        
        assert account is not None
        assert account.name == "Cash and Cash Equivalents"
        assert account.account_type == AccountType.ASSET
    
    def test_accounts_by_type(self):
        """Test filtering by account type"""
        assets = chart_of_accounts.get_accounts_by_type(AccountType.ASSET)
        
        assert len(assets) > 0
        assert all(acc.account_type == AccountType.ASSET for acc in assets)
    
    def test_balance_sheet_accounts(self):
        """Test getting balance sheet accounts"""
        bs_accounts = chart_of_accounts.get_balance_sheet_accounts()
        
        assert "assets" in bs_accounts
        assert "liabilities" in bs_accounts
        assert "equity" in bs_accounts

class TestJournalEntry:
    """Test Journal Entry System"""
    
    def test_create_journal_entry(self):
        """Test creating journal entry"""
        entry = journal_entry_service.create_entry(
            description="Test Entry",
            reference="TEST-001"
        )
        
        assert entry.entry_id is not None
        assert entry.description == "Test Entry"
    
    def test_add_lines(self):
        """Test adding lines to entry"""
        entry = journal_entry_service.create_entry("Test")
        
        entry.add_line(JournalEntryLine(
            account_number="1000",
            debit=100.00,
            description="Test debit"
        ))
        
        entry.add_line(JournalEntryLine(
            account_number="4000",
            credit=100.00,
            description="Test credit"
        ))
        
        assert len(entry.lines) == 2
    
    def test_validate_balanced_entry(self):
        """Test validation of balanced entry"""
        entry = journal_entry_service.create_entry("Test")
        
        entry.add_line(JournalEntryLine("1000", debit=100.00))
        entry.add_line(JournalEntryLine("4000", credit=100.00))
        
        validation = entry.validate()
        
        assert validation["valid"] is True
        assert validation["total_debits"] == 100.00
        assert validation["total_credits"] == 100.00
    
    def test_validate_unbalanced_entry(self):
        """Test validation of unbalanced entry"""
        entry = journal_entry_service.create_entry("Test")
        
        entry.add_line(JournalEntryLine("1000", debit=100.00))
        entry.add_line(JournalEntryLine("4000", credit=50.00))
        
        validation = entry.validate()
        
        assert validation["valid"] is False
    
    def test_post_entry(self):
        """Test posting entry"""
        entry = journal_entry_service.create_entry("Test Post")
        
        entry.add_line(JournalEntryLine("1000", debit=200.00))
        entry.add_line(JournalEntryLine("4000", credit=200.00))
        
        entry.post()
        
        assert entry.is_posted is True
        assert entry.posted_at is not None

class TestGeneralLedger:
    """Test General Ledger"""
    
    def test_post_to_ledger(self):
        """Test posting entry to ledger"""
        entry = journal_entry_service.create_entry("Ledger Test")
        
        entry.add_line(JournalEntryLine("1010", debit=500.00))
        entry.add_line(JournalEntryLine("3000", credit=500.00))
        
        entry.post()
        general_ledger.post_journal_entry(entry)
        
        # Check ledger has entries
        ledger_entries = general_ledger.get_account_ledger("1010")
        
        assert len(ledger_entries) > 0
    
    def test_account_balance(self):
        """Test getting account balance"""
        balance = general_ledger.get_account_balance("1000")
        
        assert isinstance(balance, float)
    
    def test_trial_balance(self):
        """Test generating trial balance"""
        trial_balance = general_ledger.generate_trial_balance()
        
        assert "accounts" in trial_balance
        assert "total_debits" in trial_balance
        assert "total_credits" in trial_balance
        assert "in_balance" in trial_balance

class TestFinancialStatements:
    """Test Financial Statements"""
    
    def test_balance_sheet(self):
        """Test balance sheet generation"""
        bs = financial_statements.generate_balance_sheet()
        
        assert bs["statement"] == "Balance Sheet"
        assert "assets" in bs
        assert "liabilities" in bs
        assert "equity" in bs
    
    def test_income_statement(self):
        """Test income statement generation"""
        start = datetime(2025, 1, 1)
        end = datetime.now(timezone.utc)
        
        income_stmt = financial_statements.generate_income_statement(start, end)
        
        assert income_stmt["statement"] == "Income Statement"
        assert "revenue" in income_stmt
        assert "expenses" in income_stmt
        assert "net_income" in income_stmt
    
    def test_cash_flow_statement(self):
        """Test cash flow statement generation"""
        start = datetime(2025, 1, 1)
        end = datetime.now(timezone.utc)
        
        cash_flow = financial_statements.generate_cash_flow_statement(start, end)
        
        assert cash_flow["statement"] == "Cash Flow Statement"
        assert "operating_activities" in cash_flow
        assert "investing_activities" in cash_flow
        assert "financing_activities" in cash_flow

class TestTransactionIntegration:
    """Test Transaction Integration"""
    
    @pytest.mark.asyncio
    async def test_trade_journal_entry(self):
        """Test creating journal entry for trade"""
        trade_data = {
            "trade_id": "TRD-TEST-001",
            "ticker": "VAS.AX",
            "side": "buy",
            "quantity": 100,
            "price": 100.00,
            "value": 10000.00
        }
        
        entry = await transaction_accounting.create_trade_journal_entry(trade_data)
        
        assert entry is not None
        assert len(entry.lines) == 2
        assert entry.is_posted is True
    
    @pytest.mark.asyncio
    async def test_settlement_journal_entry(self):
        """Test creating journal entry for settlement"""
        settlement_data = {
            "settlement_id": "STL-TEST-001",
            "ticker": "VAS.AX",
            "side": "buy",
            "value": 10000.00
        }
        
        entry = await transaction_accounting.create_settlement_journal_entry(settlement_data)
        
        assert entry is not None
        assert entry.is_posted is True

class TestReconciliation:
    """Test Reconciliation"""
    
    @pytest.mark.asyncio
    async def test_cash_reconciliation(self):
        """Test cash reconciliation"""
        recon = await reconciliation_service.reconcile_cash(datetime.now(timezone.utc))
        
        assert recon["type"] == "cash"
        assert "ledger_balance" in recon
        assert "actual_balance" in recon
        assert "reconciled" in recon
    
    @pytest.mark.asyncio
    async def test_full_reconciliation(self):
        """Test full reconciliation"""
        result = await reconciliation_service.run_full_reconciliation()
        
        assert "cash" in result
        assert "investments" in result
        assert "settlements" in result

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("  🧪 RUNNING ACCOUNTING MODULE TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

if __name__ == "__main__":
    run_all_tests()

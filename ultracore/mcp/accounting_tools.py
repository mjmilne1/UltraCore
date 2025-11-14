"""
MCP Tools for Accounting
Enables AI assistants to interact with accounting system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.accounting.journal_entry import journal_entry_service, JournalEntryLine
from ultracore.modules.accounting.general_ledger import general_ledger
from ultracore.modules.accounting.financial_statements import financial_statements
from ultracore.modules.accounting.reconciliation import reconciliation_service
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts

class AccountingMCPTools:
    """
    MCP tools for AI assistants to manage accounting
    """
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        return [
            {
                "name": "create_journal_entry",
                "description": "Create a new journal entry with debits and credits",
                "parameters": {
                    "description": "Description of entry",
                    "lines": "List of debit/credit lines",
                    "reference": "Reference number (optional)"
                }
            },
            {
                "name": "post_journal_entry",
                "description": "Post a journal entry to the ledger",
                "parameters": {
                    "entry_id": "Journal entry ID"
                }
            },
            {
                "name": "get_account_balance",
                "description": "Get current balance for an account",
                "parameters": {
                    "account_number": "Account number",
                    "as_of_date": "Date (optional)"
                }
            },
            {
                "name": "get_trial_balance",
                "description": "Generate trial balance",
                "parameters": {
                    "as_of_date": "Date (optional)"
                }
            },
            {
                "name": "get_balance_sheet",
                "description": "Generate balance sheet",
                "parameters": {
                    "as_of_date": "Date (optional)"
                }
            },
            {
                "name": "get_income_statement",
                "description": "Generate income statement (P&L)",
                "parameters": {
                    "start_date": "Start date",
                    "end_date": "End date (optional)"
                }
            },
            {
                "name": "get_cash_flow_statement",
                "description": "Generate cash flow statement",
                "parameters": {
                    "start_date": "Start date",
                    "end_date": "End date (optional)"
                }
            },
            {
                "name": "get_account_ledger",
                "description": "Get ledger entries for an account",
                "parameters": {
                    "account_number": "Account number",
                    "start_date": "Start date (optional)",
                    "end_date": "End date (optional)"
                }
            },
            {
                "name": "get_chart_of_accounts",
                "description": "Get all accounts in chart of accounts",
                "parameters": {}
            },
            {
                "name": "reconcile_accounts",
                "description": "Run account reconciliation",
                "parameters": {
                    "as_of_date": "Date (optional)"
                }
            }
        ]
    
    @staticmethod
    async def create_journal_entry(
        description: str,
        lines: List[Dict[str, Any]],
        reference: str = "",
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Create journal entry"""
        
        entry_date = datetime.fromisoformat(date) if date else datetime.now(timezone.utc)
        
        entry = journal_entry_service.create_entry(
            description=description,
            date=entry_date,
            reference=reference
        )
        
        # Add lines
        for line in lines:
            entry.add_line(JournalEntryLine(
                account_number=line["account_number"],
                debit=line.get("debit", 0.0),
                credit=line.get("credit", 0.0),
                description=line.get("description", "")
            ))
        
        # Validate
        validation = entry.validate()
        
        return {
            "success": True,
            "entry_id": entry.entry_id,
            "validation": validation,
            "entry": entry.to_dict()
        }
    
    @staticmethod
    async def post_journal_entry(entry_id: str) -> Dict[str, Any]:
        """MCP tool: Post journal entry"""
        
        entry = journal_entry_service.get_entry(entry_id)
        
        if not entry:
            return {"success": False, "error": "Entry not found"}
        
        if entry.is_posted:
            return {"success": False, "error": "Entry already posted"}
        
        try:
            entry.post()
            general_ledger.post_journal_entry(entry)
            
            return {
                "success": True,
                "entry_id": entry_id,
                "posted_at": entry.posted_at
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_account_balance(
        account_number: str,
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get account balance"""
        
        date = datetime.fromisoformat(as_of_date) if as_of_date else None
        
        account = chart_of_accounts.get_account(account_number)
        
        if not account:
            return {"success": False, "error": "Account not found"}
        
        balance = general_ledger.get_account_balance(account_number, date)
        
        return {
            "success": True,
            "account_number": account_number,
            "account_name": account.name,
            "balance": balance,
            "as_of_date": (date or datetime.now(timezone.utc)).isoformat()
        }
    
    @staticmethod
    async def get_trial_balance(
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get trial balance"""
        
        date = datetime.fromisoformat(as_of_date) if as_of_date else None
        
        trial_balance = general_ledger.generate_trial_balance(date)
        
        return {
            "success": True,
            "trial_balance": trial_balance
        }
    
    @staticmethod
    async def get_balance_sheet(
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get balance sheet"""
        
        date = datetime.fromisoformat(as_of_date) if as_of_date else None
        
        balance_sheet = financial_statements.generate_balance_sheet(date)
        
        return {
            "success": True,
            "balance_sheet": balance_sheet
        }
    
    @staticmethod
    async def get_income_statement(
        start_date: str,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get income statement"""
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
        
        income_statement = financial_statements.generate_income_statement(start, end)
        
        return {
            "success": True,
            "income_statement": income_statement
        }
    
    @staticmethod
    async def get_cash_flow_statement(
        start_date: str,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get cash flow statement"""
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
        
        cash_flow = financial_statements.generate_cash_flow_statement(start, end)
        
        return {
            "success": True,
            "cash_flow_statement": cash_flow
        }
    
    @staticmethod
    async def get_account_ledger(
        account_number: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get account ledger"""
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        ledger = general_ledger.get_account_ledger(account_number, start, end)
        
        return {
            "success": True,
            "account_number": account_number,
            "entries": ledger
        }
    
    @staticmethod
    async def get_chart_of_accounts() -> Dict[str, Any]:
        """MCP tool: Get chart of accounts"""
        
        accounts = chart_of_accounts.get_all_accounts()
        
        return {
            "success": True,
            "accounts": [acc.to_dict() for acc in accounts],
            "count": len(accounts)
        }
    
    @staticmethod
    async def reconcile_accounts(
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Reconcile accounts"""
        
        date = datetime.fromisoformat(as_of_date) if as_of_date else datetime.now(timezone.utc)
        
        result = await reconciliation_service.run_full_reconciliation(date)
        
        return {
            "success": True,
            "reconciliation": result
        }

# Global instance
accounting_mcp_tools = AccountingMCPTools()

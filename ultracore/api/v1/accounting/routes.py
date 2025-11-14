"""
Accounting API Routes
Complete RESTful API for accounting system
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ultracore.modules.accounting.journal_entry import journal_entry_service, JournalEntryLine
from ultracore.modules.accounting.general_ledger import general_ledger
from ultracore.modules.accounting.financial_statements import financial_statements
from ultracore.modules.accounting.reconciliation import reconciliation_service
from ultracore.modules.accounting.chart_of_accounts import chart_of_accounts

router = APIRouter(prefix="/api/v1/accounting", tags=["accounting"])

# ============================================================================
# REQUEST MODELS
# ============================================================================

class JournalLineRequest(BaseModel):
    account_number: str
    debit: float = 0.0
    credit: float = 0.0
    description: str = ""

class JournalEntryRequest(BaseModel):
    description: str
    lines: List[JournalLineRequest]
    reference: str = ""
    date: Optional[str] = None

# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@router.get("/chart-of-accounts")
async def get_chart_of_accounts():
    """Get all accounts"""
    accounts = chart_of_accounts.get_all_accounts()
    
    return {
        "accounts": [acc.to_dict() for acc in accounts],
        "count": len(accounts)
    }

@router.get("/chart-of-accounts/{account_number}")
async def get_account(account_number: str):
    """Get specific account"""
    account = chart_of_accounts.get_account(account_number)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account.to_dict()

# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

@router.post("/journal-entries/create")
async def create_journal_entry(request: JournalEntryRequest):
    """Create new journal entry"""
    try:
        entry_date = datetime.fromisoformat(request.date) if request.date else datetime.now(timezone.utc)
        
        entry = journal_entry_service.create_entry(
            description=request.description,
            date=entry_date,
            reference=request.reference
        )
        
        # Add lines
        for line in request.lines:
            entry.add_line(JournalEntryLine(
                account_number=line.account_number,
                debit=line.debit,
                credit=line.credit,
                description=line.description
            ))
        
        # Validate
        validation = entry.validate()
        
        return {
            "entry_id": entry.entry_id,
            "validation": validation,
            "entry": entry.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/journal-entries/{entry_id}/post")
async def post_journal_entry(entry_id: str):
    """Post journal entry to ledger"""
    try:
        entry = journal_entry_service.get_entry(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        if entry.is_posted:
            raise HTTPException(status_code=400, detail="Entry already posted")
        
        entry.post()
        general_ledger.post_journal_entry(entry)
        
        return {
            "entry_id": entry_id,
            "posted": True,
            "posted_at": entry.posted_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/journal-entries/{entry_id}")
async def get_journal_entry(entry_id: str):
    """Get journal entry"""
    entry = journal_entry_service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return entry.to_dict()

@router.get("/journal-entries")
async def get_all_journal_entries():
    """Get all journal entries"""
    entries = journal_entry_service.get_all_entries()
    
    return {
        "entries": [e.to_dict() for e in entries],
        "count": len(entries)
    }

# ============================================================================
# GENERAL LEDGER
# ============================================================================

@router.get("/ledger/account/{account_number}")
async def get_account_ledger(
    account_number: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get ledger entries for account"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    ledger = general_ledger.get_account_ledger(account_number, start, end)
    
    return {
        "account_number": account_number,
        "entries": ledger,
        "count": len(ledger)
    }

@router.get("/ledger/balance/{account_number}")
async def get_account_balance(
    account_number: str,
    as_of_date: Optional[str] = None
):
    """Get account balance"""
    date = datetime.fromisoformat(as_of_date) if as_of_date else None
    
    account = chart_of_accounts.get_account(account_number)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    balance = general_ledger.get_account_balance(account_number, date)
    
    return {
        "account_number": account_number,
        "account_name": account.name,
        "balance": balance,
        "as_of_date": (date or datetime.now(timezone.utc)).isoformat()
    }

@router.get("/ledger/trial-balance")
async def get_trial_balance(as_of_date: Optional[str] = None):
    """Generate trial balance"""
    date = datetime.fromisoformat(as_of_date) if as_of_date else None
    
    trial_balance = general_ledger.generate_trial_balance(date)
    
    return trial_balance

# ============================================================================
# FINANCIAL STATEMENTS
# ============================================================================

@router.get("/statements/balance-sheet")
async def get_balance_sheet(as_of_date: Optional[str] = None):
    """Generate balance sheet"""
    date = datetime.fromisoformat(as_of_date) if as_of_date else None
    
    balance_sheet = financial_statements.generate_balance_sheet(date)
    
    return balance_sheet

@router.get("/statements/income-statement")
async def get_income_statement(
    start_date: str,
    end_date: Optional[str] = None
):
    """Generate income statement"""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
    
    income_statement = financial_statements.generate_income_statement(start, end)
    
    return income_statement

@router.get("/statements/cash-flow")
async def get_cash_flow_statement(
    start_date: str,
    end_date: Optional[str] = None
):
    """Generate cash flow statement"""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
    
    cash_flow = financial_statements.generate_cash_flow_statement(start, end)
    
    return cash_flow

# ============================================================================
# RECONCILIATION
# ============================================================================

@router.post("/reconciliation/run")
async def run_reconciliation(as_of_date: Optional[str] = None):
    """Run full reconciliation"""
    date = datetime.fromisoformat(as_of_date) if as_of_date else datetime.now(timezone.utc)
    
    result = await reconciliation_service.run_full_reconciliation(date)
    
    return result

@router.get("/reconciliation/{recon_id}")
async def get_reconciliation(recon_id: str):
    """Get reconciliation details"""
    recon = reconciliation_service.get_reconciliation(recon_id)
    
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    
    return recon

@router.get("/reconciliation")
async def get_all_reconciliations():
    """Get all reconciliations"""
    reconciliations = reconciliation_service.get_all_reconciliations()
    
    return {
        "reconciliations": reconciliations,
        "count": len(reconciliations)
    }

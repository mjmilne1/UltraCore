"""
UltraCore Accounting API

Complete REST API for accounting system:
- Chart of Accounts management
- Journal entries (create, post, reverse)
- Financial statements (Balance Sheet, P&L, Cash Flow)
- Trial balance
- Reconciliation
- Financial ratios
- Dashboard analytics
- Real-time monitoring
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal

from ultracore.accounting.chart_of_accounts import (
    get_chart_of_accounts, AccountType, AccountSubType, 
    AccountClass, DataMeshDomain
)
from ultracore.accounting.general_ledger import (
    get_general_ledger, JournalEntryType, JournalEntryStatus,
    post_loan_disbursement, post_loan_repayment, post_deposit,
    post_fee_income, post_interest_expense
)
from ultracore.accounting.financial_statements import (
    get_statements_generator, StatementFormat, CashFlowMethod
)
from ultracore.accounting.reconciliation_agents import (
    get_reconciliation_orchestrator, ReconciliationType,
    ReconciliationItem, reconcile_bank_statement
)


# ============================================================================
# Pydantic Models
# ============================================================================

class AccountResponse(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    account_subtype: str
    account_class: str
    domain_owner: str
    parent_account: Optional[str]
    level: int
    active: bool
    current_balance: str  # Decimal as string
    normal_balance: str


class CreateJournalEntryRequest(BaseModel):
    entry_type: str = "STANDARD"
    entry_date: str  # ISO date
    description: str
    reference: Optional[str] = None
    lines: List[Dict[str, Any]]
    created_by: str
    auto_post: bool = False


class JournalEntryResponse(BaseModel):
    entry_id: str
    entry_type: str
    entry_date: str
    description: str
    status: str
    total_debits: str
    total_credits: str
    is_balanced: bool
    created_by: str
    posted_at: Optional[str]
    lines: List[Dict[str, Any]]


class BalanceSheetResponse(BaseModel):
    statement_id: str
    as_of_date: str
    total_assets: str
    total_liabilities: str
    total_equity: str
    is_balanced: bool
    current_assets: List[Dict[str, Any]]
    non_current_assets: List[Dict[str, Any]]
    current_liabilities: List[Dict[str, Any]]
    equity: List[Dict[str, Any]]
    ai_insights: List[str]
    health_score: float


class ProfitLossResponse(BaseModel):
    statement_id: str
    period_start: str
    period_end: str
    total_revenue: str
    total_expenses: str
    net_income: str
    net_margin_percent: float
    revenue_lines: List[Dict[str, Any]]
    expense_lines: List[Dict[str, Any]]
    ai_insights: List[str]
    profitability_score: float


class CashFlowResponse(BaseModel):
    statement_id: str
    period_start: str
    period_end: str
    beginning_cash: str
    ending_cash: str
    net_change_in_cash: str
    net_cash_from_operations: str
    operating_activities: List[Dict[str, Any]]
    ai_insights: List[str]
    liquidity_score: float


class FinancialRatiosResponse(BaseModel):
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    return_on_assets: Optional[float]
    return_on_equity: Optional[float]
    debt_to_equity: Optional[float]
    profit_margin: Optional[float]
    loan_to_deposit: Optional[float]
    liquidity_health: str
    profitability_health: str
    leverage_health: str


class ReconciliationRequest(BaseModel):
    reconciliation_type: str
    source_a: str
    source_b: str
    start_date: str
    end_date: str
    bank_transactions: Optional[List[Dict[str, Any]]] = None
    account_code: Optional[str] = None


class ReconciliationResponse(BaseModel):
    session_id: str
    status: str
    progress_percent: float
    matched_items: int
    unmatched_items: int
    total_discrepancy_amount: str
    discrepancies: List[Dict[str, Any]]
    matches: List[Dict[str, Any]]


class DashboardResponse(BaseModel):
    summary: Dict[str, Any]
    financial_health: Dict[str, Any]
    recent_entries: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    key_metrics: Dict[str, Any]


class LoanDisbursementRequest(BaseModel):
    loan_id: str
    amount: str
    customer_account: str
    disbursed_by: str


class LoanRepaymentRequest(BaseModel):
    loan_id: str
    principal: str
    interest: str
    customer_account: str
    paid_by: str


class DepositRequest(BaseModel):
    account_id: str
    amount: str
    deposited_by: str


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="UltraCore Accounting API",
    description="Enterprise accounting system with AI-powered features",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
chart = get_chart_of_accounts()
gl = get_general_ledger()
statements = get_statements_generator()
reconciliation = get_reconciliation_orchestrator()


# ============================================================================
# Chart of Accounts Endpoints
# ============================================================================

@app.get("/api/accounting/chart-of-accounts", response_model=List[AccountResponse])
async def get_chart_of_accounts_list(
    account_type: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    active_only: bool = Query(True)
):
    """Get chart of accounts"""
    
    accounts = list(chart.accounts.values())
    
    # Filter by type
    if account_type:
        accounts = [a for a in accounts if a.account_type.value == account_type]
    
    # Filter by domain
    if domain:
        accounts = [a for a in accounts if a.domain_owner.value == domain]
    
    # Filter by active
    if active_only:
        accounts = [a for a in accounts if a.active]
    
    return [
        AccountResponse(
            account_code=a.account_code,
            account_name=a.account_name,
            account_type=a.account_type.value,
            account_subtype=a.account_subtype.value,
            account_class=a.account_class.value,
            domain_owner=a.domain_owner.value,
            parent_account=a.parent_account,
            level=a.level,
            active=a.active,
            current_balance=str(a.current_balance),
            normal_balance=a.normal_balance
        )
        for a in sorted(accounts, key=lambda x: x.account_code)
    ]


@app.get("/api/accounting/accounts/{account_code}", response_model=AccountResponse)
async def get_account(account_code: str):
    """Get specific account"""
    
    account = chart.get_account(account_code)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_code} not found")
    
    return AccountResponse(
        account_code=account.account_code,
        account_name=account.account_name,
        account_type=account.account_type.value,
        account_subtype=account.account_subtype.value,
        account_class=account.account_class.value,
        domain_owner=account.domain_owner.value,
        parent_account=account.parent_account,
        level=account.level,
        active=account.active,
        current_balance=str(account.current_balance),
        normal_balance=account.normal_balance
    )


@app.get("/api/accounting/accounts/{account_code}/balance")
async def get_account_balance(
    account_code: str,
    as_of_date: Optional[str] = Query(None)
):
    """Get account balance"""
    
    as_of = date.fromisoformat(as_of_date) if as_of_date else date.today()
    
    balance = await gl.get_account_balance(account_code, as_of)
    
    return {
        'account_code': balance.account_code,
        'account_name': balance.account_name,
        'account_type': balance.account_type.value,
        'net_balance': str(balance.net_balance),
        'debit_balance': str(balance.debit_balance),
        'credit_balance': str(balance.credit_balance),
        'as_of_date': balance.as_of_date.isoformat()
    }


@app.get("/api/accounting/accounts/{account_code}/transactions")
async def get_account_transactions(
    account_code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get account transaction history"""
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    transactions = await gl.get_account_transactions(account_code, start, end)
    
    return {
        'account_code': account_code,
        'transaction_count': len(transactions),
        'transactions': [
            {
                'entry_id': entry.entry_id,
                'entry_date': entry.entry_date.isoformat(),
                'description': entry.description,
                'debit': str(line.debit_amount),
                'credit': str(line.credit_amount),
                'reference': entry.reference
            }
            for entry, line in transactions
        ]
    }


# ============================================================================
# Journal Entry Endpoints
# ============================================================================

@app.post("/api/accounting/journal-entries", response_model=JournalEntryResponse)
async def create_journal_entry(request: CreateJournalEntryRequest):
    """Create a new journal entry"""
    
    entry = await gl.create_entry(
        entry_type=JournalEntryType(request.entry_type),
        entry_date=date.fromisoformat(request.entry_date),
        description=request.description,
        lines=request.lines,
        created_by=request.created_by,
        reference=request.reference,
        auto_post=request.auto_post
    )
    
    return JournalEntryResponse(
        entry_id=entry.entry_id,
        entry_type=entry.entry_type.value,
        entry_date=entry.entry_date.isoformat(),
        description=entry.description,
        status=entry.status.value,
        total_debits=str(entry.total_debits()),
        total_credits=str(entry.total_credits()),
        is_balanced=entry.is_balanced(),
        created_by=entry.created_by,
        posted_at=entry.posted_at.isoformat() if entry.posted_at else None,
        lines=[
            {
                'line_id': line.line_id,
                'account_code': line.account_code,
                'account_name': line.account_name,
                'debit': str(line.debit_amount),
                'credit': str(line.credit_amount),
                'description': line.description
            }
            for line in entry.lines
        ]
    )


@app.get("/api/accounting/journal-entries/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(entry_id: str):
    """Get specific journal entry"""
    
    entry = await gl.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    
    return JournalEntryResponse(
        entry_id=entry.entry_id,
        entry_type=entry.entry_type.value,
        entry_date=entry.entry_date.isoformat(),
        description=entry.description,
        status=entry.status.value,
        total_debits=str(entry.total_debits()),
        total_credits=str(entry.total_credits()),
        is_balanced=entry.is_balanced(),
        created_by=entry.created_by,
        posted_at=entry.posted_at.isoformat() if entry.posted_at else None,
        lines=[
            {
                'line_id': line.line_id,
                'account_code': line.account_code,
                'account_name': line.account_name,
                'debit': str(line.debit_amount),
                'credit': str(line.credit_amount),
                'description': line.description
            }
            for line in entry.lines
        ]
    )


@app.get("/api/accounting/journal-entries")
async def get_journal_entries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    account_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Query journal entries"""
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    status_enum = JournalEntryStatus(status) if status else None
    
    entries = await gl.get_entries(
        start_date=start,
        end_date=end,
        account_code=account_code,
        status=status_enum,
        limit=limit
    )
    
    return {
        'total': len(entries),
        'entries': [
            {
                'entry_id': e.entry_id,
                'entry_date': e.entry_date.isoformat(),
                'description': e.description,
                'status': e.status.value,
                'amount': str(e.total_debits()),
                'created_by': e.created_by
            }
            for e in entries
        ]
    }


@app.post("/api/accounting/journal-entries/{entry_id}/post")
async def post_journal_entry(entry_id: str, posted_by: str = Body(..., embed=True)):
    """Post a journal entry"""
    
    success = await gl.post_entry(entry_id, posted_by)
    
    if success:
        return {'status': 'posted', 'entry_id': entry_id}
    else:
        raise HTTPException(status_code=400, detail="Failed to post entry")


@app.post("/api/accounting/journal-entries/{entry_id}/reverse")
async def reverse_journal_entry(
    entry_id: str,
    reversal_date: str = Body(...),
    reversed_by: str = Body(...),
    reason: str = Body(...)
):
    """Reverse a journal entry"""
    
    reversal = await gl.reverse_entry(
        entry_id=entry_id,
        reversal_date=date.fromisoformat(reversal_date),
        reversed_by=reversed_by,
        reason=reason
    )
    
    return {
        'status': 'reversed',
        'original_entry_id': entry_id,
        'reversal_entry_id': reversal.entry_id
    }


# ============================================================================
# Convenience Posting Endpoints
# ============================================================================

@app.post("/api/accounting/post-loan-disbursement")
async def post_loan_disbursement_endpoint(request: LoanDisbursementRequest):
    """Post loan disbursement to GL"""
    
    entry = await post_loan_disbursement(
        loan_id=request.loan_id,
        amount=Decimal(request.amount),
        customer_account=request.customer_account,
        disbursed_by=request.disbursed_by
    )
    
    return {
        'status': 'posted',
        'entry_id': entry.entry_id,
        'amount': str(entry.total_debits())
    }


@app.post("/api/accounting/post-loan-repayment")
async def post_loan_repayment_endpoint(request: LoanRepaymentRequest):
    """Post loan repayment to GL"""
    
    entries = await post_loan_repayment(
        loan_id=request.loan_id,
        principal=Decimal(request.principal),
        interest=Decimal(request.interest),
        customer_account=request.customer_account,
        paid_by=request.paid_by
    )
    
    return {
        'status': 'posted',
        'entries_created': len(entries),
        'entry_ids': [e.entry_id for e in entries]
    }


@app.post("/api/accounting/post-deposit")
async def post_deposit_endpoint(request: DepositRequest):
    """Post customer deposit to GL"""
    
    entry = await post_deposit(
        account_id=request.account_id,
        amount=Decimal(request.amount),
        deposited_by=request.deposited_by
    )
    
    return {
        'status': 'posted',
        'entry_id': entry.entry_id,
        'amount': str(entry.total_debits())
    }


# ============================================================================
# Financial Statements Endpoints
# ============================================================================

@app.get("/api/accounting/statements/balance-sheet", response_model=BalanceSheetResponse)
async def get_balance_sheet(
    as_of_date: str = Query(...),
    comparative: bool = Query(False),
    prior_date: Optional[str] = Query(None)
):
    """Generate balance sheet"""
    
    as_of = date.fromisoformat(as_of_date)
    prior = date.fromisoformat(prior_date) if prior_date else None
    
    bs = await statements.generate_balance_sheet(
        as_of_date=as_of,
        comparative=comparative,
        prior_date=prior
    )
    
    return BalanceSheetResponse(
        statement_id=bs.statement_id,
        as_of_date=bs.as_of_date.isoformat(),
        total_assets=str(bs.total_assets),
        total_liabilities=str(bs.total_liabilities),
        total_equity=str(bs.total_equity),
        is_balanced=bs.is_balanced,
        current_assets=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'level': line.level
            }
            for line in bs.current_assets
        ],
        non_current_assets=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'level': line.level
            }
            for line in bs.non_current_assets
        ],
        current_liabilities=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'level': line.level
            }
            for line in bs.current_liabilities
        ],
        equity=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'level': line.level
            }
            for line in bs.equity
        ],
        ai_insights=bs.ai_insights,
        health_score=bs.health_score
    )


@app.get("/api/accounting/statements/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss(
    period_start: str = Query(...),
    period_end: str = Query(...)
):
    """Generate profit & loss statement"""
    
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    
    pl = await statements.generate_profit_loss(
        period_start=start,
        period_end=end
    )
    
    return ProfitLossResponse(
        statement_id=pl.statement_id,
        period_start=pl.period_start.isoformat(),
        period_end=pl.period_end.isoformat(),
        total_revenue=str(pl.total_revenue),
        total_expenses=str(pl.total_expenses),
        net_income=str(pl.net_income),
        net_margin_percent=pl.net_margin_percent,
        revenue_lines=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'percent_of_revenue': line.percent_of_revenue
            }
            for line in pl.revenue_lines
        ],
        expense_lines=[
            {
                'name': line.line_name,
                'amount': str(line.amount),
                'percent_of_revenue': line.percent_of_revenue
            }
            for line in pl.expense_lines
        ],
        ai_insights=pl.ai_insights,
        profitability_score=pl.profitability_score
    )


@app.get("/api/accounting/statements/cash-flow", response_model=CashFlowResponse)
async def get_cash_flow(
    period_start: str = Query(...),
    period_end: str = Query(...),
    method: str = Query("INDIRECT")
):
    """Generate cash flow statement"""
    
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    
    cf = await statements.generate_cash_flow(
        period_start=start,
        period_end=end,
        method=CashFlowMethod(method)
    )
    
    return CashFlowResponse(
        statement_id=cf.statement_id,
        period_start=cf.period_start.isoformat(),
        period_end=cf.period_end.isoformat(),
        beginning_cash=str(cf.beginning_cash),
        ending_cash=str(cf.ending_cash),
        net_change_in_cash=str(cf.net_change_in_cash),
        net_cash_from_operations=str(cf.net_cash_from_operations),
        operating_activities=[
            {
                'name': line.line_name,
                'amount': str(line.amount)
            }
            for line in cf.operating_activities
        ],
        ai_insights=cf.ai_insights,
        liquidity_score=cf.liquidity_score
    )


@app.get("/api/accounting/statements/trial-balance")
async def get_trial_balance(as_of_date: str = Query(...)):
    """Generate trial balance"""
    
    as_of = date.fromisoformat(as_of_date)
    
    tb = await gl.get_trial_balance(as_of)
    
    return {
        'as_of_date': tb.as_of_date.isoformat(),
        'total_debits': str(tb.total_debits),
        'total_credits': str(tb.total_credits),
        'is_balanced': tb.is_balanced,
        'accounts': [
            {
                'account_code': acc.account_code,
                'account_name': acc.account_name,
                'debit_balance': str(acc.debit_balance),
                'credit_balance': str(acc.credit_balance),
                'net_balance': str(acc.net_balance)
            }
            for acc in tb.accounts
        ]
    }


@app.get("/api/accounting/financial-ratios", response_model=FinancialRatiosResponse)
async def get_financial_ratios(
    as_of_date: str = Query(...),
    period_start: str = Query(...),
    period_end: str = Query(...)
):
    """Calculate financial ratios"""
    
    as_of = date.fromisoformat(as_of_date)
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    
    ratios = await statements.calculate_financial_ratios(as_of, start, end)
    
    return FinancialRatiosResponse(
        current_ratio=ratios.current_ratio,
        quick_ratio=ratios.quick_ratio,
        return_on_assets=ratios.return_on_assets,
        return_on_equity=ratios.return_on_equity,
        debt_to_equity=ratios.debt_to_equity,
        profit_margin=ratios.profit_margin,
        loan_to_deposit=ratios.loan_to_deposit,
        liquidity_health=ratios.liquidity_health,
        profitability_health=ratios.profitability_health,
        leverage_health=ratios.leverage_health
    )


# ============================================================================
# Reconciliation Endpoints
# ============================================================================

@app.post("/api/accounting/reconciliation", response_model=ReconciliationResponse)
async def start_reconciliation(request: ReconciliationRequest):
    """Start a reconciliation session"""
    
    if request.reconciliation_type == "BANK" and request.account_code and request.bank_transactions:
        # Bank reconciliation
        session = await reconcile_bank_statement(
            account_code=request.account_code,
            bank_transactions=request.bank_transactions,
            start_date=date.fromisoformat(request.start_date),
            end_date=date.fromisoformat(request.end_date)
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid reconciliation request"
        )
    
    return ReconciliationResponse(
        session_id=session.session_id,
        status=session.status.value,
        progress_percent=session.progress_percent,
        matched_items=session.matched_items,
        unmatched_items=session.unmatched_items,
        total_discrepancy_amount=str(session.total_discrepancy_amount),
        discrepancies=[
            {
                'discrepancy_id': d.discrepancy_id,
                'type': d.discrepancy_type.value,
                'description': d.description,
                'amount': str(d.amount),
                'severity': d.severity,
                'suggested_actions': d.suggested_actions
            }
            for d in session.discrepancies
        ],
        matches=[
            {
                'match_id': m.match_id,
                'confidence': m.match_confidence,
                'amount_difference': str(m.amount_difference)
            }
            for m in session.matches
        ]
    )


@app.get("/api/accounting/reconciliation/{session_id}", response_model=ReconciliationResponse)
async def get_reconciliation_session(session_id: str):
    """Get reconciliation session details"""
    
    session = await reconciliation.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return ReconciliationResponse(
        session_id=session.session_id,
        status=session.status.value,
        progress_percent=session.progress_percent,
        matched_items=session.matched_items,
        unmatched_items=session.unmatched_items,
        total_discrepancy_amount=str(session.total_discrepancy_amount),
        discrepancies=[
            {
                'discrepancy_id': d.discrepancy_id,
                'type': d.discrepancy_type.value,
                'description': d.description,
                'amount': str(d.amount),
                'severity': d.severity,
                'suggested_actions': d.suggested_actions,
                'resolved': d.resolved
            }
            for d in session.discrepancies
        ],
        matches=[
            {
                'match_id': m.match_id,
                'confidence': m.match_confidence,
                'validated': m.validated
            }
            for m in session.matches
        ]
    )


@app.post("/api/accounting/reconciliation/{session_id}/resolve-discrepancy")
async def resolve_discrepancy(
    session_id: str,
    discrepancy_id: str = Body(...),
    resolution: str = Body(...),
    resolved_by: str = Body(...)
):
    """Resolve a discrepancy"""
    
    success = await reconciliation.resolve_discrepancy(
        session_id=session_id,
        discrepancy_id=discrepancy_id,
        resolution=resolution,
        resolved_by=resolved_by
    )
    
    if success:
        return {'status': 'resolved', 'discrepancy_id': discrepancy_id}
    else:
        raise HTTPException(status_code=404, detail="Discrepancy not found")


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@app.get("/api/accounting/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get accounting dashboard data"""
    
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # Get financial statements
    bs = await statements.generate_balance_sheet(today)
    pl = await statements.generate_profit_loss(month_start, today)
    ratios = await statements.calculate_financial_ratios(today, month_start, today)
    
    # Get recent entries
    recent_entries = await gl.get_entries(limit=10)
    
    # Get trial balance
    tb = await gl.get_trial_balance(today)
    
    return DashboardResponse(
        summary={
            'total_assets': str(bs.total_assets),
            'total_liabilities': str(bs.total_liabilities),
            'total_equity': str(bs.total_equity),
            'net_income_mtd': str(pl.net_income),
            'current_ratio': ratios.current_ratio
        },
        financial_health={
            'balance_sheet_health': bs.health_score,
            'profitability_score': pl.profitability_score,
            'liquidity_health': ratios.liquidity_health,
            'leverage_health': ratios.leverage_health
        },
        recent_entries=[
            {
                'entry_id': e.entry_id,
                'date': e.entry_date.isoformat(),
                'description': e.description,
                'amount': str(e.total_debits()),
                'status': e.status.value
            }
            for e in recent_entries
        ],
        alerts=[
            {
                'severity': 'WARNING',
                'message': 'Balance sheet out of balance'
            }
        ] if not bs.is_balanced else [],
        key_metrics={
            'accounts_with_balance': len([a for a in tb.accounts if a.net_balance != Decimal('0')]),
            'trial_balance_balanced': tb.is_balanced,
            'posted_entries_today': len([e for e in recent_entries if e.entry_date == today])
        }
    )


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'UltraCore Accounting API',
        'version': '1.0.0'
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'UltraCore Accounting API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health'
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )

"""
General Ledger API
"""
from fastapi import APIRouter
from typing import List, Dict
from pydantic import BaseModel
from decimal import Decimal

from ultracore.ledger.general_ledger import ledger, JournalEntry
from ultracore.ledger.accounts.chart_of_accounts import ChartOfAccounts, AccountType

router = APIRouter()


class PostJournalEntryRequest(BaseModel):
    description: str
    reference: str
    debits: List[Dict]
    credits: List[Dict]


@router.get('/chart-of-accounts')
async def get_chart_of_accounts():
    '''Get complete chart of accounts'''
    return {
        'accounts': ChartOfAccounts.ACCOUNTS,
        'total_accounts': len(ChartOfAccounts.ACCOUNTS)
    }


@router.get('/chart-of-accounts/type/{account_type}')
async def get_accounts_by_type(account_type: AccountType):
    '''Get accounts by type (ASSET, LIABILITY, etc)'''
    accounts = ChartOfAccounts.get_accounts_by_type(account_type)
    return {
        'account_type': account_type,
        'accounts': accounts,
        'count': len(accounts)
    }


@router.post('/journal-entries')
async def post_journal_entry(request: PostJournalEntryRequest):
    '''
    Post a journal entry (double-entry bookkeeping)
    
    Debits must equal Credits
    '''
    import uuid
    
    entry = JournalEntry(
        entry_id=f'JE-{str(uuid.uuid4())[:8]}',
        date=__import__('datetime').datetime.now(timezone.utc).isoformat(),
        description=request.description,
        reference=request.reference,
        debits=request.debits,
        credits=request.credits
    )
    
    return await ledger.post_journal_entry(entry)


@router.get('/trial-balance')
async def get_trial_balance():
    '''
    Generate trial balance report
    
    Shows all account balances
    Validates accounting equation: Assets = Liabilities + Equity
    '''
    return await ledger.get_trial_balance()


@router.get('/balance-sheet')
async def get_balance_sheet():
    '''
    Generate balance sheet
    
    Financial position statement:
    Assets = Liabilities + Equity
    '''
    trial_balance = await ledger.get_trial_balance()
    accounts = trial_balance['accounts']
    
    # Categorize accounts
    assets = {}
    liabilities = {}
    equity = {}
    
    for code, data in accounts.items():
        account = ChartOfAccounts.get_account(code)
        net = Decimal(data['net'])
        
        if account['type'].value in ['CASH', 'CUSTOMER_LOANS', 'FIXED_ASSETS', 'INTANGIBLE_ASSETS']:
            assets[code] = {**data, 'account_name': account['name']}
        elif account['type'].value in ['CUSTOMER_DEPOSITS', 'INTERBANK_BORROWINGS', 'BONDS_PAYABLE']:
            liabilities[code] = {**data, 'account_name': account['name']}
        elif account['type'].value in ['SHARE_CAPITAL', 'RETAINED_EARNINGS', 'RESERVES']:
            equity[code] = {**data, 'account_name': account['name']}
    
    total_assets = sum(Decimal(a['debit']) for a in assets.values())
    total_liabilities = sum(Decimal(l['credit']) for l in liabilities.values())
    total_equity = sum(Decimal(e['credit']) for e in equity.values())
    
    return {
        'as_of': trial_balance['as_of'],
        'assets': {
            'accounts': assets,
            'total': str(total_assets)
        },
        'liabilities': {
            'accounts': liabilities,
            'total': str(total_liabilities)
        },
        'equity': {
            'accounts': equity,
            'total': str(total_equity)
        },
        'balanced': total_assets == (total_liabilities + total_equity),
        'accounting_equation': f'{total_assets} = {total_liabilities} + {total_equity}'
    }


@router.get('/income-statement')
async def get_income_statement():
    '''
    Generate income statement (P&L)
    
    Revenue - Expenses = Net Income
    '''
    trial_balance = await ledger.get_trial_balance()
    accounts = trial_balance['accounts']
    
    revenue = {}
    expenses = {}
    
    for code, data in accounts.items():
        account = ChartOfAccounts.get_account(code)
        
        if account['type'].value in ['INTEREST_INCOME', 'FEE_INCOME', 'TRADING_INCOME']:
            revenue[code] = {**data, 'account_name': account['name']}
        elif account['type'].value in ['INTEREST_EXPENSE', 'OPERATING_EXPENSES', 'LOAN_LOSS_PROVISION']:
            expenses[code] = {**data, 'account_name': account['name']}
    
    total_revenue = sum(Decimal(r['credit']) for r in revenue.values())
    total_expenses = sum(Decimal(e['debit']) for e in expenses.values())
    net_income = total_revenue - total_expenses
    
    return {
        'period': trial_balance['as_of'],
        'revenue': {
            'accounts': revenue,
            'total': str(total_revenue)
        },
        'expenses': {
            'accounts': expenses,
            'total': str(total_expenses)
        },
        'net_income': str(net_income),
        'profitable': net_income > 0
    }

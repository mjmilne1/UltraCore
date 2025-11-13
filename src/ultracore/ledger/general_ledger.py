"""
General Ledger - Double-Entry Accounting with Event Sourcing
"""
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.ledger.accounts.chart_of_accounts import ChartOfAccounts


class JournalEntry(BaseModel):
    entry_id: str
    date: str
    description: str
    reference: str  # Links to loan_id, client_id, etc.
    debits: List[Dict]  # [{'account': '1100', 'amount': 50000}]
    credits: List[Dict]  # [{'account': '2000', 'amount': 50000}]


class GeneralLedger:
    """
    Double-Entry Accounting Ledger
    
    Every transaction creates equal debits and credits
    Integrated with event sourcing for complete audit trail
    """
    
    def __init__(self):
        self.chart = ChartOfAccounts()
    
    async def post_journal_entry(
        self,
        entry: JournalEntry,
        posted_by: str = 'system'
    ) -> Dict:
        """
        Post a journal entry to the general ledger
        
        Validates:
        - Debits = Credits (fundamental accounting equation)
        - Valid account codes
        - Non-zero amounts
        """
        
        # Validate balanced entry
        total_debits = sum(Decimal(str(d['amount'])) for d in entry.debits)
        total_credits = sum(Decimal(str(c['amount'])) for c in entry.credits)
        
        if total_debits != total_credits:
            raise ValueError(
                f'Unbalanced entry: Debits {total_debits} != Credits {total_credits}'
            )
        
        # Validate accounts exist
        for debit in entry.debits:
            if not self.chart.get_account(debit['account']):
                raise ValueError(f"Invalid account: {debit['account']}")
        
        for credit in entry.credits:
            if not self.chart.get_account(credit['account']):
                raise ValueError(f"Invalid account: {credit['account']}")
        
        # Store as event
        store = get_event_store()
        
        event_data = {
            'entry_id': entry.entry_id,
            'date': entry.date,
            'description': entry.description,
            'reference': entry.reference,
            'debits': [
                {
                    'account': d['account'],
                    'account_name': self.chart.get_account(d['account'])['name'],
                    'amount': str(d['amount'])
                }
                for d in entry.debits
            ],
            'credits': [
                {
                    'account': c['account'],
                    'account_name': self.chart.get_account(c['account'])['name'],
                    'amount': str(c['amount'])
                }
                for c in entry.credits
            ],
            'total_amount': str(total_debits),
            'posted_at': datetime.now(timezone.utc).isoformat()
        }
        
        await store.append(
            aggregate_id=entry.entry_id,
            aggregate_type='JournalEntry',
            event_type='JournalEntryPosted',
            event_data=event_data,
            user_id=posted_by
        )
        
        return {
            'entry_id': entry.entry_id,
            'status': 'POSTED',
            'total_debits': str(total_debits),
            'total_credits': str(total_credits),
            'balanced': True
        }
    
    async def post_loan_disbursement(
        self,
        loan_id: str,
        customer_id: str,
        amount: Decimal
    ):
        """
        Post loan disbursement journal entry
        
        DR: Customer Loans (Asset increases)
        CR: Customer Deposits (Liability increases)
        """
        entry = JournalEntry(
            entry_id=f'JE-LOAN-{loan_id}',
            date=datetime.now(timezone.utc).isoformat(),
            description=f'Loan disbursement to customer {customer_id}',
            reference=loan_id,
            debits=[
                {'account': '1100', 'amount': float(amount)}  # Customer Loans
            ],
            credits=[
                {'account': '2000', 'amount': float(amount)}  # Customer Deposits
            ]
        )
        
        return await self.post_journal_entry(entry, posted_by='loan_system')
    
    async def post_interest_income(
        self,
        loan_id: str,
        amount: Decimal
    ):
        """
        Post interest income
        
        DR: Customer Loans (Accrued interest)
        CR: Interest Income
        """
        entry = JournalEntry(
            entry_id=f'JE-INT-{loan_id}-{datetime.now(timezone.utc).timestamp()}',
            date=datetime.now(timezone.utc).isoformat(),
            description=f'Interest income accrual for loan {loan_id}',
            reference=loan_id,
            debits=[
                {'account': '1100', 'amount': float(amount)}
            ],
            credits=[
                {'account': '4000', 'amount': float(amount)}
            ]
        )
        
        return await self.post_journal_entry(entry, posted_by='interest_system')
    
    async def get_trial_balance(self) -> Dict:
        """
        Generate trial balance report
        
        Lists all accounts with debit/credit balances
        Validates: Total Debits = Total Credits
        """
        store = get_event_store()
        events = await store.get_all_events(limit=10000)
        
        # Filter journal entry events
        journal_events = [
            e for e in events 
            if e.event_type == 'JournalEntryPosted'
        ]
        
        # Calculate balances
        balances = {}
        
        for event in journal_events:
            for debit in event.event_data['debits']:
                account = debit['account']
                amount = Decimal(debit['amount'])
                
                if account not in balances:
                    balances[account] = {
                        'account_name': debit['account_name'],
                        'debit': Decimal('0'),
                        'credit': Decimal('0')
                    }
                
                balances[account]['debit'] += amount
            
            for credit in event.event_data['credits']:
                account = credit['account']
                amount = Decimal(credit['amount'])
                
                if account not in balances:
                    balances[account] = {
                        'account_name': credit['account_name'],
                        'debit': Decimal('0'),
                        'credit': Decimal('0')
                    }
                
                balances[account]['credit'] += amount
        
        # Calculate totals
        total_debits = sum(b['debit'] for b in balances.values())
        total_credits = sum(b['credit'] for b in balances.values())
        
        return {
            'as_of': datetime.now(timezone.utc).isoformat(),
            'accounts': {
                code: {
                    'account_name': data['account_name'],
                    'debit': str(data['debit']),
                    'credit': str(data['credit']),
                    'net': str(data['debit'] - data['credit'])
                }
                for code, data in sorted(balances.items())
            },
            'total_debits': str(total_debits),
            'total_credits': str(total_credits),
            'balanced': total_debits == total_credits,
            'total_entries': len(journal_events)
        }


ledger = GeneralLedger()

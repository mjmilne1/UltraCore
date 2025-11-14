"""
Journal Entries - Double-Entry Bookkeeping
Event-sourced, immutable accounting records
"""
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.modules.accounting.general_ledger.chart_of_accounts import get_chart_of_accounts, NormalBalance


class EntryType(str, Enum):
    STANDARD = 'STANDARD'
    ADJUSTING = 'ADJUSTING'
    CLOSING = 'CLOSING'
    REVERSING = 'REVERSING'


class JournalEntryLine:
    """Single line in a journal entry (debit or credit)"""
    
    def __init__(
        self,
        account_code: str,
        debit: Decimal = Decimal('0'),
        credit: Decimal = Decimal('0'),
        description: str = ''
    ):
        self.account_code = account_code
        self.debit = debit
        self.credit = credit
        self.description = description
        
        # Validate: can't have both debit and credit
        if debit > 0 and credit > 0:
            raise ValueError('Cannot have both debit and credit on same line')


class JournalEntry:
    """
    Double-Entry Journal Entry
    
    Immutable once posted
    Event-sourced to Kafka
    """
    
    def __init__(self, entry_id: Optional[str] = None):
        self.entry_id = entry_id or f'JE-{uuid.uuid4().hex[:12].upper()}'
        self.entry_date = datetime.now(timezone.utc)
        self.entry_type: EntryType = EntryType.STANDARD
        self.description: str = ''
        self.lines: List[JournalEntryLine] = []
        self.is_posted: bool = False
        self.posted_at: Optional[datetime] = None
        self.reference_id: Optional[str] = None  # Link to source transaction
        self.reference_type: Optional[str] = None  # PAYMENT, LOAN, DEPOSIT, etc.
    
    def add_line(
        self,
        account_code: str,
        debit: Decimal = Decimal('0'),
        credit: Decimal = Decimal('0'),
        description: str = ''
    ):
        """Add line to journal entry"""
        line = JournalEntryLine(account_code, debit, credit, description)
        self.lines.append(line)
    
    def validate(self) -> bool:
        """
        Validate double-entry bookkeeping
        
        Rules:
        1. At least 2 lines
        2. Total debits = Total credits
        3. All accounts exist in CoA
        """
        if len(self.lines) < 2:
            raise ValueError('Journal entry must have at least 2 lines')
        
        total_debits = sum(line.debit for line in self.lines)
        total_credits = sum(line.credit for line in self.lines)
        
        if total_debits != total_credits:
            raise ValueError(
                f'Debits (\) must equal Credits (\). '
                f'Difference: \'
            )
        
        # Validate accounts exist
        coa = get_chart_of_accounts()
        for line in self.lines:
            if not coa.get_account(line.account_code):
                raise ValueError(f'Account {line.account_code} not found in Chart of Accounts')
        
        return True
    
    async def post(self):
        """
        Post journal entry to General Ledger
        
        Once posted, entry is immutable
        """
        # Validate before posting
        self.validate()
        
        self.is_posted = True
        self.posted_at = datetime.now(timezone.utc)
        
        # Publish to Kafka (event-sourced)
        kafka_store = get_production_kafka_store()
        
        await kafka_store.append_event(
            entity='general_ledger',
            event_type='journal_entry_posted',
            event_data={
                'entry_id': self.entry_id,
                'entry_date': self.entry_date.isoformat(),
                'entry_type': self.entry_type.value,
                'description': self.description,
                'lines': [
                    {
                        'account_code': line.account_code,
                        'debit': str(line.debit),
                        'credit': str(line.credit),
                        'description': line.description
                    }
                    for line in self.lines
                ],
                'reference_id': self.reference_id,
                'reference_type': self.reference_type,
                'posted_at': self.posted_at.isoformat()
            },
            aggregate_id=self.entry_id,
            exactly_once=True
        )
        
        # Publish to Data Mesh
        from ultracore.data_mesh.integration import DataMeshPublisher
        await DataMeshPublisher.publish_transaction_data(
            self.entry_id,
            {
                'entry_id': self.entry_id,
                'type': 'JOURNAL_ENTRY',
                'total_amount': str(sum(line.debit for line in self.lines)),
                'posted_at': self.posted_at.isoformat()
            }
        )


class JournalEntryBuilder:
    """
    Fluent builder for common journal entries
    
    Simplifies creation of standard accounting transactions
    """
    
    @staticmethod
    async def customer_deposit(
        amount: Decimal,
        account_number: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record customer deposit
        
        DR: Cash
        CR: Customer Deposits
        """
        entry = JournalEntry()
        entry.description = f'Customer deposit - Account {account_number}'
        entry.reference_id = reference_id
        entry.reference_type = 'DEPOSIT'
        
        entry.add_line('1000-01-003', debit=amount, description='Cash received')
        entry.add_line('2000-01-001', credit=amount, description=f'Deposit to {account_number}')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def customer_withdrawal(
        amount: Decimal,
        account_number: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record customer withdrawal
        
        DR: Customer Deposits
        CR: Cash
        """
        entry = JournalEntry()
        entry.description = f'Customer withdrawal - Account {account_number}'
        entry.reference_id = reference_id
        entry.reference_type = 'WITHDRAWAL'
        
        entry.add_line('2000-01-001', debit=amount, description=f'Withdrawal from {account_number}')
        entry.add_line('1000-01-003', credit=amount, description='Cash paid')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def loan_disbursement(
        amount: Decimal,
        loan_id: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record loan disbursement
        
        DR: Loans Receivable
        CR: Cash
        """
        entry = JournalEntry()
        entry.description = f'Loan disbursement - Loan {loan_id}'
        entry.reference_id = reference_id
        entry.reference_type = 'LOAN_DISBURSEMENT'
        
        entry.add_line('1200-01-001', debit=amount, description=f'Loan {loan_id} disbursed')
        entry.add_line('1000-01-003', credit=amount, description='Cash paid')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def loan_repayment(
        principal: Decimal,
        interest: Decimal,
        loan_id: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record loan repayment
        
        DR: Cash (principal + interest)
        CR: Loans Receivable (principal)
        CR: Interest Income (interest)
        """
        entry = JournalEntry()
        entry.description = f'Loan repayment - Loan {loan_id}'
        entry.reference_id = reference_id
        entry.reference_type = 'LOAN_REPAYMENT'
        
        total = principal + interest
        entry.add_line('1000-01-003', debit=total, description='Cash received')
        entry.add_line('1200-01-001', credit=principal, description=f'Loan {loan_id} principal')
        entry.add_line('4000-01-001', credit=interest, description=f'Loan {loan_id} interest')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def osko_payment_out(
        amount: Decimal,
        from_account: str,
        to_account: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record Osko payment OUT
        
        DR: Customer Deposits (from account)
        CR: Nostro Settlement Account
        """
        entry = JournalEntry()
        entry.description = f'Osko payment {from_account} → {to_account}'
        entry.reference_id = reference_id
        entry.reference_type = 'OSKO_OUT'
        
        entry.add_line('2000-01-001', debit=amount, description=f'From {from_account}')
        entry.add_line('1100-01-002', credit=amount, description='NPP settlement')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def osko_payment_in(
        amount: Decimal,
        to_account: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record Osko payment IN
        
        DR: Nostro Settlement Account
        CR: Customer Deposits (to account)
        """
        entry = JournalEntry()
        entry.description = f'Osko payment received → {to_account}'
        entry.reference_id = reference_id
        entry.reference_type = 'OSKO_IN'
        
        entry.add_line('1100-01-002', debit=amount, description='NPP settlement')
        entry.add_line('2000-01-001', credit=amount, description=f'To {to_account}')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def interest_accrual(
        amount: Decimal,
        account_number: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record interest accrual on deposit
        
        DR: Interest Expense
        CR: Interest Payable
        """
        entry = JournalEntry()
        entry.description = f'Interest accrual - Account {account_number}'
        entry.reference_id = reference_id
        entry.reference_type = 'INTEREST_ACCRUAL'
        entry.entry_type = EntryType.ADJUSTING
        
        entry.add_line('5000-01-001', debit=amount, description='Interest expense')
        entry.add_line('2300-01-001', credit=amount, description=f'Interest payable on {account_number}')
        
        await entry.post()
        return entry
    
    @staticmethod
    async def fee_income(
        amount: Decimal,
        fee_type: str,
        account_number: str,
        reference_id: str
    ) -> JournalEntry:
        """
        Record fee income
        
        DR: Customer Deposits (or Cash)
        CR: Fee Income
        """
        entry = JournalEntry()
        entry.description = f'{fee_type} - Account {account_number}'
        entry.reference_id = reference_id
        entry.reference_type = 'FEE_INCOME'
        
        entry.add_line('2000-01-001', debit=amount, description=f'Fee charged to {account_number}')
        entry.add_line('4100-01-002', credit=amount, description=fee_type)
        
        await entry.post()
        return entry

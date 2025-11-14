"""
Savings Accounting Integration
Automatic journal entry generation for savings transactions
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from ultracore.domains.savings.models.transaction import SavingsTransaction, TransactionType


class SavingsAccountingIntegration:
    """
    Savings Accounting Integration Service
    
    Automatically generates double-entry journal entries for all savings transactions:
    - Deposits and withdrawals
    - Interest accrual and posting
    - Fee charges
    - Withholding tax
    
    Chart of Accounts Mapping:
    - 1100: Savings Accounts (Customer Deposits) - LIABILITY
    - 1110: Cash at Bank - ASSET
    - 2100: Interest Payable - LIABILITY
    - 4100: Account Fees Revenue - REVENUE
    - 5100: Interest Expense - EXPENSE
    - 5200: Withholding Tax Payable - LIABILITY
    """
    
    # Chart of Accounts
    COA_CASH_AT_BANK = "1110"
    COA_SAVINGS_DEPOSITS = "1100"
    COA_INTEREST_PAYABLE = "2100"
    COA_INTEREST_EXPENSE = "5100"
    COA_WITHHOLDING_TAX_PAYABLE = "5200"
    COA_ACCOUNT_FEES_REVENUE = "4100"
    
    @staticmethod
    def generate_journal_entries(
        transaction: SavingsTransaction,
        tenant_id: UUID
    ) -> List[Dict]:
        """
        Generate journal entries for a savings transaction
        
        Args:
            transaction: Savings transaction
            tenant_id: Tenant ID
        
        Returns:
            List of journal entry line items
        """
        if transaction.transaction_type == TransactionType.DEPOSIT:
            return SavingsAccountingIntegration._journal_deposit(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            return SavingsAccountingIntegration._journal_withdrawal(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.INTEREST_ACCRUAL:
            return SavingsAccountingIntegration._journal_interest_accrual(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.INTEREST_POSTING:
            return SavingsAccountingIntegration._journal_interest_posting(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.WITHHOLDING_TAX:
            return SavingsAccountingIntegration._journal_withholding_tax(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.FEE_CHARGE:
            return SavingsAccountingIntegration._journal_fee_charge(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.TRANSFER_IN:
            return SavingsAccountingIntegration._journal_transfer_in(transaction, tenant_id)
        
        elif transaction.transaction_type == TransactionType.TRANSFER_OUT:
            return SavingsAccountingIntegration._journal_transfer_out(transaction, tenant_id)
        
        else:
            return []
    
    @staticmethod
    def _journal_deposit(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for deposit
        
        DR: Cash at Bank
        CR: Savings Accounts (Customer Deposits)
        """
        journal_id = uuid4()
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_CASH_AT_BANK,
                "account_name": "Cash at Bank",
                "debit": float(transaction.amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_SAVINGS_DEPOSITS,
                "account_name": "Savings Accounts (Customer Deposits)",
                "debit": 0.0,
                "credit": float(transaction.amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_withdrawal(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for withdrawal
        
        DR: Savings Accounts (Customer Deposits)
        CR: Cash at Bank
        """
        journal_id = uuid4()
        amount = abs(transaction.amount)  # Withdrawals are negative
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_SAVINGS_DEPOSITS,
                "account_name": "Savings Accounts (Customer Deposits)",
                "debit": float(amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_CASH_AT_BANK,
                "account_name": "Cash at Bank",
                "debit": 0.0,
                "credit": float(amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_interest_accrual(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for interest accrual
        
        DR: Interest Expense
        CR: Interest Payable
        """
        journal_id = uuid4()
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_INTEREST_EXPENSE,
                "account_name": "Interest Expense",
                "debit": float(transaction.amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_INTEREST_PAYABLE,
                "account_name": "Interest Payable",
                "debit": 0.0,
                "credit": float(transaction.amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_interest_posting(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for interest posting
        
        DR: Interest Payable
        CR: Savings Accounts (Customer Deposits)
        """
        journal_id = uuid4()
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_INTEREST_PAYABLE,
                "account_name": "Interest Payable",
                "debit": float(transaction.amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_SAVINGS_DEPOSITS,
                "account_name": "Savings Accounts (Customer Deposits)",
                "debit": 0.0,
                "credit": float(transaction.amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_withholding_tax(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for withholding tax
        
        DR: Interest Expense
        CR: Withholding Tax Payable
        """
        journal_id = uuid4()
        amount = abs(transaction.amount)
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_INTEREST_EXPENSE,
                "account_name": "Interest Expense",
                "debit": float(amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_WITHHOLDING_TAX_PAYABLE,
                "account_name": "Withholding Tax Payable",
                "debit": 0.0,
                "credit": float(amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_fee_charge(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for fee charge
        
        DR: Savings Accounts (Customer Deposits)
        CR: Account Fees Revenue
        """
        journal_id = uuid4()
        amount = abs(transaction.amount)
        
        return [
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_SAVINGS_DEPOSITS,
                "account_name": "Savings Accounts (Customer Deposits)",
                "debit": float(amount),
                "credit": 0.0,
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
            {
                "journal_id": str(journal_id),
                "tenant_id": str(tenant_id),
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "entry_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "account_code": SavingsAccountingIntegration.COA_ACCOUNT_FEES_REVENUE,
                "account_name": "Account Fees Revenue",
                "debit": 0.0,
                "credit": float(amount),
                "description": transaction.description,
                "reference": transaction.reference_number,
            },
        ]
    
    @staticmethod
    def _journal_transfer_in(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for transfer in
        
        Same as deposit
        """
        return SavingsAccountingIntegration._journal_deposit(transaction, tenant_id)
    
    @staticmethod
    def _journal_transfer_out(transaction: SavingsTransaction, tenant_id: UUID) -> List[Dict]:
        """
        Journal entry for transfer out
        
        Same as withdrawal
        """
        return SavingsAccountingIntegration._journal_withdrawal(transaction, tenant_id)
    
    @staticmethod
    def verify_journal_balance(journal_entries: List[Dict]) -> bool:
        """
        Verify that journal entries balance (total debits = total credits)
        
        Args:
            journal_entries: List of journal entry line items
        
        Returns:
            True if balanced, False otherwise
        """
        total_debits = sum(entry.get('debit', 0.0) for entry in journal_entries)
        total_credits = sum(entry.get('credit', 0.0) for entry in journal_entries)
        
        # Allow for small rounding differences
        return abs(total_debits - total_credits) < 0.01

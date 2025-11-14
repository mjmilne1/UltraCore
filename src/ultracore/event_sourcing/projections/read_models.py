"""
Read Models.

CQRS read models for query optimization.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from ..base import Event, EventType
from .projection_manager import Projection


logger = logging.getLogger(__name__)


class CustomerReadModel(Projection):
    """Customer read model projection."""
    
    def __init__(self):
        super().__init__("CustomerReadModel")
        self.customers: Dict[str, Dict[str, Any]] = {}
    
    async def project(self, event: Event) -> None:
        """Project customer event."""
        customer_id = event.metadata.aggregate_id
        event_type = event.metadata.event_type
        
        if event_type == EventType.CUSTOMER_CREATED:
            self.customers[customer_id] = {
                "customer_id": customer_id,
                "name": event.data.get("name"),
                "email": event.data.get("email"),
                "phone": event.data.get("phone"),
                "kyc_status": "pending",
                "risk_level": "unknown",
                "created_at": event.metadata.timestamp,
                "updated_at": event.metadata.timestamp,
            }
        
        elif event_type == EventType.CUSTOMER_UPDATED:
            if customer_id in self.customers:
                self.customers[customer_id].update(event.data)
                self.customers[customer_id]["updated_at"] = event.metadata.timestamp
        
        elif event_type == EventType.CUSTOMER_KYC_COMPLETED:
            if customer_id in self.customers:
                self.customers[customer_id]["kyc_status"] = event.data.get("status")
                self.customers[customer_id]["kyc_completed_at"] = event.metadata.timestamp
        
        elif event_type == EventType.CUSTOMER_RISK_ASSESSED:
            if customer_id in self.customers:
                self.customers[customer_id]["risk_level"] = event.data.get("risk_level")
                self.customers[customer_id]["risk_score"] = event.data.get("risk_score")
    
    def can_project(self, event_type: EventType) -> bool:
        """Check if can project event type."""
        return event_type in {
            EventType.CUSTOMER_CREATED,
            EventType.CUSTOMER_UPDATED,
            EventType.CUSTOMER_KYC_COMPLETED,
            EventType.CUSTOMER_RISK_ASSESSED,
        }
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        return self.customers.get(customer_id)
    
    def list_customers(self, limit: int = 100, offset: int = 0) -> list[Dict[str, Any]]:
        """List customers with pagination."""
        customers = list(self.customers.values())
        return customers[offset:offset + limit]


class AccountReadModel(Projection):
    """Account read model projection."""
    
    def __init__(self):
        super().__init__("AccountReadModel")
        self.accounts: Dict[str, Dict[str, Any]] = {}
    
    async def project(self, event: Event) -> None:
        """Project account event."""
        account_id = event.metadata.aggregate_id
        event_type = event.metadata.event_type
        
        if event_type == EventType.ACCOUNT_OPENED:
            self.accounts[account_id] = {
                "account_id": account_id,
                "customer_id": event.data.get("customer_id"),
                "account_type": event.data.get("account_type"),
                "balance": event.data.get("initial_balance", 0),
                "currency": event.data.get("currency", "AUD"),
                "status": "active",
                "opened_at": event.metadata.timestamp,
            }
        
        elif event_type == EventType.ACCOUNT_BALANCE_UPDATED:
            if account_id in self.accounts:
                self.accounts[account_id]["balance"] = event.data.get("new_balance")
                self.accounts[account_id]["last_updated"] = event.metadata.timestamp
        
        elif event_type == EventType.ACCOUNT_FROZEN:
            if account_id in self.accounts:
                self.accounts[account_id]["status"] = "frozen"
                self.accounts[account_id]["frozen_at"] = event.metadata.timestamp
        
        elif event_type == EventType.ACCOUNT_UNFROZEN:
            if account_id in self.accounts:
                self.accounts[account_id]["status"] = "active"
                self.accounts[account_id]["unfrozen_at"] = event.metadata.timestamp
        
        elif event_type == EventType.ACCOUNT_CLOSED:
            if account_id in self.accounts:
                self.accounts[account_id]["status"] = "closed"
                self.accounts[account_id]["closed_at"] = event.metadata.timestamp
    
    def can_project(self, event_type: EventType) -> bool:
        """Check if can project event type."""
        return event_type in {
            EventType.ACCOUNT_OPENED,
            EventType.ACCOUNT_BALANCE_UPDATED,
            EventType.ACCOUNT_FROZEN,
            EventType.ACCOUNT_UNFROZEN,
            EventType.ACCOUNT_CLOSED,
        }
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        return self.accounts.get(account_id)
    
    def get_customer_accounts(self, customer_id: str) -> list[Dict[str, Any]]:
        """Get all accounts for a customer."""
        return [
            account for account in self.accounts.values()
            if account.get("customer_id") == customer_id
        ]


class TransactionReadModel(Projection):
    """Transaction read model projection."""
    
    def __init__(self):
        super().__init__("TransactionReadModel")
        self.transactions: Dict[str, Dict[str, Any]] = {}
    
    async def project(self, event: Event) -> None:
        """Project transaction event."""
        transaction_id = event.metadata.aggregate_id
        event_type = event.metadata.event_type
        
        if event_type == EventType.TRANSACTION_CREATED:
            self.transactions[transaction_id] = {
                "transaction_id": transaction_id,
                "account_id": event.data.get("account_id"),
                "amount": event.data.get("amount"),
                "currency": event.data.get("currency"),
                "type": event.data.get("type"),
                "status": "pending",
                "created_at": event.metadata.timestamp,
            }
        
        elif event_type == EventType.TRANSACTION_POSTED:
            if transaction_id in self.transactions:
                self.transactions[transaction_id]["status"] = "posted"
                self.transactions[transaction_id]["posted_at"] = event.metadata.timestamp
        
        elif event_type == EventType.TRANSACTION_SETTLED:
            if transaction_id in self.transactions:
                self.transactions[transaction_id]["status"] = "settled"
                self.transactions[transaction_id]["settled_at"] = event.metadata.timestamp
        
        elif event_type == EventType.TRANSACTION_REVERSED:
            if transaction_id in self.transactions:
                self.transactions[transaction_id]["status"] = "reversed"
                self.transactions[transaction_id]["reversed_at"] = event.metadata.timestamp
    
    def can_project(self, event_type: EventType) -> bool:
        """Check if can project event type."""
        return event_type in {
            EventType.TRANSACTION_CREATED,
            EventType.TRANSACTION_POSTED,
            EventType.TRANSACTION_SETTLED,
            EventType.TRANSACTION_REVERSED,
        }
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by ID."""
        return self.transactions.get(transaction_id)
    
    def get_account_transactions(self, account_id: str) -> list[Dict[str, Any]]:
        """Get all transactions for an account."""
        return [
            tx for tx in self.transactions.values()
            if tx.get("account_id") == account_id
        ]


class PaymentReadModel(Projection):
    """Payment read model projection."""
    
    def __init__(self):
        super().__init__("PaymentReadModel")
        self.payments: Dict[str, Dict[str, Any]] = {}
    
    async def project(self, event: Event) -> None:
        """Project payment event."""
        payment_id = event.metadata.aggregate_id
        event_type = event.metadata.event_type
        
        if event_type == EventType.PAYMENT_INITIATED:
            self.payments[payment_id] = {
                "payment_id": payment_id,
                "from_account": event.data.get("from_account"),
                "to_account": event.data.get("to_account"),
                "amount": event.data.get("amount"),
                "currency": event.data.get("currency"),
                "status": "initiated",
                "initiated_at": event.metadata.timestamp,
            }
        
        elif event_type == EventType.PAYMENT_AUTHORIZED:
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "authorized"
                self.payments[payment_id]["authorized_at"] = event.metadata.timestamp
        
        elif event_type == EventType.PAYMENT_COMPLETED:
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "completed"
                self.payments[payment_id]["completed_at"] = event.metadata.timestamp
        
        elif event_type == EventType.PAYMENT_FAILED:
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "failed"
                self.payments[payment_id]["failed_at"] = event.metadata.timestamp
                self.payments[payment_id]["failure_reason"] = event.data.get("reason")
    
    def can_project(self, event_type: EventType) -> bool:
        """Check if can project event type."""
        return event_type in {
            EventType.PAYMENT_INITIATED,
            EventType.PAYMENT_AUTHORIZED,
            EventType.PAYMENT_COMPLETED,
            EventType.PAYMENT_FAILED,
        }
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by ID."""
        return self.payments.get(payment_id)


class LoanReadModel(Projection):
    """Loan read model projection."""
    
    def __init__(self):
        super().__init__("LoanReadModel")
        self.loans: Dict[str, Dict[str, Any]] = {}
    
    async def project(self, event: Event) -> None:
        """Project loan event."""
        loan_id = event.metadata.aggregate_id
        event_type = event.metadata.event_type
        
        if event_type == EventType.LOAN_APPLICATION_SUBMITTED:
            self.loans[loan_id] = {
                "loan_id": loan_id,
                "customer_id": event.data.get("customer_id"),
                "amount": event.data.get("amount"),
                "term_months": event.data.get("term_months"),
                "status": "pending",
                "submitted_at": event.metadata.timestamp,
            }
        
        elif event_type == EventType.LOAN_APPROVED:
            if loan_id in self.loans:
                self.loans[loan_id]["status"] = "approved"
                self.loans[loan_id]["approved_at"] = event.metadata.timestamp
        
        elif event_type == EventType.LOAN_REJECTED:
            if loan_id in self.loans:
                self.loans[loan_id]["status"] = "rejected"
                self.loans[loan_id]["rejected_at"] = event.metadata.timestamp
        
        elif event_type == EventType.LOAN_DISBURSED:
            if loan_id in self.loans:
                self.loans[loan_id]["status"] = "active"
                self.loans[loan_id]["disbursed_at"] = event.metadata.timestamp
        
        elif event_type == EventType.LOAN_DEFAULTED:
            if loan_id in self.loans:
                self.loans[loan_id]["status"] = "defaulted"
                self.loans[loan_id]["defaulted_at"] = event.metadata.timestamp
    
    def can_project(self, event_type: EventType) -> bool:
        """Check if can project event type."""
        return event_type in {
            EventType.LOAN_APPLICATION_SUBMITTED,
            EventType.LOAN_APPROVED,
            EventType.LOAN_REJECTED,
            EventType.LOAN_DISBURSED,
            EventType.LOAN_DEFAULTED,
        }
    
    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan by ID."""
        return self.loans.get(loan_id)
    
    def get_customer_loans(self, customer_id: str) -> list[Dict[str, Any]]:
        """Get all loans for a customer."""
        return [
            loan for loan in self.loans.values()
            if loan.get("customer_id") == customer_id
        ]

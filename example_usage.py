"""
UltraCore Banking Platform - Usage Example

This demonstrates how to use the UltraCore package
"""

import sys
sys.path.insert(0, 'C:/Users/mjmil/ultracore-working/src')

from datetime import date, datetime
from decimal import Decimal

# Import core managers
from ultracore.customers import get_customer_manager, CustomerType
from ultracore.accounts import get_account_manager, AccountType
from ultracore.lending import get_loan_manager, LoanType
from ultracore.accounting import get_general_ledger

print("=" * 70)
print("ULTRACORE USAGE EXAMPLE")
print("=" * 70)
print()

# Initialize managers
print("1. Initializing managers...")
customer_manager = get_customer_manager()
account_manager = get_account_manager()
loan_manager = get_loan_manager()
gl = get_general_ledger()
print("   ✓ All managers initialized")
print()

# Create a customer
print("2. Creating a customer...")
customer = customer_manager.create_customer(
    customer_type=CustomerType.INDIVIDUAL,
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    mobile="+61400000000",
    date_of_birth=date(1990, 1, 1),
    created_by="SYSTEM"
)
print(f"   ✓ Customer created: {customer.customer_id}")
print(f"   ✓ Name: {customer.get_full_name()}")
print()

# Open an account
print("3. Opening a savings account...")
import asyncio

async def open_account():
    account = await account_manager.open_account(
        customer_id=customer.customer_id,
        account_type=AccountType.SAVINGS,
        opened_by="SYSTEM",
        initial_deposit=Decimal("1000.00")
    )
    return account

account = asyncio.run(open_account())
print(f"   ✓ Account opened: {account.account_number}")
print(f"   ✓ Balance: ${account.balance.ledger_balance}")
print()

# Make a deposit
print("4. Making a deposit...")
async def make_deposit():
    transaction = await account_manager.deposit(
        account_id=account.account_id,
        amount=Decimal("500.00"),
        description="Salary deposit",
        deposited_by="SYSTEM"
    )
    return transaction

txn = asyncio.run(make_deposit())
print(f"   ✓ Deposit processed: {txn.transaction_id}")
print(f"   ✓ Amount: ${txn.amount}")
print(f"   ✓ New balance: ${account.balance.ledger_balance}")
print()

print("=" * 70)
print("✅ UltraCore is working perfectly!")
print("=" * 70)
print()
print("You can now:")
print("  • Create customers")
print("  • Open accounts")
print("  • Process transactions")
print("  • Manage loans")
print("  • Run AI agents")
print("  • Process payments")
print()

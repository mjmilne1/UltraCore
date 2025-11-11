"""
UltraCore Platform Test Suite

Tests all major functionality:
- API health checks
- Customer creation
- Account operations
- Transactions
- Loan processing
"""

import asyncio
import httpx
from datetime import datetime, date
import json

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    results["tests"].append({
        "name": name,
        "passed": passed,
        "message": message
    })
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    print(f"{status} - {name}")
    if message:
        print(f"      {message}")


async def test_health():
    """Test health endpoints"""
    print("\n🏥 Testing Health Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Basic health
        try:
            response = await client.get(f"{BASE_URL}/health")
            passed = response.status_code == 200
            log_test("Health Check", passed, f"Status: {response.status_code}")
        except Exception as e:
            log_test("Health Check", False, str(e))
        
        # Detailed health
        try:
            response = await client.get(f"{BASE_URL}/health/detailed")
            passed = response.status_code == 200
            log_test("Detailed Health", passed, f"Components: {len(response.json().get('components', {}))}")
        except Exception as e:
            log_test("Detailed Health", False, str(e))


async def test_customer_lifecycle():
    """Test complete customer lifecycle"""
    print("\n👤 Testing Customer Lifecycle...")
    
    async with httpx.AsyncClient() as client:
        # Create customer
        customer_data = {
            "customer_type": "INDIVIDUAL",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "mobile": "+61400123456",
            "date_of_birth": "1990-01-15"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/customers", json=customer_data)
            passed = response.status_code == 201
            
            if passed:
                customer = response.json()
                customer_id = customer["customer_id"]
                log_test("Create Customer", True, f"ID: {customer_id}")
                
                # Get customer
                response = await client.get(f"{BASE_URL}/customers/{customer_id}")
                passed = response.status_code == 200
                log_test("Get Customer", passed, f"Name: {customer.get('first_name')} {customer.get('last_name')}")
                
                # List customers
                response = await client.get(f"{BASE_URL}/customers?limit=10")
                passed = response.status_code == 200 and response.json()["total"] > 0
                log_test("List Customers", passed, f"Total: {response.json()['total']}")
                
                return customer_id
            else:
                log_test("Create Customer", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            log_test("Create Customer", False, str(e))
            return None


async def test_account_lifecycle(customer_id: str):
    """Test complete account lifecycle"""
    print("\n💰 Testing Account Lifecycle...")
    
    if not customer_id:
        print("⚠️  Skipping account tests (no customer)")
        return None
    
    async with httpx.AsyncClient() as client:
        # Open account
        account_data = {
            "customer_id": customer_id,
            "account_type": "SAVINGS",
            "currency": "AUD",
            "initial_deposit": 1000.00
        }
        
        try:
            response = await client.post(f"{BASE_URL}/accounts", json=account_data)
            passed = response.status_code == 201
            
            if passed:
                account = response.json()
                account_id = account["account_id"]
                log_test("Open Account", True, f"ID: {account_id}, Number: {account['account_number']}")
                
                # Get account
                response = await client.get(f"{BASE_URL}/accounts/{account_id}")
                passed = response.status_code == 200
                log_test("Get Account", passed, f"Balance: ${account['balance']['ledger_balance']}")
                
                # Get balance
                response = await client.get(f"{BASE_URL}/accounts/{account_id}/balance")
                passed = response.status_code == 200
                log_test("Get Balance", passed, f"Available: ${response.json()['available_balance']}")
                
                return account_id
            else:
                log_test("Open Account", False, f"Status: {response.status_code}, Error: {response.text}")
                return None
                
        except Exception as e:
            log_test("Open Account", False, str(e))
            return None


async def test_transactions(account_id: str):
    """Test transaction processing"""
    print("\n💸 Testing Transactions...")
    
    if not account_id:
        print("⚠️  Skipping transaction tests (no account)")
        return
    
    async with httpx.AsyncClient() as client:
        # Deposit
        try:
            deposit_data = {
                "amount": 500.00,
                "description": "Test deposit"
            }
            response = await client.post(
                f"{BASE_URL}/transactions/deposit?account_id={account_id}",
                json=deposit_data
            )
            passed = response.status_code == 201
            if passed:
                txn = response.json()
                log_test("Deposit", True, f"Amount: ${txn['amount']}, Balance: ${txn['balance_after']}")
            else:
                log_test("Deposit", False, f"Status: {response.status_code}, Error: {response.text}")
        except Exception as e:
            log_test("Deposit", False, str(e))
        
        # Withdrawal
        try:
            withdrawal_data = {
                "amount": 100.00,
                "description": "Test withdrawal"
            }
            response = await client.post(
                f"{BASE_URL}/transactions/withdraw?account_id={account_id}",
                json=withdrawal_data
            )
            passed = response.status_code == 201
            if passed:
                txn = response.json()
                log_test("Withdrawal", True, f"Amount: ${txn['amount']}, Balance: ${txn['balance_after']}")
            else:
                log_test("Withdrawal", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("Withdrawal", False, str(e))
        
        # List transactions
        try:
            response = await client.get(f"{BASE_URL}/transactions?account_id={account_id}")
            passed = response.status_code == 200 and response.json()["total"] > 0
            log_test("List Transactions", passed, f"Total: {response.json()['total']}")
        except Exception as e:
            log_test("List Transactions", False, str(e))


async def test_loan_lifecycle(customer_id: str):
    """Test loan processing"""
    print("\n🏦 Testing Loan Lifecycle...")
    
    if not customer_id:
        print("⚠️  Skipping loan tests (no customer)")
        return
    
    async with httpx.AsyncClient() as client:
        # Apply for loan
        loan_data = {
            "customer_id": customer_id,
            "loan_type": "PERSONAL",
            "requested_amount": 10000.00,
            "term_months": 24,
            "interest_rate": 5.5,
            "purpose": "Test loan application"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/loans/apply", json=loan_data)
            passed = response.status_code == 201
            
            if passed:
                loan = response.json()
                loan_id = loan["loan_id"]
                log_test("Loan Application", True, f"ID: {loan_id}, Amount: ${loan['requested_amount']}")
                
                # Get loan
                response = await client.get(f"{BASE_URL}/loans/{loan_id}")
                passed = response.status_code == 200
                log_test("Get Loan", passed, f"Status: {response.json()['status']}")
                
                return loan_id
            else:
                log_test("Loan Application", False, f"Status: {response.status_code}, Error: {response.text}")
                return None
                
        except Exception as e:
            log_test("Loan Application", False, str(e))
            return None


async def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧪 ULTRACORE BANKING PLATFORM TEST SUITE")
    print("=" * 70)
    
    # Health checks
    await test_health()
    
    # Customer lifecycle
    customer_id = await test_customer_lifecycle()
    
    # Account lifecycle
    account_id = await test_account_lifecycle(customer_id)
    
    # Transactions
    await test_transactions(account_id)
    
    # Loans
    await test_loan_lifecycle(customer_id)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
    print("=" * 70)
    
    if results['failed'] > 0:
        print("\n❌ Failed Tests:")
        for test in results['tests']:
            if not test['passed']:
                print(f"   • {test['name']}: {test['message']}")
    else:
        print("\n🎉 ALL TESTS PASSED! Platform is working perfectly!")
    
    return results['failed'] == 0


if __name__ == "__main__":
    print("\n⏳ Starting tests in 3 seconds...")
    print("   (Make sure API is running at http://localhost:8000)")
    import time
    time.sleep(3)
    
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

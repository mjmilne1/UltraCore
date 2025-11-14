"""
End-to-End Integration Tests
Tests complete workflows across multiple modules
"""

import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/home/ubuntu/UltraCore')

from server import app

client = TestClient(app)

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    def test_complete_client_onboarding_workflow(self):
        """
        Test complete client onboarding workflow:
        1. Create client
        2. Verify KYC
        3. Create cash account
        4. Make initial deposit
        5. Verify balance
        """
        # Step 1: Create client
        client_response = client.post("/api/v1/clients/", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.smith@example.com",
            "phone": "+61400111222",
            "date_of_birth": "1985-05-15",
            "risk_profile": "BALANCED",
            "address": "456 Market St",
            "city": "Melbourne",
            "state": "VIC",
            "postcode": "3000",
            "country": "AU"
        })
        
        assert client_response.status_code == 201
        client_data = client_response.json()
        client_id = client_data["client_id"]
        assert client_data["status"] == "PENDING"
        
        # Step 2: Verify KYC
        kyc_response = client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        assert kyc_response.status_code == 200
        kyc_data = kyc_response.json()
        assert kyc_data["kyc_verified"] is True
        assert kyc_data["status"] == "ACTIVE"
        
        # Step 3: Create cash account
        account_response = client.post("/api/v1/cash/accounts", json={
            "client_id": client_id,
            "account_type": "SAVINGS",
            "currency": "AUD",
            "account_name": "Primary Savings"
        })
        
        assert account_response.status_code == 201
        account_data = account_response.json()
        account_id = account_data["account_id"]
        assert float(account_data["balance"]) == 0.0
        
        # Step 4: Make initial deposit
        deposit_response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "10000.00",
            "description": "Initial deposit",
            "reference": "INIT001"
        })
        
        assert deposit_response.status_code == 201
        deposit_data = deposit_response.json()
        assert float(deposit_data["amount"]) == 10000.00
        assert deposit_data["status"] == "COMPLETED"
        
        # Step 5: Verify balance
        balance_response = client.get(f"/api/v1/cash/accounts/{account_id}/balance")
        assert balance_response.status_code == 200
        balance_data = balance_response.json()
        assert float(balance_data["balance"]) == 10000.00
        assert float(balance_data["available_balance"]) == 10000.00
    
    def test_multi_account_workflow(self):
        """
        Test managing multiple accounts for one client:
        1. Create client
        2. Create savings account
        3. Create transaction account
        4. Deposit to savings
        5. Transfer between accounts (simulated with deposit/withdrawal)
        """
        # Step 1: Create client
        client_response = client.post("/api/v1/clients/", json={
            "first_name": "Bob",
            "last_name": "Johnson",
            "email": "bob.johnson@example.com",
            "phone": "+61400333444",
            "date_of_birth": "1978-03-22",
            "risk_profile": "CONSERVATIVE"
        })
        
        client_id = client_response.json()["client_id"]
        client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        
        # Step 2: Create savings account
        savings_response = client.post("/api/v1/cash/accounts", json={
            "client_id": client_id,
            "account_type": "SAVINGS",
            "currency": "AUD",
            "account_name": "High Interest Savings"
        })
        
        savings_id = savings_response.json()["account_id"]
        
        # Step 3: Create transaction account
        transaction_response = client.post("/api/v1/cash/accounts", json={
            "client_id": client_id,
            "account_type": "TRANSACTION",
            "currency": "AUD",
            "account_name": "Everyday Account"
        })
        
        transaction_id = transaction_response.json()["account_id"]
        
        # Step 4: Deposit to savings
        client.post("/api/v1/cash/transactions", json={
            "account_id": savings_id,
            "transaction_type": "DEPOSIT",
            "amount": "50000.00",
            "description": "Initial savings deposit"
        })
        
        # Step 5: Simulate transfer (withdrawal from savings, deposit to transaction)
        client.post("/api/v1/cash/transactions", json={
            "account_id": savings_id,
            "transaction_type": "WITHDRAWAL",
            "amount": "5000.00",
            "description": "Transfer to transaction account"
        })
        
        client.post("/api/v1/cash/transactions", json={
            "account_id": transaction_id,
            "transaction_type": "DEPOSIT",
            "amount": "5000.00",
            "description": "Transfer from savings account"
        })
        
        # Verify balances
        savings_balance = client.get(f"/api/v1/cash/accounts/{savings_id}/balance").json()
        transaction_balance = client.get(f"/api/v1/cash/accounts/{transaction_id}/balance").json()
        
        assert float(savings_balance["balance"]) == 45000.00
        assert float(transaction_balance["balance"]) == 5000.00
    
    def test_account_statement_workflow(self):
        """
        Test generating account statement:
        1. Create client and account
        2. Perform multiple transactions
        3. Generate statement
        4. Verify transaction history
        """
        # Setup
        client_response = client.post("/api/v1/clients/", json={
            "first_name": "Carol",
            "last_name": "Williams",
            "email": "carol.williams@example.com",
            "phone": "+61400555666",
            "date_of_birth": "1992-11-08",
            "risk_profile": "GROWTH"
        })
        
        client_id = client_response.json()["client_id"]
        client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        
        account_response = client.post("/api/v1/cash/accounts", json={
            "client_id": client_id,
            "account_type": "TRANSACTION",
            "currency": "AUD"
        })
        
        account_id = account_response.json()["account_id"]
        
        # Perform multiple transactions
        transactions = [
            {"type": "DEPOSIT", "amount": "5000.00", "desc": "Salary"},
            {"type": "WITHDRAWAL", "amount": "1000.00", "desc": "Rent"},
            {"type": "WITHDRAWAL", "amount": "200.00", "desc": "Groceries"},
            {"type": "DEPOSIT", "amount": "500.00", "desc": "Refund"},
            {"type": "FEE", "amount": "10.00", "desc": "Monthly fee"},
            {"type": "INTEREST", "amount": "5.50", "desc": "Interest credit"}
        ]
        
        for txn in transactions:
            client.post("/api/v1/cash/transactions", json={
                "account_id": account_id,
                "transaction_type": txn["type"],
                "amount": txn["amount"],
                "description": txn["desc"]
            })
        
        # Generate statement
        statement = client.get(f"/api/v1/cash/accounts/{account_id}/statement").json()
        
        assert len(statement["transactions"]) == 6
        assert statement["total_transactions"] == 6
        assert float(statement["account"]["balance"]) == 4295.50  # 5000 - 1000 - 200 + 500 - 10 + 5.50
    
    def test_client_lifecycle_workflow(self):
        """
        Test complete client lifecycle:
        1. Create client (PENDING)
        2. Verify KYC (ACTIVE)
        3. Suspend client (SUSPENDED)
        4. Reactivate client (ACTIVE)
        5. Close client (CLOSED)
        """
        # Create
        response = client.post("/api/v1/clients/", json={
            "first_name": "David",
            "last_name": "Brown",
            "email": "david.brown@example.com",
            "phone": "+61400777888",
            "date_of_birth": "1988-07-30",
            "risk_profile": "AGGRESSIVE"
        })
        
        client_id = response.json()["client_id"]
        assert response.json()["status"] == "PENDING"
        
        # Verify KYC
        response = client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        assert response.json()["status"] == "ACTIVE"
        
        # Suspend
        response = client.post(f"/api/v1/clients/{client_id}/suspend")
        assert response.json()["status"] == "SUSPENDED"
        
        # Reactivate
        response = client.post(f"/api/v1/clients/{client_id}/activate")
        assert response.json()["status"] == "ACTIVE"
        
        # Close
        client.delete(f"/api/v1/clients/{client_id}")
        response = client.get(f"/api/v1/clients/{client_id}")
        assert response.json()["status"] == "CLOSED"
    
    def test_error_handling_workflow(self):
        """
        Test error handling across modules:
        1. Try to create transaction for non-existent account
        2. Try to withdraw more than balance
        3. Try to activate client without KYC
        """
        # Non-existent account
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": "non-existent",
            "transaction_type": "DEPOSIT",
            "amount": "100.00"
        })
        assert response.status_code == 404
        
        # Insufficient funds
        account_response = client.post("/api/v1/cash/accounts", json={
            "client_id": "test-client",
            "account_type": "SAVINGS",
            "currency": "AUD"
        })
        account_id = account_response.json()["account_id"]
        
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "WITHDRAWAL",
            "amount": "1000.00"
        })
        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]
        
        # Activate without KYC
        client_response = client.post("/api/v1/clients/", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = client_response.json()["client_id"]
        
        response = client.post(f"/api/v1/clients/{client_id}/activate")
        assert response.status_code == 400
        assert "KYC" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

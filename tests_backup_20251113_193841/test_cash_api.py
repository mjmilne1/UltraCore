"""
Comprehensive test suite for Cash Management API
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

# Import the main app
import sys
sys.path.insert(0, '/home/ubuntu/UltraCore')
from server import app

client = TestClient(app)

class TestCashAPI:
    """Test suite for Cash Management API endpoints"""
    
    def test_create_cash_account(self):
        """Test creating a new cash account"""
        response = client.post("/api/v1/cash/accounts", json={
            "client_id": "test-client-123",
            "account_type": "SAVINGS",
            "currency": "AUD",
            "account_name": "My Savings Account"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["client_id"] == "test-client-123"
        assert data["account_type"] == "SAVINGS"
        assert data["currency"] == "AUD"
        assert float(data["balance"]) == 0.0
        assert data["status"] == "ACTIVE"
        assert "account_id" in data
        
        return data["account_id"]
    
    def test_list_cash_accounts(self):
        """Test listing all cash accounts"""
        # Create a test account first
        self.test_create_cash_account()
        
        response = client.get("/api/v1/cash/accounts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_cash_account(self):
        """Test getting a specific cash account"""
        account_id = self.test_create_cash_account()
        
        response = client.get(f"/api/v1/cash/accounts/{account_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == account_id
    
    def test_get_nonexistent_account(self):
        """Test getting an account that doesn't exist"""
        response = client.get("/api/v1/cash/accounts/nonexistent-id")
        assert response.status_code == 404
    
    def test_create_deposit_transaction(self):
        """Test creating a deposit transaction"""
        account_id = self.test_create_cash_account()
        
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00",
            "description": "Initial deposit",
            "reference": "DEP001"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "DEPOSIT"
        assert float(data["amount"]) == 1000.00
        assert float(data["balance_after"]) == 1000.00
        assert data["status"] == "COMPLETED"
        
        return data["transaction_id"]
    
    def test_create_withdrawal_transaction(self):
        """Test creating a withdrawal transaction"""
        account_id = self.test_create_cash_account()
        
        # First deposit some money
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        
        # Then withdraw
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "WITHDRAWAL",
            "amount": "500.00",
            "description": "Withdrawal",
            "reference": "WD001"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "WITHDRAWAL"
        assert float(data["amount"]) == 500.00
        assert float(data["balance_after"]) == 500.00
    
    def test_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        account_id = self.test_create_cash_account()
        
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "WITHDRAWAL",
            "amount": "100.00"
        })
        
        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]
    
    def test_list_transactions(self):
        """Test listing all transactions"""
        account_id = self.test_create_cash_account()
        
        # Create some transactions
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        
        response = client.get("/api/v1/cash/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_transaction(self):
        """Test getting a specific transaction"""
        transaction_id = self.test_create_deposit_transaction()
        
        response = client.get(f"/api/v1/cash/transactions/{transaction_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == transaction_id
    
    def test_get_account_balance(self):
        """Test getting account balance"""
        account_id = self.test_create_cash_account()
        
        # Deposit some money
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1500.00"
        })
        
        response = client.get(f"/api/v1/cash/accounts/{account_id}/balance")
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 1500.00
        assert float(data["available_balance"]) == 1500.00
        assert data["currency"] == "AUD"
    
    def test_get_account_statement(self):
        """Test getting account statement"""
        account_id = self.test_create_cash_account()
        
        # Create multiple transactions
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "WITHDRAWAL",
            "amount": "200.00"
        })
        
        response = client.get(f"/api/v1/cash/accounts/{account_id}/statement")
        assert response.status_code == 200
        data = response.json()
        assert "account" in data
        assert "transactions" in data
        assert len(data["transactions"]) == 2
        assert data["total_transactions"] == 2
    
    def test_filter_transactions_by_account(self):
        """Test filtering transactions by account"""
        account_id = self.test_create_cash_account()
        
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        
        response = client.get(f"/api/v1/cash/transactions?account_id={account_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(t["account_id"] == account_id for t in data)
    
    def test_filter_transactions_by_type(self):
        """Test filtering transactions by type"""
        account_id = self.test_create_cash_account()
        
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        
        response = client.get("/api/v1/cash/transactions?transaction_type=DEPOSIT")
        assert response.status_code == 200
        data = response.json()
        assert all(t["transaction_type"] == "DEPOSIT" for t in data)
    
    def test_filter_accounts_by_client(self):
        """Test filtering accounts by client ID"""
        client_id = "test-client-456"
        
        client.post("/api/v1/cash/accounts", json={
            "client_id": client_id,
            "account_type": "SAVINGS",
            "currency": "AUD"
        })
        
        response = client.get(f"/api/v1/cash/accounts?client_id={client_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(a["client_id"] == client_id for a in data)
    
    def test_filter_accounts_by_type(self):
        """Test filtering accounts by type"""
        client.post("/api/v1/cash/accounts", json={
            "client_id": "test-client-789",
            "account_type": "TRANSACTION",
            "currency": "AUD"
        })
        
        response = client.get("/api/v1/cash/accounts?account_type=TRANSACTION")
        assert response.status_code == 200
        data = response.json()
        assert all(a["account_type"] == "TRANSACTION" for a in data)
    
    def test_interest_transaction(self):
        """Test interest credit transaction"""
        account_id = self.test_create_cash_account()
        
        # Deposit initial balance
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "10000.00"
        })
        
        # Credit interest
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "INTEREST",
            "amount": "50.00",
            "description": "Monthly interest"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "INTEREST"
        assert float(data["balance_after"]) == 10050.00
    
    def test_fee_transaction(self):
        """Test fee deduction transaction"""
        account_id = self.test_create_cash_account()
        
        # Deposit initial balance
        client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "DEPOSIT",
            "amount": "1000.00"
        })
        
        # Deduct fee
        response = client.post("/api/v1/cash/transactions", json={
            "account_id": account_id,
            "transaction_type": "FEE",
            "amount": "10.00",
            "description": "Monthly account fee"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "FEE"
        assert float(data["balance_after"]) == 990.00
    
    def test_transaction_pagination(self):
        """Test transaction pagination"""
        account_id = self.test_create_cash_account()
        
        # Create multiple transactions
        for i in range(5):
            client.post("/api/v1/cash/transactions", json={
                "account_id": account_id,
                "transaction_type": "DEPOSIT",
                "amount": f"{(i+1)*100}.00"
            })
        
        response = client.get("/api/v1/cash/transactions?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Comprehensive test suite for Clients API
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date

# Import the main app
import sys
sys.path.insert(0, '/home/ubuntu/UltraCore')
from server import app

client = TestClient(app)

class TestClientsAPI:
    """Test suite for Clients API endpoints"""
    
    def test_create_client(self):
        """Test creating a new client"""
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED",
            "address": "123 Test St",
            "city": "Sydney",
            "state": "NSW",
            "postcode": "2000",
            "country": "AU"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["status"] == "PENDING"
        assert data["kyc_verified"] is False
        assert "client_id" in data
    
    def test_list_clients(self):
        """Test listing all clients"""
        # Create a test client first
        self.test_create_client()
        
        response = client.get("/api/v1/clients/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_client(self):
        """Test getting a specific client"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.get(f"/api/v1/clients/{client_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == client_id
        assert data["first_name"] == "John"
    
    def test_get_nonexistent_client(self):
        """Test getting a client that doesn't exist"""
        response = client.get("/api/v1/clients/nonexistent-id")
        assert response.status_code == 404
    
    def test_update_client(self):
        """Test updating client information"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.put(f"/api/v1/clients/{client_id}", json={
            "first_name": "Jane",
            "phone": "+61400111111"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["phone"] == "+61400111111"
        assert data["last_name"] == "Doe"  # Unchanged
    
    def test_verify_kyc(self):
        """Test KYC verification"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        assert response.status_code == 200
        data = response.json()
        assert data["kyc_verified"] is True
        assert data["status"] == "ACTIVE"
    
    def test_suspend_client(self):
        """Test suspending a client"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.post(f"/api/v1/clients/{client_id}/suspend")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUSPENDED"
    
    def test_activate_client(self):
        """Test activating a client"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        # First verify KYC
        client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        
        # Then suspend
        client.post(f"/api/v1/clients/{client_id}/suspend")
        
        # Then activate
        response = client.post(f"/api/v1/clients/{client_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACTIVE"
    
    def test_activate_without_kyc(self):
        """Test that activation fails without KYC"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.post(f"/api/v1/clients/{client_id}/activate")
        assert response.status_code == 400
        assert "KYC" in response.json()["detail"]
    
    def test_close_client(self):
        """Test closing a client account"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.delete(f"/api/v1/clients/{client_id}")
        assert response.status_code == 204
        
        # Verify client is closed
        response = client.get(f"/api/v1/clients/{client_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "CLOSED"
    
    def test_get_client_summary(self):
        """Test getting client summary"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        
        response = client.get(f"/api/v1/clients/{client_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "client" in data
        assert "summary" in data
        assert data["summary"]["kyc_status"] == "Pending"
        assert "account_age_days" in data["summary"]
    
    def test_filter_by_status(self):
        """Test filtering clients by status"""
        # Create a test client
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        client_id = response.json()["client_id"]
        client.post(f"/api/v1/clients/{client_id}/verify-kyc")
        
        response = client.get("/api/v1/clients/?status=ACTIVE")
        assert response.status_code == 200
        data = response.json()
        assert all(c["status"] == "ACTIVE" for c in data)
    
    def test_filter_by_risk_profile(self):
        """Test filtering clients by risk profile"""
        self.test_create_client()
        
        response = client.get("/api/v1/clients/?risk_profile=BALANCED")
        assert response.status_code == 200
        data = response.json()
        assert all(c["risk_profile"] == "BALANCED" for c in data)
    
    def test_pagination(self):
        """Test pagination"""
        # Create multiple clients
        for i in range(5):
            client.post("/api/v1/clients/", json={
                "first_name": f"Test{i}",
                "last_name": "User",
                "email": f"test{i}@example.com",
                "phone": "+61400000000",
                "date_of_birth": "1990-01-01",
                "risk_profile": "BALANCED"
            })
        
        response = client.get("/api/v1/clients/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
    
    def test_invalid_email(self):
        """Test creating client with invalid email"""
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "BALANCED"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_risk_profile(self):
        """Test creating client with invalid risk profile"""
        response = client.post("/api/v1/clients/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+61400000000",
            "date_of_birth": "1990-01-01",
            "risk_profile": "INVALID"
        })
        
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

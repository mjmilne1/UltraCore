"""Tests for Xero AU Connector"""
import pytest
from datetime import datetime
from ..connectors.xero_au_connector import XeroAUConnector

@pytest.mark.asyncio
async def test_export_transactions():
    """Test exporting transactions to Xero"""
    connector = XeroAUConnector(
        client_id="test_id",
        client_secret="test_secret",
        tenant_id="test_tenant"
    )
    
    transactions = [
        {
            "transaction_id": "txn_123",
            "transaction_type": "BUY",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.00,
            "transaction_date": datetime(2024, 1, 15),
            "client_name": "Test Client"
        }
    ]
    
    result = await connector.export_transactions(
        transactions,
        datetime(2024, 1, 1),
        datetime(2024, 12, 31)
    )
    
    assert result["success"] is True
    assert result["transactions_exported"] == 1

"""
Dynamic Data Mesh Integration
Auto-publishes domain data products
"""
from typing import Dict, List
from datetime import datetime

from ultracore.data_mesh.catalog.catalog import data_mesh_catalog, DataProduct


class DataMeshPublisher:
    """Automatically publish domain data to mesh"""
    
    @staticmethod
    async def publish_loan_data(loan_id: str, loan_data: Dict):
        """Publish loan data to mesh"""
        data_product = DataProduct(
            id=f"loan-{loan_id}",
            name=f"Loan {loan_id}",
            domain="Loans",
            description="Real-time loan data",
            schema={
                "loan_id": "string",
                "amount": "decimal",
                "status": "string",
                "remaining_balance": "decimal",
                "payment_history": "array"
            },
            owner="loan_domain",
            tags=["loan", "servicing", "real-time"],
            sla={"availability": "99.9%", "latency_ms": 100},
            lineage=[],
            quality_score=0.95
        )
        
        # Register in catalog
        data_mesh_catalog.register_product(data_product)
        
        # Update with actual data
        data_mesh_catalog.update_product_data(f"loan-{loan_id}", loan_data)
    
    @staticmethod
    async def publish_client_data(client_id: str, client_data: Dict):
        """Publish client data to mesh"""
        data_product = DataProduct(
            id=f"client-{client_id}",
            name=f"Client {client_id}",
            domain="Clients",
            description="Customer 360 data",
            schema={
                "client_id": "string",
                "kyc_status": "string",
                "risk_score": "integer",
                "accounts": "array",
                "loans": "array"
            },
            owner="client_domain",
            tags=["client", "kyc", "360"],
            sla={"availability": "99.9%", "latency_ms": 50},
            lineage=[],
            quality_score=0.98
        )
        
        data_mesh_catalog.register_product(data_product)
        data_mesh_catalog.update_product_data(f"client-{client_id}", client_data)
    
    @staticmethod
    async def publish_transaction_data(transaction_id: str, transaction_data: Dict):
        """Publish transaction data to mesh"""
        data_product = DataProduct(
            id=f"transaction-{transaction_id}",
            name=f"Transaction {transaction_id}",
            domain="Payments",
            description="Payment transaction data",
            schema={
                "transaction_id": "string",
                "amount": "decimal",
                "from_account": "string",
                "to_account": "string",
                "fraud_score": "float"
            },
            owner="payment_domain",
            tags=["payment", "transaction", "fraud"],
            sla={"availability": "99.99%", "latency_ms": 10},
            lineage=[],
            quality_score=0.99
        )
        
        data_mesh_catalog.register_product(data_product)
        data_mesh_catalog.update_product_data(f"transaction-{transaction_id}", transaction_data)


class DataMeshConsumer:
    """Consume data from mesh for cross-domain analytics"""
    
    @staticmethod
    def get_customer_360(client_id: str) -> Dict:
        """Get complete customer view from mesh"""
        # Query all data products related to client
        client_data = data_mesh_catalog.get_product_data(f"client-{client_id}")
        
        # Find related loans
        loans = data_mesh_catalog.search_products(
            query=f"client:{client_id}",
            domain="Loans"
        )
        
        # Find related accounts
        accounts = data_mesh_catalog.search_products(
            query=f"client:{client_id}",
            domain="Accounts"
        )
        
        # Find related transactions
        transactions = data_mesh_catalog.search_products(
            query=f"client:{client_id}",
            domain="Payments"
        )
        
        return {
            "client": client_data,
            "loans": loans,
            "accounts": accounts,
            "transactions": transactions,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

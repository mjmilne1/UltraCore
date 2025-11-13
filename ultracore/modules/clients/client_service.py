"""
Client Service - Full CRUD with Data Mesh Integration
Integrates: Data Mesh, AI Agents, ML, and MCP
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ultracore.models.client import Client, ClientStatus, RiskProfile, ClientType
from ultracore.datamesh.client_mesh import client_data_mesh, DataSource
from ultracore.agents.client_agent import client_agent

class ClientService:
    """
    Enterprise-grade client management service
    Features:
    - Full CRUD operations
    - Data Mesh integration for governance
    - AI agent integration for automation
    - Event sourcing for audit trails
    """
    
    def __init__(self):
        self.clients = {}
        self.client_counter = 0
    
    async def create_client(
        self,
        client_type: ClientType,
        email: str,
        created_by: str,
        **kwargs
    ) -> Client:
        """
        Create new client with Data Mesh integration
        """
        
        # Generate client ID
        self.client_counter += 1
        client_id = f"CLT-{self.client_counter:05d}"
        
        # Create client object
        client_data = {
            "id": client_id,
            "client_type": client_type,
            "status": ClientStatus.PROSPECT,
            "email": email,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": created_by,
            **kwargs
        }
        
        client = Client(**client_data)
        
        # Ingest into Data Mesh
        mesh_result = client_data_mesh.ingest_client_data(
            client_id=client_id,
            data=client.dict(),
            source=DataSource.MANUAL_ENTRY,
            created_by=created_by
        )
        
        # Run AI risk assessment
        risk_assessment = await client_agent.assess_client_risk(client.dict())
        
        # Store client
        self.clients[client_id] = {
            "client": client,
            "mesh_result": mesh_result,
            "risk_assessment": risk_assessment
        }
        
        print(f"✅ Client {client_id} created")
        print(f"   Data Quality: {mesh_result['quality_level']}")
        print(f"   Risk Level: {risk_assessment['risk_level']}")
        
        return client
    
    async def get_client(
        self,
        client_id: str,
        include_lineage: bool = False
    ) -> Optional[Client]:
        """
        Get client by ID with optional Data Mesh lineage
        """
        stored = self.clients.get(client_id)
        if not stored:
            return None
        
        if include_lineage:
            # Get data from Data Mesh with full lineage
            mesh_data = client_data_mesh.query_client_data(
                client_id,
                include_lineage=True
            )
            stored["client"].__dict__["_lineage"] = mesh_data.get("_lineage", [])
            stored["client"].__dict__["_quality"] = mesh_data.get("_quality", 0)
        
        return stored["client"]
    
    async def update_client(
        self,
        client_id: str,
        updated_by: str,
        **updates
    ) -> Optional[Client]:
        """
        Update client with Data Mesh version tracking
        """
        stored = self.clients.get(client_id)
        if not stored:
            return None
        
        client = stored["client"]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(client, key):
                setattr(client, key, value)
        
        client.updated_at = datetime.now(timezone.utc)
        
        # Update in Data Mesh
        mesh_result = client_data_mesh.update_client_data(
            client_id=client_id,
            updates=updates,
            source=DataSource.MANUAL_ENTRY,
            updated_by=updated_by
        )
        
        # Re-assess risk if significant changes
        if any(key in ["annual_income", "net_worth", "investment_experience"] for key in updates):
            risk_assessment = await client_agent.assess_client_risk(client.dict())
            stored["risk_assessment"] = risk_assessment
            print(f"🔄 Risk re-assessed: {risk_assessment['risk_level']}")
        
        stored["mesh_result"] = mesh_result
        
        return client
    
    async def list_clients(
        self,
        status: Optional[ClientStatus] = None,
        advisor_id: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[Client]:
        """
        List clients with filtering
        """
        clients = [stored["client"] for stored in self.clients.values()]
        
        if status:
            clients = [c for c in clients if c.status == status]
        
        if advisor_id:
            clients = [c for c in clients if c.advisor_id == advisor_id]
        
        if risk_level:
            # Filter by AI-assessed risk level
            clients = [
                c for c in clients
                if self.clients[c.id]["risk_assessment"]["risk_level"] == risk_level
            ]
        
        return clients
    
    async def get_client_with_ai_insights(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Get client with AI insights and recommendations
        """
        client = await self.get_client(client_id)
        if not client:
            return {"error": "Client not found"}
        
        stored = self.clients[client_id]
        
        # Get Data Mesh quality report
        quality_report = client_data_mesh.get_data_quality_report(client_id)
        
        # Get portfolio recommendations
        portfolio_rec = await client_agent.recommend_portfolio(
            client.dict(),
            client.risk_profile
        )
        
        return {
            "client": client.dict(),
            "risk_assessment": stored["risk_assessment"],
            "data_quality": quality_report,
            "portfolio_recommendation": portfolio_rec,
            "mesh_version": stored["mesh_result"]["version"]
        }
    
    async def calculate_portfolio_value(
        self,
        client_id: str
    ) -> float:
        """
        Calculate total portfolio value for client
        Integrates with UltraWealth market data
        """
        from ultracore.services.ultrawealth import ultrawealth_service
        
        client = await self.get_client(client_id)
        if not client:
            return 0.0
        
        # In production, this would query holdings database
        # For now, use sample holdings
        sample_holdings = {
            "VAS.AX": 1000,
            "VGS.AX": 500,
            "VAF.AX": 2000
        }
        
        try:
            prices = await ultrawealth_service.get_portfolio_prices(
                list(sample_holdings.keys())
            )
            
            total_value = sum(
                shares * prices.get(ticker, 0)
                for ticker, shares in sample_holdings.items()
            )
            
            return round(total_value, 2)
        except Exception as e:
            print(f"Error calculating portfolio value: {e}")
            return 0.0
    
    async def get_audit_trail(
        self,
        client_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit trail from Data Mesh
        """
        return client_data_mesh.get_audit_trail(client_id)
    
    async def delete_client(
        self,
        client_id: str,
        deleted_by: str,
        reason: str
    ) -> bool:
        """
        Soft delete client (mark as closed)
        """
        client = await self.get_client(client_id)
        if not client:
            return False
        
        await self.update_client(
            client_id=client_id,
            updated_by=deleted_by,
            status=ClientStatus.CLOSED
        )
        
        # Record deletion event
        client_data_mesh._record_event("CLIENT_DELETED", {
            "client_id": client_id,
            "deleted_by": deleted_by,
            "reason": reason
        })
        
        return True

# Global instance
client_service = ClientService()

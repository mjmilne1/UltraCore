"""
Client Data Mesh Integration
Provides data governance, quality, and lineage tracking for client data
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import hashlib
import json

class DataQuality(str, Enum):
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 85-94%
    ACCEPTABLE = "acceptable"  # 70-84%
    POOR = "poor"           # <70%

class DataSource(str, Enum):
    MANUAL_ENTRY = "manual_entry"
    API_IMPORT = "api_import"
    AGENT_GENERATED = "agent_generated"
    ML_PREDICTED = "ml_predicted"

class ClientDataMesh:
    """
    Data Mesh implementation for client data
    Provides:
    - Data quality scoring
    - Data lineage tracking
    - Event sourcing
    - Audit trails
    """
    
    def __init__(self):
        self.data_store = {}
        self.event_store = []
        self.lineage_store = {}
        self.quality_metrics = {}
    
    def ingest_client_data(
        self,
        client_id: str,
        data: Dict[str, Any],
        source: DataSource,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Ingest client data with full lineage tracking
        """
        mesh_key = f"client:{client_id}"
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(data)
        
        # Create data lineage
        lineage = {
            "mesh_key": mesh_key,
            "source": source,
            "created_by": created_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quality_score": quality_score,
            "data_hash": self._hash_data(data),
            "version": len(self.lineage_store.get(mesh_key, [])) + 1
        }
        
        # Store data
        self.data_store[mesh_key] = {
            "data": data,
            "metadata": lineage
        }
        
        # Track lineage
        if mesh_key not in self.lineage_store:
            self.lineage_store[mesh_key] = []
        self.lineage_store[mesh_key].append(lineage)
        
        # Record event
        self._record_event("CLIENT_DATA_INGESTED", {
            "client_id": client_id,
            "source": source,
            "quality_score": quality_score
        })
        
        return {
            "mesh_key": mesh_key,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "version": lineage["version"],
            "status": "ingested"
        }
    
    def query_client_data(
        self,
        client_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Query client data with optional lineage
        """
        mesh_key = f"client:{client_id}"
        stored = self.data_store.get(mesh_key)
        
        if not stored:
            return None
        
        result = stored["data"].copy()
        
        if include_lineage:
            result["_lineage"] = self.lineage_store.get(mesh_key, [])
            result["_quality"] = stored["metadata"]["quality_score"]
        
        return result
    
    def update_client_data(
        self,
        client_id: str,
        updates: Dict[str, Any],
        source: DataSource,
        updated_by: str
    ) -> Dict[str, Any]:
        """
        Update client data with version tracking
        """
        mesh_key = f"client:{client_id}"
        current = self.data_store.get(mesh_key)
        
        if not current:
            raise ValueError(f"Client {client_id} not found in data mesh")
        
        # Merge updates
        updated_data = {**current["data"], **updates}
        
        # Re-ingest with new version
        return self.ingest_client_data(
            client_id=client_id,
            data=updated_data,
            source=source,
            created_by=updated_by
        )
    
    def get_data_quality_report(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Generate data quality report for client
        """
        mesh_key = f"client:{client_id}"
        stored = self.data_store.get(mesh_key)
        
        if not stored:
            return {"error": "Client not found"}
        
        lineage = self.lineage_store.get(mesh_key, [])
        
        return {
            "client_id": client_id,
            "current_quality_score": stored["metadata"]["quality_score"],
            "quality_level": self._get_quality_level(
                stored["metadata"]["quality_score"]
            ),
            "total_versions": len(lineage),
            "last_updated": stored["metadata"]["timestamp"],
            "data_sources": list(set(l["source"] for l in lineage)),
            "quality_history": [
                {
                    "version": l["version"],
                    "score": l["quality_score"],
                    "timestamp": l["timestamp"]
                }
                for l in lineage
            ]
        }
    
    def get_audit_trail(
        self,
        client_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for client
        """
        return [
            event for event in self.event_store
            if event.get("data", {}).get("client_id") == client_id
        ]
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate data quality score (0-100)
        Based on completeness and validity
        """
        required_fields = [
            "first_name", "last_name", "email", "phone",
            "address", "city", "state", "postcode"
        ]
        
        optional_fields = [
            "date_of_birth", "tfn", "occupation",
            "annual_income", "net_worth"
        ]
        
        # Score for required fields (70% weight)
        required_score = sum(
            1 for field in required_fields
            if data.get(field) and str(data[field]).strip()
        ) / len(required_fields) * 70
        
        # Score for optional fields (30% weight)
        optional_score = sum(
            1 for field in optional_fields
            if data.get(field) and str(data[field]).strip()
        ) / len(optional_fields) * 30
        
        return round(required_score + optional_score, 2)
    
    def _get_quality_level(self, score: float) -> DataQuality:
        """Convert score to quality level"""
        if score >= 95:
            return DataQuality.EXCELLENT
        elif score >= 85:
            return DataQuality.GOOD
        elif score >= 70:
            return DataQuality.ACCEPTABLE
        else:
            return DataQuality.POOR
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of data for change detection"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _record_event(self, event_type: str, data: Dict[str, Any]):
        """Record event in event store"""
        self.event_store.append({
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        })

# Global instance
client_data_mesh = ClientDataMesh()

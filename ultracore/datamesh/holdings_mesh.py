"""
Holdings Data Mesh
Provides data governance, quality, and lineage for position data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from ultracore.streaming.kafka_events import kafka_producer, EventType

class HoldingDataQuality(str, Enum):
    EXCELLENT = "excellent"  # 95-100% - All data verified
    GOOD = "good"           # 85-94% - Most data verified
    ACCEPTABLE = "acceptable"  # 70-84% - Core data present
    POOR = "poor"           # <70% - Missing critical data

class HoldingsDataMesh:
    """
    Data Mesh for holdings/positions
    Manages data quality, lineage, and governance
    """
    
    def __init__(self):
        self.data_store = {}
        self.lineage_store = {}
        self.quality_metrics = {}
        self.materialized_views = {}
    
    async def ingest_position(
        self,
        position_id: str,
        position_data: Dict[str, Any],
        source: str,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Ingest position data with full lineage
        """
        
        # Calculate data quality
        quality_score = self._calculate_position_quality(position_data)
        
        # Create lineage
        lineage = {
            "position_id": position_id,
            "source": source,
            "created_by": created_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quality_score": quality_score,
            "version": len(self.lineage_store.get(position_id, [])) + 1
        }
        
        # Store data
        mesh_key = f"position:{position_id}"
        self.data_store[mesh_key] = {
            "data": position_data,
            "metadata": lineage
        }
        
        # Track lineage
        if position_id not in self.lineage_store:
            self.lineage_store[position_id] = []
        self.lineage_store[position_id].append(lineage)
        
        # Produce event to Kafka
        await kafka_producer.produce(
            topic="holdings.positions",
            event_type=EventType.POSITION_UPDATED,
            data={
                "position_id": position_id,
                "quality_score": quality_score,
                **position_data
            },
            key=position_data.get("client_id")
        )
        
        # Update materialized views
        await self._update_materialized_views(position_id, position_data)
        
        return {
            "position_id": position_id,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "version": lineage["version"]
        }
    
    def query_position(
        self,
        position_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Query position with optional lineage"""
        
        mesh_key = f"position:{position_id}"
        stored = self.data_store.get(mesh_key)
        
        if not stored:
            return None
        
        result = stored["data"].copy()
        
        if include_lineage:
            result["_lineage"] = self.lineage_store.get(position_id, [])
            result["_quality"] = stored["metadata"]["quality_score"]
        
        return result
    
    def query_client_positions(
        self,
        client_id: str
    ) -> List[Dict[str, Any]]:
        """Get all positions for a client (uses materialized view)"""
        
        view_key = f"client:{client_id}:positions"
        return self.materialized_views.get(view_key, [])
    
    def get_portfolio_valuation(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """Get real-time portfolio valuation (materialized view)"""
        
        view_key = f"client:{client_id}:valuation"
        return self.materialized_views.get(view_key, {
            "total_value": 0,
            "unrealized_gain_loss": 0,
            "positions": []
        })
    
    async def _update_materialized_views(
        self,
        position_id: str,
        position_data: Dict[str, Any]
    ):
        """
        Update materialized views for fast queries
        In production, use Kafka Streams or Flink
        """
        
        client_id = position_data.get("client_id")
        if not client_id:
            return
        
        # Update client positions view
        view_key = f"client:{client_id}:positions"
        if view_key not in self.materialized_views:
            self.materialized_views[view_key] = []
        
        # Update or add position
        positions = self.materialized_views[view_key]
        existing_idx = next(
            (i for i, p in enumerate(positions) if p.get("position_id") == position_id),
            None
        )
        
        if existing_idx is not None:
            positions[existing_idx] = position_data
        else:
            positions.append(position_data)
        
        # Update valuation view
        await self._update_valuation_view(client_id)
    
    async def _update_valuation_view(self, client_id: str):
        """Update portfolio valuation materialized view"""
        
        positions = self.query_client_positions(client_id)
        
        total_value = sum(p.get("market_value", 0) for p in positions)
        total_cost = sum(p.get("cost_basis", 0) for p in positions)
        unrealized_gl = total_value - total_cost
        
        view_key = f"client:{client_id}:valuation"
        self.materialized_views[view_key] = {
            "client_id": client_id,
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_gain_loss": unrealized_gl,
            "return_pct": (unrealized_gl / total_cost * 100) if total_cost > 0 else 0,
            "positions_count": len(positions),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_position_quality(self, position_data: Dict[str, Any]) -> float:
        """Calculate data quality score for position"""
        
        required_fields = [
            "ticker", "quantity", "cost_basis", "client_id"
        ]
        
        optional_fields = [
            "purchase_date", "market_value", "current_price",
            "asset_class", "sector"
        ]
        
        # Required fields (70% weight)
        required_score = sum(
            1 for field in required_fields
            if position_data.get(field) is not None
        ) / len(required_fields) * 70
        
        # Optional fields (30% weight)
        optional_score = sum(
            1 for field in optional_fields
            if position_data.get(field) is not None
        ) / len(optional_fields) * 30
        
        return round(required_score + optional_score, 2)
    
    def _get_quality_level(self, score: float) -> HoldingDataQuality:
        """Convert quality score to level"""
        if score >= 95:
            return HoldingDataQuality.EXCELLENT
        elif score >= 85:
            return HoldingDataQuality.GOOD
        elif score >= 70:
            return HoldingDataQuality.ACCEPTABLE
        else:
            return HoldingDataQuality.POOR

# Global instance
holdings_data_mesh = HoldingsDataMesh()

"""
Transaction Data Mesh
Data governance, quality, and lineage for all transactions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.transactions.kafka_events import transaction_kafka, TransactionEventType

class TransactionDataQuality(str):
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 85-94%
    ACCEPTABLE = "acceptable"  # 70-84%
    POOR = "poor"           # <70%

class TransactionDataMesh:
    """
    Data Mesh for transaction data
    Provides governance, quality scoring, and lineage
    """
    
    def __init__(self):
        self.data_store = {}
        self.lineage_store = {}
        self.quality_metrics = {}
        self.materialized_views = {
            "orders_by_client": {},
            "orders_by_status": {},
            "trades_by_client": {},
            "settlement_queue": []
        }
    
    async def ingest_order(
        self,
        order_id: str,
        order_data: Dict[str, Any],
        source: str,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Ingest order with full lineage tracking
        """
        
        # Calculate data quality
        quality_score = self._calculate_order_quality(order_data)
        
        # Create lineage
        lineage = {
            "order_id": order_id,
            "source": source,
            "created_by": created_by,
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": quality_score,
            "version": len(self.lineage_store.get(order_id, [])) + 1
        }
        
        # Store data
        mesh_key = f"order:{order_id}"
        self.data_store[mesh_key] = {
            "data": order_data,
            "metadata": lineage
        }
        
        # Track lineage
        if order_id not in self.lineage_store:
            self.lineage_store[order_id] = []
        self.lineage_store[order_id].append(lineage)
        
        # Update materialized views
        await self._update_order_views(order_id, order_data)
        
        # Produce event
        await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_CREATED,
            {**order_data, "quality_score": quality_score}
        )
        
        return {
            "order_id": order_id,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "version": lineage["version"]
        }
    
    async def ingest_trade(
        self,
        trade_id: str,
        trade_data: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """Ingest trade execution"""
        
        quality_score = self._calculate_trade_quality(trade_data)
        
        mesh_key = f"trade:{trade_id}"
        self.data_store[mesh_key] = {
            "data": trade_data,
            "metadata": {
                "trade_id": trade_id,
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": quality_score
            }
        }
        
        # Update views
        await self._update_trade_views(trade_id, trade_data)
        
        return {
            "trade_id": trade_id,
            "quality_score": quality_score
        }
    
    async def ingest_settlement(
        self,
        settlement_id: str,
        settlement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ingest settlement"""
        
        mesh_key = f"settlement:{settlement_id}"
        self.data_store[mesh_key] = {
            "data": settlement_data,
            "metadata": {
                "settlement_id": settlement_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Add to settlement queue
        self.materialized_views["settlement_queue"].append(settlement_data)
        
        return {
            "settlement_id": settlement_id,
            "status": "ingested"
        }
    
    def query_order(
        self,
        order_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Query order with optional lineage"""
        
        mesh_key = f"order:{order_id}"
        stored = self.data_store.get(mesh_key)
        
        if not stored:
            return None
        
        result = stored["data"].copy()
        
        if include_lineage:
            result["_lineage"] = self.lineage_store.get(order_id, [])
            result["_quality"] = stored["metadata"]["quality_score"]
        
        return result
    
    def get_orders_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all orders for client (materialized view)"""
        return self.materialized_views["orders_by_client"].get(client_id, [])
    
    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get orders by status (materialized view)"""
        return self.materialized_views["orders_by_status"].get(status, [])
    
    def get_settlement_queue(self) -> List[Dict[str, Any]]:
        """Get pending settlements"""
        return [
            s for s in self.materialized_views["settlement_queue"]
            if s.get("status") == "pending"
        ]
    
    async def _update_order_views(
        self,
        order_id: str,
        order_data: Dict[str, Any]
    ):
        """Update materialized views for orders"""
        
        client_id = order_data.get("client_id")
        status = order_data.get("status")
        
        # Update by client
        if client_id:
            if client_id not in self.materialized_views["orders_by_client"]:
                self.materialized_views["orders_by_client"][client_id] = []
            
            orders = self.materialized_views["orders_by_client"][client_id]
            
            # Update or add
            existing_idx = next(
                (i for i, o in enumerate(orders) if o.get("order_id") == order_id),
                None
            )
            
            if existing_idx is not None:
                orders[existing_idx] = order_data
            else:
                orders.append(order_data)
        
        # Update by status
        if status:
            if status not in self.materialized_views["orders_by_status"]:
                self.materialized_views["orders_by_status"][status] = []
            
            self.materialized_views["orders_by_status"][status].append(order_data)
    
    async def _update_trade_views(
        self,
        trade_id: str,
        trade_data: Dict[str, Any]
    ):
        """Update materialized views for trades"""
        
        client_id = trade_data.get("client_id")
        
        if client_id:
            if client_id not in self.materialized_views["trades_by_client"]:
                self.materialized_views["trades_by_client"][client_id] = []
            
            self.materialized_views["trades_by_client"][client_id].append(trade_data)
    
    def _calculate_order_quality(self, order_data: Dict[str, Any]) -> float:
        """Calculate order data quality score"""
        
        required_fields = [
            "client_id", "ticker", "side", "quantity", "order_type"
        ]
        
        optional_fields = [
            "limit_price", "stop_price", "time_in_force", "account_id"
        ]
        
        # Required fields (70% weight)
        required_score = sum(
            1 for field in required_fields
            if order_data.get(field) is not None
        ) / len(required_fields) * 70
        
        # Optional fields (30% weight)
        optional_score = sum(
            1 for field in optional_fields
            if order_data.get(field) is not None
        ) / len(optional_fields) * 30
        
        return round(required_score + optional_score, 2)
    
    def _calculate_trade_quality(self, trade_data: Dict[str, Any]) -> float:
        """Calculate trade data quality score"""
        
        required_fields = [
            "trade_id", "order_id", "ticker", "quantity",
            "price", "side", "timestamp"
        ]
        
        score = sum(
            1 for field in required_fields
            if trade_data.get(field) is not None
        ) / len(required_fields) * 100
        
        return round(score, 2)
    
    def _get_quality_level(self, score: float) -> str:
        """Convert quality score to level"""
        if score >= 95:
            return TransactionDataQuality.EXCELLENT
        elif score >= 85:
            return TransactionDataQuality.GOOD
        elif score >= 70:
            return TransactionDataQuality.ACCEPTABLE
        else:
            return TransactionDataQuality.POOR

# Global instance
transaction_data_mesh = TransactionDataMesh()

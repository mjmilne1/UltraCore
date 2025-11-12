"""
Order Management Service
Complete order lifecycle management with Kafka events
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ultracore.modules.transactions.kafka_events import (
    transaction_kafka, TransactionEventType, OrderStatus, 
    OrderType, OrderSide, TimeInForce
)
from ultracore.datamesh.transaction_mesh import transaction_data_mesh
from ultracore.agents.transaction_agent import transaction_agent
from ultracore.streaming.kafka_events import event_store

class OrderManagementService:
    """
    Order Management System with full lifecycle tracking
    
    Features:
    - Create/cancel orders
    - Order validation
    - Status tracking
    - Event sourcing
    - AI validation
    """
    
    def __init__(self):
        self.orders = {}
        self.order_counter = 0
        
        # Subscribe to order events
        transaction_kafka.subscribe_to_orders(self._handle_order_event)
    
    async def create_order(
        self,
        client_id: str,
        ticker: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create new order
        """
        
        self.order_counter += 1
        order_id = f"ORD-{self.order_counter:08d}"
        
        order_data = {
            "order_id": order_id,
            "client_id": client_id,
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "filled_quantity": 0,
            "remaining_quantity": quantity,
            "order_type": order_type,
            "limit_price": limit_price,
            "stop_price": stop_price,
            "time_in_force": time_in_force,
            "status": OrderStatus.DRAFT,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        # Store order
        self.orders[order_id] = order_data
        
        # Ingest into Data Mesh
        mesh_result = await transaction_data_mesh.ingest_order(
            order_id=order_id,
            order_data=order_data,
            source="order_entry",
            created_by=client_id
        )
        
        # Produce Kafka event
        await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_CREATED,
            order_data
        )
        
        # Store in event store
        event_store.create_snapshot(order_id, order_data)
        
        print(f"✅ Order created: {order_id} ({side} {quantity} {ticker})")
        
        return {
            "order_id": order_id,
            "order": order_data,
            "data_quality": mesh_result["quality_score"]
        }
    
    async def validate_order(
        self,
        order_id: str,
        client_data: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate order using AI agent
        """
        
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        
        # Run AI validation
        validation = await transaction_agent.validate_order(
            order,
            client_data,
            portfolio
        )
        
        # Update order status based on validation
        if validation["decision"] == "approved":
            await self._update_order_status(order_id, OrderStatus.VALIDATED)
            
            # Produce validation event
            await transaction_kafka.produce_order_event(
                TransactionEventType.ORDER_VALIDATED,
                {**order, "validation": validation}
            )
        else:
            await self._update_order_status(order_id, OrderStatus.REJECTED)
            
            # Produce rejection event
            await transaction_kafka.produce_order_event(
                TransactionEventType.ORDER_REJECTED,
                {**order, "validation": validation}
            )
        
        return validation
    
    async def submit_order(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Submit validated order for execution
        """
        
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        
        if order["status"] != OrderStatus.VALIDATED:
            return {"error": f"Order not validated (status: {order['status']})"}
        
        # Update status
        await self._update_order_status(order_id, OrderStatus.SUBMITTED)
        
        # Produce submission event
        await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_SUBMITTED,
            order
        )
        
        print(f"📤 Order submitted: {order_id}")
        
        return {
            "order_id": order_id,
            "status": OrderStatus.SUBMITTED,
            "message": "Order submitted for execution"
        }
    
    async def cancel_order(
        self,
        order_id: str,
        reason: str = "Client requested"
    ) -> Dict[str, Any]:
        """
        Cancel order
        """
        
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        
        # Check if order can be cancelled
        if order["status"] in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return {"error": f"Cannot cancel order with status {order['status']}"}
        
        # Update status
        await self._update_order_status(order_id, OrderStatus.CANCELLED)
        
        order["cancellation_reason"] = reason
        order["cancelled_at"] = datetime.utcnow().isoformat()
        
        # Produce cancellation event
        await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_CANCELLED,
            order
        )
        
        print(f"❌ Order cancelled: {order_id}")
        
        return {
            "order_id": order_id,
            "status": OrderStatus.CANCELLED,
            "reason": reason
        }
    
    async def update_fill(
        self,
        order_id: str,
        filled_quantity: float,
        avg_price: float
    ) -> Dict[str, Any]:
        """
        Update order with fill information
        """
        
        order = self.orders.get(order_id)
        if not order:
            return {"error": "Order not found"}
        
        previous_filled = order["filled_quantity"]
        new_filled = previous_filled + filled_quantity
        
        order["filled_quantity"] = new_filled
        order["remaining_quantity"] = order["quantity"] - new_filled
        order["avg_fill_price"] = avg_price
        order["updated_at"] = datetime.utcnow().isoformat()
        
        # Determine new status
        if new_filled >= order["quantity"]:
            new_status = OrderStatus.FILLED
            event_type = TransactionEventType.ORDER_FILLED
        else:
            new_status = OrderStatus.PARTIALLY_FILLED
            event_type = TransactionEventType.ORDER_PARTIALLY_FILLED
        
        await self._update_order_status(order_id, new_status)
        
        # Produce fill event
        await transaction_kafka.produce_order_event(
            event_type,
            {
                **order,
                "fill_quantity": filled_quantity,
                "total_filled": new_filled
            }
        )
        
        return {
            "order_id": order_id,
            "status": new_status,
            "filled_quantity": new_filled,
            "remaining_quantity": order["remaining_quantity"]
        }
    
    async def get_order(
        self,
        order_id: str,
        include_lineage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get order with optional lineage"""
        
        if include_lineage:
            return transaction_data_mesh.query_order(order_id, include_lineage=True)
        
        return self.orders.get(order_id)
    
    async def get_client_orders(
        self,
        client_id: str,
        status: Optional[OrderStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all orders for client"""
        
        # Try materialized view first
        orders = transaction_data_mesh.get_orders_by_client(client_id)
        
        if not orders:
            # Fallback to in-memory
            orders = [
                o for o in self.orders.values()
                if o["client_id"] == client_id
            ]
        
        if status:
            orders = [o for o in orders if o["status"] == status]
        
        return orders
    
    async def get_orders_by_status(
        self,
        status: OrderStatus
    ) -> List[Dict[str, Any]]:
        """Get orders by status"""
        
        return transaction_data_mesh.get_orders_by_status(status)
    
    async def _update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus
    ):
        """Update order status"""
        
        order = self.orders.get(order_id)
        if order:
            order["status"] = new_status
            order["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in Data Mesh
            await transaction_data_mesh.ingest_order(
                order_id=order_id,
                order_data=order,
                source="order_management",
                created_by=order["client_id"]
            )
    
    def _handle_order_event(self, event: Dict[str, Any]):
        """Handle order events from Kafka"""
        
        event_type = event["event_type"]
        data = event["data"]
        
        print(f"📥 Order event: {event_type} - {data.get('order_id')}")

# Global instance
order_management_service = OrderManagementService()

"""
Trade Execution Engine
Matches orders, executes trades, and manages execution lifecycle
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.transactions.kafka_events import (
    transaction_kafka, TransactionEventType, OrderStatus
)
from ultracore.modules.transactions.order_service import order_management_service
from ultracore.ml.rl.execution_agent import execution_rl_agent, ExecutionAction

class TradeExecutionEngine:
    """
    Trade Execution Engine with RL-optimized execution
    
    Features:
    - Order matching
    - Trade execution
    - Optimal execution (RL)
    - Market impact minimization
    - Execution reporting
    """
    
    def __init__(self):
        self.trades = {}
        self.trade_counter = 0
        self.execution_queue = []
        
        # Subscribe to trade events
        transaction_kafka.subscribe_to_trades(self._handle_trade_event)
    
    async def execute_order(
        self,
        order_id: str,
        market_data: Dict[str, Any],
        use_optimal_execution: bool = True
    ) -> Dict[str, Any]:
        """
        Execute order with optional RL optimization
        """
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"error": "Order not found"}
        
        if order["status"] not in [OrderStatus.SUBMITTED, OrderStatus.ACKNOWLEDGED]:
            return {"error": f"Cannot execute order with status {order['status']}"}
        
        # Acknowledge order
        await self._acknowledge_order(order_id)
        
        if use_optimal_execution:
            # Use RL agent for optimal execution
            execution_plan = execution_rl_agent.get_optimal_execution_plan(
                order,
                market_data
            )
            
            result = await self._execute_with_plan(order, execution_plan, market_data)
        else:
            # Simple immediate execution
            result = await self._execute_immediately(order, market_data)
        
        return result
    
    async def execute_market_order(
        self,
        order_id: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute market order immediately
        """
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"error": "Order not found"}
        
        # Get market price
        if order["side"] == "buy":
            execution_price = market_data.get("ask_price", market_data.get("mid_price", 100))
        else:
            execution_price = market_data.get("bid_price", market_data.get("mid_price", 100))
        
        # Create trade
        trade_result = await self._create_trade(
            order_id=order_id,
            quantity=order["quantity"],
            price=execution_price,
            market_data=market_data
        )
        
        # Update order
        await order_management_service.update_fill(
            order_id=order_id,
            filled_quantity=order["quantity"],
            avg_price=execution_price
        )
        
        return trade_result
    
    async def execute_limit_order(
        self,
        order_id: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute limit order if price is favorable
        """
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"error": "Order not found"}
        
        limit_price = order["limit_price"]
        current_price = market_data.get("mid_price", 0)
        
        # Check if limit price is met
        can_execute = False
        
        if order["side"] == "buy" and current_price <= limit_price:
            can_execute = True
            execution_price = min(current_price, limit_price)
        elif order["side"] == "sell" and current_price >= limit_price:
            can_execute = True
            execution_price = max(current_price, limit_price)
        
        if not can_execute:
            return {
                "order_id": order_id,
                "executed": False,
                "reason": f"Limit price not met (limit: {limit_price}, market: {current_price})"
            }
        
        # Execute trade
        trade_result = await self._create_trade(
            order_id=order_id,
            quantity=order["quantity"],
            price=execution_price,
            market_data=market_data
        )
        
        # Update order
        await order_management_service.update_fill(
            order_id=order_id,
            filled_quantity=order["quantity"],
            avg_price=execution_price
        )
        
        return trade_result
    
    async def execute_stop_order(
        self,
        order_id: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute stop order if triggered
        """
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"error": "Order not found"}
        
        stop_price = order["stop_price"]
        current_price = market_data.get("mid_price", 0)
        
        # Check if stop is triggered
        triggered = False
        
        if order["side"] == "buy" and current_price >= stop_price:
            triggered = True
        elif order["side"] == "sell" and current_price <= stop_price:
            triggered = True
        
        if not triggered:
            return {
                "order_id": order_id,
                "executed": False,
                "reason": f"Stop not triggered (stop: {stop_price}, market: {current_price})"
            }
        
        # Execute at market once triggered
        return await self.execute_market_order(order_id, market_data)
    
    async def _execute_with_plan(
        self,
        order: Dict[str, Any],
        execution_plan: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute order following RL execution plan
        """
        
        order_id = order["order_id"]
        total_quantity = order["quantity"]
        remaining_quantity = total_quantity
        
        trades = []
        total_value = 0
        
        for step in execution_plan["plan"]:
            if remaining_quantity <= 0:
                break
            
            action = ExecutionAction(step["action"])
            exec_quantity = min(step["quantity"], remaining_quantity)
            
            if exec_quantity > 0:
                # Execute this slice
                execution_price = self._simulate_execution_price(
                    order["side"],
                    exec_quantity,
                    market_data
                )
                
                trade = await self._create_trade(
                    order_id=order_id,
                    quantity=exec_quantity,
                    price=execution_price,
                    market_data=market_data
                )
                
                trades.append(trade)
                total_value += exec_quantity * execution_price
                remaining_quantity -= exec_quantity
                
                # Update order fill
                await order_management_service.update_fill(
                    order_id=order_id,
                    filled_quantity=exec_quantity,
                    avg_price=execution_price
                )
        
        # Calculate average price
        avg_price = total_value / total_quantity if total_quantity > 0 else 0
        
        return {
            "order_id": order_id,
            "execution_strategy": "rl_optimized",
            "trades": trades,
            "total_trades": len(trades),
            "total_quantity": total_quantity,
            "avg_price": avg_price,
            "execution_plan": execution_plan
        }
    
    async def _execute_immediately(
        self,
        order: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute entire order immediately
        """
        
        order_id = order["order_id"]
        quantity = order["quantity"]
        
        # Determine execution price
        if order["order_type"] == "market":
            if order["side"] == "buy":
                price = market_data.get("ask_price", market_data.get("mid_price", 100))
            else:
                price = market_data.get("bid_price", market_data.get("mid_price", 100))
        elif order["order_type"] == "limit":
            price = order["limit_price"]
        else:
            price = market_data.get("mid_price", 100)
        
        # Create trade
        trade = await self._create_trade(
            order_id=order_id,
            quantity=quantity,
            price=price,
            market_data=market_data
        )
        
        # Update order
        await order_management_service.update_fill(
            order_id=order_id,
            filled_quantity=quantity,
            avg_price=price
        )
        
        return {
            "order_id": order_id,
            "execution_strategy": "immediate",
            "trade": trade,
            "avg_price": price
        }
    
    async def _create_trade(
        self,
        order_id: str,
        quantity: float,
        price: float,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create trade record
        """
        
        self.trade_counter += 1
        trade_id = f"TRD-{self.trade_counter:08d}"
        
        order = await order_management_service.get_order(order_id)
        
        trade_data = {
            "trade_id": trade_id,
            "order_id": order_id,
            "client_id": order["client_id"],
            "ticker": order["ticker"],
            "side": order["side"],
            "quantity": quantity,
            "price": price,
            "value": quantity * price,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "market_data": {
                "mid_price": market_data.get("mid_price"),
                "spread": market_data.get("spread"),
                "volume": market_data.get("volume")
            }
        }
        
        # Store trade
        self.trades[trade_id] = trade_data
        
        # Ingest into Data Mesh
        from ultracore.datamesh.transaction_mesh import transaction_data_mesh
        await transaction_data_mesh.ingest_trade(
            trade_id=trade_id,
            trade_data=trade_data,
            source="execution_engine"
        )
        
        # Produce Kafka event
        await transaction_kafka.produce_trade_event(
            TransactionEventType.TRADE_EXECUTED,
            trade_data
        )
        
        print(f"✅ Trade executed: {trade_id} ({quantity} {order['ticker']} @ ${price})")
        
        return trade_data
    
    async def _acknowledge_order(self, order_id: str):
        """Acknowledge order receipt"""
        
        order = await order_management_service.get_order(order_id)
        
        await order_management_service._update_order_status(
            order_id,
            OrderStatus.ACKNOWLEDGED
        )
        
        await transaction_kafka.produce_order_event(
            TransactionEventType.ORDER_ACKNOWLEDGED,
            order
        )
    
    def _simulate_execution_price(
        self,
        side: str,
        quantity: float,
        market_data: Dict[str, Any]
    ) -> float:
        """
        Simulate execution price with market impact
        """
        
        import numpy as np
        
        mid_price = market_data.get("mid_price", 100)
        spread = market_data.get("spread", 0.001)
        avg_volume = market_data.get("avg_volume", 1000000)
        
        # Base price
        if side == "buy":
            base_price = mid_price + (spread * mid_price / 2)
        else:
            base_price = mid_price - (spread * mid_price / 2)
        
        # Market impact
        volume_pct = quantity / avg_volume if avg_volume > 0 else 0
        impact = mid_price * 0.1 * np.sqrt(volume_pct)
        
        if side == "buy":
            price = base_price + impact
        else:
            price = base_price - impact
        
        # Add small random noise
        noise = np.random.normal(0, spread * mid_price * 0.1)
        
        return round(price + noise, 2)
    
    def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get trade details"""
        return self.trades.get(trade_id)
    
    def get_order_trades(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all trades for an order"""
        return [
            trade for trade in self.trades.values()
            if trade["order_id"] == order_id
        ]
    
    def _handle_trade_event(self, event: Dict[str, Any]):
        """Handle trade events from Kafka"""
        
        event_type = event["event_type"]
        data = event["data"]
        
        print(f"📥 Trade event: {event_type} - {data.get('trade_id')}")

# Global instance
trade_execution_engine = TradeExecutionEngine()

"""
MCP Tools for Transaction Management
Enables AI assistants to interact with trading system
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ultracore.modules.transactions.order_service import order_management_service
from ultracore.modules.transactions.execution_engine import trade_execution_engine
from ultracore.modules.transactions.settlement_engine import settlement_engine
from ultracore.modules.transactions.history_service import transaction_history_service
from ultracore.agents.transaction_agent import transaction_agent
from ultracore.modules.transactions.kafka_events import OrderType, OrderSide, TimeInForce

class TransactionMCPTools:
    """
    MCP tools for AI assistants to manage transactions
    """
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        return [
            {
                "name": "create_order",
                "description": "Create a new order (market, limit, stop)",
                "parameters": {
                    "client_id": "Client ID",
                    "ticker": "Security ticker",
                    "side": "buy or sell",
                    "quantity": "Number of shares",
                    "order_type": "market, limit, or stop",
                    "limit_price": "Limit price (for limit orders)",
                    "stop_price": "Stop price (for stop orders)"
                }
            },
            {
                "name": "validate_order",
                "description": "Validate order using AI agent",
                "parameters": {
                    "order_id": "Order ID",
                    "client_id": "Client ID"
                }
            },
            {
                "name": "execute_order",
                "description": "Execute validated order",
                "parameters": {
                    "order_id": "Order ID",
                    "use_optimal_execution": "Use RL optimization (true/false)"
                }
            },
            {
                "name": "cancel_order",
                "description": "Cancel an order",
                "parameters": {
                    "order_id": "Order ID",
                    "reason": "Cancellation reason"
                }
            },
            {
                "name": "get_order_status",
                "description": "Get order status and details",
                "parameters": {
                    "order_id": "Order ID"
                }
            },
            {
                "name": "get_client_orders",
                "description": "Get all orders for client",
                "parameters": {
                    "client_id": "Client ID",
                    "status": "Filter by status (optional)"
                }
            },
            {
                "name": "get_trade_details",
                "description": "Get trade execution details",
                "parameters": {
                    "trade_id": "Trade ID"
                }
            },
            {
                "name": "get_settlement_status",
                "description": "Get settlement status",
                "parameters": {
                    "settlement_id": "Settlement ID"
                }
            },
            {
                "name": "process_settlements",
                "description": "Process pending settlements",
                "parameters": {
                    "as_of_date": "Process settlements up to this date"
                }
            },
            {
                "name": "get_transaction_history",
                "description": "Get transaction history for client",
                "parameters": {
                    "client_id": "Client ID",
                    "start_date": "Start date (optional)",
                    "end_date": "End date (optional)"
                }
            },
            {
                "name": "get_trading_summary",
                "description": "Get trading summary for period",
                "parameters": {
                    "client_id": "Client ID",
                    "period": "ytd, 1m, 3m, 1y"
                }
            },
            {
                "name": "detect_fraud",
                "description": "Run fraud detection on order",
                "parameters": {
                    "order_id": "Order ID"
                }
            }
        ]
    
    @staticmethod
    async def create_order(
        client_id: str,
        ticker: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "day"
    ) -> Dict[str, Any]:
        """MCP tool: Create order"""
        
        result = await order_management_service.create_order(
            client_id=client_id,
            ticker=ticker,
            side=OrderSide(side),
            quantity=quantity,
            order_type=OrderType(order_type),
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=TimeInForce(time_in_force)
        )
        
        return {
            "success": True,
            "order_id": result["order_id"],
            "order": result["order"],
            "data_quality": result["data_quality"]
        }
    
    @staticmethod
    async def validate_order(
        order_id: str,
        client_id: str
    ) -> Dict[str, Any]:
        """MCP tool: Validate order"""
        
        # Get client data (mock for now)
        client_data = {
            "client_id": client_id,
            "kyc_completed": True,
            "status": "active",
            "trading_enabled": True
        }
        
        # Get portfolio (mock for now)
        from ultracore.modules.holdings.holdings_service import holdings_service
        portfolio = await holdings_service.get_portfolio_value(client_id, real_time=False)
        
        validation = await order_management_service.validate_order(
            order_id=order_id,
            client_data=client_data,
            portfolio=portfolio
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "validation": validation
        }
    
    @staticmethod
    async def execute_order(
        order_id: str,
        use_optimal_execution: bool = True
    ) -> Dict[str, Any]:
        """MCP tool: Execute order"""
        
        # Mock market data
        market_data = {
            "mid_price": 100.00,
            "bid_price": 99.95,
            "ask_price": 100.05,
            "spread": 0.001,
            "volume": 1000000,
            "avg_volume": 1000000,
            "volatility": 0.02
        }
        
        result = await trade_execution_engine.execute_order(
            order_id=order_id,
            market_data=market_data,
            use_optimal_execution=use_optimal_execution
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "execution": result
        }
    
    @staticmethod
    async def cancel_order(
        order_id: str,
        reason: str = "Client requested"
    ) -> Dict[str, Any]:
        """MCP tool: Cancel order"""
        
        result = await order_management_service.cancel_order(
            order_id=order_id,
            reason=reason
        )
        
        if "error" in result:
            return {"success": False, "error": result["error"]}
        
        return {
            "success": True,
            "order_id": order_id,
            "status": result["status"]
        }
    
    @staticmethod
    async def get_order_status(order_id: str) -> Dict[str, Any]:
        """MCP tool: Get order status"""
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        return {
            "success": True,
            "order": order
        }
    
    @staticmethod
    async def get_client_orders(
        client_id: str,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get client orders"""
        
        from ultracore.modules.transactions.kafka_events import OrderStatus
        
        orders = await order_management_service.get_client_orders(
            client_id=client_id,
            status=OrderStatus(status) if status else None
        )
        
        return {
            "success": True,
            "client_id": client_id,
            "orders": orders,
            "count": len(orders)
        }
    
    @staticmethod
    async def get_trade_details(trade_id: str) -> Dict[str, Any]:
        """MCP tool: Get trade details"""
        
        trade = trade_execution_engine.get_trade(trade_id)
        
        if not trade:
            return {"success": False, "error": "Trade not found"}
        
        return {
            "success": True,
            "trade": trade
        }
    
    @staticmethod
    async def get_settlement_status(settlement_id: str) -> Dict[str, Any]:
        """MCP tool: Get settlement status"""
        
        settlement = settlement_engine.get_settlement(settlement_id)
        
        if not settlement:
            return {"success": False, "error": "Settlement not found"}
        
        return {
            "success": True,
            "settlement": settlement
        }
    
    @staticmethod
    async def process_settlements(
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Process settlements"""
        
        date = datetime.fromisoformat(as_of_date) if as_of_date else None
        
        result = await settlement_engine.process_settlements(as_of_date=date)
        
        return {
            "success": True,
            "result": result
        }
    
    @staticmethod
    async def get_transaction_history(
        client_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP tool: Get transaction history"""
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        history = await transaction_history_service.get_client_history(
            client_id=client_id,
            start_date=start,
            end_date=end
        )
        
        return {
            "success": True,
            "client_id": client_id,
            "history": history,
            "count": len(history)
        }
    
    @staticmethod
    async def get_trading_summary(
        client_id: str,
        period: str = "ytd"
    ) -> Dict[str, Any]:
        """MCP tool: Get trading summary"""
        
        summary = await transaction_history_service.get_trading_summary(
            client_id=client_id,
            period=period
        )
        
        return {
            "success": True,
            "summary": summary
        }
    
    @staticmethod
    async def detect_fraud(order_id: str) -> Dict[str, Any]:
        """MCP tool: Detect fraud"""
        
        order = await order_management_service.get_order(order_id)
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Mock client history
        client_history = []
        
        fraud_analysis = await transaction_agent.detect_fraud(
            order=order,
            client_history=client_history
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "fraud_analysis": fraud_analysis
        }

# Global instance
transaction_mcp_tools = TransactionMCPTools()

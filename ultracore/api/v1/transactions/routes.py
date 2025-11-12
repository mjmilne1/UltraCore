"""
Transaction Management API Routes
Complete RESTful API for trading system
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ultracore.modules.transactions.order_service import order_management_service
from ultracore.modules.transactions.execution_engine import trade_execution_engine
from ultracore.modules.transactions.settlement_engine import settlement_engine
from ultracore.modules.transactions.history_service import transaction_history_service
from ultracore.modules.transactions.kafka_events import OrderType, OrderSide, TimeInForce

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

@router.post("/orders/create")
async def create_order(
    client_id: str,
    ticker: str,
    side: str,
    quantity: float,
    order_type: str,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: str = "day"
):
    """Create new order"""
    try:
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
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/validate")
async def validate_order(order_id: str, client_id: str):
    """Validate order"""
    try:
        # Mock client data
        client_data = {
            "client_id": client_id,
            "kyc_completed": True,
            "status": "active",
            "trading_enabled": True
        }
        
        # Mock portfolio
        from ultracore.modules.holdings.holdings_service import holdings_service
        portfolio = await holdings_service.get_portfolio_value(client_id, real_time=False)
        
        validation = await order_management_service.validate_order(
            order_id=order_id,
            client_data=client_data,
            portfolio=portfolio
        )
        
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/submit")
async def submit_order(order_id: str):
    """Submit order for execution"""
    try:
        result = await order_management_service.submit_order(order_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, reason: str = "Client requested"):
    """Cancel order"""
    try:
        result = await order_management_service.cancel_order(order_id, reason)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_id}")
async def get_order(order_id: str, include_lineage: bool = False):
    """Get order details"""
    order = await order_management_service.get_order(order_id, include_lineage)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.get("/orders/client/{client_id}")
async def get_client_orders(client_id: str, status: Optional[str] = None):
    """Get all orders for client"""
    from ultracore.modules.transactions.kafka_events import OrderStatus
    
    orders = await order_management_service.get_client_orders(
        client_id=client_id,
        status=OrderStatus(status) if status else None
    )
    
    return {
        "client_id": client_id,
        "orders": orders,
        "count": len(orders)
    }

# ============================================================================
# TRADE EXECUTION
# ============================================================================

@router.post("/orders/{order_id}/execute")
async def execute_order(
    order_id: str,
    use_optimal_execution: bool = True
):
    """Execute order"""
    try:
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
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get trade details"""
    trade = trade_execution_engine.get_trade(trade_id)
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade

@router.get("/trades/order/{order_id}")
async def get_order_trades(order_id: str):
    """Get all trades for order"""
    trades = trade_execution_engine.get_order_trades(order_id)
    
    return {
        "order_id": order_id,
        "trades": trades,
        "count": len(trades)
    }

# ============================================================================
# SETTLEMENT
# ============================================================================

@router.post("/settlements/process")
async def process_settlements(as_of_date: Optional[str] = None):
    """Process pending settlements"""
    try:
        date = datetime.fromisoformat(as_of_date) if as_of_date else None
        
        result = await settlement_engine.process_settlements(as_of_date=date)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settlements/{settlement_id}")
async def get_settlement(settlement_id: str):
    """Get settlement details"""
    settlement = settlement_engine.get_settlement(settlement_id)
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    return settlement

@router.get("/settlements/pending")
async def get_pending_settlements():
    """Get all pending settlements"""
    settlements = settlement_engine.get_pending_settlements()
    
    return {
        "settlements": settlements,
        "count": len(settlements)
    }

@router.get("/settlements/due-today")
async def get_settlements_due_today():
    """Get settlements due today"""
    settlements = settlement_engine.get_settlements_due_today()
    
    return {
        "settlements": settlements,
        "count": len(settlements)
    }

# ============================================================================
# TRANSACTION HISTORY
# ============================================================================

@router.get("/history/client/{client_id}")
async def get_client_history(
    client_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None
):
    """Get transaction history for client"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        history = await transaction_history_service.get_client_history(
            client_id=client_id,
            start_date=start,
            end_date=end,
            transaction_type=transaction_type
        )
        
        return {
            "client_id": client_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/ticker/{ticker}")
async def get_ticker_history(ticker: str, client_id: Optional[str] = None):
    """Get transaction history for ticker"""
    try:
        history = await transaction_history_service.get_ticker_history(
            ticker=ticker,
            client_id=client_id
        )
        
        return {
            "ticker": ticker,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/summary/{client_id}")
async def get_trading_summary(client_id: str, period: str = "ytd"):
    """Get trading summary"""
    try:
        summary = await transaction_history_service.get_trading_summary(
            client_id=client_id,
            period=period
        )
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/tax/{client_id}/{tax_year}")
async def get_tax_report(client_id: str, tax_year: int):
    """Get tax report"""
    try:
        report = await transaction_history_service.get_tax_report(
            client_id=client_id,
            tax_year=tax_year
        )
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

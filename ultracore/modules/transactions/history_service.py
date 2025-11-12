"""
Transaction History Service
Complete audit trail and history queries
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class TransactionHistoryService:
    """
    Transaction history and audit trail
    
    Features:
    - Complete transaction history
    - Query by client, ticker, date
    - Performance tracking
    - Tax reporting support
    """
    
    def __init__(self):
        self.history = []
    
    async def record_transaction(
        self,
        transaction_type: str,
        data: Dict[str, Any]
    ):
        """Record transaction in history"""
        
        record = {
            "transaction_id": data.get("order_id") or data.get("trade_id") or data.get("settlement_id"),
            "type": transaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        self.history.append(record)
    
    async def get_client_history(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transaction history for client"""
        
        history = [
            h for h in self.history
            if h["data"].get("client_id") == client_id
        ]
        
        # Filter by date
        if start_date:
            history = [
                h for h in history
                if datetime.fromisoformat(h["timestamp"]) >= start_date
            ]
        
        if end_date:
            history = [
                h for h in history
                if datetime.fromisoformat(h["timestamp"]) <= end_date
            ]
        
        # Filter by type
        if transaction_type:
            history = [h for h in history if h["type"] == transaction_type]
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return history
    
    async def get_ticker_history(
        self,
        ticker: str,
        client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transaction history for ticker"""
        
        history = [
            h for h in self.history
            if h["data"].get("ticker") == ticker
        ]
        
        if client_id:
            history = [
                h for h in history
                if h["data"].get("client_id") == client_id
            ]
        
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return history
    
    async def get_trading_summary(
        self,
        client_id: str,
        period: str = "ytd"
    ) -> Dict[str, Any]:
        """Get trading summary for period"""
        
        # Determine date range
        now = datetime.utcnow()
        
        if period == "ytd":
            start_date = datetime(now.year, 1, 1)
        elif period == "1m":
            start_date = now - timedelta(days=30)
        elif period == "3m":
            start_date = now - timedelta(days=90)
        elif period == "1y":
            start_date = now - timedelta(days=365)
        else:
            start_date = datetime(2000, 1, 1)
        
        # Get history
        history = await self.get_client_history(
            client_id=client_id,
            start_date=start_date
        )
        
        # Calculate summary
        orders = [h for h in history if h["type"] == "order"]
        trades = [h for h in history if h["type"] == "trade"]
        
        total_trade_value = sum(
            t["data"].get("value", 0)
            for t in trades
        )
        
        buy_trades = [t for t in trades if t["data"].get("side") == "buy"]
        sell_trades = [t for t in trades if t["data"].get("side") == "sell"]
        
        return {
            "client_id": client_id,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "total_orders": len(orders),
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_trade_value": total_trade_value,
            "avg_trade_value": total_trade_value / len(trades) if trades else 0
        }
    
    async def get_tax_report(
        self,
        client_id: str,
        tax_year: int
    ) -> Dict[str, Any]:
        """Generate tax report for year"""
        
        start_date = datetime(tax_year, 1, 1)
        end_date = datetime(tax_year, 12, 31, 23, 59, 59)
        
        # Get all trades for year
        history = await self.get_client_history(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type="trade"
        )
        
        # Separate by holding period
        short_term_gains = []
        long_term_gains = []
        
        # This is simplified - in production would calculate actual gains/losses
        total_short_term = 0
        total_long_term = 0
        
        return {
            "client_id": client_id,
            "tax_year": tax_year,
            "total_trades": len(history),
            "short_term_gains": total_short_term,
            "long_term_gains": total_long_term,
            "total_capital_gains": total_short_term + total_long_term
        }

# Global instance
transaction_history_service = TransactionHistoryService()

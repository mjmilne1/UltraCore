"""Trades Data Product for Data Mesh"""
from typing import List, Optional
from datetime import datetime
import pandas as pd

from ultracore.data_mesh.base import DataProduct
from ultracore.data_mesh.catalog import DataCatalog
from ..events import OrderExecutedEvent, OpenMarketsEventStore


class TradesDataProduct(DataProduct):
    """
    Data Product: Historical Trades
    
    Domain: Trading
    Owner: OpenMarkets Integration Team
    
    Description:
    Complete historical record of all executed trades with event sourcing.
    Provides temporal queries, analytics, and compliance reporting.
    
    SLA:
    - Freshness: Real-time (< 1 second)
    - Availability: 99.9%
    - Completeness: 100% (event-sourced)
    """
    
    def __init__(self, event_store: OpenMarketsEventStore):
        super().__init__(
            product_id="openmarkets.trades",
            product_name="Executed Trades",
            domain="trading",
            owner="openmarkets-integration",
            description="Complete historical trades with audit trail"
        )
        self.event_store = event_store
    
    async def get_trades(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get trades from event store as DataFrame.
        
        Args:
            account_id: Trading account
            start_date: Start date filter
            end_date: End date filter
            symbol: Symbol filter
        
        Returns:
            DataFrame with trade history
        """
        # Query event store
        events = await self.event_store.get_account_trades(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert to DataFrame
        trades_data = []
        for event in events:
            if symbol and event.symbol != symbol:
                continue
            
            trades_data.append({
                "trade_id": event.trade_id,
                "order_id": event.order_id,
                "timestamp": event.executed_at,
                "symbol": event.symbol,
                "side": event.side,
                "quantity": event.quantity,
                "price": float(event.price),
                "value": float(event.net_value),
                "commission": float(event.commission),
                "exchange": event.exchange
            })
        
        return pd.DataFrame(trades_data)
    
    async def get_trade_analytics(
        self,
        account_id: str,
        period: str = "1M"
    ) -> dict:
        """Get aggregated trade analytics."""
        trades_df = await self.get_trades(account_id)
        
        if trades_df.empty:
            return {"message": "No trades found"}
        
        return {
            "total_trades": len(trades_df),
            "total_volume": float(trades_df["value"].sum()),
            "total_commission": float(trades_df["commission"].sum()),
            "unique_symbols": trades_df["symbol"].nunique(),
            "buy_trades": len(trades_df[trades_df["side"] == "BUY"]),
            "sell_trades": len(trades_df[trades_df["side"] == "SELL"]),
            "average_trade_size": float(trades_df["value"].mean())
        }
    
    async def register_in_catalog(self, catalog: DataCatalog):
        """Register this data product in the data catalog."""
        await catalog.register_product(
            product=self,
            schema={
                "trade_id": "string",
                "order_id": "string",
                "timestamp": "datetime",
                "symbol": "string",
                "side": "string",
                "quantity": "integer",
                "price": "decimal",
                "value": "decimal",
                "commission": "decimal",
                "exchange": "string"
            },
            quality_metrics={
                "freshness_sla_seconds": 1,
                "completeness_pct": 100.0,
                "accuracy_pct": 100.0
            }
        )

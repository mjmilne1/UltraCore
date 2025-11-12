"""Positions Data Product for Data Mesh"""
import pandas as pd

from ultracore.data_mesh.base import DataProduct
from ..client import OpenMarketsClient


class PositionsDataProduct(DataProduct):
    """
    Data Product: Current Positions
    
    Real-time portfolio positions with P&L tracking.
    """
    
    def __init__(self, client: OpenMarketsClient):
        super().__init__(
            product_id="openmarkets.positions",
            product_name="Current Positions",
            domain="portfolio",
            owner="openmarkets-integration",
            description="Real-time portfolio positions"
        )
        self.client = client
    
    async def get_positions(self, account_id: str) -> pd.DataFrame:
        """Get current positions as DataFrame."""
        positions = await self.client.get_positions(account_id)
        
        positions_data = [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "average_cost": float(p.average_cost),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pnl": float(p.unrealized_pnl),
                "unrealized_pnl_pct": float(p.unrealized_pnl_percent),
                "exchange": p.exchange
            }
            for p in positions
        ]
        
        return pd.DataFrame(positions_data)

"""Market Data Product for Data Mesh"""
from ultracore.data_mesh.base import DataProduct


class MarketDataProduct(DataProduct):
    """
    Data Product: Real-time Market Data
    
    Streaming market data from ASX, Chi-X, NSX.
    """
    
    def __init__(self):
        super().__init__(
            product_id="openmarkets.market_data",
            product_name="Real-time Market Data",
            domain="market_data",
            owner="openmarkets-integration",
            description="Streaming market data from Australian exchanges"
        )

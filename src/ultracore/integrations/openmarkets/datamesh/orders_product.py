"""Orders Data Product for Data Mesh"""
from ultracore.data_mesh.base import DataProduct


class OrdersDataProduct(DataProduct):
    """
    Data Product: Order History
    
    Complete order lifecycle tracking from event store.
    """
    
    def __init__(self):
        super().__init__(
            product_id="openmarkets.orders",
            product_name="Order History",
            domain="trading",
            owner="openmarkets-integration",
            description="Complete order audit trail"
        )

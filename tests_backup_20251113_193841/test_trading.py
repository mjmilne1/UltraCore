"""Trading Engine Integration Tests"""
import unittest
from decimal import Decimal
from ultracore.trading.aggregates.order_aggregate import OrderAggregate
from ultracore.trading.events import *

class TestTradingEngine(unittest.TestCase):
    def test_order_lifecycle(self):
        """Test complete order lifecycle"""
        order = OrderAggregate(tenant_id="t1", order_id="order_123")
        
        # Create order
        order.create(
            user_id="user_1",
            portfolio_id="port_1",
            symbol="CBA.AX",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            limit_price=Decimal("100.50"),
            stop_price=None,
            time_in_force=TimeInForce.DAY,
            created_by="user_1"
        )
        self.assertEqual(order.status, OrderStatus.PENDING)
        
        # Validate
        order.validate(is_valid=True, validation_checks=["buying_power"], errors=[])
        
        # Submit
        order.submit(venue=ExecutionVenue.ASX, venue_order_id="asx_123")
        self.assertEqual(order.status, OrderStatus.SUBMITTED)
        
        # Accept
        order.accept(venue=ExecutionVenue.ASX, venue_order_id="asx_123")
        self.assertEqual(order.status, OrderStatus.ACCEPTED)
        
        # Fill
        order.fill(
            total_filled_quantity=Decimal("100"),
            average_fill_price=Decimal("100.50"),
            total_commission=Decimal("9.95"),
            fills=[{"fill_id": "fill_1", "quantity": 100, "price": 100.50}]
        )
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertEqual(order.filled_quantity, Decimal("100"))

if __name__ == '__main__':
    unittest.main()

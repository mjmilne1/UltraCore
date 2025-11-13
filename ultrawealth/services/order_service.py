"""
Order Management Service

Handles trade order creation, execution, and settlement
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from ultrawealth.models.wealth_models import WealthOrder, OrderType, OrderStatus
from ultracore.services.ultrawealth import ultrawealth_service
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class OrderManagementService:
    """Order management service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.kafka_store = get_production_kafka_store()
        self.etf_service = ultrawealth_service
    
    async def create_order(
        self,
        portfolio_id: str,
        ticker: str,
        order_type: str,
        quantity: Decimal,
        order_price: Optional[Decimal] = None
    ) -> WealthOrder:
        """
        Create a new trade order
        
        Args:
            portfolio_id: Portfolio ID
            ticker: ETF ticker
            order_type: Order type (buy/sell)
            quantity: Quantity to trade
            order_price: Limit price (None for market order)
            
        Returns:
            WealthOrder: Created order
        """
        
        # Generate order ID
        order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        
        # Validate order type
        order_type_enum = OrderType(order_type.lower())
        
        # Get current price for market orders
        if order_price is None:
            price_data = await self.etf_service.get_etf_price(ticker)
            order_price = Decimal(str(price_data.get('current_price', 0)))
        
        # Calculate total amount
        total_amount = quantity * order_price
        
        # Create order
        order = WealthOrder(
            order_id=order_id,
            portfolio_id=portfolio_id,
            ticker=ticker,
            order_type=order_type_enum,
            quantity=quantity,
            order_price=order_price,
            total_amount=total_amount,
            status=OrderStatus.PENDING
        )
        
        self.db.add(order)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='order_created',
            event_data={
                'order_id': order_id,
                'portfolio_id': portfolio_id,
                'ticker': ticker,
                'order_type': order_type,
                'quantity': float(quantity),
                'order_price': float(order_price),
                'total_amount': float(total_amount),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        return order
    
    async def submit_order(self, order_id: str) -> WealthOrder:
        """Submit order to broker/exchange"""
        
        order = self.db.query(WealthOrder).filter_by(order_id=order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError(f"Order {order_id} is not in pending status")
        
        # In production, this would integrate with broker API
        # For now, simulate submission
        broker_order_id = f"BRK-{uuid.uuid4().hex[:8].upper()}"
        
        order.status = OrderStatus.SUBMITTED
        order.broker_order_id = broker_order_id
        order.submitted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='order_submitted',
            event_data={
                'order_id': order_id,
                'broker_order_id': broker_order_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        # Auto-execute for demo (in production, wait for broker confirmation)
        await self.execute_order(order_id)
        
        return order
    
    async def execute_order(
        self,
        order_id: str,
        executed_price: Optional[Decimal] = None,
        executed_quantity: Optional[Decimal] = None
    ) -> WealthOrder:
        """Execute order"""
        
        order = self.db.query(WealthOrder).filter_by(order_id=order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Use order price if executed price not provided
        if executed_price is None:
            executed_price = order.order_price
        
        # Use full quantity if not provided
        if executed_quantity is None:
            executed_quantity = order.quantity
        
        # Update order
        order.status = OrderStatus.EXECUTED
        order.executed_price = executed_price
        order.executed_quantity = executed_quantity
        order.total_amount = executed_quantity * executed_price
        order.executed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='order_executed',
            event_data={
                'order_id': order_id,
                'portfolio_id': order.portfolio_id,
                'ticker': order.ticker,
                'order_type': order.order_type.value,
                'executed_quantity': float(executed_quantity),
                'executed_price': float(executed_price),
                'total_amount': float(order.total_amount),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        # Update portfolio holdings
        await self._update_holdings_from_order(order)
        
        return order
    
    async def cancel_order(self, order_id: str) -> WealthOrder:
        """Cancel order"""
        
        order = self.db.query(WealthOrder).filter_by(order_id=order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status in [OrderStatus.EXECUTED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order in {order.status.value} status")
        
        order.status = OrderStatus.CANCELLED
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='order_cancelled',
            event_data={
                'order_id': order_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        return order
    
    async def get_order(self, order_id: str) -> Optional[WealthOrder]:
        """Get order by ID"""
        return self.db.query(WealthOrder).filter_by(order_id=order_id).first()
    
    async def get_portfolio_orders(self, portfolio_id: str) -> list:
        """Get all orders for a portfolio"""
        return self.db.query(WealthOrder).filter_by(portfolio_id=portfolio_id).all()
    
    async def _update_holdings_from_order(self, order: WealthOrder):
        """Update portfolio holdings after order execution"""
        
        # Import here to avoid circular dependency
        from ultrawealth.services.portfolio_service import PortfolioManagementService
        
        portfolio_service = PortfolioManagementService(self.db)
        
        # Get existing holding
        from ultrawealth.models.wealth_models import WealthHolding
        holding = self.db.query(WealthHolding).filter_by(
            portfolio_id=order.portfolio_id,
            ticker=order.ticker
        ).first()
        
        if order.order_type == OrderType.BUY:
            if holding:
                # Update existing holding
                await portfolio_service.update_holding(
                    holding_id=holding.holding_id,
                    quantity_change=order.executed_quantity,
                    price=order.executed_price
                )
            else:
                # Create new holding
                await portfolio_service.add_holding(
                    portfolio_id=order.portfolio_id,
                    ticker=order.ticker,
                    quantity=order.executed_quantity,
                    average_cost=order.executed_price
                )
        
        elif order.order_type == OrderType.SELL:
            if holding:
                # Reduce holding
                await portfolio_service.update_holding(
                    holding_id=holding.holding_id,
                    quantity_change=-order.executed_quantity,
                    price=order.executed_price
                )
            else:
                raise ValueError(f"Cannot sell {order.ticker} - no holding found")

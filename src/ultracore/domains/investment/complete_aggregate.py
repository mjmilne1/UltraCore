"""
Complete Investment Domain - Order Management with Kafka
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.enhanced_pipeline import enhanced_ml


class OrderSide(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class OrderType(str, Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP_LOSS = 'STOP_LOSS'


class OrderStatus(str, Enum):
    PENDING = 'PENDING'
    PLACED = 'PLACED'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'


class CompleteInvestmentAggregate:
    """Complete investment portfolio with order management"""
    
    def __init__(self, portfolio_id: str):
        self.portfolio_id = portfolio_id
        self.account_id: Optional[str] = None
        self.holdings: Dict[str, Dict] = {}
        self.orders: List[Dict] = []
        self.cash_balance: Decimal = Decimal('0')
        self.total_value: Decimal = Decimal('0')
    
    async def create_portfolio(self, account_id: str, initial_cash: Decimal):
        """Create investment portfolio"""
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'account_id': account_id,
            'initial_cash': str(initial_cash),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='investments',
            event_type='portfolio_created',
            event_data=event_data,
            aggregate_id=self.portfolio_id
        )
        
        self.account_id = account_id
        self.cash_balance = initial_cash
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        limit_price: Optional[Decimal] = None
    ):
        """Place investment order"""
        kafka_store = get_production_kafka_store()
        
        order_id = f'ORD-{self.portfolio_id}-{datetime.now(timezone.utc).timestamp()}'
        execution_price = limit_price or Decimal('100')
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'order_id': order_id,
            'symbol': symbol,
            'side': side.value,
            'quantity': quantity,
            'order_type': order_type.value,
            'limit_price': str(limit_price) if limit_price else None,
            'status': OrderStatus.PLACED.value,
            'placed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='investments',
            event_type='order_placed',
            event_data=event_data,
            aggregate_id=self.portfolio_id
        )
        
        # Publish to orders topic
        await kafka_store.append_event(
            entity='orders',
            event_type='order_created',
            event_data=event_data,
            aggregate_id=order_id
        )
        
        self.orders.append(event_data)
        
        # Execute order (simulated)
        await self._fill_order(order_id, execution_price, quantity)
        
        return order_id
    
    async def _fill_order(self, order_id: str, execution_price: Decimal, quantity: int):
        """Execute order fill"""
        order = next((o for o in self.orders if o['order_id'] == order_id), None)
        if not order:
            return
        
        kafka_store = get_production_kafka_store()
        
        symbol = order['symbol']
        side = OrderSide(order['side'])
        total_cost = execution_price * quantity
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'order_id': order_id,
            'symbol': symbol,
            'execution_price': str(execution_price),
            'quantity': quantity,
            'total_cost': str(total_cost),
            'filled_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='investments',
            event_type='order_filled',
            event_data=event_data,
            aggregate_id=self.portfolio_id,
            exactly_once=True
        )
        
        # Publish to fills topic
        await kafka_store.append_event(
            entity='fills',
            event_type='order_execution',
            event_data=event_data,
            aggregate_id=order_id
        )
        
        # Update holdings
        if side == OrderSide.BUY:
            self.cash_balance -= total_cost
            if symbol in self.holdings:
                self.holdings[symbol]['quantity'] += quantity
            else:
                self.holdings[symbol] = {'symbol': symbol, 'quantity': quantity, 'avg_price': execution_price}
        else:
            self.cash_balance += total_cost
            self.holdings[symbol]['quantity'] -= quantity
        
        order['status'] = OrderStatus.FILLED.value
    
    async def optimize_portfolio(self):
        """ML-powered portfolio optimization"""
        optimization = await enhanced_ml.optimize_investment_portfolio({
            'allocation': self.holdings,
            'risk_tolerance': 'MODERATE'
        })
        
        kafka_store = get_production_kafka_store()
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'optimization': optimization,
            'optimized_at': datetime.now(timezone.utc).isoformat()
        }
        
        await kafka_store.append_event(
            entity='investments',
            event_type='portfolio_optimized',
            event_data=event_data,
            aggregate_id=self.portfolio_id
        )
        
        return optimization
    
    async def load_from_events(self):
        """Rebuild from events"""
        from ultracore.infrastructure.event_store.store import get_event_store
        store = get_event_store()
        events = await store.get_events(self.portfolio_id)
        
        for event in events:
            if event.event_type == 'portfolio_created':
                self.account_id = event.event_data['account_id']
                self.cash_balance = Decimal(event.event_data['initial_cash'])
            elif event.event_type == 'order_placed':
                self.orders.append(event.event_data)
            elif event.event_type == 'order_filled':
                symbol = event.event_data['symbol']
                quantity = event.event_data['quantity']
                total_cost = Decimal(event.event_data['total_cost'])
                
                if symbol in self.holdings:
                    self.holdings[symbol]['quantity'] += quantity
                else:
                    self.holdings[symbol] = {'symbol': symbol, 'quantity': quantity}

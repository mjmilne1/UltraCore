"""
Investment Domain - Stocks, Funds, Portfolio Management
Complete investment platform: Buy/Sell securities, Portfolio tracking
"""
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import random

from ultracore.infrastructure.event_store.store import get_event_store
from ultracore.domains.account.aggregate import AccountAggregate


class SecurityType(str, Enum):
    STOCK = 'STOCK'
    ETF = 'ETF'
    MUTUAL_FUND = 'MUTUAL_FUND'
    BOND = 'BOND'


class OrderType(str, Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'


class OrderSide(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class OrderStatus(str, Enum):
    PENDING = 'PENDING'
    EXECUTED = 'EXECUTED'
    CANCELLED = 'CANCELLED'
    REJECTED = 'REJECTED'


class CreatePortfolioRequest(BaseModel):
    client_id: str
    portfolio_name: str
    strategy: str = 'BALANCED'


class PlaceOrderRequest(BaseModel):
    portfolio_id: str
    symbol: str
    security_type: SecurityType
    order_side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Optional[float] = None


class PortfolioAggregate:
    def __init__(self, portfolio_id: str):
        self.portfolio_id = portfolio_id
        self.client_id: Optional[str] = None
        self.portfolio_name: Optional[str] = None
        self.cash_balance: Decimal = Decimal('0')
        self.holdings: Dict[str, Dict] = {}
        self.total_value: Decimal = Decimal('0')
    
    async def create_portfolio(
        self,
        client_id: str,
        portfolio_name: str,
        initial_cash: Decimal
    ):
        """Create investment portfolio"""
        store = get_event_store()
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'client_id': client_id,
            'portfolio_name': portfolio_name,
            'initial_cash': str(initial_cash),
            'created_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.portfolio_id,
            aggregate_type='Portfolio',
            event_type='PortfolioCreated',
            event_data=event_data,
            user_id='investment_system'
        )
        
        self.client_id = client_id
        self.portfolio_name = portfolio_name
        self.cash_balance = initial_cash
    
    async def place_order(
        self,
        symbol: str,
        security_type: SecurityType,
        order_side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[Decimal] = None
    ):
        """Place buy/sell order"""
        store = get_event_store()
        
        # Simulate market price
        market_price = Decimal(str(random.uniform(10, 500)))
        execution_price = limit_price if order_type == OrderType.LIMIT else market_price
        
        total_cost = execution_price * quantity
        
        # Validate funds for buy orders
        if order_side == OrderSide.BUY:
            if total_cost > self.cash_balance:
                raise ValueError(f'Insufficient funds. Need {total_cost}, have {self.cash_balance}')
        
        # Validate holdings for sell orders
        if order_side == OrderSide.SELL:
            if symbol not in self.holdings or self.holdings[symbol]['quantity'] < quantity:
                raise ValueError(f'Insufficient holdings of {symbol}')
        
        order_id = f'ORD-{str(__import__("uuid").uuid4())[:8]}'
        
        event_data = {
            'portfolio_id': self.portfolio_id,
            'order_id': order_id,
            'symbol': symbol,
            'security_type': security_type.value,
            'order_side': order_side.value,
            'order_type': order_type.value,
            'quantity': quantity,
            'execution_price': str(execution_price),
            'total_value': str(total_cost),
            'executed_at': datetime.utcnow().isoformat()
        }
        
        await store.append(
            aggregate_id=self.portfolio_id,
            aggregate_type='Portfolio',
            event_type='OrderExecuted',
            event_data=event_data,
            user_id='investment_system'
        )
        
        # Update holdings
        if order_side == OrderSide.BUY:
            self.cash_balance -= total_cost
            if symbol not in self.holdings:
                self.holdings[symbol] = {
                    'quantity': 0,
                    'average_price': Decimal('0'),
                    'security_type': security_type.value
                }
            
            # Update average price
            current_qty = self.holdings[symbol]['quantity']
            current_avg = self.holdings[symbol]['average_price']
            new_qty = current_qty + quantity
            new_avg = ((current_avg * current_qty) + (execution_price * quantity)) / new_qty
            
            self.holdings[symbol]['quantity'] = new_qty
            self.holdings[symbol]['average_price'] = new_avg
        
        else:  # SELL
            self.cash_balance += total_cost
            self.holdings[symbol]['quantity'] -= quantity
            if self.holdings[symbol]['quantity'] == 0:
                del self.holdings[symbol]
        
        return order_id
    
    async def get_performance(self):
        """Calculate portfolio performance"""
        # Simulate current market prices
        current_value = self.cash_balance
        
        holdings_value = []
        for symbol, holding in self.holdings.items():
            current_price = Decimal(str(random.uniform(10, 500)))
            position_value = current_price * holding['quantity']
            current_value += position_value
            
            gain_loss = (current_price - holding['average_price']) * holding['quantity']
            gain_loss_pct = (gain_loss / (holding['average_price'] * holding['quantity'])) * 100
            
            holdings_value.append({
                'symbol': symbol,
                'quantity': holding['quantity'],
                'average_price': str(holding['average_price']),
                'current_price': str(current_price),
                'position_value': str(position_value),
                'gain_loss': str(gain_loss),
                'gain_loss_pct': f'{gain_loss_pct:.2f}%'
            })
        
        return {
            'cash_balance': str(self.cash_balance),
            'holdings_value': holdings_value,
            'total_value': str(current_value),
            'holdings_count': len(self.holdings)
        }
    
    async def load_from_events(self):
        """Rebuild portfolio state from events"""
        store = get_event_store()
        events = await store.get_events(self.portfolio_id)
        
        for event in events:
            if event.event_type == 'PortfolioCreated':
                self.client_id = event.event_data['client_id']
                self.portfolio_name = event.event_data['portfolio_name']
                self.cash_balance = Decimal(event.event_data['initial_cash'])
            elif event.event_type == 'OrderExecuted':
                symbol = event.event_data['symbol']
                quantity = event.event_data['quantity']
                price = Decimal(event.event_data['execution_price'])
                side = event.event_data['order_side']
                security_type = event.event_data['security_type']
                total = Decimal(event.event_data['total_value'])
                
                if side == 'BUY':
                    self.cash_balance -= total
                    if symbol not in self.holdings:
                        self.holdings[symbol] = {
                            'quantity': 0,
                            'average_price': Decimal('0'),
                            'security_type': security_type
                        }
                    
                    current_qty = self.holdings[symbol]['quantity']
                    current_avg = self.holdings[symbol]['average_price']
                    new_qty = current_qty + quantity
                    new_avg = ((current_avg * current_qty) + (price * quantity)) / new_qty if new_qty > 0 else Decimal('0')
                    
                    self.holdings[symbol]['quantity'] = new_qty
                    self.holdings[symbol]['average_price'] = new_avg
                else:
                    self.cash_balance += total
                    if symbol in self.holdings:
                        self.holdings[symbol]['quantity'] -= quantity
                        if self.holdings[symbol]['quantity'] <= 0:
                            del self.holdings[symbol]

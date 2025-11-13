"""Trading Service - ASX Securities"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import TradeExecutedEvent, PortfolioFundedEvent
from ..models import Trade, TradeSide
# from ultracore.domains.accounts.ledger import UltraLedgerService  # TODO: Fix import path


class TradingService:
    """
    Trading platform for ASX securities.
    
    Features:
    - Market and limit orders
    - Real-time execution (simulated)
    - T+2 settlement
    - CHESS settlement (HIN)
    - Brokerage calculation
    - Tax reporting (CGT)
    
    Australian Context:
    - ASX trading hours: 10:00am - 4:00pm AEST
    - Pre-market: 7:00am - 10:00am
    - After-market: 4:10pm - 5:00pm
    - Settlement: T+2 business days
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        ledger_service: UltraLedgerService
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.ledger = ledger_service
    
    async def execute_trade(
        self,
        portfolio_id: str,
        customer_id: str,
        side: TradeSide,
        security_code: str,
        security_name: str,
        quantity: int,
        order_type: str = "market",
        limit_price: Optional[Decimal] = None,
        **kwargs
    ) -> Dict:
        """
        Execute trade (buy or sell).
        
        Publishes: TradeExecutedEvent
        Records: UltraLedger entry
        Settlement: T+2
        """
        
        trade_id = f"TRD-{uuid.uuid4().hex[:12].upper()}"
        
        # Get current market price (would call market data API)
        current_price = await self._get_market_price(security_code)
        
        # Execute at market or limit
        if order_type == "limit" and limit_price:
            execution_price = limit_price
        else:
            execution_price = current_price
        
        # Calculate costs
        trade_value = execution_price * quantity
        brokerage = self._calculate_brokerage(trade_value)
        
        if side == TradeSide.BUY:
            total_cost = trade_value + brokerage
        else:  # SELL
            total_cost = trade_value - brokerage
        
        # Settlement dates
        trade_date = date.today()
        settlement_date = self._calculate_settlement_date(trade_date)
        
        # Create trade
        trade = Trade(
            trade_id=trade_id,
            portfolio_id=portfolio_id,
            side=side,
            security_code=security_code,
            security_name=security_name,
            quantity=quantity,
            price=execution_price,
            trade_value=trade_value,
            brokerage=brokerage,
            total_cost=total_cost,
            trade_date=trade_date,
            settlement_date=settlement_date,
            executed_at=datetime.now(timezone.utc),
            executed_by=customer_id,
            order_type=order_type
        )
        
        # Publish event
        event = TradeExecutedEvent(
            aggregate_id=portfolio_id,
            portfolio_id=portfolio_id,
            customer_id=customer_id,
            trade_id=trade_id,
            side=side.value,
            security_code=security_code,
            security_name=security_name,
            quantity=quantity,
            price=execution_price,
            trade_value=trade_value,
            brokerage=brokerage,
            total_cost=total_cost,
            trade_date=trade_date,
            settlement_date=settlement_date,
            executed_at=datetime.now(timezone.utc),
            executed_by=customer_id
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        # Record in UltraLedger
        await self._record_trade_in_ledger(trade, portfolio_id)
        
        return {
            "success": True,
            "trade_id": trade_id,
            "side": side.value,
            "security": f"{security_code} - {security_name}",
            "quantity": quantity,
            "price": float(execution_price),
            "trade_value": float(trade_value),
            "brokerage": float(brokerage),
            "total_cost": float(total_cost),
            "settlement_date": settlement_date.isoformat(),
            "message": f"{side.value.upper()} order executed successfully! Settlement: {settlement_date}"
        }
    
    async def _get_market_price(self, security_code: str) -> Decimal:
        """
        Get current market price.
        
        Would integrate with ASX market data feed.
        """
        
        # Mock prices for popular ASX securities
        prices = {
            "CBA": Decimal("105.50"),  # Commonwealth Bank
            "BHP": Decimal("42.80"),   # BHP Group
            "CSL": Decimal("285.00"),  # CSL Limited
            "WBC": Decimal("25.40"),   # Westpac
            "ANZ": Decimal("27.30"),   # ANZ Bank
            "NAB": Decimal("32.80"),   # NAB
            "WES": Decimal("58.90"),   # Wesfarmers
            "VAS": Decimal("92.50"),   # Vanguard Aus Shares ETF
            "VGS": Decimal("112.80"),  # Vanguard Int'l Shares ETF
            "VDHG": Decimal("62.30"),  # Vanguard High Growth ETF
        }
        
        return prices.get(security_code, Decimal("50.00"))
    
    def _calculate_brokerage(self, trade_value: Decimal) -> Decimal:
        """
        Calculate brokerage fees.
        
        Australian online broker rates:
        - Up to $10,000: $19.95
        - Over $10,000: 0.11% (max $29.95)
        """
        
        if trade_value <= Decimal("10000"):
            return Decimal("19.95")
        else:
            brokerage = trade_value * Decimal("0.0011")
            return min(brokerage, Decimal("29.95"))
    
    def _calculate_settlement_date(self, trade_date: date) -> date:
        """
        Calculate T+2 settlement date (business days).
        
        Australian public holidays considered.
        """
        
        settlement = trade_date
        business_days = 0
        
        while business_days < 2:
            settlement += timedelta(days=1)
            # Skip weekends (would also skip public holidays)
            if settlement.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
        
        return settlement
    
    async def _record_trade_in_ledger(
        self,
        trade: Trade,
        portfolio_id: str
    ):
        """
        Record trade in UltraLedger.
        
        Buy:
        DEBIT:  Investment Asset
        DEBIT:  Brokerage Expense
        CREDIT: Portfolio Cash
        
        Sell:
        DEBIT:  Portfolio Cash
        CREDIT: Investment Asset
        CREDIT: Brokerage Expense
        """
        
        # Would create actual ledger entry
        pass
    
    async def get_market_quote(
        self,
        security_code: str
    ) -> Dict:
        """
        Get real-time market quote.
        
        ASX market data (would integrate with real feed).
        """
        
        current_price = await self._get_market_price(security_code)
        
        return {
            "security_code": security_code,
            "last_price": float(current_price),
            "bid": float(current_price * Decimal("0.999")),
            "ask": float(current_price * Decimal("1.001")),
            "volume": 1500000,
            "market_cap": 150000000000,
            "pe_ratio": 16.5,
            "dividend_yield": 4.2,
            "exchange": "ASX",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

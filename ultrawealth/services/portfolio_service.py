"""
Portfolio Management Service

Manages portfolio operations including holdings, valuations, and rebalancing
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from ultrawealth.models.wealth_models import (
    WealthPortfolio, WealthHolding, WealthPerformance, WealthRebalance,
    PortfolioStatus
)
from ultracore.services.ultrawealth import ultrawealth_service, australian_etf_universe
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class PortfolioManagementService:
    """Portfolio management service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.kafka_store = get_production_kafka_store()
        self.etf_service = ultrawealth_service
        self.etf_universe = australian_etf_universe
    
    async def get_portfolio_holdings(self, portfolio_id: str) -> List[WealthHolding]:
        """Get all holdings for a portfolio"""
        return self.db.query(WealthHolding).filter_by(portfolio_id=portfolio_id).all()
    
    async def add_holding(
        self,
        portfolio_id: str,
        ticker: str,
        quantity: Decimal,
        average_cost: Decimal
    ) -> WealthHolding:
        """Add a new holding to portfolio"""
        
        # Get ETF info
        etf_info = self.etf_universe.get_etf_info(ticker)
        if not etf_info:
            raise ValueError(f"ETF {ticker} not found")
        
        # Generate holding ID
        holding_id = f"HLD-{uuid.uuid4().hex[:12].upper()}"
        
        # Get current price
        price_data = await self.etf_service.get_etf_price(ticker)
        current_price = Decimal(str(price_data.get('current_price', average_cost)))
        
        # Calculate values
        current_value = quantity * current_price
        unrealized_gain_loss = (current_price - average_cost) * quantity
        unrealized_gain_loss_pct = float((current_price - average_cost) / average_cost * 100)
        
        # Create holding
        holding = WealthHolding(
            holding_id=holding_id,
            portfolio_id=portfolio_id,
            ticker=ticker,
            security_name=etf_info.get('name'),
            asset_class=etf_info.get('category'),
            quantity=quantity,
            average_cost=average_cost,
            current_price=current_price,
            current_value=current_value,
            unrealized_gain_loss=unrealized_gain_loss,
            unrealized_gain_loss_pct=unrealized_gain_loss_pct
        )
        
        self.db.add(holding)
        self.db.commit()
        
        # Update portfolio value
        await self.update_portfolio_value(portfolio_id)
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='holding_added',
            event_data={
                'holding_id': holding_id,
                'portfolio_id': portfolio_id,
                'ticker': ticker,
                'quantity': float(quantity),
                'average_cost': float(average_cost),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
        
        return holding
    
    async def update_holding(
        self,
        holding_id: str,
        quantity_change: Decimal,
        price: Decimal
    ) -> WealthHolding:
        """Update holding quantity (buy more or sell some)"""
        
        holding = self.db.query(WealthHolding).filter_by(holding_id=holding_id).first()
        if not holding:
            raise ValueError(f"Holding {holding_id} not found")
        
        old_quantity = holding.quantity
        old_cost_basis = holding.average_cost * holding.quantity
        
        # Update quantity
        new_quantity = old_quantity + quantity_change
        
        if new_quantity < 0:
            raise ValueError("Cannot sell more than current holdings")
        
        if new_quantity == 0:
            # Fully sold - remove holding
            self.db.delete(holding)
            self.db.commit()
            return None
        
        # Update average cost (for buys)
        if quantity_change > 0:
            new_cost_basis = old_cost_basis + (quantity_change * price)
            holding.average_cost = new_cost_basis / new_quantity
        
        holding.quantity = new_quantity
        
        # Update current values
        current_price_data = await self.etf_service.get_etf_price(holding.ticker)
        current_price = Decimal(str(current_price_data.get('current_price', price)))
        
        holding.current_price = current_price
        holding.current_value = new_quantity * current_price
        holding.unrealized_gain_loss = (current_price - holding.average_cost) * new_quantity
        holding.unrealized_gain_loss_pct = float((current_price - holding.average_cost) / holding.average_cost * 100)
        holding.last_updated = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Update portfolio value
        await self.update_portfolio_value(holding.portfolio_id)
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='holding_updated',
            event_data={
                'holding_id': holding_id,
                'portfolio_id': holding.portfolio_id,
                'ticker': holding.ticker,
                'old_quantity': float(old_quantity),
                'new_quantity': float(new_quantity),
                'quantity_change': float(quantity_change),
                'price': float(price),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=holding.portfolio_id
        )
        
        return holding
    
    async def update_portfolio_value(self, portfolio_id: str):
        """Recalculate and update portfolio total value"""
        
        portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Get all holdings
        holdings = await self.get_portfolio_holdings(portfolio_id)
        
        # Calculate total value
        total_value = sum(holding.current_value or Decimal(0) for holding in holdings)
        
        # Update portfolio
        old_value = portfolio.current_value
        portfolio.current_value = total_value
        
        # Calculate total return
        if portfolio.total_invested > 0:
            portfolio.total_return = float((total_value - portfolio.total_invested) / portfolio.total_invested * 100)
        
        portfolio.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='portfolio_value_updated',
            event_data={
                'portfolio_id': portfolio_id,
                'old_value': float(old_value) if old_value else 0,
                'new_value': float(total_value),
                'total_return': portfolio.total_return,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
    
    async def get_current_allocation(self, portfolio_id: str) -> Dict:
        """Get current asset allocation"""
        
        holdings = await self.get_portfolio_holdings(portfolio_id)
        
        if not holdings:
            return {}
        
        # Calculate total value
        total_value = sum(h.current_value or Decimal(0) for h in holdings)
        
        if total_value == 0:
            return {}
        
        # Group by asset class
        allocation = {}
        for holding in holdings:
            asset_class = holding.asset_class or "Other"
            current_allocation = allocation.get(asset_class, Decimal(0))
            allocation[asset_class] = current_allocation + (holding.current_value or Decimal(0))
        
        # Convert to percentages
        allocation_pct = {
            asset_class: float(value / total_value * 100)
            for asset_class, value in allocation.items()
        }
        
        return allocation_pct
    
    async def rebalance_portfolio(
        self,
        portfolio_id: str,
        trigger_reason: str = "scheduled"
    ) -> WealthRebalance:
        """Rebalance portfolio to target allocation"""
        
        portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Get current allocation
        current_allocation = await self.get_current_allocation(portfolio_id)
        target_allocation = portfolio.target_allocation
        
        # Generate rebalance ID
        rebalance_id = f"REB-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate required trades
        orders_to_create = []
        total_value = portfolio.current_value
        
        for asset_class, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset_class, 0)
            drift = target_pct - current_pct
            
            # Only rebalance if drift > 5%
            if abs(drift) > 5:
                target_value = total_value * Decimal(target_pct) / 100
                current_value = total_value * Decimal(current_pct) / 100
                trade_value = target_value - current_value
                
                orders_to_create.append({
                    'asset_class': asset_class,
                    'trade_value': float(trade_value),
                    'drift': drift
                })
        
        # Create rebalance record
        rebalance = WealthRebalance(
            rebalance_id=rebalance_id,
            portfolio_id=portfolio_id,
            trigger_reason=trigger_reason,
            allocation_before=current_allocation,
            allocation_after=target_allocation,
            orders_created=orders_to_create,
            status="pending"
        )
        
        self.db.add(rebalance)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='portfolio_rebalanced',
            event_data={
                'rebalance_id': rebalance_id,
                'portfolio_id': portfolio_id,
                'trigger_reason': trigger_reason,
                'allocation_before': current_allocation,
                'allocation_after': target_allocation,
                'orders_count': len(orders_to_create),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
        
        return rebalance
    
    async def calculate_performance(
        self,
        portfolio_id: str,
        period_days: int = 90
    ) -> WealthPerformance:
        """Calculate portfolio performance for a period"""
        
        portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        period_end = datetime.now(timezone.utc)
        
        # Get historical performance (simplified - would use actual historical data)
        start_value = portfolio.total_invested
        end_value = portfolio.current_value
        
        # Calculate returns
        if start_value > 0:
            total_return = float((end_value - start_value) / start_value * 100)
        else:
            total_return = 0.0
        
        # Benchmark (simplified - would use actual benchmark data)
        benchmark_return = 8.0  # Assume 8% annual benchmark
        benchmark_return_period = benchmark_return * (period_days / 365)
        
        excess_return = total_return - benchmark_return_period
        
        # Risk metrics (simplified)
        volatility = 12.0  # Would calculate from actual price history
        sharpe_ratio = (total_return - 2.0) / volatility if volatility > 0 else 0  # 2% risk-free rate
        max_drawdown = -5.0  # Would calculate from actual price history
        
        # Generate performance ID
        performance_id = f"PERF-{uuid.uuid4().hex[:12].upper()}"
        
        # Create performance record
        performance = WealthPerformance(
            performance_id=performance_id,
            portfolio_id=portfolio_id,
            period_start=period_start,
            period_end=period_end,
            total_return=total_return,
            benchmark_return=benchmark_return_period,
            excess_return=excess_return,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            max_drawdown=max_drawdown,
            start_value=start_value,
            end_value=end_value,
            net_contributions=Decimal(0)
        )
        
        self.db.add(performance)
        self.db.commit()
        
        return performance
    
    async def generate_performance_report(
        self,
        portfolio_id: str,
        period_days: int = 90
    ) -> Dict:
        """Generate comprehensive performance report"""
        
        portfolio = self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Calculate performance
        performance = await self.calculate_performance(portfolio_id, period_days)
        
        # Get holdings
        holdings = await self.get_portfolio_holdings(portfolio_id)
        
        # Get current allocation
        current_allocation = await self.get_current_allocation(portfolio_id)
        
        # Build report
        report = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.portfolio_name,
            'report_date': datetime.now(timezone.utc).isoformat(),
            'period': {
                'start': performance.period_start.isoformat(),
                'end': performance.period_end.isoformat(),
                'days': period_days
            },
            'values': {
                'current_value': float(portfolio.current_value),
                'total_invested': float(portfolio.total_invested),
                'total_return': portfolio.total_return,
                'total_return_amount': float(portfolio.current_value - portfolio.total_invested)
            },
            'performance': {
                'total_return': performance.total_return,
                'benchmark_return': performance.benchmark_return,
                'excess_return': performance.excess_return,
                'sharpe_ratio': performance.sharpe_ratio,
                'volatility': performance.volatility,
                'max_drawdown': performance.max_drawdown
            },
            'allocation': {
                'current': current_allocation,
                'target': portfolio.target_allocation
            },
            'holdings': [
                {
                    'ticker': h.ticker,
                    'name': h.security_name,
                    'quantity': float(h.quantity),
                    'current_value': float(h.current_value),
                    'unrealized_gain_loss': float(h.unrealized_gain_loss),
                    'unrealized_gain_loss_pct': h.unrealized_gain_loss_pct
                }
                for h in holdings
            ]
        }
        
        return report

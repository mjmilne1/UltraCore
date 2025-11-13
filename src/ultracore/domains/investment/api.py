"""
Complete Investment API - Order Management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import uuid

# from ultracore.domains.investment.complete_aggregate import (  # TODO: Fix import path
    CompleteInvestmentAggregate,
    OrderSide,
    OrderType
)

router = APIRouter()


class CreatePortfolioRequest(BaseModel):
    account_id: str
    initial_cash: float


class PlaceOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: float = None


@router.post('/portfolios')
async def create_portfolio(request: CreatePortfolioRequest):
    '''Create investment portfolio'''
    portfolio_id = f'PRT-{str(uuid.uuid4())[:8]}'
    
    portfolio = CompleteInvestmentAggregate(portfolio_id)
    await portfolio.create_portfolio(
        account_id=request.account_id,
        initial_cash=Decimal(str(request.initial_cash))
    )
    
    return {
        'portfolio_id': portfolio_id,
        'account_id': request.account_id,
        'cash_balance': str(portfolio.cash_balance)
    }


@router.post('/portfolios/{portfolio_id}/orders')
async def place_order(portfolio_id: str, request: PlaceOrderRequest):
    '''
    Place investment order
    
    Supports market, limit, stop-loss orders
    '''
    portfolio = CompleteInvestmentAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    if not portfolio.account_id:
        raise HTTPException(status_code=404, detail='Portfolio not found')
    
    order_id = await portfolio.place_order(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=Decimal(str(request.limit_price)) if request.limit_price else None
    )
    
    return {
        'portfolio_id': portfolio_id,
        'order_id': order_id,
        'symbol': request.symbol,
        'side': request.side.value,
        'quantity': request.quantity
    }


@router.get('/portfolios/{portfolio_id}')
async def get_portfolio(portfolio_id: str):
    '''Get portfolio details'''
    portfolio = CompleteInvestmentAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    if not portfolio.account_id:
        raise HTTPException(status_code=404, detail='Portfolio not found')
    
    return {
        'portfolio_id': portfolio_id,
        'account_id': portfolio.account_id,
        'cash_balance': str(portfolio.cash_balance),
        'holdings': portfolio.holdings,
        'total_value': str(portfolio.total_value)
    }


@router.post('/portfolios/{portfolio_id}/optimize')
async def optimize_portfolio(portfolio_id: str):
    '''
    ML-powered portfolio optimization
    
    Modern Portfolio Theory + ML
    '''
    portfolio = CompleteInvestmentAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    if not portfolio.account_id:
        raise HTTPException(status_code=404, detail='Portfolio not found')
    
    optimization = await portfolio.optimize_portfolio()
    
    return {
        'portfolio_id': portfolio_id,
        'optimization': optimization
    }

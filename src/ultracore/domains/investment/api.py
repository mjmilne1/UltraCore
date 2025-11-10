"""
Investment Domain API
"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal
import uuid

from ultracore.domains.investment.aggregate import (
    PortfolioAggregate, CreatePortfolioRequest, PlaceOrderRequest
)

router = APIRouter()


@router.post('/portfolios')
async def create_portfolio(request: CreatePortfolioRequest):
    '''Create investment portfolio'''
    portfolio_id = f'PORT-{str(uuid.uuid4())[:8]}'
    
    portfolio = PortfolioAggregate(portfolio_id)
    await portfolio.create_portfolio(
        client_id=request.client_id,
        portfolio_name=request.portfolio_name,
        initial_cash=Decimal('10000')  # Default starting cash
    )
    
    return {
        'portfolio_id': portfolio_id,
        'client_id': request.client_id,
        'portfolio_name': request.portfolio_name,
        'cash_balance': str(portfolio.cash_balance)
    }


@router.get('/portfolios/{portfolio_id}')
async def get_portfolio(portfolio_id: str):
    '''Get portfolio details'''
    portfolio = PortfolioAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    if not portfolio.client_id:
        raise HTTPException(status_code=404, detail='Portfolio not found')
    
    performance = await portfolio.get_performance()
    
    return {
        'portfolio_id': portfolio.portfolio_id,
        'client_id': portfolio.client_id,
        'portfolio_name': portfolio.portfolio_name,
        **performance
    }


@router.post('/portfolios/{portfolio_id}/orders')
async def place_order(portfolio_id: str, request: PlaceOrderRequest):
    '''
    Place buy/sell order
    
    Supports: STOCK, ETF, MUTUAL_FUND, BOND
    '''
    portfolio = PortfolioAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    if not portfolio.client_id:
        raise HTTPException(status_code=404, detail='Portfolio not found')
    
    try:
        order_id = await portfolio.place_order(
            symbol=request.symbol,
            security_type=request.security_type,
            order_side=request.order_side,
            quantity=request.quantity,
            order_type=request.order_type,
            limit_price=Decimal(str(request.limit_price)) if request.limit_price else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'order_id': order_id,
        'portfolio_id': portfolio_id,
        'symbol': request.symbol,
        'side': request.order_side.value,
        'quantity': request.quantity,
        'status': 'EXECUTED',
        'cash_balance': str(portfolio.cash_balance)
    }

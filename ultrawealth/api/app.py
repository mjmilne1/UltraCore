"""
UltraWealth FastAPI Application

Main API application for UltraWealth automated investment system
"""

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel

from ultrawealth.database.init_db import get_session
from ultrawealth.services.application_service import UltraWealthApplication
from ultracore.security.auth.jwt_auth import get_current_user, User


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="UltraWealth API",
    description="Fully Digital Automated Investment System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_db():
    """Get database session"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_ultrawealth_app(db: Session = Depends(get_db)) -> UltraWealthApplication:
    """Get UltraWealth application service"""
    return UltraWealthApplication(db)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OnboardClientRequest(BaseModel):
    client_id: str
    risk_profile: str
    investment_goals: List[dict]
    time_horizon_years: int
    liquidity_needs: dict
    tax_file_number: Optional[str] = None


class CreatePortfolioRequest(BaseModel):
    client_id: str
    portfolio_name: str
    strategy_type: str = "mda"
    initial_investment: Optional[float] = None


class ExecuteTradeRequest(BaseModel):
    portfolio_id: str
    ticker: str
    order_type: str
    quantity: float
    order_price: Optional[float] = None


class UpdateRiskProfileRequest(BaseModel):
    new_risk_profile: str


class GenerateSOARequest(BaseModel):
    client_id: str
    portfolio_id: str
    soa_type: str = "initial"


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ultrawealth",
        "version": "1.0.0"
    }


# ============================================================================
# CLIENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/ultrawealth/clients/onboard")
async def onboard_client(
    request: OnboardClientRequest,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Onboard a new wealth management client"""
    
    try:
        client = await ultrawealth.onboard_client(
            client_id=request.client_id,
            risk_profile=request.risk_profile,
            investment_goals=request.investment_goals,
            time_horizon_years=request.time_horizon_years,
            liquidity_needs=request.liquidity_needs,
            tax_file_number=request.tax_file_number
        )
        
        return {
            "success": True,
            "client_id": client.client_id,
            "risk_profile": client.risk_profile.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/v1/ultrawealth/clients/{client_id}/risk-profile")
async def update_risk_profile(
    client_id: str,
    request: UpdateRiskProfileRequest,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Update client risk profile"""
    
    try:
        client = await ultrawealth.update_risk_profile(
            client_id=client_id,
            new_risk_profile=request.new_risk_profile
        )
        
        return {
            "success": True,
            "client_id": client.client_id,
            "risk_profile": client.risk_profile.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.post("/api/v1/ultrawealth/portfolios")
async def create_portfolio(
    request: CreatePortfolioRequest,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Create a new investment portfolio"""
    
    try:
        portfolio = await ultrawealth.create_portfolio(
            client_id=request.client_id,
            portfolio_name=request.portfolio_name,
            strategy_type=request.strategy_type,
            initial_investment=Decimal(str(request.initial_investment)) if request.initial_investment else None
        )
        
        return {
            "success": True,
            "portfolio_id": portfolio.portfolio_id,
            "portfolio_name": portfolio.portfolio_name,
            "target_allocation": portfolio.target_allocation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/ultrawealth/portfolios/{portfolio_id}")
async def get_portfolio(
    portfolio_id: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio details"""
    
    portfolio = await ultrawealth.get_portfolio(portfolio_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "portfolio_id": portfolio.portfolio_id,
        "client_id": portfolio.client_id,
        "portfolio_name": portfolio.portfolio_name,
        "strategy_type": portfolio.strategy_type,
        "status": portfolio.status.value,
        "current_value": float(portfolio.current_value),
        "total_invested": float(portfolio.total_invested),
        "total_return": portfolio.total_return,
        "target_allocation": portfolio.target_allocation
    }


@app.get("/api/v1/ultrawealth/clients/{client_id}/portfolios")
async def get_client_portfolios(
    client_id: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Get all portfolios for a client"""
    
    portfolios = await ultrawealth.get_client_portfolios(client_id)
    
    return {
        "client_id": client_id,
        "portfolios": [
            {
                "portfolio_id": p.portfolio_id,
                "portfolio_name": p.portfolio_name,
                "status": p.status.value,
                "current_value": float(p.current_value),
                "total_return": p.total_return
            }
            for p in portfolios
        ]
    }


@app.get("/api/v1/ultrawealth/portfolios/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: str,
    period_days: int = 90,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio performance report"""
    
    try:
        report = await ultrawealth.generate_performance_report(
            portfolio_id=portfolio_id,
            period_days=period_days
        )
        
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/ultrawealth/portfolios/{portfolio_id}/rebalance")
async def rebalance_portfolio(
    portfolio_id: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Trigger portfolio rebalancing"""
    
    try:
        rebalance = await ultrawealth.rebalance_portfolio(
            portfolio_id=portfolio_id,
            trigger_reason="manual_request"
        )
        
        return {
            "success": True,
            "rebalance_id": rebalance.rebalance_id,
            "status": rebalance.status,
            "allocation_before": rebalance.allocation_before,
            "allocation_after": rebalance.allocation_after
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# INVESTMENT ADVISORY ENDPOINTS
# ============================================================================

@app.get("/api/v1/ultrawealth/clients/{client_id}/recommendations")
async def get_recommendations(
    client_id: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered investment recommendations"""
    
    try:
        recommendations = await ultrawealth.get_investment_recommendations(client_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

@app.post("/api/v1/ultrawealth/orders")
async def execute_trade(
    request: ExecuteTradeRequest,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Execute a trade order"""
    
    try:
        order = await ultrawealth.execute_trade(
            portfolio_id=request.portfolio_id,
            ticker=request.ticker,
            order_type=request.order_type,
            quantity=Decimal(str(request.quantity)),
            order_price=Decimal(str(request.order_price)) if request.order_price else None
        )
        
        return {
            "success": True,
            "order_id": order.order_id,
            "status": order.status.value,
            "ticker": order.ticker,
            "quantity": float(order.quantity),
            "order_price": float(order.order_price) if order.order_price else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================

@app.post("/api/v1/ultrawealth/soa/generate")
async def generate_soa(
    request: GenerateSOARequest,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app),
    current_user: User = Depends(get_current_user)
):
    """Generate Statement of Advice"""
    
    try:
        soa = await ultrawealth.generate_soa(
            client_id=request.client_id,
            portfolio_id=request.portfolio_id,
            soa_type=request.soa_type
        )
        
        return {
            "success": True,
            "soa_id": soa.soa_id,
            "soa_type": soa.soa_type.value,
            "generated_at": soa.generated_at.isoformat(),
            "content": soa.content
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ETF DATA ENDPOINTS
# ============================================================================

@app.get("/api/v1/ultrawealth/etfs")
async def get_etf_universe(
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app)
):
    """Get Australian ETF universe"""
    return ultrawealth.get_etf_universe()


@app.get("/api/v1/ultrawealth/etfs/{ticker}/price")
async def get_etf_price(
    ticker: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app)
):
    """Get current ETF price"""
    try:
        return await ultrawealth.get_etf_price(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/ultrawealth/etfs/{ticker}/predict")
async def get_etf_prediction(
    ticker: str,
    ultrawealth: UltraWealthApplication = Depends(get_ultrawealth_app)
):
    """Get ML price prediction for ETF"""
    try:
        return await ultrawealth.get_etf_prediction(ticker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8891)

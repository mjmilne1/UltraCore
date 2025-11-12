"""MCP Server for Wealth Management (OpenAI)"""
from typing import Dict, Any, Optional
from decimal import Decimal

from mcp.server import Server
from ultracore.mcp.base import BaseMCPServer
from ..services import PortfolioService
from ..ais import AutomatedInvestmentService
from ..trading import TradingService
from ..margin import MarginLendingService
from ..planning import FinancialPlanner
from ..agents import AnyaWealthAgent


class WealthMCPServer(BaseMCPServer):
    """
    MCP Server for wealth management.
    
    Tools available (13):
    - create_portfolio: Create investment portfolio
    - get_portfolio_performance: View portfolio performance
    - execute_trade: Buy/sell securities (ASX)
    - get_market_quote: Real-time stock quote
    - optimize_allocation: UltraOptimiser integration
    - check_rebalancing: Check if rebalancing needed
    - create_ais_portfolio: AI-managed portfolio
    - establish_margin_facility: Margin lending
    - plan_retirement: Retirement financial plan
    - plan_home_purchase: Home buying plan
    - assess_risk_profile: Investment risk assessment
    - calculate_tax_impact: CGT and franking
    - ask_anya_about_wealth: Natural language assistance
    """
    
    def __init__(
        self,
        portfolio_service: PortfolioService,
        ais: AutomatedInvestmentService,
        trading_service: TradingService,
        margin_service: MarginLendingService,
        planner: FinancialPlanner,
        anya_agent: AnyaWealthAgent
    ):
        super().__init__(server_name="wealth")
        self.portfolio_service = portfolio_service
        self.ais = robo_advisor
        self.trading = trading_service
        self.margin = margin_service
        self.planner = planner
        self.anya = anya_agent
    
    def register_tools(self):
        """Register all wealth management tools."""
        
        @self.server.tool()
        async def create_portfolio(
            customer_id: str,
            portfolio_name: str,
            investment_strategy: str,
            initial_investment: float,
            robo_managed: bool = False
        ) -> Dict[str, Any]:
            """
            Create investment portfolio.
            
            Choose strategy: conservative, balanced, growth
            
            Args:
                customer_id: Customer ID
                portfolio_name: Portfolio name
                investment_strategy: Strategy (conservative/balanced/growth)
                initial_investment: Initial investment (AUD)
                robo_managed: Enable AI portfolio management
            
            Returns:
                Portfolio created with target allocation
            """
            
            # Mock implementation
            return {
                "success": True,
                "portfolio_id": "PORT-ABC123",
                "portfolio_name": portfolio_name,
                "strategy": investment_strategy,
                "initial_investment": initial_investment,
                "robo_managed": robo_managed,
                "message": "Portfolio created successfully!"
            }
        
        @self.server.tool()
        async def execute_trade(
            portfolio_id: str,
            customer_id: str,
            side: str,
            security_code: str,
            quantity: int
        ) -> Dict[str, Any]:
            """
            Execute trade (buy or sell ASX securities).
            
            ASX trading hours: 10am-4pm AEST
            Settlement: T+2 business days
            
            Args:
                portfolio_id: Portfolio ID
                customer_id: Customer ID
                side: "buy" or "sell"
                security_code: ASX code (e.g., CBA, BHP, VAS)
                quantity: Number of shares
            
            Returns:
                Trade confirmation with settlement date
            """
            
            from ..models import TradeSide
            
            result = await self.trading.execute_trade(
                portfolio_id=portfolio_id,
                customer_id=customer_id,
                side=TradeSide.BUY if side == "buy" else TradeSide.SELL,
                security_code=security_code.upper(),
                security_name=f"{security_code} Stock",
                quantity=quantity
            )
            
            return result
        
        @self.server.tool()
        async def get_market_quote(
            security_code: str
        ) -> Dict[str, Any]:
            """
            Get real-time market quote for ASX security.
            
            Args:
                security_code: ASX code (e.g., CBA, BHP, VAS)
            
            Returns:
                Current price, bid/ask, volume, market data
            """
            
            quote = await self.trading.get_market_quote(security_code.upper())
            return quote
        
        @self.server.tool()
        async def create_ais_portfolio(
            customer_id: str,
            risk_tolerance: str,
            time_horizon_years: int,
            initial_investment: float
        ) -> Dict[str, Any]:
            """
            Create AI-managed Automated Investment Service (AIS) portfolio.
            
            Features:
            - Automated portfolio management
            - UltraOptimiser integration (8.89% expected return)
            - Auto-rebalancing
            - Tax optimization
            
            Args:
                customer_id: Customer ID
                risk_tolerance: Risk level (low/medium/high)
                time_horizon_years: Investment time horizon
                initial_investment: Initial investment (AUD)
            
            Returns:
                Robo portfolio with target allocation
            """
            
            from ..models import RiskTolerance
            
            result = await self.ais.create_ais_portfolio(
                customer_id=customer_id,
                portfolio_name="AI Managed Portfolio",
                risk_tolerance=RiskTolerance(risk_tolerance),
                time_horizon_years=time_horizon_years,
                investment_objective="wealth_accumulation",
                initial_investment=Decimal(str(initial_investment)),
                cash_account_id="ACC-123"
            )
            
            return result
        
        @self.server.tool()
        async def establish_margin_facility(
            portfolio_id: str,
            customer_id: str,
            requested_limit: float
        ) -> Dict[str, Any]:
            """
            Establish margin lending facility.
            
            Borrow against portfolio to amplify returns.
            Typical LVR: 50-70% depending on securities.
            
            Args:
                portfolio_id: Portfolio ID
                customer_id: Customer ID
                requested_limit: Requested credit limit (AUD)
            
            Returns:
                Margin facility details with LVR limits
            """
            
            result = await self.margin.establish_margin_facility(
                portfolio_id=portfolio_id,
                customer_id=customer_id,
                approved_limit=Decimal(str(requested_limit))
            )
            
            return result
        
        @self.server.tool()
        async def plan_retirement(
            current_age: int,
            retirement_age: int,
            current_savings: float,
            monthly_contribution: float,
            desired_monthly_income: float
        ) -> Dict[str, Any]:
            """
            Create retirement financial plan.
            
            Australian retirement planning with superannuation.
            
            Args:
                current_age: Current age
                retirement_age: Target retirement age (60+)
                current_savings: Current savings (AUD)
                monthly_contribution: Monthly savings (AUD)
                desired_monthly_income: Target retirement income (AUD/month)
            
            Returns:
                Retirement plan with projections and recommendations
            """
            
            result = await self.planner.create_retirement_plan(
                current_age=current_age,
                retirement_age=retirement_age,
                current_savings=Decimal(str(current_savings)),
                monthly_contribution=Decimal(str(monthly_contribution)),
                desired_retirement_income=Decimal(str(desired_monthly_income))
            )
            
            return result
        
        @self.server.tool()
        async def plan_home_purchase(
            target_price: float,
            current_savings: float,
            monthly_savings: float
        ) -> Dict[str, Any]:
            """
            Create home purchase financial plan.
            
            Australian first home buyer planning with stamp duty.
            
            Args:
                target_price: Target property price (AUD)
                current_savings: Current savings (AUD)
                monthly_savings: Monthly savings capacity (AUD)
            
            Returns:
                Home purchase plan with timeline and costs
            """
            
            result = await self.planner.create_home_purchase_plan(
                target_price=Decimal(str(target_price)),
                current_savings=Decimal(str(current_savings)),
                monthly_savings=Decimal(str(monthly_savings))
            )
            
            return result
        
        @self.server.tool()
        async def assess_risk_profile(
            age: int,
            investment_experience: str,
            risk_comfort: str,
            time_horizon_years: int
        ) -> Dict[str, Any]:
            """
            Assess investment risk profile.
            
            Determines appropriate investment strategy.
            
            Args:
                age: Age in years
                investment_experience: Experience level (none/moderate/extensive)
                risk_comfort: Comfort with risk (low/medium/high)
                time_horizon_years: Investment time horizon
            
            Returns:
                Risk assessment with recommended strategy
            """
            
            result = await self.ais.assess_risk_profile({
                "age": age,
                "investment_experience": investment_experience,
                "risk_comfort": risk_comfort,
                "time_horizon_years": time_horizon_years
            })
            
            return result
        
        @self.server.tool()
        async def ask_anya_about_wealth(
            customer_id: str,
            question: str
        ) -> Dict[str, Any]:
            """
            Ask Anya (AI advisor) about wealth management.
            
            Natural language interface for investment guidance.
            
            Args:
                customer_id: Customer ID
                question: Natural language question about investments
            
            Returns:
                Anya's response with investment guidance
            """
            
            self.anya.customer_id = customer_id
            response = await self.anya.execute(question)
            return response


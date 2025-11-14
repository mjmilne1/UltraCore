"""
UltraWealth Application Service

Main orchestration service for all wealth management operations
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from ultrawealth.models.wealth_models import (
    WealthClient, WealthPortfolio, WealthHolding, WealthOrder,
    WealthSOA, WealthPerformance, WealthRebalance,
    RiskProfile, PortfolioStatus, OrderType, OrderStatus, SOAType
)
from ultrawealth.services.portfolio_service import PortfolioManagementService
from ultrawealth.services.advisory_service import InvestmentAdvisoryService
from ultrawealth.services.order_service import OrderManagementService
from ultrawealth.services.compliance_service import ComplianceService

# Import existing UltraCore services
from ultracore.services.ultrawealth import ultrawealth_service, australian_etf_universe
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class UltraWealthApplication:
    """
    Main UltraWealth Application Service
    
    Orchestrates all wealth management operations and integrates with
    UltraCore banking infrastructure.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.kafka_store = get_production_kafka_store()
        
        # Initialize sub-services
        self.portfolio_service = PortfolioManagementService(db_session)
        self.advisory_service = InvestmentAdvisoryService(db_session)
        self.order_service = OrderManagementService(db_session)
        self.compliance_service = ComplianceService(db_session)
        
        # Existing services
        self.etf_service = ultrawealth_service
        self.etf_universe = australian_etf_universe
    
    # ========================================================================
    # CLIENT ONBOARDING
    # ========================================================================
    
    async def onboard_client(
        self,
        client_id: str,
        risk_profile: str,
        investment_goals: List[Dict],
        time_horizon_years: int,
        liquidity_needs: Dict,
        tax_file_number: Optional[str] = None
    ) -> WealthClient:
        """
        Onboard a new wealth management client
        
        Args:
            client_id: UltraCore client ID
            risk_profile: Risk profile (conservative, moderate, aggressive, etc.)
            investment_goals: List of investment goals
            time_horizon_years: Investment time horizon
            liquidity_needs: Liquidity requirements
            tax_file_number: Australian TFN
            
        Returns:
            WealthClient: Created wealth client
        """
        
        # Validate risk profile
        risk_profile_enum = RiskProfile(risk_profile.lower())
        
        # Create wealth client
        wealth_client = WealthClient(
            client_id=client_id,
            risk_profile=risk_profile_enum,
            investment_goals=investment_goals,
            time_horizon_years=time_horizon_years,
            liquidity_needs=liquidity_needs,
            tax_file_number=tax_file_number
        )
        
        self.db.add(wealth_client)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='client_onboarded',
            event_data={
                'client_id': client_id,
                'risk_profile': risk_profile,
                'time_horizon_years': time_horizon_years,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        return wealth_client
    
    async def update_risk_profile(
        self,
        client_id: str,
        new_risk_profile: str
    ) -> WealthClient:
        """Update client risk profile"""
        
        wealth_client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not wealth_client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        old_profile = wealth_client.risk_profile
        wealth_client.risk_profile = RiskProfile(new_risk_profile.lower())
        wealth_client.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='risk_profile_updated',
            event_data={
                'client_id': client_id,
                'old_profile': old_profile.value,
                'new_profile': new_risk_profile,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        return wealth_client
    
    # ========================================================================
    # PORTFOLIO MANAGEMENT
    # ========================================================================
    
    async def create_portfolio(
        self,
        client_id: str,
        portfolio_name: str,
        strategy_type: str = "mda",
        initial_investment: Optional[Decimal] = None
    ) -> WealthPortfolio:
        """
        Create a new investment portfolio for a client
        
        Args:
            client_id: Client ID
            portfolio_name: Portfolio name
            strategy_type: Strategy type (mda, sma, etc.)
            initial_investment: Initial investment amount
            
        Returns:
            WealthPortfolio: Created portfolio
        """
        
        # Get client
        wealth_client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not wealth_client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        # Generate portfolio ID
        portfolio_id = f"PF-{uuid.uuid4().hex[:12].upper()}"
        
        # Get recommended allocation based on risk profile
        target_allocation = await self.advisory_service.get_target_allocation(
            wealth_client.risk_profile.value
        )
        
        # Create portfolio
        portfolio = WealthPortfolio(
            portfolio_id=portfolio_id,
            client_id=client_id,
            portfolio_name=portfolio_name,
            strategy_type=strategy_type,
            target_allocation=target_allocation,
            status=PortfolioStatus.PENDING,
            total_invested=initial_investment or Decimal(0)
        )
        
        self.db.add(portfolio)
        self.db.commit()
        
        # Publish event
        await self.kafka_store.append_event(
            entity='ultrawealth',
            event_type='portfolio_created',
            event_data={
                'portfolio_id': portfolio_id,
                'client_id': client_id,
                'portfolio_name': portfolio_name,
                'strategy_type': strategy_type,
                'target_allocation': target_allocation,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
        
        return portfolio
    
    async def get_portfolio(self, portfolio_id: str) -> Optional[WealthPortfolio]:
        """Get portfolio by ID"""
        return self.db.query(WealthPortfolio).filter_by(portfolio_id=portfolio_id).first()
    
    async def get_client_portfolios(self, client_id: str) -> List[WealthPortfolio]:
        """Get all portfolios for a client"""
        return self.db.query(WealthPortfolio).filter_by(client_id=client_id).all()
    
    # ========================================================================
    # INVESTMENT RECOMMENDATIONS
    # ========================================================================
    
    async def get_investment_recommendations(
        self,
        client_id: str,
        portfolio_id: Optional[str] = None
    ) -> Dict:
        """
        Get AI-powered investment recommendations
        
        Args:
            client_id: Client ID
            portfolio_id: Optional portfolio ID
            
        Returns:
            Dict: Investment recommendations
        """
        
        wealth_client = self.db.query(WealthClient).filter_by(client_id=client_id).first()
        if not wealth_client:
            raise ValueError(f"Wealth client {client_id} not found")
        
        # Get recommendations from advisory service
        recommendations = await self.advisory_service.generate_recommendations(
            risk_profile=wealth_client.risk_profile.value,
            investment_goals=wealth_client.investment_goals,
            time_horizon_years=wealth_client.time_horizon_years
        )
        
        return recommendations
    
    # ========================================================================
    # ORDER EXECUTION
    # ========================================================================
    
    async def execute_trade(
        self,
        portfolio_id: str,
        ticker: str,
        order_type: str,
        quantity: Decimal,
        order_price: Optional[Decimal] = None
    ) -> WealthOrder:
        """
        Execute a trade order
        
        Args:
            portfolio_id: Portfolio ID
            ticker: ETF ticker
            order_type: Order type (buy/sell)
            quantity: Quantity to trade
            order_price: Limit price (None for market order)
            
        Returns:
            WealthOrder: Created order
        """
        
        # Validate portfolio
        portfolio = await self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Validate ticker
        etf_info = self.etf_universe.get_etf_info(ticker)
        if not etf_info:
            raise ValueError(f"ETF {ticker} not found in universe")
        
        # Create order
        order = await self.order_service.create_order(
            portfolio_id=portfolio_id,
            ticker=ticker,
            order_type=order_type,
            quantity=quantity,
            order_price=order_price
        )
        
        return order
    
    # ========================================================================
    # PORTFOLIO REBALANCING
    # ========================================================================
    
    async def rebalance_portfolio(
        self,
        portfolio_id: str,
        trigger_reason: str = "scheduled"
    ) -> WealthRebalance:
        """
        Rebalance portfolio to target allocation
        
        Args:
            portfolio_id: Portfolio ID
            trigger_reason: Reason for rebalancing
            
        Returns:
            WealthRebalance: Rebalancing record
        """
        
        return await self.portfolio_service.rebalance_portfolio(
            portfolio_id=portfolio_id,
            trigger_reason=trigger_reason
        )
    
    # ========================================================================
    # COMPLIANCE & REPORTING
    # ========================================================================
    
    async def generate_soa(
        self,
        client_id: str,
        portfolio_id: str,
        soa_type: str = "initial",
        advisor_id: str = "ADV-001",
        advisor_name: str = "UltraWealth Advisory"
    ) -> WealthSOA:
        """
        Generate Statement of Advice
        
        Args:
            client_id: Client ID
            portfolio_id: Portfolio ID
            soa_type: SOA type (initial, review, variation)
            advisor_id: Advisor ID
            advisor_name: Advisor name
            
        Returns:
            WealthSOA: Generated SOA
        """
        
        return await self.compliance_service.generate_soa(
            client_id=client_id,
            portfolio_id=portfolio_id,
            soa_type=soa_type,
            advisor_id=advisor_id,
            advisor_name=advisor_name
        )
    
    async def generate_performance_report(
        self,
        portfolio_id: str,
        period_days: int = 90
    ) -> Dict:
        """Generate portfolio performance report"""
        
        return await self.portfolio_service.generate_performance_report(
            portfolio_id=portfolio_id,
            period_days=period_days
        )
    
    # ========================================================================
    # ETF DATA & PREDICTIONS
    # ========================================================================
    
    async def get_etf_price(self, ticker: str) -> Dict:
        """Get current ETF price"""
        return await self.etf_service.get_etf_price(ticker)
    
    async def get_etf_prediction(self, ticker: str) -> Dict:
        """Get ML price prediction for ETF"""
        return await self.etf_service.get_etf_prediction(ticker)
    
    def get_etf_universe(self) -> Dict:
        """Get complete Australian ETF universe"""
        return self.etf_service.get_universe_summary()

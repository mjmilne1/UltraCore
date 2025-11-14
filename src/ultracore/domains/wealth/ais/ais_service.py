"""Automated Investment Service (AIS) - AI Portfolio Management"""
from typing import Dict, List
from decimal import Decimal
from datetime import datetime, date
import uuid

from ultracore.infrastructure.event_store import EventStore
from ultracore.infrastructure.kafka_event_store import KafkaEventStore
from ..events import PortfolioCreatedEvent, RebalancedEvent
from ..models import Portfolio, RiskTolerance, InvestmentStrategy
from ..integration import UltraOptimiserAdapter


class AutomatedInvestmentService:
    """
    Automated Investment Service (AIS) - AI-powered portfolio management.
    
    Replaces traditional "robo-advisory" with professional terminology.
    
    Features:
    - Risk profiling
    - Automated portfolio construction
    - Continuous monitoring
    - Automatic rebalancing
    - Tax-aware optimization
    - UltraOptimiser integration
    
    Australian Context:
    - ASIC guidance on automated advice
    - Appropriate advice requirements
    - Best interest duty
    - Fee disclosure
    
    Brand: AIS (Automated Investment Service)
    """
    
    def __init__(
        self,
        event_store: EventStore,
        kafka_producer: KafkaEventStore,
        optimiser_adapter: UltraOptimiserAdapter
    ):
        self.event_store = event_store
        self.kafka = kafka_producer
        self.optimiser = optimiser_adapter
    
    async def create_ais_portfolio(
        self,
        customer_id: str,
        portfolio_name: str,
        risk_tolerance: RiskTolerance,
        time_horizon_years: int,
        investment_objective: str,
        initial_investment: Decimal,
        cash_account_id: str,
        **kwargs
    ) -> Dict:
        """
        Create AIS-managed portfolio.
        
        Process:
        1. Risk profiling
        2. Asset allocation using UltraOptimiser
        3. Portfolio construction
        4. Initial investment
        5. Ongoing monitoring
        """
        
        portfolio_id = f"PORT-{uuid.uuid4().hex[:12].upper()}"
        
        # Map risk tolerance to investment strategy
        strategy_mapping = {
            RiskTolerance.LOW: InvestmentStrategy.CONSERVATIVE,
            RiskTolerance.MEDIUM: InvestmentStrategy.BALANCED,
            RiskTolerance.HIGH: InvestmentStrategy.GROWTH
        }
        
        investment_strategy = strategy_mapping.get(
            risk_tolerance,
            InvestmentStrategy.BALANCED
        )
        
        # Get optimal allocation from UltraOptimiser
        optimization = await self.optimiser.optimize_portfolio(
            risk_tolerance=risk_tolerance.value,
            time_horizon_years=time_horizon_years,
            current_holdings={},
            available_cash=initial_investment
        )
        
        # Create portfolio
        event = PortfolioCreatedEvent(
            aggregate_id=portfolio_id,
            portfolio_id=portfolio_id,
            customer_id=customer_id,
            portfolio_name=portfolio_name,
            portfolio_type="balanced",
            investment_strategy=investment_strategy.value,
            risk_tolerance=risk_tolerance.value,
            time_horizon_years=time_horizon_years,
            investment_objective=investment_objective,
            cash_account_id=cash_account_id,
            robo_managed=True,  # Technical flag, still "AIS-managed" in user-facing
            auto_rebalance=True,
            created_at=datetime.now(timezone.utc),
            created_by="ais"  # Automated Investment Service
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "portfolio_id": portfolio_id,
            "risk_profile": {
                "risk_tolerance": risk_tolerance.value,
                "investment_strategy": investment_strategy.value,
                "time_horizon": f"{time_horizon_years} years"
            },
            "target_allocation": optimization["target_allocation"],
            "expected_return": f"{optimization['expected_return']:.2f}% p.a.",
            "sharpe_ratio": optimization["sharpe_ratio"],
            "ais_features": {
                "auto_rebalance": True,
                "tax_optimization": True,
                "dividend_reinvestment": True,
                "continuous_monitoring": True,
                "ai_powered": "UltraOptimiser + ML allocation"
            },
            "message": "AIS-managed portfolio created successfully!"
        }
    
    async def monitor_and_rebalance(
        self,
        portfolio_id: str,
        portfolio: Portfolio,
        threshold: Decimal = Decimal("0.05")
    ) -> Dict:
        """
        Monitor portfolio and rebalance if needed.
        
        Triggers:
        - Allocation drift > threshold (5%)
        - Quarterly review
        - Market volatility events
        """
        
        # Check if rebalancing needed
        rebalance_check = await self.optimiser.check_rebalancing_needed(
            current_allocation=portfolio.current_allocation,
            target_allocation=portfolio.target_allocation,
            threshold=threshold
        )
        
        if not rebalance_check["needs_rebalancing"]:
            return {
                "action": "no_action",
                "message": "Portfolio within target allocation"
            }
        
        # Get new optimal allocation
        optimization = await self.optimiser.optimize_portfolio(
            risk_tolerance=portfolio.risk_tolerance.value,
            time_horizon_years=portfolio.time_horizon_years,
            current_holdings={
                h.security_code: h.market_value
                for h in portfolio.holdings
            },
            available_cash=portfolio.cash_balance
        )
        
        # Execute rebalancing
        event = RebalancedEvent(
            aggregate_id=portfolio_id,
            portfolio_id=portfolio_id,
            customer_id=portfolio.customer_id,
            reason="drift",
            previous_allocation=portfolio.current_allocation,
            target_allocation=optimization["target_allocation"],
            new_allocation=optimization["target_allocation"],
            trades=optimization["recommended_trades"],
            total_brokerage=Decimal("0.00"),  # Would calculate
            rebalanced_at=datetime.now(timezone.utc),
            rebalanced_by="ais"  # Automated Investment Service
        )
        
        await self.kafka.publish(event)
        await self.event_store.append_event(event)
        
        return {
            "action": "rebalanced",
            "trades_executed": len(optimization["recommended_trades"]),
            "new_allocation": optimization["target_allocation"],
            "expected_improvement": f"{optimization['expected_return']:.2f}% p.a.",
            "message": "Portfolio rebalanced automatically by AIS"
        }
    
    async def assess_risk_profile(
        self,
        questionnaire_responses: Dict
    ) -> Dict:
        """
        Assess customer risk profile from questionnaire.
        
        Australian Appropriate Advice:
        - Investment objectives
        - Financial situation
        - Risk tolerance
        - Time horizon
        """
        
        # Simple scoring model (would be more sophisticated)
        score = 0
        
        # Age (younger = higher risk tolerance)
        age = questionnaire_responses.get("age", 40)
        if age < 35:
            score += 3
        elif age < 50:
            score += 2
        else:
            score += 1
        
        # Investment experience
        experience = questionnaire_responses.get("investment_experience", "none")
        if experience == "extensive":
            score += 3
        elif experience == "moderate":
            score += 2
        else:
            score += 1
        
        # Risk comfort
        risk_comfort = questionnaire_responses.get("risk_comfort", "low")
        if risk_comfort == "high":
            score += 3
        elif risk_comfort == "medium":
            score += 2
        else:
            score += 1
        
        # Time horizon
        time_horizon = questionnaire_responses.get("time_horizon_years", 5)
        if time_horizon > 10:
            score += 3
        elif time_horizon > 5:
            score += 2
        else:
            score += 1
        
        # Determine risk tolerance
        if score >= 10:
            risk_tolerance = "high"
            investment_strategy = "growth"
        elif score >= 7:
            risk_tolerance = "medium"
            investment_strategy = "balanced"
        else:
            risk_tolerance = "low"
            investment_strategy = "conservative"
        
        return {
            "risk_tolerance": risk_tolerance,
            "investment_strategy": investment_strategy,
            "risk_score": score,
            "recommended_allocation": self._get_model_allocation(investment_strategy)
        }
    
    def _get_model_allocation(self, strategy: str) -> Dict[str, float]:
        """Get model portfolio allocation for strategy."""
        
        allocations = {
            "conservative": {
                "australian_shares": 20.0,
                "international_shares": 10.0,
                "property": 10.0,
                "fixed_income": 40.0,
                "cash": 20.0
            },
            "balanced": {
                "australian_shares": 35.0,
                "international_shares": 25.0,
                "property": 10.0,
                "fixed_income": 20.0,
                "cash": 10.0
            },
            "growth": {
                "australian_shares": 45.0,
                "international_shares": 35.0,
                "property": 10.0,
                "fixed_income": 5.0,
                "cash": 5.0
            }
        }
        
        return allocations.get(strategy, allocations["balanced"])

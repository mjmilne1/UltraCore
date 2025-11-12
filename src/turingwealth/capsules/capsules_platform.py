"""
TuringWealth Capsules - Investment Goal Containers
Data Mesh + ML + Agentic AI + MCP Architecture
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import asyncio
import uuid
import json

# Kafka-First Architecture for TuringWealth
class TuringKafkaStream:
    """All capsule events through Kafka first"""
    
    def __init__(self):
        self.topics = {
            'capsule_created': 'turingwealth.capsules.created',
            'capsule_funded': 'turingwealth.capsules.funded',
            'capsule_rebalanced': 'turingwealth.capsules.rebalanced',
            'capsule_goal_met': 'turingwealth.capsules.goal_met',
            'capsule_ml_optimized': 'turingwealth.capsules.ml_optimized'
        }
    
    async def write_capsule_event(self, event: Dict, event_type: str) -> str:
        """Write to Kafka FIRST (mandatory)"""
        event_id = str(uuid.uuid4())
        kafka_event = {
            'event_id': event_id,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'capsule_data': event
        }
        # In production: write to actual Kafka
        return event_id

# Capsule Types
class CapsuleType(Enum):
    RETIREMENT = "retirement"
    HOUSE_DEPOSIT = "house_deposit"
    EDUCATION = "education"
    WEALTH_BUILDING = "wealth_building"
    EMERGENCY_FUND = "emergency"
    TRAVEL = "travel"
    CUSTOM = "custom"

@dataclass
class InvestmentCapsule:
    """Core Capsule Structure"""
    capsule_id: str
    customer_id: str
    capsule_type: CapsuleType
    goal_amount: Decimal
    target_date: datetime
    risk_tolerance: str  # conservative, moderate, aggressive
    current_value: Decimal
    asset_allocation: Dict[str, float]
    ml_optimization_score: float
    auto_rebalance: bool
    status: str  # active, paused, completed

# Data Mesh for Capsules
class CapsulesDataMesh:
    """Capsules domain in Data Mesh"""
    
    def __init__(self):
        self.domain = "investment_capsules"
        self.data_products = {
            
            "capsule_portfolio": {
                "product_id": "dp_capsule_portfolios",
                "owner": "wealth_team",
                "description": "All active investment capsules with ML optimization",
                "schema": {
                    "capsule_id": "string",
                    "customer_id": "string",
                    "capsule_type": "enum",
                    "goal_amount": "decimal",
                    "current_value": "decimal",
                    "progress_percent": "float",
                    "expected_return": "float",
                    "risk_score": "float",
                    "optimization_score": "float"
                },
                "quality_sla": {
                    "freshness_seconds": 60,
                    "completeness": 0.999,
                    "accuracy": 0.98
                }
            },
            
            "capsule_performance": {
                "product_id": "dp_capsule_performance",
                "owner": "analytics_team",
                "description": "Capsule performance metrics and ML predictions",
                "schema": {
                    "capsule_id": "string",
                    "daily_return": "float",
                    "volatility": "float",
                    "sharpe_ratio": "float",
                    "goal_probability": "float",
                    "days_to_goal": "integer",
                    "recommended_actions": "array"
                },
                "quality_sla": {
                    "calculation_accuracy": 0.95,
                    "update_frequency_minutes": 15
                }
            },
            
            "capsule_recommendations": {
                "product_id": "dp_capsule_recommendations",
                "owner": "ml_team",
                "description": "ML-generated capsule recommendations",
                "schema": {
                    "customer_id": "string",
                    "recommended_capsules": "array",
                    "personalization_score": "float",
                    "expected_outcomes": "json"
                },
                "quality_sla": {
                    "model_accuracy": 0.88,
                    "recommendation_relevance": 0.85
                }
            }
        }

# ML Models for Capsule Optimization
class CapsuleOptimizationML:
    """ML models for capsule portfolio optimization"""
    
    def __init__(self):
        self.models = {
            'portfolio_optimizer': self.load_portfolio_model(),
            'goal_predictor': self.load_goal_prediction_model(),
            'risk_assessor': self.load_risk_model()
        }
    
    def load_portfolio_model(self):
        """Load portfolio optimization model"""
        return {"type": "markowitz", "enhanced": True}
    
    def load_goal_prediction_model(self):
        """Load goal achievement prediction model"""
        return {"type": "monte_carlo", "simulations": 10000}
    
    def load_risk_model(self):
        """Load risk assessment model"""
        return {"type": "var_cvar", "confidence": 0.95}
    
    async def optimize_capsule_allocation(self, capsule: InvestmentCapsule) -> Dict:
        """ML optimization for capsule asset allocation"""
        
        # Calculate optimal allocation based on goal
        time_to_goal = (capsule.target_date - datetime.now()).days / 365
        risk_profile = self.get_risk_profile(capsule.risk_tolerance, time_to_goal)
        
        # Markowitz optimization
        optimal_allocation = await self.markowitz_optimization(
            risk_profile,
            time_to_goal,
            capsule.goal_amount,
            capsule.current_value
        )
        
        # Monte Carlo simulation for goal probability
        goal_probability = await self.simulate_goal_achievement(
            capsule.current_value,
            capsule.goal_amount,
            optimal_allocation,
            time_to_goal
        )
        
        # Risk metrics
        risk_metrics = await self.calculate_risk_metrics(optimal_allocation)
        
        return {
            "optimal_allocation": optimal_allocation,
            "expected_return": self.calculate_expected_return(optimal_allocation),
            "goal_probability": goal_probability,
            "risk_metrics": risk_metrics,
            "rebalance_required": self.needs_rebalancing(
                capsule.asset_allocation,
                optimal_allocation
            )
        }
    
    def get_risk_profile(self, risk_tolerance: str, time_horizon: float) -> Dict:
        """Determine risk profile based on tolerance and time"""
        
        base_profiles = {
            "conservative": {"equity": 0.3, "bonds": 0.6, "cash": 0.1},
            "moderate": {"equity": 0.6, "bonds": 0.35, "cash": 0.05},
            "aggressive": {"equity": 0.85, "bonds": 0.13, "cash": 0.02}
        }
        
        profile = base_profiles.get(risk_tolerance, base_profiles["moderate"])
        
        # Adjust for time horizon
        if time_horizon < 2:
            # Short term - more conservative
            profile["cash"] += 0.2
            profile["equity"] -= 0.2
        elif time_horizon > 10:
            # Long term - can be more aggressive
            profile["equity"] += 0.1
            profile["bonds"] -= 0.1
        
        return profile
    
    async def markowitz_optimization(self, risk_profile: Dict,
                                    time_horizon: float,
                                    goal_amount: Decimal,
                                    current_value: Decimal) -> Dict:
        """Markowitz mean-variance optimization"""
        
        # Simplified optimization
        # In production, use scipy.optimize
        
        # Asset classes
        assets = {
            "ASX200": {"return": 0.089, "vol": 0.15, "type": "equity"},
            "US_STOCKS": {"return": 0.105, "vol": 0.18, "type": "equity"},
            "INT_STOCKS": {"return": 0.082, "vol": 0.20, "type": "equity"},
            "AU_BONDS": {"return": 0.035, "vol": 0.05, "type": "bonds"},
            "GLOBAL_BONDS": {"return": 0.042, "vol": 0.07, "type": "bonds"},
            "CASH": {"return": 0.025, "vol": 0.01, "type": "cash"},
            "ALTERNATIVES": {"return": 0.075, "vol": 0.12, "type": "alternatives"}
        }
        
        # Build allocation
        allocation = {}
        remaining = 1.0
        
        for asset, details in assets.items():
            if details["type"] == "equity" and risk_profile["equity"] > 0:
                weight = risk_profile["equity"] / 3  # Split equally
                allocation[asset] = min(weight, remaining)
                remaining -= allocation[asset]
            elif details["type"] == "bonds" and risk_profile["bonds"] > 0:
                weight = risk_profile["bonds"] / 2
                allocation[asset] = min(weight, remaining)
                remaining -= allocation[asset]
            elif details["type"] == "cash":
                allocation[asset] = risk_profile["cash"]
        
        return allocation
    
    async def simulate_goal_achievement(self, current: Decimal,
                                       goal: Decimal,
                                       allocation: Dict,
                                       years: float) -> float:
        """Monte Carlo simulation for goal achievement probability"""
        
        # Simplified Monte Carlo
        simulations = 1000
        successful = 0
        
        for _ in range(simulations):
            value = float(current)
            
            # Simulate each year
            for year in range(int(years)):
                # Calculate portfolio return with randomness
                portfolio_return = 0
                for asset, weight in allocation.items():
                    # Random return based on historical stats
                    asset_return = np.random.normal(0.08, 0.15)  # Simplified
                    portfolio_return += weight * asset_return
                
                value *= (1 + portfolio_return)
            
            if value >= float(goal):
                successful += 1
        
        return successful / simulations
    
    async def calculate_risk_metrics(self, allocation: Dict) -> Dict:
        """Calculate risk metrics for allocation"""
        
        # Portfolio statistics
        portfolio_return = self.calculate_expected_return(allocation)
        portfolio_vol = 0.12  # Simplified calculation
        
        # Value at Risk (95% confidence)
        var_95 = portfolio_return - 1.645 * portfolio_vol
        
        # Conditional VaR
        cvar_95 = portfolio_return - 2.063 * portfolio_vol
        
        # Sharpe ratio (risk-free rate = 2.5%)
        sharpe = (portfolio_return - 0.025) / portfolio_vol if portfolio_vol > 0 else 0
        
        return {
            "expected_return": portfolio_return,
            "volatility": portfolio_vol,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "sharpe_ratio": sharpe,
            "max_drawdown": -0.15  # Historical estimate
        }
    
    def calculate_expected_return(self, allocation: Dict) -> float:
        """Calculate expected return for allocation"""
        
        # Asset class returns (simplified)
        returns = {
            "ASX200": 0.089,
            "US_STOCKS": 0.105,
            "INT_STOCKS": 0.082,
            "AU_BONDS": 0.035,
            "GLOBAL_BONDS": 0.042,
            "CASH": 0.025,
            "ALTERNATIVES": 0.075
        }
        
        portfolio_return = 0
        for asset, weight in allocation.items():
            portfolio_return += weight * returns.get(asset, 0.05)
        
        return portfolio_return
    
    def needs_rebalancing(self, current: Dict, target: Dict,
                         threshold: float = 0.05) -> bool:
        """Check if rebalancing is needed"""
        
        for asset in target:
            current_weight = current.get(asset, 0)
            target_weight = target.get(asset, 0)
            
            if abs(current_weight - target_weight) > threshold:
                return True
        
        return False

# Agentic AI for Capsule Management
class CapsuleAgents:
    """Autonomous agents for capsule management"""
    
    def __init__(self):
        self.ml_optimizer = CapsuleOptimizationML()
        self.kafka_stream = TuringKafkaStream()
    
    async def capsule_creation_agent(self, customer_profile: Dict,
                                    goal: Dict) -> InvestmentCapsule:
        """Agent to create personalized capsule"""
        
        # Analyze customer profile
        risk_tolerance = self.assess_risk_tolerance(customer_profile)
        
        # Determine capsule type
        capsule_type = self.determine_capsule_type(goal)
        
        # Calculate initial allocation
        initial_allocation = await self.ml_optimizer.markowitz_optimization(
            self.ml_optimizer.get_risk_profile(risk_tolerance, goal.get("years", 5)),
            goal.get("years", 5),
            Decimal(str(goal.get("target_amount", 10000))),
            Decimal(str(goal.get("initial_deposit", 1000)))
        )
        
        # Create capsule
        capsule = InvestmentCapsule(
            capsule_id=f"CAP_{uuid.uuid4().hex[:8]}",
            customer_id=customer_profile.get("customer_id"),
            capsule_type=capsule_type,
            goal_amount=Decimal(str(goal.get("target_amount", 10000))),
            target_date=datetime.now() + timedelta(days=365 * goal.get("years", 5)),
            risk_tolerance=risk_tolerance,
            current_value=Decimal(str(goal.get("initial_deposit", 1000))),
            asset_allocation=initial_allocation,
            ml_optimization_score=0.0,
            auto_rebalance=True,
            status="active"
        )
        
        # Write to Kafka
        await self.kafka_stream.write_capsule_event(
            {
                "capsule_id": capsule.capsule_id,
                "customer_id": capsule.customer_id,
                "type": capsule.capsule_type.value,
                "goal": float(capsule.goal_amount)
            },
            "capsule_created"
        )
        
        return capsule
    
    async def rebalancing_agent(self, capsule: InvestmentCapsule) -> Dict:
        """Agent to handle automatic rebalancing"""
        
        # Get ML optimization
        optimization = await self.ml_optimizer.optimize_capsule_allocation(capsule)
        
        if optimization["rebalance_required"]:
            # Execute rebalancing
            trades = self.calculate_rebalancing_trades(
                capsule.asset_allocation,
                optimization["optimal_allocation"],
                capsule.current_value
            )
            
            # Update capsule
            capsule.asset_allocation = optimization["optimal_allocation"]
            capsule.ml_optimization_score = optimization["goal_probability"]
            
            # Write to Kafka
            await self.kafka_stream.write_capsule_event(
                {
                    "capsule_id": capsule.capsule_id,
                    "new_allocation": optimization["optimal_allocation"],
                    "trades": trades
                },
                "capsule_rebalanced"
            )
            
            return {
                "rebalanced": True,
                "trades": trades,
                "new_allocation": optimization["optimal_allocation"],
                "goal_probability": optimization["goal_probability"]
            }
        
        return {"rebalanced": False, "reason": "Within threshold"}
    
    async def monitoring_agent(self, capsule: InvestmentCapsule) -> Dict:
        """Agent to monitor capsule progress"""
        
        # Calculate progress
        progress = float(capsule.current_value / capsule.goal_amount)
        
        # Time analysis
        days_elapsed = (datetime.now() - datetime.now()).days  # Would use creation date
        days_remaining = (capsule.target_date - datetime.now()).days
        time_progress = days_elapsed / (days_elapsed + days_remaining) if days_remaining > 0 else 1
        
        # Performance analysis
        on_track = progress >= time_progress * 0.9  # 90% of expected progress
        
        # ML prediction update
        optimization = await self.ml_optimizer.optimize_capsule_allocation(capsule)
        
        # Generate insights
        insights = []
        
        if not on_track:
            insights.append({
                "type": "warning",
                "message": "Behind schedule for goal",
                "action": "Consider increasing contributions"
            })
        
        if optimization["goal_probability"] < 0.7:
            insights.append({
                "type": "recommendation",
                "message": f"Goal achievement probability: {optimization['goal_probability']:.1%}",
                "action": "Review risk tolerance or extend timeline"
            })
        
        return {
            "progress_percent": progress * 100,
            "on_track": on_track,
            "goal_probability": optimization["goal_probability"],
            "days_remaining": days_remaining,
            "insights": insights,
            "recommended_monthly_contribution": self.calculate_required_contribution(
                capsule.current_value,
                capsule.goal_amount,
                days_remaining / 30
            )
        }
    
    def assess_risk_tolerance(self, profile: Dict) -> str:
        """Assess customer risk tolerance"""
        
        age = profile.get("age", 35)
        income = profile.get("annual_income", 60000)
        investment_experience = profile.get("experience_years", 0)
        
        score = 0
        
        # Age factor
        if age < 30:
            score += 3
        elif age < 45:
            score += 2
        elif age < 60:
            score += 1
        
        # Income factor
        if income > 100000:
            score += 2
        elif income > 70000:
            score += 1
        
        # Experience factor
        if investment_experience > 5:
            score += 2
        elif investment_experience > 2:
            score += 1
        
        # Determine tolerance
        if score >= 5:
            return "aggressive"
        elif score >= 3:
            return "moderate"
        else:
            return "conservative"
    
    def determine_capsule_type(self, goal: Dict) -> CapsuleType:
        """Determine appropriate capsule type"""
        
        purpose = goal.get("purpose", "").lower()
        
        if "retire" in purpose:
            return CapsuleType.RETIREMENT
        elif "house" in purpose or "property" in purpose:
            return CapsuleType.HOUSE_DEPOSIT
        elif "education" in purpose or "university" in purpose:
            return CapsuleType.EDUCATION
        elif "emergency" in purpose:
            return CapsuleType.EMERGENCY_FUND
        elif "travel" in purpose or "holiday" in purpose:
            return CapsuleType.TRAVEL
        elif "wealth" in purpose:
            return CapsuleType.WEALTH_BUILDING
        else:
            return CapsuleType.CUSTOM
    
    def calculate_rebalancing_trades(self, current: Dict,
                                    target: Dict,
                                    value: Decimal) -> List[Dict]:
        """Calculate trades needed for rebalancing"""
        
        trades = []
        
        for asset in set(list(current.keys()) + list(target.keys())):
            current_weight = current.get(asset, 0)
            target_weight = target.get(asset, 0)
            
            current_value = float(value) * current_weight
            target_value = float(value) * target_weight
            
            diff = target_value - current_value
            
            if abs(diff) > 100:  # Minimum trade size
                trades.append({
                    "asset": asset,
                    "action": "BUY" if diff > 0 else "SELL",
                    "amount": abs(diff)
                })
        
        return trades
    
    def calculate_required_contribution(self, current: Decimal,
                                      goal: Decimal,
                                      months: float) -> float:
        """Calculate required monthly contribution"""
        
        if months <= 0:
            return 0
        
        gap = float(goal - current)
        
        # Simple calculation (without considering returns)
        return max(0, gap / months)

# MCP Tools for Capsules
class CapsuleMCPTools:
    """Model Context Protocol tools for capsules"""
    
    def __init__(self):
        self.agents = CapsuleAgents()
        self.tools = self.register_capsule_tools()
    
    def register_capsule_tools(self) -> Dict:
        """Register MCP tools for capsule operations"""
        
        return {
            "create_capsule": {
                "description": "Create a new investment capsule",
                "parameters": {
                    "customer_id": "string",
                    "goal_type": "string",
                    "target_amount": "number",
                    "target_years": "number",
                    "initial_deposit": "number"
                },
                "handler": self.create_capsule_handler
            },
            
            "get_capsule_status": {
                "description": "Get capsule progress and status",
                "parameters": {
                    "capsule_id": "string"
                },
                "handler": self.get_status_handler
            },
            
            "add_to_capsule": {
                "description": "Add funds to capsule",
                "parameters": {
                    "capsule_id": "string",
                    "amount": "number"
                },
                "handler": self.add_funds_handler
            },
            
            "optimize_capsule": {
                "description": "Run ML optimization on capsule",
                "parameters": {
                    "capsule_id": "string"
                },
                "handler": self.optimize_handler
            },
            
            "get_recommendations": {
                "description": "Get AI recommendations for capsules",
                "parameters": {
                    "customer_id": "string"
                },
                "handler": self.get_recommendations_handler
            },
            
            "simulate_scenario": {
                "description": "Simulate different scenarios",
                "parameters": {
                    "capsule_id": "string",
                    "scenario": "object"
                },
                "handler": self.simulate_handler
            }
        }
    
    async def create_capsule_handler(self, params: Dict) -> Dict:
        """Handle capsule creation via MCP"""
        
        customer_profile = {
            "customer_id": params["customer_id"],
            "age": 35,  # Would fetch from profile
            "annual_income": 75000,
            "experience_years": 3
        }
        
        goal = {
            "purpose": params["goal_type"],
            "target_amount": params["target_amount"],
            "years": params["target_years"],
            "initial_deposit": params["initial_deposit"]
        }
        
        capsule = await self.agents.capsule_creation_agent(customer_profile, goal)
        
        return {
            "capsule_id": capsule.capsule_id,
            "status": "created",
            "allocation": capsule.asset_allocation,
            "goal_probability": capsule.ml_optimization_score
        }
    
    async def get_status_handler(self, params: Dict) -> Dict:
        """Get capsule status via MCP"""
        
        # Would fetch actual capsule
        capsule = InvestmentCapsule(
            capsule_id=params["capsule_id"],
            customer_id="CUST_001",
            capsule_type=CapsuleType.RETIREMENT,
            goal_amount=Decimal("100000"),
            target_date=datetime.now() + timedelta(days=3650),
            risk_tolerance="moderate",
            current_value=Decimal("25000"),
            asset_allocation={},
            ml_optimization_score=0.75,
            auto_rebalance=True,
            status="active"
        )
        
        status = await self.agents.monitoring_agent(capsule)
        
        return status
    
    async def add_funds_handler(self, params: Dict) -> Dict:
        """Add funds to capsule via MCP"""
        
        return {
            "capsule_id": params["capsule_id"],
            "amount_added": params["amount"],
            "new_balance": 25000 + params["amount"],
            "status": "funded"
        }
    
    async def optimize_handler(self, params: Dict) -> Dict:
        """Optimize capsule via MCP"""
        
        # Would fetch actual capsule
        ml_optimizer = CapsuleOptimizationML()
        
        # Mock optimization
        optimization = {
            "optimal_allocation": {
                "ASX200": 0.35,
                "US_STOCKS": 0.25,
                "AU_BONDS": 0.30,
                "CASH": 0.10
            },
            "expected_return": 0.078,
            "goal_probability": 0.82,
            "risk_metrics": {
                "volatility": 0.12,
                "sharpe_ratio": 1.2
            }
        }
        
        return optimization
    
    async def get_recommendations_handler(self, params: Dict) -> Dict:
        """Get recommendations via MCP"""
        
        return {
            "customer_id": params["customer_id"],
            "recommendations": [
                {
                    "capsule_type": "RETIREMENT",
                    "reason": "Start early for compound growth",
                    "suggested_amount": 500,
                    "expected_outcome": "1.2M by age 65"
                },
                {
                    "capsule_type": "EMERGENCY_FUND",
                    "reason": "Financial security foundation",
                    "suggested_amount": 300,
                    "expected_outcome": "6 months expenses in 2 years"
                }
            ]
        }
    
    async def simulate_handler(self, params: Dict) -> Dict:
        """Simulate scenarios via MCP"""
        
        scenario = params.get("scenario", {})
        
        # Run simulation
        return {
            "capsule_id": params["capsule_id"],
            "scenario": scenario,
            "outcome": {
                "final_value": 125000,
                "goal_achieved": True,
                "probability": 0.85
            }
        }

# Main TuringWealth Capsules Platform
class TuringWealthCapsules:
    """Complete TuringWealth Capsules Platform"""
    
    def __init__(self):
        self.data_mesh = CapsulesDataMesh()
        self.ml_optimizer = CapsuleOptimizationML()
        self.agents = CapsuleAgents()
        self.mcp_tools = CapsuleMCPTools()
        self.kafka_stream = TuringKafkaStream()
    
    async def create_capsule(self, customer_id: str, goal: Dict) -> Dict:
        """Create a new investment capsule"""
        
        # Get customer profile (would fetch from DB)
        customer_profile = {
            "customer_id": customer_id,
            "age": 35,
            "annual_income": 75000,
            "experience_years": 3
        }
        
        # Create capsule through agent
        capsule = await self.agents.capsule_creation_agent(customer_profile, goal)
        
        # Run initial ML optimization
        optimization = await self.ml_optimizer.optimize_capsule_allocation(capsule)
        
        # Update data mesh
        await self.update_data_products(capsule, optimization)
        
        return {
            "capsule": capsule,
            "optimization": optimization,
            "status": "active"
        }
    
    async def update_data_products(self, capsule: InvestmentCapsule,
                                  optimization: Dict):
        """Update data mesh products"""
        
        # Update capsule portfolio data product
        portfolio_data = {
            "capsule_id": capsule.capsule_id,
            "customer_id": capsule.customer_id,
            "capsule_type": capsule.capsule_type.value,
            "goal_amount": float(capsule.goal_amount),
            "current_value": float(capsule.current_value),
            "progress_percent": float(capsule.current_value / capsule.goal_amount * 100),
            "expected_return": optimization["expected_return"],
            "optimization_score": optimization["goal_probability"]
        }
        
        # Write to Kafka
        await self.kafka_stream.write_capsule_event(
            portfolio_data,
            "data_product_update"
        )
